#!/usr/bin/env python3
"""
MangaGen - Panel Image Generator

Generates manga panel images from scene plans using SDXL + IP-Adapter for character consistency.

Usage:
    # Mock mode (for local testing without GPU)
    python scripts/generate_panels.py --scene scene_plan.json --mock
    
    # Full generation (requires GPU - run on Kaggle)
    python scripts/generate_panels.py --scene scene_plan.json --output outputs/

Features:
    - SDXL + Animagine for high-quality anime/manga style
    - IP-Adapter FaceID for character consistency
    - Automatic character reference generation
    - Mock mode for testing without GPU
"""

import os
import sys
import json
import argparse
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw, ImageFont
    from tqdm import tqdm
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install Pillow tqdm")
    sys.exit(1)

from src.schemas import MangaScenePlan, PanelScene


# ============================================
# Configuration
# ============================================

@dataclass
class GenerationConfig:
    """Image generation configuration."""
    # Model settings
    base_model: str = "stabilityai/stable-diffusion-xl-base-1.0"
    anime_lora: str = "Linaqruf/animagine-xl-3.1"  # Optional anime LoRA
    ip_adapter_model: str = "h94/IP-Adapter"
    
    # Generation settings
    width: int = 768
    height: int = 1024
    num_inference_steps: int = 30
    guidance_scale: float = 7.5
    
    # Character reference settings
    generate_character_ref: bool = True
    ip_adapter_scale: float = 0.6
    
    # Style-specific settings
    bw_manga_negative: str = (
        "color, colorful, vibrant, saturated, "
        "bad anatomy, bad hands, missing fingers, extra fingers, deformed, blurry, "
        "low quality, worst quality, jpeg artifacts, watermark, text, signature"
    )
    color_anime_negative: str = (
        "bad anatomy, bad hands, missing fingers, extra fingers, deformed, blurry, "
        "low quality, worst quality, jpeg artifacts, watermark, text, signature, "
        "monochrome, grayscale, black and white"
    )


# ============================================
# Mock Generator (for testing without GPU)
# ============================================

class MockPanelGenerator:
    """
    Generates placeholder images for testing without GPU.
    Creates solid-color panels with text overlay showing what would be generated.
    """
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        print("🎭 Mock Generator initialized (no GPU required)")
    
    def generate_character_reference(
        self,
        character_name: str,
        character_prompt: str,
        output_path: Path
    ) -> Image.Image:
        """Generate a mock character reference image."""
        img = Image.new("RGB", (512, 512), color=(100, 149, 237))
        draw = ImageDraw.Draw(img)
        
        # Add text
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
            small_font = font
        
        draw.text((20, 20), f"CHARACTER REF", fill="white", font=font)
        draw.text((20, 60), f"{character_name}", fill="yellow", font=font)
        draw.text((20, 100), "─" * 30, fill="white")
        
        # Wrap prompt text
        words = character_prompt.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 35:
                lines.append(" ".join(current_line[:-1]))
                current_line = [word]
        if current_line:
            lines.append(" ".join(current_line))
        
        y = 130
        for line in lines[:8]:
            draw.text((20, y), line, fill="white", font=small_font)
            y += 20
        
        draw.text((20, 450), "[MOCK - GPU would generate real image]", fill="gray", font=small_font)
        
        img.save(output_path)
        return img
    
    def generate_panel(
        self,
        panel: PanelScene,
        style: str,
        character_refs: Dict[str, Image.Image],
        output_path: Path
    ) -> Image.Image:
        """Generate a mock panel image."""
        # Different base colors for different moods
        mood_colors = {
            "mysterious": (40, 40, 80),
            "tense": (80, 40, 40),
            "peaceful": (60, 100, 60),
            "exciting": (100, 80, 40),
            "sad": (60, 60, 80),
            "neutral": (70, 70, 70)
        }
        
        base_color = mood_colors.get(panel.mood.lower(), mood_colors["neutral"])
        
        # Adjust for style
        if style == "bw_manga":
            # Convert to grayscale equivalent
            gray = int(0.299 * base_color[0] + 0.587 * base_color[1] + 0.114 * base_color[2])
            base_color = (gray, gray, gray)
        
        img = Image.new("RGB", (self.config.width, self.config.height), color=base_color)
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 24)
            small_font = ImageFont.truetype("arial.ttf", 16)
            tiny_font = ImageFont.truetype("arial.ttf", 12)
        except:
            font = ImageFont.load_default()
            small_font = font
            tiny_font = font
        
        text_color = "white" if style == "color_anime" else "black" if sum(base_color) > 400 else "white"
        
        # Panel number
        draw.text((20, 20), f"PANEL {panel.panel_number}", fill=text_color, font=font)
        draw.text((20, 55), f"[{panel.camera_angle.upper()}]", fill="yellow", font=small_font)
        
        # Description
        draw.text((20, 90), "─" * 40, fill=text_color)
        y = 110
        desc_words = panel.description.split()
        lines = []
        current = []
        for word in desc_words:
            current.append(word)
            if len(" ".join(current)) > 45:
                lines.append(" ".join(current[:-1]))
                current = [word]
        if current:
            lines.append(" ".join(current))
        
        for line in lines[:6]:
            draw.text((20, y), line, fill=text_color, font=small_font)
            y += 22
        
        # Characters
        y += 20
        draw.text((20, y), "Characters:", fill="cyan", font=small_font)
        y += 25
        for char in panel.characters_present[:4]:
            draw.text((40, y), f"• {char}", fill=text_color, font=small_font)
            y += 22
        
        # Background
        y += 20
        draw.text((20, y), f"BG: {panel.background[:50]}", fill="orange", font=small_font)
        
        # Mood
        y += 30
        draw.text((20, y), f"Mood: {panel.mood}", fill="lime", font=small_font)
        
        # Dialogue preview
        y += 40
        if panel.dialogue:
            draw.text((20, y), "Dialogue:", fill="magenta", font=small_font)
            y += 22
            for d in panel.dialogue[:3]:
                text = f'{d.speaker}: "{d.text[:30]}..."' if len(d.text) > 30 else f'{d.speaker}: "{d.text}"'
                draw.text((30, y), text, fill=text_color, font=tiny_font)
                y += 18
        
        # Footer
        draw.text((20, self.config.height - 40), f"[MOCK - {style}]", fill="gray", font=tiny_font)
        draw.text((20, self.config.height - 25), "GPU would generate real manga panel", fill="gray", font=tiny_font)
        
        img.save(output_path)
        return img


