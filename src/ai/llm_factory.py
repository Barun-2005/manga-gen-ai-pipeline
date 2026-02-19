"""
MangaGen - LLM Provider Factory with Automatic Fallback

Modular LLM architecture supporting multiple providers:
- Groq (FREE, fast) - PRIMARY
- NVIDIA NIM (40 req/min, FREE) - FALLBACK
- Google Gemini (if user has paid key)
- OpenRouter (pay-per-use, 100+ models)

AUTOMATIC FALLBACK: If Groq hits rate limit, auto-switches to NVIDIA NIM!

Usage:
    from src.ai.llm_factory import get_llm
    
    llm = get_llm()  # Auto-selects best available with fallback
    response = llm.generate("Write a story about...")
"""

import os
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List


class LLMProvider(ABC):
    """Base class for all LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod  
    def is_available(self) -> bool:
        """Check if provider is configured and available."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name for logging."""
        pass


class GroqProvider(LLMProvider):
    """Groq - Fast inference with generous free tier."""
    
    # Available models by capability
    MODELS = {
        "fast": "llama-3.1-8b-instant",      # Quick, simple tasks
        "balanced": "mixtral-8x7b-32768",     # Good balance
        "powerful": "llama-3.3-70b-versatile" # Complex story/dialogue
    }
    
    def __init__(self, api_key: Optional[str] = None, model_tier: str = "powerful"):
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        self.model = self.MODELS.get(model_tier, self.MODELS["powerful"])
        self.client = None
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    @property
    def name(self) -> str:
        return f"Groq ({self.model.split('/')[-1]})"
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Groq API key not configured")
        
        try:
            from groq import Groq
            if self.client is None:
                self.client = Groq(api_key=self.api_key)
            
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            # Check for rate limit errors
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"Groq rate limit hit: {e}")
            raise RuntimeError(f"Groq generation failed: {e}")


class NVIDIANIMProvider(LLMProvider):
    """NVIDIA NIM - 40 req/min unlimited, OpenAI compatible.
    
    DeepSeek v3.1 is actually GREAT for creative writing, not just coding!
    It has strong reasoning which helps with story structure.
    """
    
    # Models for different tasks - DeepSeek is excellent for creative too!
    MODELS = {
        "story": "deepseek-ai/deepseek-v3.1-terminus",      # Best for stories - strong reasoning!
        "creative": "mistralai/mistral-large-3-675b-instruct-2512",  # Also great
        "fast": "meta/llama-3.2-3b-instruct",               # Quick responses
        "coding": "deepseek-ai/deepseek-r1",                # Code-specific
    }
    
    def __init__(self, api_key: Optional[str] = None, task_type: str = "story"):
        self.api_key = api_key or os.environ.get("NVIDIA_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        self.task_type = task_type
        self.default_model = self.MODELS.get(task_type, self.MODELS["story"])
        self.client = None
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    @property
    def name(self) -> str:
        return f"NVIDIA NIM ({self.default_model.split('/')[-1]})"
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("NVIDIA API key not configured")
        
        try:
            from openai import OpenAI
            if self.client is None:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
            
            # Allow overriding task type per-call
            task = kwargs.get("task_type", self.task_type)
            model = self.MODELS.get(task, self.default_model)
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg:
                raise RateLimitError(f"NVIDIA rate limit hit: {e}")
            raise RuntimeError(f"NVIDIA NIM generation failed: {e}")


class GeminiProvider(LLMProvider):
    """Google Gemini - requires API key (free tier is dead as of Dec 2024)."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model = "gemini-2.0-flash"
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    @property
    def name(self) -> str:
        return "Google Gemini"
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("Gemini API key not configured")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            
            model = genai.GenerativeModel(kwargs.get("model", self.model))
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_msg = str(e).lower()
            if "rate" in error_msg or "limit" in error_msg or "429" in error_msg or "quota" in error_msg:
                raise RateLimitError(f"Gemini rate limit hit: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}")


class OpenRouterProvider(LLMProvider):
    """OpenRouter - Access 100+ models via unified API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        self.default_model = "meta-llama/llama-3.1-8b-instruct:free"
        self.client = None
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    @property
    def name(self) -> str:
        return "OpenRouter"
    
    def generate(self, prompt: str, **kwargs) -> str:
        if not self.is_available():
            raise ValueError("OpenRouter API key not configured")
        
        try:
            from openai import OpenAI
            if self.client is None:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key
                )
            
            response = self.client.chat.completions.create(
                model=kwargs.get("model", self.default_model),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.7),
                max_tokens=kwargs.get("max_tokens", 4096),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenRouter generation failed: {e}")


