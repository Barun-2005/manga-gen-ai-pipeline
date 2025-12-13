#!/usr/bin/env python3
"""
MangaGen - Panel Generator (Using Pollinations.ai)
Generates multiple manga panels from scene descriptions.
"""

import requests
import urllib.parse
import os
import time
import json
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor


class PollinationsGenerator:
    """Generate anime images using Pollinations.ai (FREE, no API key!)"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_image(
        self,
        prompt: str,
        filename: str,
        width: int = 768,
        height: int = 768,
        style: str = "anime"
    ) -> Optional[str]:
        """Generate a single image."""
        
        # Build style prefix based on manga style
        if style == "bw_manga":
            style_prefix = "black and white manga art, high contrast, ink drawing style, detailed linework"
        else:  # color_anime
            style_prefix = "anime style, vibrant colors, cel shaded, studio ghibli inspired"
        
        full_prompt = f"{style_prefix}, masterpiece, best quality, {prompt}"
        encoded_prompt = urllib.parse.quote(full_prompt)
        
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true"
        
        try:
            response = requests.get(url, timeout=60)
            
            if response.status_code == 200:
                filepath = self.output_dir / filename
                with open(filepath, "wb") as f:
                    f.write(response.content)
                return str(filepath)
            else:
                print(f"   ❌ Error generating {filename}: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return None
    
    def generate_panels(
        self,
        scene_data: dict,
        style: str = "color_anime"
    ) -> list:
        """Generate all panels from scene data."""
        
        panels = scene_data.get("panels", [])
        characters = {c["name"]: c for c in scene_data.get("characters", [])}
        
        print(f"\n🎨 Generating {len(panels)} panels...")
        print(f"   Style: {style}")
        print()
        
        generated_files = []
        
        for i, panel in enumerate(panels, 1):
            panel_num = f"{i:02d}"
            filename = f"panel_{panel_num}.png"
            
            # Build prompt from panel data
            description = panel.get("description", panel.get("visual_description", ""))
            shot_type = panel.get("shot_type", "medium")
            
            # Add character details
            char_details = []
            for char_name in panel.get("characters_present", []):
                if char_name in characters:
                    char = characters[char_name]
                    char_details.append(f"{char_name} ({char.get('appearance', '')})")
            
            prompt_parts = [
                f"{shot_type} shot",
                description,
                ", ".join(char_details) if char_details else "",
            ]
            prompt = ", ".join(p for p in prompt_parts if p)
            
            print(f"   Panel {i}/{len(panels)}: {description[:50]}...")
            
            result = self.generate_image(prompt, filename, style=style)
            
            if result:
                generated_files.append(result)
                print(f"   ✅ {filename}")
            else:
                print(f"   ❌ Failed: {filename}")
            
            # Small delay between requests
            time.sleep(1)
        
        return generated_files


def main():
    """Generate panels from scene_plan.json"""
    
    print("=" * 50)
    print("🎨 MangaGen - Panel Generator")
    print("=" * 50)
    
    # Load scene plan
    scene_file = "scene_plan.json"
    if not os.path.exists(scene_file):
        print(f"❌ {scene_file} not found!")
        print("   Run scene generation first.")
        return
    
    with open(scene_file, "r") as f:
        scene_data = json.load(f)
    
    print(f"📄 Scene: {scene_data.get('title', 'Untitled')}")
    print(f"   Panels: {len(scene_data.get('panels', []))}")
    
    # Generate panels
    generator = PollinationsGenerator()
    style = scene_data.get("style", "color_anime")
    
    start_time = time.time()
    files = generator.generate_panels(scene_data, style=style)
    elapsed = time.time() - start_time
    
    print()
    print("=" * 50)
    print(f"✅ Generated {len(files)} panels in {elapsed:.1f} seconds!")
    print("=" * 50)
    
    for f in files:
        print(f"   📸 {f}")
    
    print()
    print("🎉 Now run compose_page.py to create the final manga!")


if __name__ == "__main__":
    main()
