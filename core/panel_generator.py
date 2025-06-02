#!/usr/bin/env python3
"""
Enhanced Panel Generator with ControlNet and T2I Adapter Support

Supports multiple generation methods:
- Plain txt2img
- ControlNet-conditioned generation
- T2I Adapter-assisted generation
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from image_gen.comfy_client import ComfyUIClient
from core.story_memory import StoryMemoryManager

class EnhancedPanelGenerator:
    """Enhanced panel generator with ControlNet and T2I Adapter support."""
    
    def __init__(self, config_file: str = "config/pipeline_config.json",
                 output_config_file: str = "config/output_config.json"):
        """Initialize the enhanced panel generator."""
        self.config = self._load_config(config_file)
        self.output_config = self._load_output_config(output_config_file)
        self.client = ComfyUIClient()

        # Initialize story memory if enabled
        self.story_memory = None
        if self.output_config.get("story_memory", {}).get("enabled", False):
            memory_dir = self.output_config["story_memory"]["memory_dir"]
            self.story_memory = StoryMemoryManager(memory_dir=memory_dir)
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load pipeline configuration."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            print(f"Config file not found: {config_file}, using defaults")
            return self._get_default_config()
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return self._get_default_config()

    def _load_output_config(self, config_file: str) -> Dict[str, Any]:
        """Load output configuration."""
        config_path = Path(config_file)

        if not config_path.exists():
            print(f"Output config file not found: {config_file}, using defaults")
            return {"color_mode": "color", "story_memory": {"enabled": False}}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading output config: {e}, using defaults")
            return {"color_mode": "color", "story_memory": {"enabled": False}}

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "generation_method": "txt2img",
            "controlnet_type": "depth",
            "adapter_type": "sketch",
            "generation_settings": {
                "controlnet_strength": 0.8,
                "adapter_strength": 0.7,
                "fallback_to_txt2img": True
            },
            "workflow_templates": {
                "txt2img": "assets/workflows/manga_graph.json",
                "controlnet": "assets/workflows/controlnet_workflow.json",
                "adapter": "assets/workflows/adapter_workflow.json"
            }
        }
    
    def generate_panel(self, prompt: str, output_path: str,
                      generation_method: str = None, control_type: str = None,
                      reference_image: str = None, color_mode: str = None,
                      story_context: Dict[str, Any] = None) -> bool:
        """
        Generate a manga panel with specified method.

        Args:
            prompt: Text prompt for generation
            output_path: Output file path
            generation_method: "txt2img", "controlnet", or "adapter"
            control_type: Type of control (e.g., "depth", "canny", "sketch")
            reference_image: Path to reference image (optional)
            color_mode: "color" or "black_and_white" (optional)
            story_context: Story context for continuity (optional)

        Returns:
            True if generation successful
        """

        # Use config defaults if not specified
        method = generation_method or self.config["generation_method"]
        mode = color_mode or self.output_config.get("color_mode", "color")

        # Enhance prompt with story continuity if available
        enhanced_prompt = self._enhance_prompt_with_story_context(prompt, story_context)

        # Apply color mode styling
        final_prompt = self._apply_color_mode_styling(enhanced_prompt, mode)
        
        print(f"Generating panel: {Path(output_path).name}")
        print(f"Method: {method}, Color mode: {mode}")
        print(f"Prompt: {final_prompt[:100]}...")

        # Check ComfyUI status
        if not self.client.is_server_ready():
            print("ComfyUI not accessible. Please ensure ComfyUI is running at http://127.0.0.1:8188")
            return False

        try:
            # Prepare workflow based on method and color mode
            workflow = self._prepare_workflow(final_prompt, output_path, method, control_type, reference_image, mode)
            if not workflow:
                return False
            
            # Generate image
            result = self._execute_workflow(workflow, output_path, mode)
            
            if result:
                print("Panel generation successful!")
                return True
            else:
                print("Panel generation failed")
                return False
                
        except Exception as e:
            print(f"Error during generation: {e}")
            
            # Fallback to txt2img if enabled
            if method != "txt2img" and self.config["generation_settings"].get("fallback_to_txt2img", True):
                print("Falling back to txt2img generation...")
                return self.generate_panel(prompt, output_path, "txt2img", color_mode=mode)

            return False

    def _enhance_prompt_with_story_context(self, prompt: str, story_context: Dict[str, Any] = None) -> str:
        """Enhance prompt with story continuity context."""
        if not story_context or not self.story_memory:
            return prompt

        # Use story memory to generate continuity-aware prompt
        continuity_prompt = self.story_memory.generate_continuity_prompt(prompt)
        return continuity_prompt

    def _apply_color_mode_styling(self, prompt: str, color_mode: str) -> str:
        """Apply color mode specific styling to prompt."""
        color_settings = self.output_config.get("color_settings", {})
        mode_config = color_settings.get(color_mode, {})

        style_prompt = mode_config.get("style_prompt", "")

        if style_prompt:
            return f"{prompt}, {style_prompt}"
        else:
            return prompt

    def _prepare_workflow(self, prompt: str, output_path: str, method: str,
                         control_type: str = None, reference_image: str = None,
                         color_mode: str = "color") -> Optional[Dict[str, Any]]:
        """Prepare ComfyUI workflow based on generation method."""
        
        if method == "txt2img":
            return self._prepare_txt2img_workflow(prompt, output_path, color_mode)
        elif method == "controlnet":
            return self._prepare_controlnet_workflow(prompt, output_path, control_type, reference_image, color_mode)
        elif method == "adapter":
            return self._prepare_adapter_workflow(prompt, output_path, control_type, reference_image, color_mode)
        else:
            print(f"Unknown generation method: {method}")
            return None

    def _prepare_txt2img_workflow(self, prompt: str, output_path: str, color_mode: str = "color") -> Dict[str, Any]:
        """Prepare standard txt2img workflow with color mode support."""

        # Use color-specific workflow template if available
        color_settings = self.output_config.get("color_settings", {})
        mode_config = color_settings.get(color_mode, {})
        color_template = mode_config.get("workflow_template")

        if color_template and Path(color_template).exists():
            template_path = color_template
            print(f"Using {color_mode} workflow template: {template_path}")
        else:
            template_path = self.config["workflow_templates"]["txt2img"]
            print(f"Using default workflow template: {template_path}")

        workflow = self._load_workflow_template(template_path)

        if not workflow:
            return None

        # Update prompt (already includes color mode styling)
        workflow["1"]["inputs"]["text"] = prompt

        # Add color mode specific negative prompt
        if "2" in workflow and "inputs" in workflow["2"]:
            negative_prompt = mode_config.get("negative_prompt", "")
            if negative_prompt:
                existing_negative = workflow["2"]["inputs"].get("text", "")
                workflow["2"]["inputs"]["text"] = f"{existing_negative}, {negative_prompt}"

        # Update output filename with color mode prefix
        output_name = Path(output_path).stem
        if self.output_config.get("output_settings", {}).get("include_color_mode_in_filename", True):
            mode_prefix = "color" if color_mode == "color" else "bw"
            output_name = f"{mode_prefix}_{output_name}"

        workflow["7"]["inputs"]["filename_prefix"] = output_name

        return workflow
    
    def _prepare_controlnet_workflow(self, prompt: str, output_path: str,
                                   control_type: str = None, reference_image: str = None,
                                   color_mode: str = "color") -> Optional[Dict[str, Any]]:
        """Prepare ControlNet workflow."""
        
        control_type = control_type or self.config["controlnet_type"]
        
        # Get model path
        model_path = self.config.get("model_paths", {}).get("controlnet", {}).get(control_type)
        if not model_path:
            print(f"ControlNet model path not found for type: {control_type}")
            return None
        
        # Get reference image
        if not reference_image:
            reference_image = self.config.get("reference_paths", {}).get("controlnet", {}).get(control_type)
        
        if not reference_image or not Path(reference_image).exists():
            print(f"Reference image not found: {reference_image}")
            if not self.config["generation_settings"].get("fallback_to_txt2img", True):
                return None
            print("No reference image available, falling back to txt2img")
            return self._prepare_txt2img_workflow(prompt, output_path, color_mode)
        
        # Load workflow template
        template_path = self.config["workflow_templates"]["controlnet"]
        workflow = self._load_workflow_template(template_path)
        
        if not workflow:
            return None
        
        # Update workflow
        workflow["1"]["inputs"]["text"] = prompt
        workflow["7"]["inputs"]["filename_prefix"] = Path(output_path).stem
        workflow["8"]["inputs"]["control_net_name"] = Path(model_path).name
        workflow["9"]["inputs"]["strength"] = self.config["generation_settings"]["controlnet_strength"]
        workflow["10"]["inputs"]["image"] = reference_image
        
        print(f"Using ControlNet: {control_type} with reference: {Path(reference_image).name}")
        
        return workflow
    
    def _prepare_adapter_workflow(self, prompt: str, output_path: str,
                                control_type: str = None, reference_image: str = None,
                                color_mode: str = "color") -> Optional[Dict[str, Any]]:
        """Prepare T2I Adapter workflow."""
        
        control_type = control_type or self.config["adapter_type"]
        
        # Get model path
        model_path = self.config.get("model_paths", {}).get("adapter", {}).get(control_type)
        if not model_path:
            print(f"T2I Adapter model path not found for type: {control_type}")
            return None
        
        # Get reference image
        if not reference_image:
            reference_image = self.config.get("reference_paths", {}).get("adapter", {}).get(control_type)
        
        if not reference_image or not Path(reference_image).exists():
            print(f"Reference image not found: {reference_image}")
            if not self.config["generation_settings"].get("fallback_to_txt2img", True):
                return None
            print("No reference image available, falling back to txt2img")
            return self._prepare_txt2img_workflow(prompt, output_path, color_mode)
        
        # Load workflow template
        template_path = self.config["workflow_templates"]["adapter"]
        workflow = self._load_workflow_template(template_path)
        
        if not workflow:
            return None
        
        # Update workflow
        workflow["1"]["inputs"]["text"] = prompt
        workflow["7"]["inputs"]["filename_prefix"] = Path(output_path).stem
        workflow["8"]["inputs"]["adapter_name"] = Path(model_path).name
        workflow["9"]["inputs"]["strength"] = self.config["generation_settings"]["adapter_strength"]
        workflow["10"]["inputs"]["image"] = reference_image
        
        print(f"Using T2I Adapter: {control_type} with reference: {Path(reference_image).name}")
        
        return workflow
    
    def _load_workflow_template(self, template_path: str) -> Optional[Dict[str, Any]]:
        """Load workflow template from file."""
        
        path = Path(template_path)
        if not path.exists():
            print(f"Workflow template not found: {template_path}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading workflow template: {e}")
            return None
    
    def _execute_workflow(self, workflow: Dict[str, Any], output_path: str, color_mode: str = "color") -> bool:
        """Execute ComfyUI workflow."""
        
        try:
            # Queue the workflow
            prompt_id = self.client.queue_prompt(workflow)
            print(f"Queued prompt with ID: {prompt_id}")
            
            # Wait for completion
            if not self.client.wait_for_completion(prompt_id):
                print("Generation timed out")
                return False
            
            # Get generated images
            images = self.client.get_images(prompt_id)
            
            if not images:
                print("No images generated")
                return False
            
            # Save the first image
            _, image_data = images[0]
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save image
            with open(output_path, 'wb') as f:
                f.write(image_data)

            # Apply grayscale conversion for black_and_white mode
            if color_mode == "black_and_white":
                self._convert_to_grayscale(output_path)
                print(f"Image converted to grayscale for B&W mode")

            print(f"Image saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error executing workflow: {e}")
            return False

    def _convert_to_grayscale(self, image_path: str) -> bool:
        """Convert image to true grayscale for black_and_white mode."""
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                print(f"Warning: Could not load image for grayscale conversion: {image_path}")
                return False

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Convert back to 3-channel for consistency but keep grayscale values
            gray_3channel = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

            # Save the grayscale image
            cv2.imwrite(image_path, gray_3channel)

            return True

        except Exception as e:
            print(f"Error converting to grayscale: {e}")
            return False

    def get_available_methods(self) -> Dict[str, list]:
        """Get available generation methods and their types."""
        
        methods = {
            "txt2img": ["standard"],
            "controlnet": [],
            "adapter": []
        }
        
        # Check available ControlNet models
        controlnet_models = self.config.get("model_paths", {}).get("controlnet", {})
        for control_type, model_path in controlnet_models.items():
            if Path(model_path).exists():
                methods["controlnet"].append(control_type)
        
        # Check available T2I Adapter models
        adapter_models = self.config.get("model_paths", {}).get("adapter", {})
        for control_type, model_path in adapter_models.items():
            if Path(model_path).exists():
                methods["adapter"].append(control_type)
        
        return methods

def main():
    """Test the enhanced panel generator."""
    
    generator = EnhancedPanelGenerator()
    
    # Test prompt
    test_prompt = "masterpiece, best quality, manga style, ninja in ancient temple"
    
    # Test different methods
    methods_to_test = [
        ("txt2img", None),
        ("controlnet", "depth"),
        ("adapter", "sketch")
    ]
    
    for method, control_type in methods_to_test:
        output_path = f"outputs/test_{method}_{control_type or 'standard'}.png"
        
        print(f"\nTesting {method} generation...")
        success = generator.generate_panel(
            prompt=test_prompt,
            output_path=output_path,
            generation_method=method,
            control_type=control_type
        )
        
        print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    
    # Show available methods
    available = generator.get_available_methods()
    print(f"\nAvailable methods: {available}")

if __name__ == "__main__":
    main()