# ============================================
# Real Generator (requires GPU)
# ============================================

class RealPanelGenerator:
    """
    Generates real manga panels using SDXL + IP-Adapter.
    Requires GPU (run on Kaggle).
    """
    
    def __init__(self, config: GenerationConfig):
        self.config = config
        self.pipe = None
        self.ip_adapter_loaded = False
        
        print("🎨 Initializing Real Panel Generator...")
        self._load_models()
    
    def _load_models(self):
        """Load SDXL and IP-Adapter models."""
        try:
            import torch
            from diffusers import StableDiffusionXLPipeline, AutoencoderKL
            
            print(f"   Loading SDXL base model...")
            
            # Check for GPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            dtype = torch.float16 if device == "cuda" else torch.float32
            
            print(f"   Device: {device}, Dtype: {dtype}")
            
            # Load VAE for better quality
            vae = AutoencoderKL.from_pretrained(
                "madebyollin/sdxl-vae-fp16-fix",
                torch_dtype=dtype
            )
            
            # Load SDXL pipeline
            self.pipe = StableDiffusionXLPipeline.from_pretrained(
                self.config.base_model,
                vae=vae,
                torch_dtype=dtype,
                use_safetensors=True,
                variant="fp16" if dtype == torch.float16 else None
            )
            
            self.pipe = self.pipe.to(device)
            
            # Enable memory optimizations
            if device == "cuda":
                self.pipe.enable_model_cpu_offload()
                # self.pipe.enable_xformers_memory_efficient_attention()  # Optional
            
            print("   ✅ SDXL loaded successfully")
            
            # Try to load IP-Adapter
            self._load_ip_adapter()
            
        except Exception as e:
            print(f"   ⚠️ Failed to load models: {e}")
            print("   Falling back to mock generator...")
            raise
    
    def _load_ip_adapter(self):
        """Load IP-Adapter for character consistency."""
        try:
            print("   Loading IP-Adapter...")
            
            # IP-Adapter for SDXL
            self.pipe.load_ip_adapter(
                "h94/IP-Adapter",
                subfolder="sdxl_models",
                weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors"
            )
            
            self.pipe.set_ip_adapter_scale(self.config.ip_adapter_scale)
            self.ip_adapter_loaded = True
            
            print("   ✅ IP-Adapter loaded successfully")
            
        except Exception as e:
            print(f"   ⚠️ IP-Adapter not loaded: {e}")
            print("   Character consistency will be limited")
            self.ip_adapter_loaded = False
    
    def generate_character_reference(
        self,
        character_name: str,
        character_prompt: str,
        output_path: Path
    ) -> Image.Image:
        """Generate a character reference image."""
        import torch
        
        prompt = (
            f"character portrait, {character_prompt}, "
            f"front view, neutral pose, simple background, high quality, detailed"
        )
        
        negative_prompt = self.config.color_anime_negative
        
        print(f"   Generating reference for {character_name}...")
        
        with torch.inference_mode():
            image = self.pipe(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=512,
                height=512,
                num_inference_steps=self.config.num_inference_steps,
                guidance_scale=self.config.guidance_scale,
            ).images[0]
        
        image.save(output_path)
        return image
    
    def generate_panel(
        self,
        panel: PanelScene,
        style: str,
        character_refs: Dict[str, Image.Image],
        output_path: Path
    ) -> Image.Image:
        """Generate a manga panel image."""
        import torch
        
        # Build prompt from panel data
        prompt = panel.to_image_prompt(style=style)
        
        # Style-specific negative prompt
        negative_prompt = (
            self.config.bw_manga_negative if style == "bw_manga" 
            else self.config.color_anime_negative
        )
        
        # Prepare IP-Adapter image if available
        ip_adapter_image = None
        if self.ip_adapter_loaded and character_refs:
            # Use first character's reference
            if panel.characters_present:
                main_char = panel.characters_present[0]
                if main_char in character_refs:
                    ip_adapter_image = character_refs[main_char]
        
        print(f"   Generating panel {panel.panel_number}...")
        
        with torch.inference_mode():
            if ip_adapter_image:
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    ip_adapter_image=ip_adapter_image,
                    width=self.config.width,
                    height=self.config.height,
                    num_inference_steps=self.config.num_inference_steps,
                    guidance_scale=self.config.guidance_scale,
                ).images[0]
            else:
                image = self.pipe(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    width=self.config.width,
                    height=self.config.height,
                    num_inference_steps=self.config.num_inference_steps,
                    guidance_scale=self.config.guidance_scale,
                ).images[0]
        
        image.save(output_path)
        return image


