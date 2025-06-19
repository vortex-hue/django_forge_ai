"""
Custom model fields for AI-powered functionality.
"""
from django.db import models
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from typing import Optional, Dict, Any
import json

from .utils.llm_client import get_llm_client
from .utils.validation import ModerationResult


class AICharField(models.CharField):
    """
    A CharField that can automatically generate content using an LLM.
    
    Usage:
        summary = AICharField(
            max_length=200,
            ai_generate_from=['title', 'content'],
            ai_prompt_template="Generate a summary of: {title} - {content}"
        )
    """
    
    def __init__(
        self,
        *args,
        ai_generate_from: Optional[list] = None,
        ai_prompt_template: Optional[str] = None,
        ai_auto_generate: bool = False,
        **kwargs
    ):
        """
        Initialize AICharField.
        
        Args:
            ai_generate_from: List of field names to use as context for generation
            ai_prompt_template: Template string for the generation prompt
            ai_auto_generate: If True, automatically generates on save if field is empty
        """
        self.ai_generate_from = ai_generate_from or []
        self.ai_prompt_template = ai_prompt_template
        self.ai_auto_generate = ai_auto_generate
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance, add):
        """Generate content before saving if needed"""
        value = getattr(model_instance, self.attname)
        
        if self.ai_auto_generate and not value:
            # Generate content if field is empty and auto_generate is enabled
            value = self._generate_content(model_instance)
            setattr(model_instance, self.attname, value)
        
        return value
    
    def _generate_content(self, model_instance) -> str:
        """Generate content using LLM"""
        if not self.ai_prompt_template:
            raise ValueError("ai_prompt_template is required for AI generation")
        
        # Build context from specified fields
        context = {}
        for field_name in self.ai_generate_from:
            if hasattr(model_instance, field_name):
                context[field_name] = str(getattr(model_instance, field_name, ""))
        
        # Format prompt template with context
        try:
            prompt = self.ai_prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context field in prompt template: {e}")
        
        # Generate using LLM
        llm_client = get_llm_client()
        generated = llm_client.generate(
            prompt=prompt,
            max_tokens=self.max_length // 4  # Rough estimate: 1 token ≈ 4 characters
        )
        
        # Truncate to max_length if needed
        if len(generated) > self.max_length:
            generated = generated[:self.max_length]
        
        return generated
    
    def deconstruct(self):
        """Support for migrations"""
        name, path, args, kwargs = super().deconstruct()
        if self.ai_generate_from:
            kwargs['ai_generate_from'] = self.ai_generate_from
        if self.ai_prompt_template:
            kwargs['ai_prompt_template'] = self.ai_prompt_template
        if self.ai_auto_generate:
            kwargs['ai_auto_generate'] = self.ai_auto_generate
        return name, path, args, kwargs


class AITextField(models.TextField):
    """
    A TextField that can automatically generate content using an LLM.
    
    Usage:
        content = AITextField(
            ai_generate_from=['title'],
            ai_prompt_template="Write an article about: {title}"
        )
    """
    
    def __init__(
        self,
        *args,
        ai_generate_from: Optional[list] = None,
        ai_prompt_template: Optional[str] = None,
        ai_auto_generate: bool = False,
        **kwargs
    ):
        """
        Initialize AITextField.
        
        Args:
            ai_generate_from: List of field names to use as context for generation
            ai_prompt_template: Template string for the generation prompt
            ai_auto_generate: If True, automatically generates on save if field is empty
        """
        self.ai_generate_from = ai_generate_from or []
        self.ai_prompt_template = ai_prompt_template
        self.ai_auto_generate = ai_auto_generate
        super().__init__(*args, **kwargs)
    
    def pre_save(self, model_instance, add):
        """Generate content before saving if needed"""
        value = getattr(model_instance, self.attname)
        
        if self.ai_auto_generate and not value:
            value = self._generate_content(model_instance)
            setattr(model_instance, self.attname, value)
        
        return value
    
    def _generate_content(self, model_instance) -> str:
        """Generate content using LLM"""
        if not self.ai_prompt_template:
            raise ValueError("ai_prompt_template is required for AI generation")
        
        # Build context from specified fields
        context = {}
        for field_name in self.ai_generate_from:
            if hasattr(model_instance, field_name):
                context[field_name] = str(getattr(model_instance, field_name, ""))
        
        # Format prompt template with context
        try:
            prompt = self.ai_prompt_template.format(**context)
        except KeyError as e:
            raise ValueError(f"Missing context field in prompt template: {e}")
        
        # Generate using LLM
        llm_client = get_llm_client()
        generated = llm_client.generate(prompt=prompt)
        
        return generated
    
    def deconstruct(self):
        """Support for migrations"""
        name, path, args, kwargs = super().deconstruct()
        if self.ai_generate_from:
            kwargs['ai_generate_from'] = self.ai_generate_from
        if self.ai_prompt_template:
            kwargs['ai_prompt_template'] = self.ai_prompt_template
        if self.ai_auto_generate:
            kwargs['ai_auto_generate'] = self.ai_auto_generate
        return name, path, args, kwargs


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
        """Run moderation before saving"""
        value = getattr(model_instance, self.attname)
        
        if value:
            moderation_result = self._moderate_content(value)
            
            if moderation_result.get("flagged", False):
                if self.raise_on_violation:
                    raise ValidationError(
                        _("Content moderation failed. Content violates policy.")
                    )
                # Store moderation result in a hidden field if available
                if hasattr(model_instance, '_moderation_result'):
                    setattr(model_instance, '_moderation_result', moderation_result)
        
        return value
    
    def _moderate_content(self, text: str) -> Dict[str, Any]:
        """Run content moderation"""
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

