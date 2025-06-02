"""
Scene-Aware Generator for Visual Coherence

Extends ComfyUI generation with reference image support and scene consistency
for multi-panel manga generation with visual continuity.
"""

import json
import time
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from scripts.generate_panel import ComfyUIGenerator
from core.scene_manager import SceneManager, PanelReference


class SceneAwareGenerator(ComfyUIGenerator):
    """Extended generator with scene coherence and reference image support."""
    
    def __init__(self, base_url: str = "http://127.0.0.1:8188"):
        """Initialize scene-aware generator."""
        super().__init__(base_url)
        self.scene_manager = SceneManager()
        self.reference_workflow_path = Path("assets/workflows/scene_reference_workflow.json")
        
    def load_reference_workflow(self) -> Optional[dict]:
        """Load workflow with reference image support."""
        if self.reference_workflow_path.exists():
            try:
                with open(self.reference_workflow_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading reference workflow: {e}")
        
        # Fallback to standard workflow
        print("Reference workflow not found, using standard workflow")
        return self.load_workflow()
    
    def prepare_reference_workflow(
        self, 
        prompt: str, 
        output_filename: str,
        reference_image_path: Optional[str] = None,
        reference_strength: float = 0.7
    ) -> Optional[dict]:
        """
        Prepare workflow with optional reference image.
        
        Args:
            prompt: Text prompt for generation
            output_filename: Output file name
            reference_image_path: Path to reference image (optional)
            reference_strength: Strength of reference influence (0.0-1.0)
            
        Returns:
            Prepared workflow or None if failed
        """
        # For now, use standard workflow (reference image support needs ComfyUI setup)
        # TODO: Implement proper reference image loading for ComfyUI
        if reference_image_path:
            print(f"Note: Reference image support requires ComfyUI configuration")

        # Use standard workflow for all generations
        return self.prepare_workflow(prompt, output_filename)
    
    def _configure_reference_workflow(
        self,
        workflow: dict,
        prompt: str,
        output_filename: str,
        reference_image_path: str,
        reference_strength: float
    ) -> dict:
        """Configure workflow with reference image settings."""
        
        # Update prompt
        for node_id, node in workflow.items():
            if node.get("class_type") == "CLIPTextEncode":
                if "PROMPT_PLACEHOLDER" in node["inputs"].get("text", ""):
                    node["inputs"]["text"] = prompt
                    print(f"Set prompt in reference node {node_id}")
            
            # Set output filename
            elif node.get("class_type") == "SaveImage":
                node["inputs"]["filename_prefix"] = Path(output_filename).stem
                print(f"Set reference output filename: {Path(output_filename).stem}")
            
            # Configure reference image loader (if present)
            elif node.get("class_type") == "LoadImage":
                node["inputs"]["image"] = str(reference_image_path)
                print(f"Set reference image: {reference_image_path}")
            
            # Configure reference strength (if present)
            elif node.get("class_type") in ["ControlNetApply", "T2IAdapterApply"]:
                node["inputs"]["strength"] = reference_strength
                print(f"Set reference strength: {reference_strength}")
        
        return workflow
    
    def generate_scene_panel(
        self,
        panel_ref: PanelReference,
        output_path: str,
        reference_strength: float = 0.7
    ) -> bool:
        """
        Generate a panel with scene coherence.
        
        Args:
            panel_ref: Panel reference with prompt and metadata
            output_path: Output file path
            reference_strength: Reference image influence strength
            
        Returns:
            True if generation successful
        """
        print(f"Generating scene panel {panel_ref.panel_index}: {Path(output_path).name}")
        print(f"Prompt: {panel_ref.prompt[:100]}...")
        
        if panel_ref.reference_image_path:
            print(f"Using reference: {panel_ref.reference_image_path}")
        
        # Check ComfyUI status
        if not self.check_comfyui_status():
            print("ComfyUI not accessible. Please ensure ComfyUI is running at http://127.0.0.1:8188")
            return False
        
        # Prepare workflow with reference support
        workflow = self.prepare_reference_workflow(
            panel_ref.prompt,
            output_path,
            panel_ref.reference_image_path,
            reference_strength
        )
        
        if not workflow:
            print("Failed to prepare workflow")
            return False
        
        # Queue prompt
        prompt_id = self.queue_prompt(workflow)
        if not prompt_id:
            print("Failed to queue prompt")
            return False
        
        # Wait for completion
        result = self.wait_for_completion(prompt_id)
        if not result:
            print("Generation failed or timed out")
            return False
        
        # Download result
        success = self.download_image(result, output_path)
        if success:
            # Update scene manager with generated image path
            self.scene_manager.update_panel_image_path(panel_ref.panel_index, output_path)
            print(f"Successfully generated scene panel: {Path(output_path).name}")
        
        return success
    
    def generate_scene_sequence(
        self,
        scene_name: str,
        panel_prompts: List[str],
        output_dir: Path,
        character_focus: Optional[List[str]] = None,
        emotions: Optional[List[str]] = None,
        dialogues: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate a sequence of panels for a scene with visual coherence.
        
        Args:
            scene_name: Name of the scene
            panel_prompts: List of prompts for each panel
            output_dir: Output directory for panels
            character_focus: Character focus for each panel (optional)
            emotions: Emotions for each panel (optional)
            dialogues: Dialogue for each panel (optional)
            
        Returns:
            List of generated image paths
        """
        print(f"🎬 Generating scene sequence: {scene_name}")
        print(f"📋 Panels: {len(panel_prompts)}")
        
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create scene in scene manager
        from core.scene_manager import create_sample_scene
        characters, settings = create_sample_scene()
        scene_id = self.scene_manager.create_scene(scene_name, characters, settings, len(panel_prompts))
        
        generated_paths = []
        
        # Generate each panel with reference to previous
        for i, prompt in enumerate(panel_prompts):
            # Get panel metadata
            char_focus = character_focus[i] if character_focus and i < len(character_focus) else None
            emotion = emotions[i] if emotions and i < len(emotions) else "neutral"
            dialogue = dialogues[i] if dialogues and i < len(dialogues) else ""
            
            # Reference previous panel (except for first panel)
            reference_panel_index = i - 1 if i > 0 else None
            
            # Add panel to scene
            panel_ref = self.scene_manager.add_panel_to_scene(
                panel_index=i,
                prompt=prompt,
                character_focus=char_focus,
                emotion=emotion,
                dialogue=dialogue,
                reference_panel_index=reference_panel_index
            )
            
            # Generate output filename
            panel_filename = f"scene_panel_{i+1:03d}_{scene_name.replace(' ', '_')}.png"
            output_path = output_dir / panel_filename
            
            # Generate panel
            success = self.generate_scene_panel(panel_ref, str(output_path))
            
            if success:
                generated_paths.append(str(output_path))
                print(f"   ✅ Panel {i+1}/{len(panel_prompts)}: {panel_filename}")
            else:
                print(f"   ❌ Failed to generate panel {i+1}")
                # Continue with remaining panels
        
        # Save scene metadata
        scene_info_path = self.scene_manager.save_scene_metadata(output_dir.parent)
        print(f"💾 Scene metadata saved: {scene_info_path}")
        
        print(f"🎉 Scene generation complete: {len(generated_paths)}/{len(panel_prompts)} panels")
        return generated_paths
    
    def create_reference_workflow_template(self):
        """Create a reference workflow template if it doesn't exist."""
        if self.reference_workflow_path.exists():
            print(f"Reference workflow already exists: {self.reference_workflow_path}")
            return
        
        # Create reference workflow based on standard workflow
        standard_workflow = self.load_workflow()
        if not standard_workflow:
            print("Cannot create reference workflow: standard workflow not found")
            return
        
        # For now, use standard workflow as reference workflow
        # In a real implementation, this would add ControlNet/T2I adapter nodes
        reference_workflow = standard_workflow.copy()
        
        # Ensure workflow directory exists
        self.reference_workflow_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save reference workflow
        with open(self.reference_workflow_path, 'w') as f:
            json.dump(reference_workflow, f, indent=2)
        
        print(f"Created reference workflow template: {self.reference_workflow_path}")


def test_scene_generation():
    """Test scene generation functionality."""
    print("🧪 Testing Scene Generation")
    print("-" * 40)
    
    generator = SceneAwareGenerator()
    
    # Create reference workflow if needed
    generator.create_reference_workflow_template()
    
    # Test scene sequence
    test_prompts = [
        "ninja approaches ancient temple entrance, dramatic lighting",
        "ninja examines mysterious symbols on temple wall, focused expression",
        "ninja discovers hidden chamber behind wall, surprised expression"
    ]
    
    test_output_dir = Path("outputs/test_scene")
    
    if generator.check_comfyui_status():
        generated_paths = generator.generate_scene_sequence(
            scene_name="Temple Discovery",
            panel_prompts=test_prompts,
            output_dir=test_output_dir,
            character_focus=["ninja", "ninja", "ninja"],
            emotions=["curious", "focused", "surprised"]
        )
        
        print(f"Generated {len(generated_paths)} panels")
        for path in generated_paths:
            print(f"  - {path}")
    else:
        print("ComfyUI not available - skipping actual generation")
        print("Scene framework ready for use when ComfyUI is available")


if __name__ == "__main__":
    test_scene_generation()
