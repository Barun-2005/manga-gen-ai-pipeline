"""
Scene Manager for Visual Coherence System

Manages scene-level metadata, character consistency, and visual references
for multi-panel manga generation with coherent visual flow.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CharacterDescriptor:
    """Character appearance descriptor for consistency."""
    name: str
    appearance: str  # Physical description
    clothing: str    # Outfit description
    age_group: str   # child, teen, adult, elderly
    hair_style: str  # Hair description
    distinctive_features: str  # Scars, accessories, etc.


@dataclass
class SceneSettings:
    """Scene environment and setting descriptor."""
    location: str           # temple, forest, city, etc.
    time_of_day: str       # morning, noon, evening, night
    weather: str           # sunny, cloudy, rainy, etc.
    lighting: str          # bright, dim, dramatic, soft
    mood: str              # peaceful, tense, mysterious, etc.
    background_elements: List[str]  # props, objects, details


@dataclass
class PanelReference:
    """Reference information for a panel in a scene."""
    panel_index: int
    prompt: str
    reference_image_path: Optional[str] = None
    character_focus: Optional[str] = None
    emotion: str = "neutral"
    dialogue: str = ""
    generated_image_path: Optional[str] = None


class SceneManager:
    """Manages scene-level coherence and visual consistency."""
    
    def __init__(self, output_dir: str = "outputs/runs"):
        """Initialize scene manager."""
        self.output_dir = Path(output_dir)
        self.current_scene_id = None
        self.scene_metadata = {}
        
    def create_scene(
        self, 
        scene_name: str,
        characters: List[CharacterDescriptor],
        settings: SceneSettings,
        panel_count: int = 3
    ) -> str:
        """
        Create a new scene with metadata.
        
        Args:
            scene_name: Descriptive name for the scene
            characters: List of character descriptors
            settings: Scene environment settings
            panel_count: Number of panels in the scene
            
        Returns:
            Scene ID for tracking
        """
        scene_id = str(uuid.uuid4())[:8]
        
        self.scene_metadata = {
            "scene_id": scene_id,
            "scene_name": scene_name,
            "created_at": datetime.now().isoformat(),
            "characters": [asdict(char) for char in characters],
            "settings": asdict(settings),
            "panel_count": panel_count,
            "panels": [],
            "visual_references": {},
            "consistency_rules": self._generate_consistency_rules(characters, settings)
        }
        
        self.current_scene_id = scene_id
        print(f"Created scene '{scene_name}' with ID: {scene_id}")
        return scene_id
    
    def _generate_consistency_rules(
        self, 
        characters: List[CharacterDescriptor], 
        settings: SceneSettings
    ) -> Dict[str, str]:
        """Generate consistency rules for the scene."""
        rules = {
            "character_consistency": f"Maintain consistent appearance for {len(characters)} characters",
            "setting_consistency": f"Keep {settings.location} setting with {settings.lighting} lighting",
            "style_consistency": "Maintain manga art style throughout scene",
            "color_palette": f"Use {settings.weather} weather appropriate colors"
        }
        
        # Add character-specific rules
        for char in characters:
            rules[f"character_{char.name}"] = f"{char.appearance}, {char.clothing}, {char.hair_style}"
            
        return rules
    
    def add_panel_to_scene(
        self,
        panel_index: int,
        prompt: str,
        character_focus: Optional[str] = None,
        emotion: str = "neutral",
        dialogue: str = "",
        reference_panel_index: Optional[int] = None
    ) -> PanelReference:
        """
        Add a panel to the current scene.
        
        Args:
            panel_index: Panel position in scene (0-based)
            prompt: Base prompt for the panel
            character_focus: Main character in this panel
            emotion: Emotional tone
            dialogue: Dialogue text
            reference_panel_index: Previous panel to use as visual reference
            
        Returns:
            Panel reference object
        """
        if not self.current_scene_id:
            raise ValueError("No active scene. Create a scene first.")
        
        # Enhance prompt with scene consistency
        enhanced_prompt = self._enhance_prompt_for_consistency(
            prompt, character_focus, reference_panel_index
        )
        
        panel_ref = PanelReference(
            panel_index=panel_index,
            prompt=enhanced_prompt,
            character_focus=character_focus,
            emotion=emotion,
            dialogue=dialogue
        )
        
        # Set reference image if specified
        if reference_panel_index is not None and reference_panel_index < len(self.scene_metadata["panels"]):
            ref_panel = self.scene_metadata["panels"][reference_panel_index]
            panel_ref.reference_image_path = ref_panel.get("generated_image_path")
        
        self.scene_metadata["panels"].append(asdict(panel_ref))
        print(f"Added panel {panel_index} to scene {self.current_scene_id}")
        
        return panel_ref
    
    def _enhance_prompt_for_consistency(
        self,
        base_prompt: str,
        character_focus: Optional[str],
        reference_panel_index: Optional[int]
    ) -> str:
        """Enhance prompt with scene consistency elements."""
        if not self.scene_metadata:
            return base_prompt
        
        settings = self.scene_metadata["settings"]
        characters = self.scene_metadata["characters"]
        
        # Build consistency elements
        consistency_parts = []
        
        # Add setting consistency
        consistency_parts.append(f"in {settings['location']}")
        consistency_parts.append(f"{settings['lighting']} lighting")
        consistency_parts.append(f"{settings['time_of_day']}")
        
        # Add character consistency if focused
        if character_focus:
            for char in characters:
                if char["name"].lower() == character_focus.lower():
                    consistency_parts.append(f"{char['appearance']}")
                    consistency_parts.append(f"wearing {char['clothing']}")
                    consistency_parts.append(f"{char['hair_style']}")
                    break
        
        # Add reference context if available
        if reference_panel_index is not None:
            consistency_parts.append("maintaining visual continuity from previous panel")
        
        # Combine with base prompt
        consistency_text = ", ".join(consistency_parts)
        enhanced_prompt = f"{base_prompt}, {consistency_text}, manga style, consistent art style"
        
        return enhanced_prompt
    
    def save_scene_metadata(self, run_dir: Path) -> Path:
        """Save scene metadata to run directory."""
        if not self.scene_metadata:
            raise ValueError("No scene metadata to save")
        
        # Create scene directory
        scene_dir = run_dir / "scene"
        scene_dir.mkdir(exist_ok=True)
        
        # Save scene info
        scene_info_path = scene_dir / "scene_info.json"
        with open(scene_info_path, 'w') as f:
            json.dump(self.scene_metadata, f, indent=2)
        
        print(f"Saved scene metadata to: {scene_info_path}")
        return scene_info_path
    
    def update_panel_image_path(self, panel_index: int, image_path: str):
        """Update the generated image path for a panel."""
        if panel_index < len(self.scene_metadata["panels"]):
            self.scene_metadata["panels"][panel_index]["generated_image_path"] = image_path
            print(f"Updated panel {panel_index} image path: {image_path}")
    
    def get_scene_panels(self) -> List[Dict[str, Any]]:
        """Get all panels in the current scene."""
        return self.scene_metadata.get("panels", [])
    
    def get_consistency_prompt_base(self) -> str:
        """Get base consistency prompt for the scene."""
        if not self.scene_metadata:
            return ""
        
        settings = self.scene_metadata["settings"]
        base = f"manga style, {settings['location']}, {settings['lighting']} lighting, {settings['time_of_day']}"
        return base


def create_sample_scene() -> Tuple[List[CharacterDescriptor], SceneSettings]:
    """Create sample scene data for testing."""
    
    # Sample characters
    characters = [
        CharacterDescriptor(
            name="ninja",
            appearance="young male ninja with determined expression",
            clothing="dark blue ninja outfit with hood",
            age_group="teen",
            hair_style="short black hair",
            distinctive_features="scar on left cheek"
        )
    ]
    
    # Sample settings
    settings = SceneSettings(
        location="ancient temple",
        time_of_day="evening",
        weather="clear",
        lighting="dramatic shadows",
        mood="mysterious",
        background_elements=["stone pillars", "ancient symbols", "flickering torches"]
    )
    
    return characters, settings


if __name__ == "__main__":
    # Test scene manager
    manager = SceneManager()
    
    # Create sample scene
    characters, settings = create_sample_scene()
    scene_id = manager.create_scene("Temple Discovery", characters, settings, 3)
    
    # Add sample panels
    manager.add_panel_to_scene(0, "ninja approaches ancient temple entrance", "ninja", "curious")
    manager.add_panel_to_scene(1, "ninja examines mysterious symbols on wall", "ninja", "focused", reference_panel_index=0)
    manager.add_panel_to_scene(2, "ninja discovers hidden chamber", "ninja", "surprised", reference_panel_index=1)
    
    print(f"Scene created with {len(manager.get_scene_panels())} panels")
