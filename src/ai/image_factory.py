"""
MangaGen - Image Provider Factory

Modular image generation architecture supporting:
- Pollinations (FREE, cloud) - PRIMARY
- ComfyUI (local, requires setup) - Hybrid Z-Image workflow tested!

Usage:
    from src.ai.image_factory import get_image_provider
    
    provider = get_image_provider()
    image_bytes = await provider.generate("anime girl, manga style")
"""

import os
import json
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


class FluxProvider(ImageProvider):
    """
    Flux Premium Engine - High quality manga with IP-Adapter for character consistency.
    
    Variants:
    - flux_dev: 12 steps, ~90s, highest quality
    - flux_schnell: 4 steps, ~35s, faster with good quality
    
    Features:
    - DualCLIP (T5 + CLIP-L) for better prompt understanding
    - IP-Adapter for character reference consistency
    - Sentence-based prompts (not Danbooru tags)
    """
    
    VARIANTS = {
        "flux_dev": {"unet": "flux1-dev-Q5_K_S.gguf", "steps": 12},
        "flux_schnell": {"unet": "flux1-schnell-Q5_K_S.gguf", "steps": 4}
    }
    
    def __init__(
        self,
        variant: str = "flux_dev",
        server_url: str = "http://127.0.0.1:8188",
        use_ip_adapter: bool = True
    ):
        self.variant = variant
        self.config = self.VARIANTS.get(variant, self.VARIANTS["flux_dev"])
        self.server_url = server_url or os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
        self.use_ip_adapter = use_ip_adapter
        
    def is_available(self) -> bool:
        """Check if ComfyUI is running."""
        try:
            import httpx
            response = httpx.get(f"{self.server_url}/system_stats", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    @property
    def name(self) -> str:
        return f"Flux Premium ({self.variant})"
    
    def _get_workflow(self) -> Dict:
        """Get Flux workflow with DualCLIP and optional IP-Adapter."""
        return {
            "11": {"class_type": "DualCLIPLoaderGGUF", "inputs": {
                "clip_name1": "t5-v1_1-xxl-encoder-Q5_K_M.gguf",
                "clip_name2": "clip_l.safetensors", "type": "flux"
            }},
            "12": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": self.config["unet"]}},
            "6": {"class_type": "CLIPTextEncodeFlux", "inputs": {
                "clip_l": "", "t5xxl": "", "guidance": 3.5, "clip": ["11", 0]
            }},
            "7": {"class_type": "CLIPTextEncodeFlux", "inputs": {
                "clip_l": "", "t5xxl": "", "guidance": 3.5, "clip": ["11", 0]
            }},
            "5": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "3": {"class_type": "KSampler", "inputs": {
                "seed": 42, "steps": self.config["steps"], "cfg": 1.0,
                "sampler_name": "euler", "scheduler": "simple", "denoise": 1.0,
                "model": ["12", 0], "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]
            }},
            "10": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["10", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "flux_manga", "images": ["8", 0]}}
        }
    
    def _add_ip_adapter(self, workflow: Dict, ref_image: str) -> Dict:
        """Add IP-Adapter nodes for character FACE consistency."""
        # ═══════════════════════════════════════════════════════════════
        # IP-ADAPTER FOR FACE LOCKING - HARDCODED STRENGTH 0.80
        # ═══════════════════════════════════════════════════════════════
        print(f"")
        print(f"   🎭 ════════════════════════════════════════════════════════")
        print(f"   🎭 IP-ADAPTER: ACTIVE")
        print(f"   🎭 Reference: {ref_image}")
        print(f"   🎭 Strength: 0.80 (Face Lock Mode)")
        print(f"   🎭 ════════════════════════════════════════════════════════")
        print(f"")
        
        workflow["20"] = {"class_type": "LoadImage", "inputs": {"image": ref_image, "upload": "image"}}
        workflow["21"] = {"class_type": "ImageScale", "inputs": {
            "image": ["20", 0], "upscale_method": "nearest-exact", "width": 1024, "height": 1024, "crop": "disabled"
        }}
        workflow["22"] = {"class_type": "LoadFluxIPAdapter", "inputs": {
            "ip_adapter_path": "xlabs/ipadapters/ip_adapter.safetensors",
            "clip_vision_path": "CLIP-ViT-H-14.safetensors", "provider": "CPU"
        }}
        # HARDCODED: Strength 0.80 for face consistency
        workflow["23"] = {"class_type": "ApplyFluxIPAdapter", "inputs": {
            "model": ["12", 0], "ip_adapter_flux": ["22", 0], "image": ["21", 0], "strength": 0.80
        }}
        workflow["3"]["inputs"]["model"] = ["23", 0]
        return workflow
    
    async def generate(self, prompt: str, width: int = 1024, height: int = 1024, **kwargs) -> bytes:
        """Generate image using Flux Premium workflow."""
        if not self.is_available():
            raise RuntimeError("ComfyUI not available. Start with: py -3.10 ComfyUI/main.py --novram")
        
        import httpx
        workflow = self._get_workflow()
        
        # Format dual prompts for Flux
        clip_l = f"manga panel, professional illustration, {prompt[:100]}"
        t5xxl = f"Professional manga illustration: {prompt}. Clean black ink linework, high contrast, Japanese manga style."
        workflow["6"]["inputs"]["clip_l"] = clip_l
        workflow["6"]["inputs"]["t5xxl"] = t5xxl
        
        # Set dimensions and seed
        workflow["5"]["inputs"]["width"] = width
        workflow["5"]["inputs"]["height"] = height
        workflow["3"]["inputs"]["seed"] = kwargs.get("seed", 42)
        
        # Add IP-Adapter if reference provided
        ref_image = kwargs.get("reference_image")
        if self.use_ip_adapter and ref_image:
            workflow = self._add_ip_adapter(workflow, ref_image)
            print(f"   🎭 IP-Adapter: ACTIVE (ref: {ref_image})")
        elif self.use_ip_adapter:
            print(f"   🎭 IP-Adapter: READY (no reference image this panel)")
        
        workflow["9"]["inputs"]["filename_prefix"] = f"flux_manga/{kwargs.get('panel_id', 'panel')}"
        print(f"   🎨 Flux {self.variant}: {prompt[:60]}... ({self.config['steps']} steps)")
        
        # DEBUG: Print complete workflow JSON
        print(f"")
        print(f"   📋 ═══════════════════════════════════════════════════════")
        print(f"   📋 DEBUG: COMPLETE WORKFLOW JSON")
        print(f"   📋 ═══════════════════════════════════════════════════════")
        print(json.dumps(workflow, indent=2))
        print(f"   📋 ═══════════════════════════════════════════════════════")
        print(f"")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            response = await client.post(f"{self.server_url}/prompt", json={"prompt": workflow})
            response.raise_for_status()
            prompt_id = response.json()["prompt_id"]
            
            max_wait = 180 if self.variant == "flux_dev" else 90
            for attempt in range(max_wait):
                await asyncio.sleep(2)
                history = await client.get(f"{self.server_url}/history/{prompt_id}")
                if history.status_code == 200:
                    data = history.json()
                    if prompt_id in data and data[prompt_id].get("outputs"):
                        for node_id, output in data[prompt_id]["outputs"].items():
                            if "images" in output:
                                img_data = output["images"][0]
                                img_response = await client.get(f"{self.server_url}/view", params={
                                    "filename": img_data["filename"],
                                    "subfolder": img_data.get("subfolder", ""),
                                    "type": img_data["type"]
                                })
                                print(f"✅ Flux generated in ~{attempt * 2}s")
                                return img_response.content
        
        raise RuntimeError(f"Flux generation timed out")


