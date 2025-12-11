"""
Custom model fields for AI-powered functionality.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Optional, Dict, Any

from .utils.llm_client import get_llm_client


class BaseAIField:
    """Base class for AI-powered fields with common generation logic."""
    
    def __init__(
        self,
        *args,
        ai_generate_from: Optional[list] = None,
        ai_prompt_template: Optional[str] = None,
        ai_auto_generate: bool = False,
        **kwargs
    ):
        self.ai_generate_from = ai_generate_from or []
        self.ai_prompt_template = ai_prompt_template
        self.ai_auto_generate = ai_auto_generate
        super().__init__(*args, **kwargs)
    
    def _build_context(self, model_instance) -> Dict[str, str]:
        """Build context dictionary from specified fields."""
        context = {}
        for field_name in self.ai_generate_from:
            if hasattr(model_instance, field_name):
                context[field_name] = str(getattr(model_instance, field_name, ""))
        return context
    
    def _format_prompt(self, context: Dict[str, str]) -> str:
        """Format prompt template with context."""
        if not self.ai_prompt_template:
            raise ValueError("ai_prompt_template is required for AI generation")
        
        try:
            return self.ai_prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context field in prompt template: {e}")
    
    def _generate_content(self, model_instance) -> str:
        """Generate content using LLM."""
        context = self._build_context(model_instance)
        prompt = self._format_prompt(context)
        llm_client = get_llm_client()
        
        max_tokens = getattr(self, 'max_length', None)
        if max_tokens:
            max_tokens = max_tokens // 4
        
        generated = llm_client.generate(prompt=prompt, max_tokens=max_tokens)
        
        if hasattr(self, 'max_length') and len(generated) > self.max_length:
            generated = generated[:self.max_length]
        
        return generated
    
    def pre_save(self, model_instance, add):
        """Generate content before saving if needed."""
        value = getattr(model_instance, self.attname)
        
        if self.ai_auto_generate and not value:
            value = self._generate_content(model_instance)
            setattr(model_instance, self.attname, value)
        
        return value
    
    def deconstruct(self):
        """Support for migrations."""
        name, path, args, kwargs = super().deconstruct()
        if self.ai_generate_from:
            kwargs['ai_generate_from'] = self.ai_generate_from
        if self.ai_prompt_template:
            kwargs['ai_prompt_template'] = self.ai_prompt_template
        if self.ai_auto_generate:
            kwargs['ai_auto_generate'] = self.ai_auto_generate
        return name, path, args, kwargs


class AICharField(BaseAIField, models.CharField):
    """
    A CharField that can automatically generate content using an LLM.
    
    Usage:
        summary = AICharField(
            max_length=200,
            ai_generate_from=['title', 'content'],
            ai_prompt_template="Generate a summary of: {title} - {content}"
        )
    """


class AITextField(BaseAIField, models.TextField):
    """
    A TextField that can automatically generate content using an LLM.
    
    Usage:
        content = AITextField(
            ai_generate_from=['title'],
            ai_prompt_template="Write an article about: {title}"
        )
    """


class AIModeratedField(models.TextField):
    """
    A TextField that automatically runs content moderation on save.
    
    Usage:
        content = AIModeratedField(
            moderation_strict=True,
            raise_on_violation=True
        )
    """
    
    def __init__(
        self,
        *args,
        moderation_strict: bool = True,
        raise_on_violation: bool = False,
        **kwargs
    ):
        """
        Initialize AIModeratedField.
        
        Args:
            moderation_strict: If True, uses strict moderation
            raise_on_violation: If True, raises ValidationError on violation
        """
        self.moderation_strict = moderation_strict
        self.raise_on_violation = raise_on_violation
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance, add):
        """Run moderation before saving."""
        value = getattr(model_instance, self.attname)
        
        if not value:
            return value
        
        moderation_result = self._moderate_content(value)
        is_flagged = moderation_result.get("flagged", False)
        
        if is_flagged and self.raise_on_violation:
            raise ValidationError(
                _("Content moderation failed. Content violates policy.")
            )
        
        if is_flagged and hasattr(model_instance, '_moderation_result'):
            setattr(model_instance, '_moderation_result', moderation_result)
        
        return value
    
    def _moderate_content(self, text: str) -> Dict[str, Any]:
        """Run content moderation."""
        llm_client = get_llm_client()
        return llm_client.moderate(text)
    
    def deconstruct(self):
        """Support for migrations"""
        name, path, args, kwargs = super().deconstruct()
        if self.moderation_strict:
            kwargs['moderation_strict'] = self.moderation_strict
        if self.raise_on_violation:
            kwargs['raise_on_violation'] = self.raise_on_violation
        return name, path, args, kwargs

