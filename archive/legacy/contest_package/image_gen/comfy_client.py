"""
ComfyUI Client Module - Phase 18 Update
 
Handles interaction with ComfyUI API for image generation.
Provides workflow execution and image retrieval functionality.
Updated to use centralized configuration system.
"""

import os
import json
import requests
import time
import uuid
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_manager import get_config


class ComfyUIClient:
    """
    Client for interacting with ComfyUI API.
    Updated for Phase 18 with centralized configuration.
    """
    
    def __init__(self, base_url: str = None, timeout: int = None):
        """
        Initialize ComfyUI client.
        
        Args:
            base_url: ComfyUI server URL (defaults to config)
            timeout: Request timeout in seconds (defaults to config)
        """
        self.config = get_config()
        
        # Use provided values or fall back to configuration
        self.base_url = base_url or self.config.get_comfyui_url()
        self.timeout = timeout or self.config.get("comfyui.server.timeout", 300)
        
        self.session = requests.Session()
        
        # Get retry settings from config
        self.max_retries = self.config.get("comfyui.server.max_retries", 3)
        self.retry_delay = self.config.get("comfyui.server.retry_delay", 2)
        # Use provided values or fall back to configuration
        self.base_url = base_url or self.config.get_comfyui_url()
        self.timeout = timeout or self.config.get("comfyui.server.timeout", 300)
        
        self.session = requests.Session()
        
        # Get retry settings from config
        self.max_retries = self.config.get("comfyui.server.max_retries", 3)
        self.retry_delay = self.config.get("comfyui.server.retry_delay", 2)
    
    def is_server_ready(self) -> bool:
        """
        Check if ComfyUI server is ready to accept requests.
        
        Returns:
            True if server is ready, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/system_stats", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def safe_generate(self, url: str, payload: Dict[str, Any], method: str = "POST") -> requests.Response:
        """
        Make HTTP request with exponential backoff for rate limiting.

        Args:
            url: Request URL
            payload: Request payload
            method: HTTP method (POST, GET)

        Returns:
            Response object
        """
        retries = 0
        while retries < self.max_retries:
            try:
                if method.upper() == "POST":
                    response = self.session.post(url, json=payload, timeout=self.timeout)
                else:
                    response = self.session.get(url, timeout=self.timeout)

                if response.status_code == 429:
                    wait_time = self.retry_delay * (2 ** retries)  # Exponential backoff
                    print(f"Rate limited, waiting {wait_time}s before retry {retries + 1}/{self.max_retries}...")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if retries >= self.max_retries - 1:  # Last retry
                    raise Exception(f"Request failed after {self.max_retries} retries: {e}")
                retries += 1
                wait_time = self.retry_delay * (2 ** retries)
                print(f"Request error, waiting {wait_time}s before retry {retries}/{self.max_retries}...")
                time.sleep(wait_time)

        raise Exception(f"Rate limit exceeded after {self.max_retries} retries")

    def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """
        Queue a workflow for execution.

        Args:
            workflow: ComfyUI workflow definition

        Returns:
            Prompt ID for tracking execution
        """
        prompt_id = str(uuid.uuid4())

        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }

        try:
            response = self.safe_generate(f"{self.base_url}/prompt", payload, "POST")
            result = response.json()
            return result.get("prompt_id", prompt_id)

        except Exception as e:
            raise Exception(f"Error queuing prompt: {e}")
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get current queue status.

        Returns:
            Queue status information
        """
        try:
            response = self.safe_generate(f"{self.base_url}/queue", {}, "GET")
            return response.json()
        except Exception as e:
            raise Exception(f"Error getting queue status: {e}")
    
    def wait_for_completion(self, prompt_id: str, check_interval: int = 2) -> bool:
        """
        Wait for a prompt to complete execution.
        
        Args:
            prompt_id: ID of the prompt to wait for
            check_interval: Seconds between status checks
            
        Returns:
            True if completed successfully, False if failed
        """
        start_time = time.time()
        
        while time.time() - start_time < self.timeout:
            try:
                history = self.get_history(prompt_id)
                if prompt_id in history:
                    return True
                
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Error checking completion status: {e}")
                time.sleep(check_interval)
        
        return False
    
    def get_history(self, prompt_id: str = None) -> Dict[str, Any]:
        """
        Get execution history.

        Args:
            prompt_id: Specific prompt ID to get history for

        Returns:
            History data
        """
        url = f"{self.base_url}/history"
        if prompt_id:
            url += f"/{prompt_id}"

        try:
            response = self.safe_generate(url, {}, "GET")
            return response.json()
        except Exception as e:
            raise Exception(f"Error getting history: {e}")
    
    def get_images(self, prompt_id: str) -> List[Tuple[str, bytes]]:
        """
        Retrieve generated images for a completed prompt.
        
        Args:
            prompt_id: ID of the completed prompt
            
        Returns:
            List of (filename, image_data) tuples
        """
        history = self.get_history(prompt_id)
        
        if prompt_id not in history:
            raise Exception(f"Prompt {prompt_id} not found in history")
        
        images = []
        outputs = history[prompt_id].get("outputs", {})
        
        for node_id, node_output in outputs.items():
            if "images" in node_output:
                for image_info in node_output["images"]:
                    filename = image_info["filename"]
                    subfolder = image_info.get("subfolder", "")
                    
                    # Download image
                    image_url = f"{self.base_url}/view"
                    params = {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": image_info.get("type", "output")
                    }
                    
                    try:
                        response = self.session.get(image_url, params=params)
                        response.raise_for_status()
                        images.append((filename, response.content))
                    except requests.exceptions.RequestException as e:
                        print(f"Error downloading image {filename}: {e}")
        
        return images
    
    def generate_images(
        self, 
        workflow: Dict[str, Any], 
        output_dir: str = None
    ) -> List[str]:
        """
        Complete workflow: queue, wait, and retrieve images.
        
        Args:
            workflow: ComfyUI workflow definition
            output_dir: Directory to save images (optional)
            
        Returns:
            List of saved image file paths
        """
        # Queue the workflow
        prompt_id = self.queue_prompt(workflow)
        print(f"Queued workflow with ID: {prompt_id}")
        
        # Wait for completion
        if not self.wait_for_completion(prompt_id):
            raise Exception(f"Workflow {prompt_id} did not complete within timeout")
        
        # Retrieve images
        images = self.get_images(prompt_id)
        saved_paths = []
        
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            for filename, image_data in images:
                file_path = output_path / filename
                with open(file_path, "wb") as f:
                    f.write(image_data)
                saved_paths.append(str(file_path))
                print(f"Saved image: {file_path}")
        
        return saved_paths