# ============================================
# Main Pipeline
# ============================================

def generate_panels(
    scene_plan: MangaScenePlan,
    output_dir: Path,
    mock: bool = False,
    config: Optional[GenerationConfig] = None
) -> List[Path]:
    """
    Generate all panel images from a scene plan.
    
    Args:
        scene_plan: The scene plan to generate panels for
        output_dir: Directory to save generated images
        mock: If True, use mock generator (no GPU needed)
        config: Generation configuration
        
    Returns:
        List of paths to generated panel images
    """
    if config is None:
        config = GenerationConfig()
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Create refs subdirectory
    refs_dir = output_dir / "character_refs"
    refs_dir.mkdir(exist_ok=True)
    
    # Initialize generator
    if mock:
        generator = MockPanelGenerator(config)
    else:
        try:
            generator = RealPanelGenerator(config)
        except Exception as e:
            print(f"⚠️ Failed to initialize real generator: {e}")
            print("🎭 Falling back to mock generator...")
            generator = MockPanelGenerator(config)
    
    # Generate character references
    print("\n📸 Generating character references...")
    character_refs: Dict[str, Image.Image] = {}
    
    for char in tqdm(scene_plan.characters, desc="Characters"):
        ref_path = refs_dir / f"{char.name.lower().replace(' ', '_')}_ref.png"
        
        if ref_path.exists():
            print(f"   ✅ Found existing reference for {char.name}")
            character_refs[char.name] = Image.open(ref_path)
        else:
            char_prompt = char.to_prompt()
            ref_image = generator.generate_character_reference(
                char.name,
                char_prompt,
                ref_path
            )
            character_refs[char.name] = ref_image
    
    # Generate panels
    print(f"\n🖼️ Generating {len(scene_plan.panels)} panels...")
    panel_paths: List[Path] = []
    
    for panel in tqdm(scene_plan.panels, desc="Panels"):
        panel_path = output_dir / f"panel_{panel.panel_number:02d}.png"
        
        generator.generate_panel(
            panel=panel,
            style=scene_plan.style,
            character_refs=character_refs,
            output_path=panel_path
        )
        
        panel_paths.append(panel_path)
    
    print(f"\n✅ Generated {len(panel_paths)} panels")
    return panel_paths


def main():
    parser = argparse.ArgumentParser(
        description="Generate manga panel images from scene plan",
        epilog="Example: python generate_panels.py --scene scene_plan.json --mock"
    )
    parser.add_argument(
        "--scene",
        type=str,
        required=True,
        help="Path to scene_plan.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output directory (default: outputs)"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock generator (no GPU required, for testing)"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=30,
        help="Number of inference steps (default: 30)"
    )
    parser.add_argument(
        "--guidance",
        type=float,
        default=7.5,
        help="Guidance scale (default: 7.5)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🎨 MangaGen - Panel Generator")
    print("=" * 50)
    
    # Load scene plan
    scene_path = Path(args.scene)
    if not scene_path.exists():
        print(f"❌ Scene plan not found: {scene_path}")
        sys.exit(1)
    
    print(f"📄 Loading scene plan: {scene_path}")
    with open(scene_path, "r", encoding="utf-8") as f:
        scene_data = json.load(f)
    
    scene_plan = MangaScenePlan(**scene_data)
    print(f"   Title: {scene_plan.title}")
    print(f"   Style: {scene_plan.style}")
    print(f"   Panels: {len(scene_plan.panels)}")
    
    # Configure generation
    config = GenerationConfig(
        num_inference_steps=args.steps,
        guidance_scale=args.guidance
    )
    
    # Generate panels
    panel_paths = generate_panels(
        scene_plan=scene_plan,
        output_dir=Path(args.output),
        mock=args.mock,
        config=config
    )
    
    # Summary
    print()
    print("=" * 50)
    print("📋 Generation Summary")
    print("=" * 50)
    print(f"Mode: {'Mock' if args.mock else 'Real (GPU)'}")
    print(f"Output directory: {args.output}")
    print("Generated files:")
    for path in panel_paths:
        size_kb = path.stat().st_size / 1024
        print(f"  • {path.name} ({size_kb:.1f} KB)")
    
    print()
    print("✅ Panel generation complete!")
    print(f"📁 Output: {args.output}/")


if __name__ == "__main__":
    main()