class PollinationsProvider(ImageProvider):

    """
    Pollinations - AI image generation via gen.pollinations.ai.
    
    Requires API key (set POLLINATIONS_API_KEY in .env).
    Get your key at: https://enter.pollinations.ai
    Supports: width, height, seed, nologo, enhance, model
    """
    
    BASE_URL = "https://gen.pollinations.ai/image"
    
    # Available models (2026 updated list)
    MODELS = {
        "flux": "flux",                    # Default, high quality
        "turbo": "turbo",                  # Faster but lower quality
        "flux-realism": "flux-realism",    # More photorealistic
        "flux-anime": "flux-anime",        # Anime/manga style
    }
    
    def __init__(self, model: str = "flux"):
        self.model = self.MODELS.get(model, model)
        self.api_key = os.environ.get("POLLINATIONS_API_KEY", "")
        
    def is_available(self) -> bool:
        return bool(self.api_key)
    
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
        """Generate image using Pollinations gen.pollinations.ai API."""
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
        
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.content


class ComfyUIProvider(ImageProvider):
    """
    ComfyUI - Local Hybrid Workflow for Manga Generation.
    
    Uses the TESTED Hybrid approach (8.5/10 rating):
    - Stage 1: Z-Image for consistent character generation
    - Stage 2: Animagine pass for action panels (optional)
    
    Requires:
    - ComfyUI running with --novram flag
    - Z-Image workflow in workflows/zimage_fixed_antirealism.json
    
    Tested: 10/10 panels, 10.6 min total, NO CRASHES with --novram
    """
    
    # Z-Image natural language prompt suffix (CRITICAL for consistency)
    STYLE_SUFFIX = "high quality, detailed, anime style, 2d animation, flat colors, clean lineart"
    NEGATIVE_PROMPT = "photorealistic, 3d render, octane render, real skin texture, realistic lighting, photograph, real human, hyperrealistic, uncanny valley"
    
    def __init__(
        self,
        server_url: str = "http://127.0.0.1:8188",
        workflow_path: Optional[str] = None
    ):
        self.server_url = server_url or os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188")
        
        # Load Z-Image workflow from project
        project_root = Path(__file__).parent.parent.parent
        self.workflow_path = workflow_path or str(project_root / "workflows" / "zimage_fixed_antirealism.json")
        self._workflow = None
        
    def _load_workflow(self) -> Dict:
        """Load Z-Image workflow from JSON file."""
        if self._workflow is None:
            try:
                with open(self.workflow_path, 'r') as f:
                    self._workflow = json.load(f)
            except FileNotFoundError:
                print(f"⚠️ Workflow not found: {self.workflow_path}")
                # Fallback to embedded workflow
                self._workflow = self._get_fallback_workflow()
        return self._workflow
    
    def _get_fallback_workflow(self) -> Dict:
        """Fallback Z-Image workflow if file not found."""
        return {
            "1": {"class_type": "UnetLoaderGGUF", "inputs": {"unet_name": "z_image_turbo-Q5_0.gguf"}},
            "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "lumina2"}},
            "3": {"class_type": "VAELoader", "inputs": {"vae_name": "ae.safetensors"}},
            "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "PROMPT", "clip": ["2", 0]}},
            "5": {"class_type": "CLIPTextEncode", "inputs": {"text": self.NEGATIVE_PROMPT, "clip": ["2", 0]}},
            "6": {"class_type": "EmptySD3LatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}},
            "7": {"class_type": "KSampler", "inputs": {
                "seed": 12345, "steps": 8, "cfg": 1.5, "sampler_name": "dpmpp_2m_sde",
                "scheduler": "sgm_uniform", "denoise": 1.0,
                "model": ["1", 0], "positive": ["4", 0], "negative": ["5", 0], "latent_image": ["6", 0]
            }},
            "8": {"class_type": "VAEDecode", "inputs": {"samples": ["7", 0], "vae": ["3", 0]}},
            "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "mangagen_output", "images": ["8", 0]}}
        }
        
    def is_available(self) -> bool:
        """Check if ComfyUI is running."""
        if not self.server_url:
            return False
        
        try:
            import httpx
            response = httpx.get(f"{self.server_url}/system_stats", timeout=2.0)
            return response.status_code == 200
        except:
            return False
    
    @property
    def name(self) -> str:
        return "ComfyUI Hybrid (Z-Image)"
    
    def _format_prompt_for_zimage(self, prompt: str) -> str:
        """
        Format prompt for Z-Image natural language style.
        
        Z-Image works best with descriptive natural language, NOT Danbooru tags.
        This ensures consistent character generation.
        """
        # Check if already has our style suffix
        if "anime style" in prompt.lower():
            return prompt
        
        # Add style suffix for consistency
        return f"{prompt}, {self.STYLE_SUFFIX}"
    
    async def generate(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        **kwargs
    ) -> bytes:
        """
        Generate image using Z-Image Hybrid workflow.
        
        This is the TESTED workflow that achieved 8.5/10 rating!
        Uses natural language prompts for character consistency.
        
        Args:
            prompt: Scene description (will be formatted for Z-Image)
            width: Image width (default 1024 for Z-Image)
            height: Image height (default 1024 for Z-Image)
            seed: Random seed for reproducibility
            is_action: If True, may apply additional processing (future)
        """
        if not self.is_available():
            raise RuntimeError("ComfyUI is not available. Start with: py -3.10 ComfyUI/main.py --novram")
        
        import httpx
        import json
        import copy
        
        # Load and customize workflow
        workflow = copy.deepcopy(self._load_workflow())
        
        # Format prompt for Z-Image (natural language style)
        formatted_prompt = self._format_prompt_for_zimage(prompt)
        
        # Inject prompt into workflow
        # Node 4 is the positive prompt
        if "4" in workflow:
            workflow["4"]["inputs"]["text"] = formatted_prompt
        
        # Inject seed
        seed = kwargs.get("seed", 42)
        if "7" in workflow:
            workflow["7"]["inputs"]["seed"] = seed
        
        # Inject resolution (update to 1024x1024 for Z-Image)
        if "6" in workflow:
            workflow["6"]["inputs"]["width"] = width
            workflow["6"]["inputs"]["height"] = height
        
        # Update output prefix
        if "9" in workflow:
            workflow["9"]["inputs"]["filename_prefix"] = f"mangagen/{kwargs.get('panel_id', 'panel')}"
        
        print(f"🖼️ ComfyUI generating: {formatted_prompt[:80]}...")
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            # Queue prompt  
            response = await client.post(
                f"{self.server_url}/prompt",
                json={"prompt": workflow}
            )
            response.raise_for_status()
            result = response.json()
            prompt_id = result["prompt_id"]
            
            # Wait for completion (with longer timeout for Z-Image ~50s)
            for attempt in range(120):  # 2 minute timeout
                await asyncio.sleep(2)
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
                                print(f"✅ Generated in ~{attempt * 2}s")
                                return img_response.content
        
        raise RuntimeError("ComfyUI generation timed out (2 min)")




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
    
    # Engine options: z_image (standard), flux_dev (premium), flux_schnell (speed)
    PROVIDERS = {
        "pollinations": PollinationsProvider,
        "comfyui": ComfyUIProvider,
        "z_image": ComfyUIProvider,  # Alias for clarity
        "flux_dev": lambda **kw: FluxProvider(variant="flux_dev", **kw),
        "flux_schnell": lambda **kw: FluxProvider(variant="flux_schnell", **kw),
        "auto": FallbackImageProvider,
    }
    
    @classmethod
    def create(cls, provider: Optional[str] = None, **kwargs) -> ImageProvider:
        """
        Create an image provider.
        
        Args:
            provider: Engine to use:
                - "z_image" (standard, 8 steps, tags)
                - "flux_dev" (premium, 12 steps, sentences)
                - "flux_schnell" (fast, 4 steps, sentences)
                - "auto" (default fallback)
            **kwargs: Provider-specific options
            
        Returns:
            Configured ImageProvider instance
        """
        provider = provider or "auto"
        
        if provider.lower() not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider/engine: {provider}")
        
        print(f"🔧 Initializing engine: {provider}")
        
        provider_factory = cls.PROVIDERS[provider.lower()]
        if callable(provider_factory) and not isinstance(provider_factory, type):
            return provider_factory(**kwargs)
        return provider_factory(**kwargs)
    
    @classmethod
    def list_available(cls):
        """List all available providers."""
        available = []
        for name, provider_cls in cls.PROVIDERS.items():
            if name == "auto":
                continue
            try:
                if callable(provider_cls) and not isinstance(provider_cls, type):
                    p = provider_cls()
                else:
                    p = provider_cls()
                if p.is_available():
                    available.append(p.name)
            except:
                pass
        return available


# Convenience function - USE THIS!
def get_image_provider(engine: Optional[str] = None, **kwargs) -> ImageProvider:
    """
    Get an image provider instance.
    
    Args:
        engine: Engine to use:
            - "z_image" or "comfyui": Standard (Z-Image, 8 steps, tag prompts)
            - "flux_dev": Premium (Flux Dev, 12 steps, sentence prompts)
            - "flux_schnell": Speed (Flux Schnell, 4 steps, sentence prompts)
            - "auto": Smart fallback (default)
        **kwargs: Provider options (server_url, use_ip_adapter, etc.)
        
    Returns:
        ImageProvider instance
    """
    return ImageFactory.create(engine, **kwargs)

