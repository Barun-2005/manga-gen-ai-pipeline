#!/usr/bin/env python3
"""
Sample Manga Panel Generation Script

Generates high-quality sample panels for the specified prompts:
1. "ninja dodging kunai"
2. "girl with umbrella in the rain"
3. "boy jumping off rooftop"

Saves images to outputs/2025-06-01/ with quality filtering.
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from image_gen.image_generator import generate_image
from image_gen.comfy_client import ComfyUIClient


def enhance_prompt_for_quality(base_prompt: str) -> str:
    """
    Enhance a basic prompt with quality and style modifiers for manga generation.
    
    Args:
        base_prompt: Basic scene description
        
    Returns:
        Enhanced prompt with quality modifiers
    """
    quality_modifiers = [
        "masterpiece", "best quality", "high resolution", "detailed",
        "manga style", "black and white", "clean lineart", "professional illustration",
        "dynamic composition", "dramatic lighting"
    ]
    
    negative_modifiers = [
        "blurry", "low quality", "bad anatomy", "deformed", "ugly",
        "poorly drawn", "extra limbs", "duplicate", "cropped", "worst quality"
    ]
    
    enhanced_prompt = f"{', '.join(quality_modifiers)}, {base_prompt}"
    negative_prompt = f"NEGATIVE: {', '.join(negative_modifiers)}"
    
    return f"{enhanced_prompt} | {negative_prompt}"


def generate_sample_panels():
    """Generate the three sample panels with quality filtering."""
    
    # Define the sample prompts
    sample_prompts = [
        ("ninja_dodging_kunai", "ninja dodging kunai, action scene, dynamic pose, throwing stars in air"),
        ("girl_umbrella_rain", "girl with umbrella in the rain, melancholic atmosphere, water droplets"),
        ("boy_jumping_rooftop", "boy jumping off rooftop, urban background, dramatic leap, city skyline")
    ]
    
    # Create output directory
    output_dir = Path("outputs/2025-06-01")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🎨 Generating sample manga panels...")
    print(f"Output directory: {output_dir}")
    
    # Check ComfyUI availability
    client = ComfyUIClient()
    if not client.is_server_ready():
        print("⚠️  ComfyUI server not available. Please start ComfyUI first.")
        return False
    
    generated_files = []
    
    for i, (filename_base, prompt) in enumerate(sample_prompts, 1):
        print(f"\n📸 Generating panel {i}/3: {filename_base}")
        
        # Enhance prompt for quality
        enhanced_prompt = enhance_prompt_for_quality(prompt)
        print(f"Prompt: {enhanced_prompt[:100]}...")
        
        try:
            # Generate image with custom index for this session
            temp_path = generate_image(enhanced_prompt, 1000 + i)
            
            if temp_path and Path(temp_path).exists():
                # Move to our sample directory with descriptive name
                target_path = output_dir / f"{filename_base}.png"
                Path(temp_path).rename(target_path)
                
                generated_files.append(target_path)
                print(f"✅ Generated: {target_path}")
                
                # Quality check (basic file size check)
                file_size = target_path.stat().st_size
                if file_size < 10000:  # Less than 10KB probably indicates an issue
                    print(f"⚠️  Warning: Small file size ({file_size} bytes) - may be low quality")
                else:
                    print(f"📊 File size: {file_size:,} bytes")
            else:
                print(f"❌ Failed to generate {filename_base}")
                
        except Exception as e:
            print(f"❌ Error generating {filename_base}: {e}")
        
        # Small delay between generations
        time.sleep(2)
    
    print(f"\n🎉 Sample generation complete!")
    print(f"Generated {len(generated_files)} panels:")
    for file_path in generated_files:
        print(f"  - {file_path}")
    
    return len(generated_files) > 0


def main():
    """Main entry point."""
    print("MangaGen Sample Panel Generator")
    print("=" * 40)
    
    success = generate_sample_panels()
    
    if success:
        print("\n✅ Sample panels generated successfully!")
        print("Check outputs/2025-06-01/ for the generated images.")
    else:
        print("\n❌ Sample generation failed.")
        print("Please ensure ComfyUI is running and try again.")


if __name__ == "__main__":
    main()
