"""
MangaGen - Image Provider Factory

Modular image generation architecture supporting:
- Pollinations (FREE, cloud) - PRIMARY
- ComfyUI (local, requires setup) - FUTURE

Usage:
    from src.ai.image_factory import get_image_provider
    
    provider = get_image_provider()
    image_bytes = await provider.generate("anime girl, manga style")
"""

import os
import asyncio
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path


class ImageProvider(ABC):
    """Base class for all image providers."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        width: int = 768,
        height: int = 768,
        **kwargs
    ) -> bytes:
        """Generate image from prompt."""
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


class PollinationsProvider(ImageProvider):
    """
    Pollinations - Free image generation API.
    
    No API key required!
    Supports: width, height, seed, nologo, enhance, model
    """
    
    BASE_URL = "https://image.pollinations.ai/prompt"
    
    # Available models
    MODELS = {
        "flux": "flux",                    # Default, high quality
        "turbo": "turbo",                  # Faster but lower quality
        "flux-realism": "flux-realism",    # More photorealistic
        "flux-anime": "flux-anime",        # Anime/manga style
    }
    
    def __init__(self, model: str = "flux"):
        self.model = self.MODELS.get(model, model)
        
    def is_available(self) -> bool:
        return True  # Always available, no API key needed
    
    @property
    def name(self) -> str:
        return f"Pollinations ({self.model})"
    
    async def generate(
        self,
        prompt: str,
        width: int = 768,
        height: int = 768,
        **kwargs
    ) -> bytes:
        """Generate image using Pollinations API."""
        import httpx
        from urllib.parse import quote
        import random
        
        # Build URL with parameters
        seed = kwargs.get("seed", random.randint(1000, 9999))
        enhance = kwargs.get("enhance", True)
        
        encoded_prompt = quote(prompt)
        url = (
            f"{self.BASE_URL}/{encoded_prompt}"
            f"?width={width}&height={height}"
            f"&seed={seed}&nologo=true"
            f"&model={self.model}"
        )
        if enhance:
            url += "&enhance=true"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content


class ComfyUIProvider(ImageProvider):
    """
    ComfyUI - Local image generation for advanced workflows.
    
    Requires:
    - ComfyUI running locally
    - API enabled on port 8188
    
    Supports: Custom workflows, LoRAs, ControlNet, IP-Adapter
    """
    
    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8188",
        workflow_path: Optional[str] = None
    ):
        self.server_url = server_url or os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
        self.workflow_path = workflow_path
        
    def is_available(self) -> bool:
        """Check if ComfyUI is running."""
        if not self.server_url:
            return False
        
        try:
            import httpx
            # Quick sync check
            response = httpx.get(f"{self.server_url}/system_stats", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    @property
    def name(self) -> str:
        return "ComfyUI (local)"
    
    async def generate(
        self,
        prompt: str,
        width: int = 768,
        height: int = 768,
        **kwargs
    ) -> bytes:
        """
        Generate image using ComfyUI workflow.
        
        Note: This is a simplified implementation.
        Full implementation would load workflow JSON and inject prompt.
        """
        if not self.is_available():
            raise RuntimeError("ComfyUI is not available")
        
        import httpx
        import json
        import uuid
        
        # Simple txt2img workflow
        workflow = {
            "prompt": {
                "3": {
                    "class_type": "KSampler",
                    "inputs": {
                        "seed": kwargs.get("seed", 42),
                        "steps": kwargs.get("steps", 20),
                        "cfg": kwargs.get("cfg", 7),
                        "sampler_name": "euler",
                        "scheduler": "normal",
                        "denoise": 1,
                    }
                },
                "4": {
                    "class_type": "CheckpointLoaderSimple",
                    "inputs": {
                        "ckpt_name": kwargs.get("model", "sd_xl_base_1.0.safetensors")
                    }
                },
                "6": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": prompt
                    }
                },
                "7": {
                    "class_type": "CLIPTextEncode",
                    "inputs": {
                        "text": "ugly, blurry, bad quality"
                    }
                },
                "5": {
                    "class_type": "EmptyLatentImage",
                    "inputs": {
                        "width": width,
                        "height": height,
                        "batch_size": 1
                    }
                }
            },
            "client_id": str(uuid.uuid4())
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Queue prompt
            response = await client.post(
                f"{self.server_url}/prompt",
                json=workflow
            )
            response.raise_for_status()
            result = response.json()
            prompt_id = result["prompt_id"]
            
            # Wait for completion (simplified - should use websocket)
            for _ in range(60):  # 60 second timeout
                await asyncio.sleep(1)
                history = await client.get(f"{self.server_url}/history/{prompt_id}")
                if history.status_code == 200:
                    data = history.json()
                    if prompt_id in data and data[prompt_id].get("outputs"):
                        # Get output image
                        outputs = data[prompt_id]["outputs"]
                        for node_id, output in outputs.items():
                            if "images" in output:
                                img_data = output["images"][0]
                                img_response = await client.get(
                                    f"{self.server_url}/view",
                                    params={
                                        "filename": img_data["filename"],
                                        "subfolder": img_data.get("subfolder", ""),
                                        "type": img_data["type"]
                                    }
                                )
                                return img_response.content
        
        raise RuntimeError("ComfyUI generation timed out")


class FallbackImageProvider(ImageProvider):
    """
    Smart image provider with fallback.
    
    Priority: ComfyUI (local) -> Pollinations (cloud)
    """
    
    def __init__(self, prefer_local: bool = False):
        self.providers = []
        self.prefer_local = prefer_local
        self._init_providers()
        
    def _init_providers(self):
        """Initialize providers in priority order."""
        if self.prefer_local:
            # Local first
            providers = [
                (ComfyUIProvider, {}),
                (PollinationsProvider, {"model": "flux-anime"}),
            ]
        else:
            # Cloud first (default)
            providers = [
                (PollinationsProvider, {"model": "flux"}),
                (ComfyUIProvider, {}),
            ]
        
        for cls, kwargs in providers:
            try:
                p = cls(**kwargs)
                if p.is_available():
                    self.providers.append(p)
                    print(f"   ✓ {p.name} available")
            except:
                pass
        
        if not self.providers:
            # Fallback to Pollinations even if check failed
            self.providers.append(PollinationsProvider())
            print("   ⚠️ Fallback to Pollinations")
    
    def is_available(self) -> bool:
        return len(self.providers) > 0
    
    @property
    def name(self) -> str:
        if self.providers:
            return f"FallbackImage (primary: {self.providers[0].name})"
        return "FallbackImage (no providers)"
    
    async def generate(
        self,
        prompt: str,
        width: int = 768,
        height: int = 768,
        **kwargs
    ) -> bytes:
        """Generate with automatic fallback."""
        errors = []
        
        for provider in self.providers:
            try:
                print(f"🖼️ Using: {provider.name}")
                return await provider.generate(prompt, width, height, **kwargs)
            except Exception as e:
                print(f"⚠️ {provider.name} failed: {e}")
                errors.append(f"{provider.name}: {e}")
                continue
        
        raise RuntimeError(
            f"All image providers failed!\n" + "\n".join(errors)
        )


class ImageFactory:
    """Factory for creating image providers."""
    
    PROVIDERS = {
        "pollinations": PollinationsProvider,
        "comfyui": ComfyUIProvider,
        "auto": FallbackImageProvider,
    }
    
    @classmethod
    def create(cls, provider: Optional[str] = None, **kwargs) -> ImageProvider:
        """
        Create an image provider.
        
        Args:
            provider: "pollinations", "comfyui", or "auto" (default)
            **kwargs: Provider-specific options
            
        Returns:
            Configured ImageProvider instance
        """
        provider = provider or "auto"
        
        if provider.lower() not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider}")
        
        print(f"🔧 Initializing image provider: {provider}")
        return cls.PROVIDERS[provider.lower()](**kwargs)
    
    @classmethod
    def list_available(cls):
        """List all available providers."""
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
def get_image_provider(provider: Optional[str] = None, **kwargs) -> ImageProvider:
    """
    Get an image provider instance.
    
    Args:
        provider: "auto" (default), "pollinations", "comfyui"
        **kwargs: Provider options (model, server_url, etc.)
        
    Returns:
        ImageProvider with smart fallback
    """
    return ImageFactory.create(provider, **kwargs)
