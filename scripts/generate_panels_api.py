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
    """Generate anime images using Pollinations.ai (FREE, no API key!)
    
    Features:
    - Parallel batch generation (4 workers)
    - Retry with prompt variations
    - Fallback images for failed generations
    """
    
    # Prompt variations for retries
    PROMPT_VARIATIONS = [
        "",  # Original
        "masterpiece, best quality, ",
        "highly detailed anime, ",
        "professional anime art, studio quality, ",
    ]
    
    # Fallback images by scene type
    FALLBACK_SCENES = {
        "action": "dynamic action scene placeholder",
        "dialogue": "character conversation placeholder",
        "landscape": "scenic background placeholder",
        "closeup": "character closeup placeholder",
        "default": "manga panel placeholder",
    }
    
    def __init__(self, output_dir: str = "outputs", max_workers: int = 4):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.max_workers = max_workers
        
        # Create fallback directory
        self.fallback_dir = self.output_dir / "fallbacks"
        self.fallback_dir.mkdir(exist_ok=True)
        
    def generate_image(
        self,
        prompt: str,
        filename: str,
        width: int = 768,
        height: int = 768,
        style: str = "anime",
        max_retries: int = 3,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """Generate a single image with retry logic and prompt variations."""
        
        # Build style prefix based on manga style
        if style == "bw_manga":
            # Strong B/W instructions to avoid any colors
            style_prefix = (
                "black and white manga art, monochrome only, NO COLOR, "
                "grayscale, high contrast ink drawing, detailed linework, "
                "traditional manga style, screentone shading, NO colored hair, NO color at all"
            )
        else:  # color_anime
            style_prefix = "anime style, vibrant colors, cel shaded, studio ghibli inspired"
        
        # Retry with different prompt variations
        for attempt in range(max_retries):
            # Get variation prefix
            variation = self.PROMPT_VARIATIONS[attempt % len(self.PROMPT_VARIATIONS)]
            
            full_prompt = f"{style_prefix}, {variation}{prompt}"
            encoded_prompt = urllib.parse.quote(full_prompt)
            
            # Add seed for consistency/variation
            attempt_seed = (seed or 42) + (attempt * 100)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={attempt_seed}"
            
            try:
                # Increase timeout for retries
                timeout = 60 + (attempt * 30)
                response = requests.get(url, timeout=timeout)
                
                if response.status_code == 200:
                    filepath = self.output_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return str(filepath)
                elif response.status_code == 429:
                    # Too Many Requests - Exponential Backoff
                    wait_time = (2 ** attempt) + 1  # 2s, 3s, 5s...
                    print(f"   ⚠️ Rate limit (429), waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 502:
                    print(f"   ⚠️ Server error (502), retry {attempt + 1}/{max_retries}...")
                    time.sleep(3 * (attempt + 1))
                    continue
                else:
                    print(f"   ❌ Error generating {filename}: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"   ⚠️ Timeout, retry {attempt + 1}/{max_retries}...")
                time.sleep(3 * (attempt + 1))
                continue
            except Exception as e:
                print(f"   ❌ Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return None
        
        print(f"   ❌ Failed after {max_retries} retries: {filename}")
        return None
    
    def generate_single_panel(
        self,
        panel_info: dict,
        characters: dict,
        style: str,
        panel_index: int
    ) -> dict:
        """Generate a single panel - used for parallel execution."""
        panel_num = f"{panel_index:02d}"
        filename = f"panel_{panel_num}.png"
        
        # Build prompt from panel data
        description = panel_info.get("description", panel_info.get("visual_description", ""))
        shot_type = panel_info.get("shot_type", "medium")
        
        # Add character details
        char_details = []
        for char_name in panel_info.get("characters_present", []):
            if char_name in characters:
                char = characters[char_name]
                char_details.append(f"{char_name} ({char.get('appearance', '')})")
        
        prompt_parts = [
            f"{shot_type} shot",
            description,
            ", ".join(char_details) if char_details else "",
        ]
        prompt = ", ".join(p for p in prompt_parts if p)
        
        print(f"   🎨 Panel {panel_index}: {description[:40]}...")
        
        result = self.generate_image(prompt, filename, style=style, seed=panel_index * 42)
        
        return {
            "panel_index": panel_index,
            "filename": filename,
            "filepath": result,
            "success": result is not None,
            "is_fallback": False
        }
    
    def generate_panels_parallel(
        self,
        scene_data: dict,
        style: str = "color_anime",
        progress_callback=None
    ) -> list:
        """Generate all panels in parallel using ThreadPoolExecutor.
        
        Args:
            scene_data: Scene data with panels and characters
            style: Style to use (bw_manga or color_anime)
            progress_callback: Optional callback(panel_index, total, filepath) for progress updates
        """
        panels = scene_data.get("panels", [])
        characters = {c["name"]: c for c in scene_data.get("characters", [])}
        
        print(f"\n🚀 PARALLEL Generation: {len(panels)} panels with {self.max_workers} workers")
        print(f"   Style: {style}")
        print()
        
        results = []
        completed = 0
        
        # Use ThreadPoolExecutor for parallel generation
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all panel generation tasks
            futures = {
                executor.submit(
                    self.generate_single_panel,
                    panel,
                    characters,
                    style,
                    i + 1
                ): i for i, panel in enumerate(panels)
            }
            
            # Collect results as they complete
            from concurrent.futures import as_completed
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    if result["success"]:
                        print(f"   ✅ {result['filename']} ({completed}/{len(panels)})")
                    else:
                        print(f"   ❌ {result['filename']} failed ({completed}/{len(panels)})")
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(result["panel_index"], len(panels), result["filepath"])
                        
                except Exception as e:
                    print(f"   ❌ Panel generation error: {e}")
                    completed += 1
        
        # Sort by panel index
        results.sort(key=lambda x: x["panel_index"])
        
        # Return list of filepaths
        return [r["filepath"] for r in results if r["filepath"]]
    
    def generate_panels(
        self,
        scene_data: dict,
        style: str = "color_anime"
    ) -> list:
        """Generate all panels from scene data.
        
        This is the main entry point - uses parallel generation by default.
        """
        return self.generate_panels_parallel(scene_data, style)


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
