#!/usr/bin/env python3
"""
Manga Panel Generation Script

Automates the manga panel generation process using ComfyUI workflows.
Accepts JSON input with prompt, pose image, and style image parameters.

Usage:
    python scripts/generate_panel.py --input config.json
    python scripts/generate_panel.py --prompt "ninja jumping" --pose jump.png --style naruto.png
"""

import os
import json
import time
import uuid
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from image_gen.comfy_client import ComfyUIClient


class MangaPanelGenerator:
    """
    Automated manga panel generation using ComfyUI workflows.
    """
    
    def __init__(self, comfyui_url: str = "http://127.0.0.1:8188"):
        """
        Initialize the manga panel generator.
        
        Args:
            comfyui_url: ComfyUI server URL
        """
        self.comfyui_url = comfyui_url
        self.client = ComfyUIClient(comfyui_url)
        self.workflows_dir = project_root / "workflows" / "manga"
        self.assets_dir = project_root / "assets"
        self.outputs_dir = project_root / "outputs" / "panels"
        
        # Ensure output directory exists
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Load a workflow JSON file.
        
        Args:
            workflow_name: Name of the workflow file (without .json)
            
        Returns:
            Workflow dictionary
        """
        workflow_path = self.workflows_dir / f"{workflow_name}.json"
        
        if not workflow_path.exists():
            raise FileNotFoundError(f"Workflow not found: {workflow_path}")
        
        with open(workflow_path, 'r') as f:
            return json.load(f)
    
    def substitute_placeholders(self, workflow: Dict[str, Any], substitutions: Dict[str, str]) -> Dict[str, Any]:
        """
        Replace placeholder values in workflow with actual values.
        
        Args:
            workflow: Workflow dictionary
            substitutions: Dictionary of placeholder -> value mappings
            
        Returns:
            Modified workflow with substitutions applied
        """
        workflow_str = json.dumps(workflow)
        
        for placeholder, value in substitutions.items():
            workflow_str = workflow_str.replace(f"{{{placeholder}}}", str(value))
        
        return json.loads(workflow_str)
    
    def generate_pose_image(self, pose_description: str) -> str:
        """
        Generate a pose reference image from text description.
        
        Args:
            pose_description: Description of the desired pose
            
        Returns:
            Path to generated pose image
        """
        print(f"Generating pose image for: {pose_description}")
        
        workflow = self.load_workflow("text_to_pose_image")
        
        substitutions = {
            "pose_description": pose_description
        }
        
        workflow = self.substitute_placeholders(workflow, substitutions)
        
        # Execute workflow
        prompt_id = self.client.queue_prompt(workflow)
        
        if self.client.wait_for_completion(prompt_id):
            images = self.client.get_images(prompt_id)
            if images:
                # Save the pose image
                filename, image_data = images[0]
                pose_path = self.assets_dir / "poses" / f"pose_{int(time.time())}.png"
                pose_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(pose_path, "wb") as f:
                    f.write(image_data)
                
                print(f"Pose image saved: {pose_path}")
                return str(pose_path)
        
        raise Exception("Failed to generate pose image")
    
    def process_style_image(self, style_name: str) -> str:
        """
        Process a style reference image.
        
        Args:
            style_name: Name of the style (without extension)
            
        Returns:
            Path to processed style image
        """
        print(f"Processing style image: {style_name}")
        
        workflow = self.load_workflow("style_image_selector")
        
        substitutions = {
            "style_name": style_name
        }
        
        workflow = self.substitute_placeholders(workflow, substitutions)
        
        # Execute workflow
        prompt_id = self.client.queue_prompt(workflow)
        
        if self.client.wait_for_completion(prompt_id):
            images = self.client.get_images(prompt_id)
            if images:
                # Save the processed style image
                filename, image_data = images[0]
                style_path = self.assets_dir / "styles" / f"processed_{style_name}.png"
                style_path.parent.mkdir(parents=True, exist_ok=True)
                
                with open(style_path, "wb") as f:
                    f.write(image_data)
                
                print(f"Style image processed: {style_path}")
                return str(style_path)
        
        raise Exception("Failed to process style image")
    
    def generate_manga_panel(
        self, 
        prompt: str, 
        pose_image_path: str, 
        style_image_path: str,
        seed: Optional[int] = None
    ) -> str:
        """
        Generate a manga panel using the main workflow.
        
        Args:
            prompt: Text prompt for the manga panel
            pose_image_path: Path to pose reference image
            style_image_path: Path to style reference image
            seed: Random seed (optional)
            
        Returns:
            Path to generated manga panel
        """
        print(f"Generating manga panel: {prompt}")
        
        workflow = self.load_workflow("generate_manga_panel")
        
        if seed is None:
            seed = int(time.time())
        
        timestamp = int(time.time())
        
        substitutions = {
            "prompt": prompt,
            "pose_image_path": pose_image_path,
            "style_image_path": style_image_path,
            "seed": seed,
            "timestamp": timestamp
        }
        
        workflow = self.substitute_placeholders(workflow, substitutions)
        
        # Execute workflow
        prompt_id = self.client.queue_prompt(workflow)
        
        if self.client.wait_for_completion(prompt_id):
            images = self.client.get_images(prompt_id)
            if images:
                # Save the manga panel
                filename, image_data = images[0]
                panel_path = self.outputs_dir / f"manga_panel_{timestamp}.png"
                
                with open(panel_path, "wb") as f:
                    f.write(image_data)
                
                print(f"Manga panel saved: {panel_path}")
                return str(panel_path)
        
        raise Exception("Failed to generate manga panel")
    
    def generate_from_config(self, config: Dict[str, Any]) -> str:
        """
        Generate manga panel from configuration dictionary.
        
        Args:
            config: Configuration with prompt, pose_image, style_image
            
        Returns:
            Path to generated manga panel
        """
        prompt = config.get("prompt", "")
        pose_image = config.get("pose_image", "")
        style_image = config.get("style_image", "")
        seed = config.get("seed")
        
        if not prompt:
            raise ValueError("Prompt is required")
        
        # Handle pose image
        if pose_image.startswith("generate:"):
            # Generate pose from description
            pose_description = pose_image[9:]  # Remove "generate:" prefix
            pose_image_path = self.generate_pose_image(pose_description)
        else:
            # Use existing pose image
            pose_image_path = str(self.assets_dir / "poses" / pose_image)
            if not Path(pose_image_path).exists():
                raise FileNotFoundError(f"Pose image not found: {pose_image_path}")
        
        # Handle style image
        if style_image.startswith("process:"):
            # Process style from name
            style_name = style_image[8:]  # Remove "process:" prefix
            style_image_path = self.process_style_image(style_name)
        else:
            # Use existing style image
            style_image_path = str(self.assets_dir / "styles" / style_image)
            if not Path(style_image_path).exists():
                raise FileNotFoundError(f"Style image not found: {style_image_path}")
        
        return self.generate_manga_panel(prompt, pose_image_path, style_image_path, seed)


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Generate manga panels using ComfyUI")
    
    # Input methods
    parser.add_argument("--input", "-i", help="JSON configuration file")
    parser.add_argument("--prompt", "-p", help="Text prompt for the panel")
    parser.add_argument("--pose", help="Pose image or description (prefix with 'generate:' for auto-generation)")
    parser.add_argument("--style", "-s", help="Style image or name (prefix with 'process:' for auto-processing)")
    parser.add_argument("--seed", type=int, help="Random seed")
    parser.add_argument("--comfyui-url", default="http://127.0.0.1:8188", help="ComfyUI server URL")
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = MangaPanelGenerator(args.comfyui_url)
    
    # Check if ComfyUI is available
    if not generator.client.is_server_ready():
        print("Error: ComfyUI server is not available")
        print(f"Make sure ComfyUI is running at {args.comfyui_url}")
        return 1
    
    try:
        if args.input:
            # Load from JSON file
            with open(args.input, 'r') as f:
                config = json.load(f)
            
            result_path = generator.generate_from_config(config)
            
        elif args.prompt:
            # Use command line arguments
            config = {
                "prompt": args.prompt,
                "pose_image": args.pose or "generate:standing pose",
                "style_image": args.style or "process:default",
                "seed": args.seed
            }
            
            result_path = generator.generate_from_config(config)
            
        else:
            print("Error: Either --input or --prompt is required")
            return 1
        
        print(f"\nSuccess! Manga panel generated: {result_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
