"""
ComfyUI Client Module

Handles interaction with ComfyUI API for image generation.
Provides workflow execution and image retrieval functionality.
"""

import os
import json
import requests
import time
import uuid
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class ComfyUIClient:
    """
    Client for interacting with ComfyUI API.
    """
    
    def __init__(self, base_url: str = None, timeout: int = 300):
        """
        Initialize ComfyUI client.
        
        Args:
            base_url: ComfyUI server URL (defaults to env var or localhost)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
        self.timeout = timeout
        self.session = requests.Session()
    
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
        while retries < 5:
            try:
                if method.upper() == "POST":
                    response = self.session.post(url, json=payload, timeout=self.timeout)
                else:
                    response = self.session.get(url, timeout=self.timeout)

                if response.status_code == 429:
                    wait_time = 2 ** retries  # 1s, 2s, 4s, 8s, 16s
                    print(f"Rate limited, waiting {wait_time}s before retry {retries + 1}/5...")
                    time.sleep(wait_time)
                    retries += 1
                    continue

                response.raise_for_status()
                return response

            except requests.exceptions.RequestException as e:
                if retries >= 4:  # Last retry
                    raise Exception(f"Request failed after 5 retries: {e}")
                retries += 1
                wait_time = 2 ** retries
                print(f"Request error, waiting {wait_time}s before retry {retries}/5...")
                time.sleep(wait_time)

        raise Exception("Rate limit exceeded after 5 retries")

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
    height: int = 512,
    steps: int = 20,
    cfg_scale: float = 7.0,
    seed: int = -1
) -> Dict[str, Any]:
    """
    Create a basic text-to-image workflow.
    
    Args:
        prompt: Positive prompt
        negative_prompt: Negative prompt
        width: Image width
        height: Image height
        steps: Sampling steps
        cfg_scale: CFG scale
        seed: Random seed (-1 for random)
        
    Returns:
        ComfyUI workflow dictionary
    """
    # TODO: Implement actual ComfyUI workflow structure
    # This is a placeholder that should be replaced with actual workflow nodes
    workflow = {
        "1": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": prompt,
                "clip": ["4", 1]
            }
        },
        "2": {
            "class_type": "CLIPTextEncode", 
            "inputs": {
                "text": negative_prompt,
                "clip": ["4", 1]
            }
        },
        # Add more nodes as needed for complete workflow
    }
    
    return workflow


if __name__ == "__main__":
    # Example usage
    client = ComfyUIClient()
    
    if client.is_server_ready():
        print("ComfyUI server is ready")
        
        # Example workflow generation
        workflow = create_basic_txt2img_workflow(
            prompt="a manga character in action pose",
            width=512,
            height=768
        )
        
        # Note: This would fail without a proper workflow and running ComfyUI
        # images = client.generate_images(workflow, "output/images")
        print("Workflow created (server integration pending)")
    else:
        print("ComfyUI server not available")