def load_workflow_template(template_path: str) -> Dict[str, Any]:
    """
    Load a ComfyUI workflow template from JSON file.
    
    Args:
        template_path: Path to workflow JSON file
        
    Returns:
        Workflow dictionary
    """
    with open(template_path, 'r') as f:
        return json.load(f)


def create_basic_txt2img_workflow(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 768,
    steps: int = 25,
    cfg_scale: float = 7.5,
    seed: int = -1,
    use_config: bool = True
) -> Dict[str, Any]:
    """
    Create a basic text-to-image workflow optimized for manga generation.
    Updated for Phase 18 with new models and centralized configuration.

    Args:
        prompt: Positive prompt
        negative_prompt: Negative prompt
        width: Image width (default 512 for manga)
        height: Image height (default 768 for manga)
        steps: Sampling steps
        cfg_scale: CFG scale
        seed: Random seed (-1 for random)
        use_config: Whether to use centralized configuration

    Returns:
        ComfyUI workflow dictionary
    """
    import random
    
    if use_config:
        config = get_config()
        gen_settings = config.get_generation_settings()
        
        # Use config defaults if not explicitly provided
        dimensions = gen_settings.get("dimensions", {})
        sampling = gen_settings.get("sampling", {})
        
        width = dimensions.get("width", width)
        height = dimensions.get("height", height)
        steps = sampling.get("steps", steps)
        cfg_scale = sampling.get("cfg_scale", cfg_scale)
        sampler_name = sampling.get("sampler_name", "dpmpp_2m")
        scheduler = sampling.get("scheduler", "karras")
        
        # Get model names from config
        checkpoint_name = config.get("models.checkpoint.name", "anything-v4.5-pruned.safetensors")
        
        # Enhanced negative prompt with embeddings
        prompt_config = config.get_prompt_config()
        quality_negative = prompt_config.get("quality_negative", "")
        if negative_prompt and quality_negative:
            enhanced_negative = f"{negative_prompt}, {quality_negative}"
        elif quality_negative:
            enhanced_negative = quality_negative
        else:
            enhanced_negative = negative_prompt
    else:
        # Fallback values
        sampler_name = "dpmpp_2m"
        scheduler = "karras"
        checkpoint_name = "anything-v4.5-pruned.safetensors"
        enhanced_negative = negative_prompt + ", blurry, low quality, distorted, bad anatomy, worst quality, low quality, normal quality, lowres, bad hands, bad fingers, missing fingers, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, mutation, deformed, ugly, blurry, bad proportions, extra limbs, cloned face, disfigured, out of frame, ugly, extra limbs, bad anatomy, gross proportions, malformed limbs, missing arms, missing legs, extra arms, extra legs, mutated hands, fused fingers, too many fingers, long neck, easynegative, badhandv4"
    
    if seed == -1:
        seed = random.randint(1, 1000000)

    workflow = {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["4", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": enhanced_negative,
                "clip": ["4", 1]
            },
            "_meta": {"title": "CLIP Text Encode (Negative)"}
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg_scale,
                "sampler_name": sampler_name,
                "scheduler": scheduler,
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["1", 0],
                "negative": ["2", 0],
                "latent_image": ["5", 0]
            },
            "_meta": {"title": "KSampler"}
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": checkpoint_name
            },
            "_meta": {"title": "Load Checkpoint"}
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "_meta": {"title": "Empty Latent Image"}
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "_meta": {"title": "VAE Decode"}
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "manga_panel",
                "images": ["6", 0]
            },
            "_meta": {"title": "Save Image"}
        }
    }

    return workflow


if __name__ == "__main__":
    # Test configuration manager integration
    print("=== ComfyUI Client - Phase 18 Test ===")
    
    try:
        config = get_config()
        print(f"ComfyUI URL: {config.get_comfyui_url()}")
        print(f"ComfyUI Installation: {config.get_comfyui_installation_path()}")
        
        client = ComfyUIClient()
        
        if client.is_server_ready():
            print("✓ ComfyUI server is ready")
            
            # Test workflow generation with new models
            workflow = create_basic_txt2img_workflow(
                prompt="a manga character in action pose, masterpiece, best quality",
                width=512,
                height=768,
                use_config=True
            )
            
            print("✓ Workflow created with new models")
            print(f"  - Checkpoint: {workflow['4']['inputs']['ckpt_name']}")
            print(f"  - Dimensions: {workflow['5']['inputs']['width']}x{workflow['5']['inputs']['height']}")
            print(f"  - Sampler: {workflow['3']['inputs']['sampler_name']}")
            
        else:
            print("✗ ComfyUI server not available")
            print("  Please ensure ComfyUI is running at the configured URL")
            
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        print("  Please check config/settings.yaml and .env files")
