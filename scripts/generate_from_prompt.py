#!/usr/bin/env python3
"""
Text-to-Manga Panel Generator

Generates a single manga panel from a text prompt with automatic pose and style detection.
This script provides a simple interface for creating manga panels from natural language descriptions.

Usage:
    python scripts/generate_from_prompt.py "ninja dodging kunai in moonlight"
    python scripts/generate_from_prompt.py "girl reading book in library" --style shoujo
    python scripts/generate_from_prompt.py "robot fighting monster" --pose combat_stance
"""

import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.automation_stubs import generate_pose_from_text, assign_style_automatically
from image_gen.image_generator import generate_image
from pipeline.prompt_builder import enhance_prompt_for_style


def build_enhanced_prompt(
    text_prompt: str,
    pose_data: Dict[str, Any],
    style_data: Dict[str, str]
) -> str:
    """
    Build an enhanced image generation prompt from text, pose, and style data.
    
    Args:
        text_prompt: Original text description
        pose_data: Pose and composition information
        style_data: Style configuration
        
    Returns:
        Enhanced prompt for image generation
    """
    # Base quality modifiers
    quality_terms = [
        "masterpiece", "best quality", "highly detailed",
        "manga style", "black and white", "clean lineart"
    ]
    
    # Add style-specific terms
    style_terms = []
    if style_data.get("line_weight") == "bold":
        style_terms.append("bold lines")
    elif style_data.get("line_weight") == "delicate":
        style_terms.append("delicate lineart")
    
    if style_data.get("shading_style") == "dramatic":
        style_terms.append("dramatic shadows")
    elif style_data.get("shading_style") == "soft":
        style_terms.append("soft shading")
    
    # Add composition terms
    composition_terms = []
    if pose_data.get("composition") == "close_up":
        composition_terms.append("close-up shot")
    elif pose_data.get("composition") == "wide_shot":
        composition_terms.append("wide shot")
    else:
        composition_terms.append("medium shot")
    
    if pose_data.get("dynamic_level") == "medium":
        composition_terms.append("dynamic composition")
    
    # Combine all elements
    all_terms = quality_terms + style_terms + composition_terms
    enhanced_base = f"{', '.join(all_terms)}, {text_prompt}"
    
    # Add negative prompt
    negative_terms = [
        "blurry", "low quality", "bad anatomy", "deformed",
        "poorly drawn", "extra limbs", "duplicate", "cropped"
    ]
    
    return f"{enhanced_base} | NEGATIVE: {', '.join(negative_terms)}"


def generate_manga_panel(
    text_prompt: str,
    pose_override: Optional[str] = None,
    style_override: Optional[str] = None,
    seed: Optional[int] = None
) -> str:
    """
    Generate a manga panel from a text prompt with automatic pose and style detection.
    
    Args:
        text_prompt: Natural language description of the scene
        pose_override: Optional manual pose specification
        style_override: Optional manual style specification
        seed: Optional random seed
        
    Returns:
        Path to the generated image file
    """
    print(f"🎨 Generating manga panel from: '{text_prompt}'")
    
    # Step 1: Generate pose data
    if pose_override:
        print(f"📐 Using manual pose: {pose_override}")
        pose_data = {
            "pose_type": pose_override,
            "composition": "medium_shot",
            "suggested_angle": "eye_level",
            "dynamic_level": "medium",
            "character_count": 1,
            "notes": f"Manual override: {pose_override}"
        }
    else:
        print("📐 Auto-detecting pose from text...")
        pose_data = generate_pose_from_text(text_prompt)
        print(f"   Detected: {pose_data['pose_type']} ({pose_data['composition']})")
    
    # Step 2: Assign style
    if style_override:
        print(f"🎭 Using manual style: {style_override}")
        style_data = {
            "manga_genre": style_override,
            "line_weight": "medium",
            "shading_style": "standard",
            "background_detail": "medium",
            "color_palette": "monochrome",
            "notes": f"Manual override: {style_override}"
        }
    else:
        print("🎭 Auto-detecting style from text...")
        style_data = assign_style_automatically(text_prompt)
        print(f"   Detected: {style_data['manga_genre']} style")
    
    # Step 3: Build enhanced prompt
    print("✨ Building enhanced prompt...")
    enhanced_prompt = build_enhanced_prompt(text_prompt, pose_data, style_data)
    print(f"   Prompt: {enhanced_prompt[:80]}...")
    
    # Step 4: Generate image
    print("🖼️  Generating image...")
    
    # Create timestamped output directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("outputs") / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate with a unique index based on timestamp
    panel_index = int(time.time()) % 10000
    temp_image_path = generate_image(enhanced_prompt, panel_index)
    
    # Move to our timestamped directory with descriptive name
    if temp_image_path and Path(temp_image_path).exists():
        final_path = output_dir / "panel.png"
        Path(temp_image_path).rename(final_path)
        
        # Save generation metadata
        metadata = {
            "original_prompt": text_prompt,
            "pose_data": pose_data,
            "style_data": style_data,
            "enhanced_prompt": enhanced_prompt,
            "generation_time": datetime.now().isoformat(),
            "seed": seed
        }
        
        metadata_path = output_dir / "metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return str(final_path)
    else:
        raise Exception("Failed to generate manga panel")


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(
        description="Generate manga panel from text prompt",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_from_prompt.py "ninja dodging kunai"
  python scripts/generate_from_prompt.py "girl with umbrella in rain" --style shoujo
  python scripts/generate_from_prompt.py "robot vs monster" --pose combat_stance --seed 12345
        """
    )
    
    parser.add_argument(
        "prompt",
        help="Text description of the manga panel scene"
    )
    parser.add_argument(
        "--pose",
        help="Manual pose override (e.g., standing, combat_stance, mid_jump)"
    )
    parser.add_argument(
        "--style", 
        help="Manual style override (e.g., shonen, seinen, shoujo, slice_of_life)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        help="Random seed for reproducible generation"
    )
    
    args = parser.parse_args()
    
    try:
        print("Text-to-Manga Panel Generator")
        print("=" * 40)
        
        # Generate the panel
        result_path = generate_manga_panel(
            text_prompt=args.prompt,
            pose_override=args.pose,
            style_override=args.style,
            seed=args.seed
        )
        
        print(f"\n✅ Success! Manga panel generated:")
        print(f"📁 {result_path}")
        
        # Show file size
        file_size = Path(result_path).stat().st_size
        print(f"📊 File size: {file_size:,} bytes")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