class RateLimitError(Exception):
    """Raised when a provider hits its rate limit."""
    pass


class FallbackLLM(LLMProvider):
    """
    Smart LLM that automatically falls back to next provider on rate limit.
    
    Chain: Groq -> NVIDIA NIM -> Gemini -> OpenRouter
    """
    
    def __init__(self):
        self.providers: List[LLMProvider] = []
        self.current_idx = 0
        self._init_providers()
        
    def _init_providers(self):
        """Initialize all available providers in priority order."""
        provider_classes = [
            (GroqProvider, {}),
            (NVIDIANIMProvider, {"task_type": "story"}),  # Use story mode!
            (GeminiProvider, {}),
            (OpenRouterProvider, {}),
        ]
        
        for cls, kwargs in provider_classes:
            try:
                p = cls(**kwargs)
                if p.is_available():
                    self.providers.append(p)
                    print(f"   ✓ {p.name} available")
            except Exception:
                pass
        
        if not self.providers:
            raise ValueError("No LLM providers available! Check your API keys.")
    
    def is_available(self) -> bool:
        return len(self.providers) > 0
    
    @property
    def name(self) -> str:
        if self.providers:
            return f"FallbackLLM (primary: {self.providers[0].name})"
        return "FallbackLLM (no providers)"
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate with automatic fallback on rate limit."""
        
        errors = []
        
        for i, provider in enumerate(self.providers):
            try:
                # Show actual model if overridden
                model_override = kwargs.get("model")
                if model_override:
                    print(f"🤖 Using: {provider.name} → MODEL OVERRIDE: {model_override}")
                else:
                    print(f"🤖 Using: {provider.name}")
                result = provider.generate(prompt, **kwargs)
                return result
                
            except RateLimitError as e:
                print(f"⚠️ {provider.name} rate limited, trying next...")
                errors.append(f"{provider.name}: {e}")
                
                # Small delay before trying next provider
                time.sleep(1)
                continue
                
            except Exception as e:
                print(f"❌ {provider.name} failed: {e}")
                errors.append(f"{provider.name}: {e}")
                continue
        
        # All providers failed
        raise RuntimeError(
            f"All LLM providers failed!\n" + "\n".join(errors)
        )


class LLMFactory:
    """Factory for creating LLM providers."""
    
    PROVIDERS = {
        "groq": GroqProvider,
        "nvidia": NVIDIANIMProvider,
        "gemini": GeminiProvider,
        "openrouter": OpenRouterProvider,
        "auto": FallbackLLM,  # Smart fallback!
    }
    
    @classmethod
    def create(cls, provider: Optional[str] = None) -> LLMProvider:
        """
        Create an LLM provider.
        
        Args:
            provider: Provider name, or None/"auto" for smart fallback
            
        Returns:
            Configured LLMProvider instance
        """
        provider = provider or "auto"
        
        if provider.lower() not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        print(f"🔧 Initializing LLM provider: {provider}")
        return cls.PROVIDERS[provider.lower()]()
    
    @classmethod
    def list_available(cls) -> List[str]:
        """List all available (configured) providers."""
        available = []
        for name, provider_cls in cls.PROVIDERS.items():
            if name == "auto":
                continue
            try:
                p = provider_cls()
                if p.is_available():
                    available.append(p.name)
            except:
                pass
        return available


# Convenience function - USE THIS!
def get_llm(provider: Optional[str] = None) -> LLMProvider:
    """
    Get an LLM provider instance with automatic fallback.
    
    Args:
        provider: "auto" (default), "groq", "nvidia", "gemini", "openrouter"
        
    Returns:
        LLMProvider with smart fallback on rate limits
    """
    return LLMFactory.create(provider)
