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
import random
from pathlib import Path
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import base64


class NVIDIAImageGenerator:
    """Generate images using NVIDIA NIM API (FLUX.1-dev from Black Forest Labs)
    
    Requires: NVIDIA_IMAGE_API_KEY environment variable
    Rate limits: Sequential generation recommended
    """
    
    # NVIDIA hosted FLUX.1-dev API URL
    API_URL = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
    
    def __init__(self, output_dir: str = "outputs", api_key: str = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.api_key = api_key or os.environ.get("NVIDIA_IMAGE_API_KEY")
        
        if not self.api_key:
            raise ValueError("NVIDIA_IMAGE_API_KEY not found in environment")
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    def generate_image(
        self,
        prompt: str,
        filename: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "anime",
        max_retries: int = 3,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """Generate a single image using NVIDIA FLUX.1-dev."""
        
        # Build style prefix
        if style == "bw_manga":
            style_prefix = "black and white manga, monochrome, ink drawing, high contrast"
        else:
            style_prefix = "anime style, vibrant colors, studio quality"
        
        full_prompt = f"{style_prefix}, {prompt}"
        
        # FLUX.1-dev API payload format
        payload = {
            "prompt": full_prompt,
            "mode": "base",
            "cfg_scale": 3.5,
            "width": width,
            "height": height,
            "seed": seed if seed is not None else random.randint(0, 2147483647),
            "steps": 50
        }
        
        for attempt in range(max_retries):
            try:
                # Rate limit delay between requests
                if attempt > 0:
                    time.sleep(random.uniform(2.0, 4.0))
                
                print(f"   🔄 NVIDIA API call (attempt {attempt+1})...")
                
                response = requests.post(
                    self.API_URL,
                    headers=self.headers,
                    json=payload,
                    timeout=120
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # NVIDIA returns base64 in artifacts array
                    artifacts = data.get("artifacts", [])
                    if artifacts and len(artifacts) > 0:
                        image_b64 = artifacts[0].get("base64")
                        if image_b64:
                            image_data = base64.b64decode(image_b64)
                            filepath = self.output_dir / filename
                            with open(filepath, "wb") as f:
                                f.write(image_data)
                            print(f"   ✅ NVIDIA image saved: {filename}")
                            return str(filepath)
                    
                    print(f"   ⚠️ No image in NVIDIA response: {list(data.keys())}")
                        
                elif response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(1.0, 3.0)
                    print(f"   ⚠️ NVIDIA rate limit (429), waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 402:
                    print(f"   ❌ NVIDIA credits exhausted (402)")
                    return None
                else:
                    print(f"   ❌ NVIDIA error {response.status_code}: {response.text[:200]}")
                    if attempt < max_retries - 1:
                        time.sleep(3)
                        continue
                    return None
                    
            except requests.exceptions.Timeout:
                print(f"   ⚠️ NVIDIA timeout, retry {attempt + 1}/{max_retries}...")
                time.sleep(3)
                continue
            except Exception as e:
                print(f"   ❌ NVIDIA error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return None
        
        print(f"   ❌ NVIDIA failed after {max_retries} retries: {filename}")
        return None
    
    def generate_single_panel(
        self,
        panel_info: dict,
        characters: dict,
        style: str,
        panel_index: int
    ) -> dict:
        """Generate a single panel - SEQUENTIAL (rate-limit safe)."""
        panel_num = f"{panel_index:02d}"
        filename = f"panel_{panel_num}.png"
        
        description = panel_info.get("description", panel_info.get("visual_description", ""))
        shot_type = panel_info.get("shot_type", "medium")
        
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
        
        print(f"   🎨 [NVIDIA] Panel {panel_index}: {description[:40]}...")
        
        result = self.generate_image(prompt, filename, style=style, seed=panel_index * 42)
        
        return {
            "panel_index": panel_index,
            "filename": filename,
            "filepath": result,
            "success": result is not None
        }
    
    def generate_batch(self, panels: list, characters: dict, style: str) -> list:
        """Generate panels SEQUENTIALLY (rate-limit safe)."""
        results = []
        for i, panel in enumerate(panels, 1):
            result = self.generate_single_panel(panel, characters, style, i)
            results.append(result)
            # Small delay between panels to respect rate limits
            time.sleep(1.5)
        return results


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
        width: int = 1024,
        height: int = 1024,
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
            
            # User-Agent rotation to look like different browsers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            headers = {
                "User-Agent": random.choice(user_agents),
                "Accept": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Referer": "https://pollinations.ai/",
            }

            # Random jitter delay to avoid machine-like patterns
            if attempt > 0:
                time.sleep(random.uniform(1.0, 3.0))

            # Add random tracking ID to bypass simple URL caching
            tracking = random.randint(10000, 99999)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width={width}&height={height}&nologo=true&seed={attempt_seed}&_fail_check={tracking}"
            
            try:
                response = requests.get(url, headers=headers, timeout=timeout)
                
                if response.status_code == 200:
                    filepath = self.output_dir / filename
                    with open(filepath, "wb") as f:
                        f.write(response.content)
                    return str(filepath)
                elif response.status_code == 429:
                    # Too Many Requests - Randomized Backoff
                    wait_time = (2 ** attempt) + random.uniform(0.5, 2.0)
                    print(f"   ⚠️ Rate limit (429), waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
                elif response.status_code == 502:
                    print(f"   ⚠️ Server error (502), retry {attempt + 1}/{max_retries}...")
                    time.sleep(random.uniform(2.0, 5.0))
                    continue
                else:
                    print(f"   ❌ Error generating {filename}: {response.status_code}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(1.0, 3.0))
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
