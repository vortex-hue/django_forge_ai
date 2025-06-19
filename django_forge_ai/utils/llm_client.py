"""
Centralized LLM client for handling API calls to various LLM providers.
"""
import os
from typing import Optional, Dict, Any, List
from enum import Enum

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from django.conf import settings


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """
    Centralized client for interacting with various LLM providers.
    Supports OpenAI and Anthropic APIs.
    """
    
    def __init__(self, provider: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize LLM client.
        
        Args:
            provider: LLM provider name (openai, anthropic). If None, uses settings.
            api_key: API key for the provider. If None, uses settings.
        """
        self.provider = provider or getattr(settings, "DJANGO_FORGE_AI_LLM_PROVIDER", "openai")
        self.api_key = api_key or self._get_api_key()
        self._client = None
        self._initialize_client()
    
    def _get_api_key(self) -> str:
        """Get API key from settings or environment"""
        if self.provider == LLMProvider.OPENAI:
            return getattr(
                settings,
                "DJANGO_FORGE_AI_OPENAI_API_KEY",
                os.getenv("OPENAI_API_KEY", "")
            )
        elif self.provider == LLMProvider.ANTHROPIC:
            return getattr(
                settings,
                "DJANGO_FORGE_AI_ANTHROPIC_API_KEY",
                os.getenv("ANTHROPIC_API_KEY", "")
            )
        return ""
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        if self.provider == LLMProvider.OPENAI:
            if not OPENAI_AVAILABLE:
                raise ImportError("OpenAI package not installed. Install with: pip install openai")
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == LLMProvider.ANTHROPIC:
            if not ANTHROPIC_AVAILABLE:
                raise ImportError("Anthropic package not installed. Install with: pip install anthropic")
            self._client = anthropic.Anthropic(api_key=self.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text using the configured LLM.
        
        Args:
            prompt: The user prompt
            model: Model name (if None, uses default from settings)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0 to 2.0)
            system_prompt: Optional system prompt
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Generated text string
        """
        if self.provider == LLMProvider.OPENAI:
            return self._generate_openai(prompt, model, max_tokens, temperature, system_prompt, **kwargs)
        elif self.provider == LLMProvider.ANTHROPIC:
            return self._generate_anthropic(prompt, model, max_tokens, temperature, system_prompt, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_openai(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: Optional[int],
        temperature: float,
        system_prompt: Optional[str],
        **kwargs
    ) -> str:
        """Generate using OpenAI API"""
        if not model:
            model = getattr(settings, "DJANGO_FORGE_AI_OPENAI_MODEL", "gpt-3.5-turbo")
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens or getattr(settings, "DJANGO_FORGE_AI_MAX_TOKENS", 1000),
            temperature=temperature,
            **kwargs
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_anthropic(
        self,
        prompt: str,
        model: Optional[str],
        max_tokens: Optional[int],
        temperature: float,
        system_prompt: Optional[str],
        **kwargs
    ) -> str:
        """Generate using Anthropic API"""
        if not model:
            model = getattr(settings, "DJANGO_FORGE_AI_ANTHROPIC_MODEL", "claude-3-sonnet-20240229")
        
        message = self._client.messages.create(
            model=model,
            max_tokens=max_tokens or getattr(settings, "DJANGO_FORGE_AI_MAX_TOKENS", 1000),
            temperature=temperature,
            system=system_prompt or "",
            messages=[{"role": "user", "content": prompt}],
            **kwargs
        )
        
        return message.content[0].text.strip()
    
    def moderate(self, text: str) -> Dict[str, Any]:
        """
        Check if text violates content moderation policies.
        
        Args:
            text: Text to moderate
        
        Returns:
            Dictionary with moderation results including 'flagged' boolean
        """
        # Use OpenAI moderation API if available
        if self.provider == LLMProvider.OPENAI and OPENAI_AVAILABLE:
            try:
                response = self._client.moderations.create(input=text)
                result = response.results[0]
                return {
                    "flagged": result.flagged,
                    "categories": result.categories.model_dump() if hasattr(result.categories, 'model_dump') else {},
                    "category_scores": result.category_scores.model_dump() if hasattr(result.category_scores, 'model_dump') else {},
                }
            except Exception as e:
                # Fallback to basic keyword check
                return self._basic_moderation(text)
        
        # Fallback to basic moderation
        return self._basic_moderation(text)
    
    def _basic_moderation(self, text: str) -> Dict[str, Any]:
        """Basic keyword-based moderation fallback"""
        # Simple keyword check - can be enhanced
        inappropriate_keywords = getattr(
            settings,
            "DJANGO_FORGE_AI_MODERATION_KEYWORDS",
            []
        )
        
        text_lower = text.lower()
        flagged = any(keyword.lower() in text_lower for keyword in inappropriate_keywords)
        
        return {
            "flagged": flagged,
            "categories": {},
            "category_scores": {},
        }
    
    def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        """
        Generate embeddings for text.
        
        Args:
            text: Text to embed
            model: Embedding model name
        
        Returns:
            List of embedding values
        """
        if self.provider == LLMProvider.OPENAI:
            if not model:
                model = getattr(settings, "DJANGO_FORGE_AI_EMBEDDING_MODEL", "text-embedding-3-small")
            
            response = self._client.embeddings.create(
                model=model,
                input=text
            )
            return response.data[0].embedding
        else:
            raise ValueError(f"Embeddings not supported for provider: {self.provider}")


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """
    Factory function to get an LLM client instance.
    
    Args:
        provider: Optional provider name
    
    Returns:
        LLMClient instance
    """
    return LLMClient(provider=provider)

