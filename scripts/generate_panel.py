#!/usr/bin/env python3
"""
ComfyUI Panel Generation Script
Generates manga panels using local ComfyUI instance.
"""

import json
import time
import requests
import argparse
import uuid
import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.output_manager import OutputManager

class ComfyUIGenerator:
    """Interface for ComfyUI panel generation."""

    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188"):
        """Initialize ComfyUI generator."""
        self.comfyui_url = comfyui_url
        self.api_url = f"{comfyui_url}/api"
        self.workflow_path = Path("assets/workflows/manga_graph.json")
        
    def check_comfyui_status(self) -> bool:
        """Check if ComfyUI is running and accessible."""
        try:
            response = requests.get(f"{self.comfyui_url}/system_stats", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"ComfyUI connection failed: {e}")
            return False

    def load_workflow(self) -> Optional[dict]:
        """Load workflow from JSON file."""
        if not self.workflow_path.exists():
            print(f"Workflow file not found: {self.workflow_path}")
            return None

        try:
            with open(self.workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            return workflow
        except Exception as e:
            print(f"Failed to load workflow: {e}")
            return None

    def prepare_workflow(self, prompt: str, output_filename: str) -> Optional[dict]:
        """Prepare workflow with custom prompt and output filename."""
        workflow = self.load_workflow()
        if not workflow:
            return None

        # Replace prompt placeholder in the workflow
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode":
                if "PROMPT_PLACEHOLDER" in node["inputs"].get("text", ""):
                    node["inputs"]["text"] = prompt
                    print(f"Set prompt in node {node_id}")

            # Set output filename
            elif node.get("class_type") == "SaveImage":
                node["inputs"]["filename_prefix"] = Path(output_filename).stem
                print(f"Set output filename: {Path(output_filename).stem}")

        return workflow
    
    def queue_prompt(self, workflow: dict) -> Optional[str]:
        """Queue a prompt in ComfyUI and return the prompt ID."""
        try:
            # Generate a unique client_id
            client_id = str(uuid.uuid4())

            data = {
                "prompt": workflow,
                "client_id": client_id
            }

            response = requests.post(f"{self.api_url}/prompt", json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                prompt_id = result.get("prompt_id")
                print(f"Queued prompt with ID: {prompt_id}")
                return prompt_id
            else:
                print(f"Failed to queue prompt: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"Error queuing prompt: {e}")
            return None
    
    def wait_for_completion(self, prompt_id: str, timeout: int = 300) -> Optional[dict]:
        """Wait for prompt completion and return the result."""
        start_time = time.time()
        print(f"Waiting for completion (timeout: {timeout}s)...")

        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{self.api_url}/history/{prompt_id}", timeout=10)
                if response.status_code == 200:
                    history = response.json()
                    if prompt_id in history:
                        result = history[prompt_id]
                        print("Generation completed!")
                        return result

                # Show progress
                elapsed = int(time.time() - start_time)
                print(f"Waiting... ({elapsed}s elapsed)", end='\r')
                time.sleep(2)
            except Exception as e:
                print(f"Error checking status: {e}")
                time.sleep(2)

        print(f"\nTimeout after {timeout}s")
        return None

    def download_image(self, result: dict, output_path: str) -> bool:
        """Download the generated image from ComfyUI."""
        try:
            # Find the SaveImage node output
            for node_id, node_output in result.get("outputs", {}).items():
                if "images" in node_output:
                    images = node_output["images"]
                    if images:
                        # Get the first image
                        image_info = images[0]
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")

                        # Construct the download URL
                        params = {"filename": filename}
                        if subfolder:
                            params["subfolder"] = subfolder

                        # Download the image
                        response = requests.get(f"{self.comfyui_url}/view", params=params, timeout=30)

                        if response.status_code == 200:
                            # Create output directory if it doesn't exist
                            Path(output_path).parent.mkdir(parents=True, exist_ok=True)

                            # Save the image
                            with open(output_path, 'wb') as f:
                                f.write(response.content)

                            print(f"Image saved to: {output_path}")
                            return True
                        else:
                            print(f"Failed to download image: {response.status_code}")
                            return False

            print("No images found in result")
            return False

        except Exception as e:
            print(f"Error downloading image: {e}")
            return False

    def generate_panel(self, prompt: str, output_path: str) -> bool:
        """Generate a single manga panel."""

        print(f"Generating panel: {Path(output_path).name}")
        print(f"Prompt: {prompt[:100]}...")

        # Check ComfyUI status
        if not self.check_comfyui_status():
            print("ComfyUI not accessible. Please ensure ComfyUI is running at http://127.0.0.1:8188")
            return False

        # Prepare workflow
        workflow = self.prepare_workflow(prompt, output_path)
        if not workflow:
            return False

        # Queue prompt
        prompt_id = self.queue_prompt(workflow)
        if not prompt_id:
            return False

        # Wait for completion
        result = self.wait_for_completion(prompt_id)
        if not result:
            print("Generation failed or timed out")
            return False

        # Download the generated image
        if self.download_image(result, output_path):
            print("Panel generation successful!")
            return True
        else:
            print("Failed to download generated image")
            return False

def generate_panels_from_file(prompt_file: str, output_dir: str, prefix: str = "panel") -> bool:
    """Generate panels from a prompt file."""

    print(f"Generating panels from: {prompt_file}")
    print(f"Output directory: {output_dir}")
    
    # Read prompts
    prompt_path = Path(prompt_file)
    if not prompt_path.exists():
        print(f"❌ Prompt file not found: {prompt_file}")
        return False
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f.readlines() if line.strip()]
    
    if not prompts:
        print("No prompts found in file")
        return False

    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Initialize generator
    generator = ComfyUIGenerator()

    # Generate panels with meaningful names
    success_count = 0
    for i, prompt in enumerate(prompts):
        # Extract meaningful name from prompt
        prompt_summary = prompt.split(',')[0].strip()[:30]  # First part of prompt
        clean_summary = "".join(c for c in prompt_summary if c.isalnum() or c in " -_").strip()
        clean_summary = clean_summary.replace(" ", "_")

        if clean_summary:
            filename = f"{prefix}_{i+1:03d}_{clean_summary}.png"
        else:
            filename = f"{prefix}_{i+1:03d}.png"

        output_file = output_path / filename

        if generator.generate_panel(prompt, str(output_file)):
            success_count += 1
            print(f"   Saved: {filename}")
        else:
            print(f"Failed to generate panel {i+1}")

    print(f"\nGeneration Summary:")
    print(f"   Total prompts: {len(prompts)}")
    print(f"   Successful: {success_count}")
    print(f"   Failed: {len(prompts) - success_count}")

    return success_count == len(prompts)

def main():
    """Main generation function."""

    parser = argparse.ArgumentParser(description="Generate manga panels using ComfyUI")

    # Positional arguments for simple usage
    parser.add_argument("prompt", nargs="?", help="Prompt text for generation")
    parser.add_argument("output", nargs="?", help="Output file path")

    # Optional arguments
    parser.add_argument("--prompt-file", type=str, help="File containing prompts (one per line)")
    parser.add_argument("--output-dir", type=str, help="Output directory for batch generation")
    parser.add_argument("--prefix", type=str, default="panel", help="Filename prefix for batch generation")
    parser.add_argument("--comfyui-url", type=str, default="http://127.0.0.1:8188", help="ComfyUI URL")
    parser.add_argument("--use-output-manager", action="store_true", help="Use organized output management")
    parser.add_argument("--run-name", type=str, help="Name for the generation run (used with --use-output-manager)")

    args = parser.parse_args()

    # Initialize generator
    generator = ComfyUIGenerator(args.comfyui_url)

    if args.prompt and args.output:
        # Single panel generation (positional args)
        print(f"Single panel generation:")
        print(f"Prompt: {args.prompt}")
        print(f"Output: {args.output}")
        success = generator.generate_panel(args.prompt, args.output)
        return 0 if success else 1

    elif args.prompt_file and args.output_dir:
        # Batch generation
        print(f"Batch generation:")
        print(f"Prompt file: {args.prompt_file}")
        print(f"Output directory: {args.output_dir}")
        success = generate_panels_from_file(args.prompt_file, args.output_dir, args.prefix)
        return 0 if success else 1

    else:
        print("Usage:")
        print("  Single generation: python generate_panel.py \"prompt text\" output.png")
        print("  Batch generation:  python generate_panel.py --prompt-file prompts.txt --output-dir outputs/")
        return 1

if __name__ == "__main__":
    exit(main())
