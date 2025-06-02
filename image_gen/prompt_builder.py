"""
Prompt Builder Module

Converts story data into Stable Diffusion prompts optimized for manga-style image generation.
Handles character consistency, scene composition, and visual style.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import sys

# Add project root to path for layout enhancer import
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from scripts.panel_prompt_enhancer import PanelPromptEnhancer
    LAYOUT_ENHANCER_AVAILABLE = True
except ImportError:
    LAYOUT_ENHANCER_AVAILABLE = False
    print("Warning: Layout enhancer not available. Prompts will not be enhanced with layout memory.")


@dataclass
class Character:
    """Character description for consistent generation."""
    name: str
    appearance: str
    clothing: str
    personality_traits: str
    age_group: str = "young adult"


@dataclass
class Scene:
    """Scene information for image generation."""
    description: str
    location: str
    time_of_day: str
    mood: str
    characters: List[str]
    action: str
    dialogue: str = ""


class PromptBuilder:
    """
    Builds Stable Diffusion prompts from story data for manga generation.
    """
    
    def __init__(self, use_layout_enhancer: bool = True):
        """Initialize the prompt builder with manga-specific settings."""
        self.base_style = "manga style, anime art, black and white, high contrast"
        self.quality_tags = "masterpiece, best quality, highly detailed"
        self.negative_prompt = "blurry, low quality, distorted, ugly, bad anatomy, extra limbs"

        # Character consistency tracking
        self.characters: Dict[str, Character] = {}

        # Style presets
        self.style_presets = {
            "action": "dynamic pose, motion lines, dramatic angle, intense expression",
            "dialogue": "close-up, emotional expression, speech bubble composition",
            "establishing": "wide shot, detailed background, atmospheric lighting",
            "dramatic": "dramatic lighting, shadows, intense mood, cinematic angle"
        }

        # Layout enhancer integration
        self.use_layout_enhancer = use_layout_enhancer and LAYOUT_ENHANCER_AVAILABLE
        self.layout_enhancer = None
        if self.use_layout_enhancer:
            try:
                self.layout_enhancer = PanelPromptEnhancer()
                print("🎨 Layout enhancer initialized for improved panel coherence")
            except Exception as e:
                print(f"Warning: Could not initialize layout enhancer: {e}")
                self.use_layout_enhancer = False
    
    def add_character(self, character: Character) -> None:
        """
        Add a character for consistent generation.
        
        Args:
            character: Character description
        """
        self.characters[character.name] = character
    
    def build_character_prompt(self, character_name: str) -> str:
        """
        Build character-specific prompt components.
        
        Args:
            character_name: Name of the character
            
        Returns:
            Character prompt string
        """
        if character_name not in self.characters:
            return f"{character_name}, manga character"
        
        char = self.characters[character_name]
        return f"{char.appearance}, {char.clothing}, {char.age_group}, {char.personality_traits}"
    
    def build_scene_prompt(
        self, 
        scene: Scene, 
        style_type: str = "establishing",
        panel_type: str = "medium_shot"
    ) -> str:
        """
        Build a complete scene prompt for image generation.
        
        Args:
            scene: Scene information
            style_type: Visual style (action, dialogue, establishing, dramatic)
            panel_type: Panel composition (close_up, medium_shot, wide_shot)
            
        Returns:
            Complete prompt string
        """
        prompt_parts = []
        
        # Add base quality and style
        prompt_parts.append(self.quality_tags)
        prompt_parts.append(self.base_style)
        
        # Add style preset
        if style_type in self.style_presets:
            prompt_parts.append(self.style_presets[style_type])
        
        # Add panel composition
        panel_compositions = {
            "close_up": "close-up shot, detailed facial expression",
            "medium_shot": "medium shot, upper body visible",
            "wide_shot": "wide shot, full scene visible, detailed background"
        }
        if panel_type in panel_compositions:
            prompt_parts.append(panel_compositions[panel_type])
        
        # Add characters
        character_prompts = []
        for char_name in scene.characters:
            char_prompt = self.build_character_prompt(char_name)
            character_prompts.append(char_prompt)
        
        if character_prompts:
            prompt_parts.append(", ".join(character_prompts))
        
        # Add scene elements
        prompt_parts.append(f"setting: {scene.location}")
        prompt_parts.append(f"time: {scene.time_of_day}")
        prompt_parts.append(f"mood: {scene.mood}")
        prompt_parts.append(f"action: {scene.action}")
        
        # Add scene description
        cleaned_description = self._clean_description(scene.description)
        prompt_parts.append(cleaned_description)
        
        return ", ".join(prompt_parts)
    
    def build_manga_panel_prompt(
        self,
        story_data: Dict[str, Any],
        scene_index: int,
        panel_index: int = 0
    ) -> Tuple[str, str]:
        """
        Build prompt for a specific manga panel with optional layout enhancement.

        Args:
            story_data: Complete story data
            scene_index: Index of the scene
            panel_index: Index of the panel within the scene

        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        # Extract actual scene content from story data
        scene_description = f"manga panel {scene_index + 1}"

        # Try different ways to extract scene content
        if isinstance(story_data, list) and scene_index < len(story_data):
            # If story_data is a list of scenes/paragraphs
            scene_description = story_data[scene_index]
        elif isinstance(story_data, dict):
            # If story_data is a dictionary, try various keys
            if "scenes" in story_data and scene_index < len(story_data["scenes"]):
                scene_description = story_data["scenes"][scene_index]
            elif "story_text" in story_data:
                # Parse story_text into paragraphs
                paragraphs = [p.strip() for p in story_data["story_text"].split('\n\n') if p.strip()]
                if scene_index < len(paragraphs):
                    scene_description = paragraphs[scene_index]

        # Parse scene description to extract elements
        location, time_of_day, mood, characters, action = self._parse_scene_description(scene_description)

        # Create scene object with parsed information
        scene = Scene(
            description=scene_description,
            location=location,
            time_of_day=time_of_day,
            mood=mood,
            characters=characters,
            action=action
        )

        # Build base prompt
        base_positive_prompt = self.build_scene_prompt(scene)
        negative_prompt = self.get_negative_prompt()

        # Apply layout enhancement if available
        if self.use_layout_enhancer and self.layout_enhancer:
            try:
                enhanced_prompt, layout_metadata = self.layout_enhancer.enhance_prompt(
                    base_prompt=base_positive_prompt,
                    scene_description=scene_description,
                    panel_index=panel_index
                )

                # Update layout memory for next panel
                self.layout_enhancer.update_panel_memory(layout_metadata)

                return enhanced_prompt, negative_prompt
            except Exception as e:
                print(f"Warning: Layout enhancement failed for panel {panel_index}: {e}")
                # Fall back to base prompt
                return base_positive_prompt, negative_prompt
        else:
            return base_positive_prompt, negative_prompt

    def _parse_scene_description(self, description: str) -> Tuple[str, str, str, List[str], str]:
        """
        Parse a scene description to extract key elements.

        Args:
            description: Scene description text

        Returns:
            Tuple of (location, time_of_day, mood, characters, action)
        """
        # Default values
        location = "indoor setting"
        time_of_day = "day"
        mood = "neutral"
        characters = ["character"]
        action = "standing"

        desc_lower = description.lower()

        # Extract location clues
        if any(word in desc_lower for word in ["forest", "woods", "trees"]):
            location = "forest"
        elif any(word in desc_lower for word in ["city", "street", "building", "urban"]):
            location = "city street"
        elif any(word in desc_lower for word in ["school", "classroom", "desk"]):
            location = "school"
        elif any(word in desc_lower for word in ["home", "house", "room", "kitchen", "bedroom"]):
            location = "indoor home"
        elif any(word in desc_lower for word in ["mountain", "cliff", "peak"]):
            location = "mountain"
        elif any(word in desc_lower for word in ["beach", "ocean", "sea", "water"]):
            location = "beach"

        # Extract time clues
        if any(word in desc_lower for word in ["night", "dark", "moon", "stars"]):
            time_of_day = "night"
        elif any(word in desc_lower for word in ["sunset", "dusk", "evening"]):
            time_of_day = "sunset"
        elif any(word in desc_lower for word in ["sunrise", "dawn", "morning"]):
            time_of_day = "morning"

        # Extract mood clues
        if any(word in desc_lower for word in ["angry", "rage", "furious", "mad"]):
            mood = "angry"
        elif any(word in desc_lower for word in ["sad", "crying", "tears", "sorrow"]):
            mood = "sad"
        elif any(word in desc_lower for word in ["happy", "joy", "smile", "laugh"]):
            mood = "happy"
        elif any(word in desc_lower for word in ["scared", "fear", "afraid", "terror"]):
            mood = "fearful"
        elif any(word in desc_lower for word in ["serious", "determined", "focused"]):
            mood = "serious"
        elif any(word in desc_lower for word in ["surprised", "shock", "amazed"]):
            mood = "surprised"

        # Extract action clues
        if any(word in desc_lower for word in ["running", "run", "sprint"]):
            action = "running"
        elif any(word in desc_lower for word in ["fighting", "fight", "battle", "attack"]):
            action = "fighting"
        elif any(word in desc_lower for word in ["walking", "walk", "moving"]):
            action = "walking"
        elif any(word in desc_lower for word in ["sitting", "sit", "seated"]):
            action = "sitting"
        elif any(word in desc_lower for word in ["talking", "speak", "conversation"]):
            action = "talking"
        elif any(word in desc_lower for word in ["looking", "watching", "observing"]):
            action = "looking"

        return location, time_of_day, mood, characters, action
    
    def get_negative_prompt(self, additional_negatives: List[str] = None) -> str:
        """
        Get negative prompt with optional additions.
        
        Args:
            additional_negatives: Additional negative terms
            
        Returns:
            Complete negative prompt
        """
        negatives = [self.negative_prompt]
        
        if additional_negatives:
            negatives.extend(additional_negatives)
        
        return ", ".join(negatives)
    
    def _clean_description(self, description: str) -> str:
        """
        Clean and optimize description text for SD prompts.
        
        Args:
            description: Raw description text
            
        Returns:
            Cleaned description
        """
        # Remove dialogue quotes
        cleaned = re.sub(r'"[^"]*"', '', description)
        
        # Remove excessive punctuation
        cleaned = re.sub(r'[.!?]+', '.', cleaned)
        
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Limit length
        if len(cleaned) > 200:
            cleaned = cleaned[:200] + "..."
        
        return cleaned
    
    def create_character_sheet_prompt(self, character: Character) -> str:
        """
        Create a character reference sheet prompt.
        
        Args:
            character: Character to create sheet for
            
        Returns:
            Character sheet prompt
        """
        prompt_parts = [
            self.quality_tags,
            "character reference sheet, multiple views, front view, side view, back view",
            self.base_style,
            f"character name: {character.name}",
            character.appearance,
            character.clothing,
            f"age: {character.age_group}",
            "white background, clean design, model sheet"
        ]
        
        return ", ".join(prompt_parts)
    
    def optimize_prompt_for_manga(self, base_prompt: str) -> str:
        """
        Optimize any prompt for manga-style generation.
        
        Args:
            base_prompt: Base prompt to optimize
            
        Returns:
            Manga-optimized prompt
        """
        manga_enhancers = [
            "manga style",
            "black and white",
            "high contrast",
            "clean line art",
            "screen tones",
            "dramatic shading"
        ]
        
        # Add manga enhancers if not already present
        enhanced_prompt = base_prompt
        for enhancer in manga_enhancers:
            if enhancer.lower() not in enhanced_prompt.lower():
                enhanced_prompt += f", {enhancer}"
        
        return enhanced_prompt

    def reset_layout_memory(self, sequence_id: str = None):
        """
        Reset layout memory for new manga sequence.

        Args:
            sequence_id: Optional sequence identifier
        """
        if self.use_layout_enhancer and self.layout_enhancer:
            self.layout_enhancer.reset_sequence(sequence_id)

    def get_layout_summary(self) -> Dict[str, Any]:
        """
        Get summary of current layout memory state.

        Returns:
            Dictionary with layout memory summary
        """
        if self.use_layout_enhancer and self.layout_enhancer:
            return self.layout_enhancer.get_sequence_summary()
        return {"layout_enhancer": "not_available"}


def create_story_prompts(story_data: Dict[str, Any], use_layout_enhancer: bool = True,
                        sequence_id: str = None) -> List[Tuple[str, str]]:
    """
    Create prompts for all scenes in a story with optional layout enhancement.

    Args:
        story_data: Complete story data
        use_layout_enhancer: Whether to use layout enhancement
        sequence_id: Optional sequence identifier for layout memory

    Returns:
        List of (positive_prompt, negative_prompt) tuples
    """
    builder = PromptBuilder(use_layout_enhancer=use_layout_enhancer)
    prompts = []

    # Reset layout memory for new sequence
    if use_layout_enhancer and sequence_id:
        builder.reset_layout_memory(sequence_id)

    # Determine number of scenes based on story data
    num_scenes = 6  # default

    if isinstance(story_data, list):
        # If story_data is a list of scenes/paragraphs
        num_scenes = len(story_data)
    elif isinstance(story_data, dict):
        if "scenes" in story_data:
            num_scenes = len(story_data["scenes"])
        elif "story_text" in story_data:
            # Count paragraphs in story_text
            paragraphs = [p.strip() for p in story_data["story_text"].split('\n\n') if p.strip()]
            num_scenes = len(paragraphs)
        else:
            num_scenes = story_data.get("scenes_count", 6)

    # Generate prompts for each scene with panel index
    for i in range(num_scenes):
        positive, negative = builder.build_manga_panel_prompt(story_data, i, panel_index=i)
        prompts.append((positive, negative))

    return prompts


if __name__ == "__main__":
    # Example usage
    builder = PromptBuilder()
    
    # Create example character
    protagonist = Character(
        name="Akira",
        appearance="spiky black hair, determined eyes, athletic build",
        clothing="school uniform, red scarf",
        personality_traits="brave, determined, hot-headed",
        age_group="teenager"
    )
    
    builder.add_character(protagonist)
    
    # Create example scene
    scene = Scene(
        description="The protagonist stands on a rooftop overlooking the city",
        location="city rooftop",
        time_of_day="sunset",
        mood="determined",
        characters=["Akira"],
        action="standing confidently"
    )
    
    prompt = builder.build_scene_prompt(scene, "dramatic", "medium_shot")
    print(f"Generated prompt: {prompt}")
    
    # Character sheet example
    char_sheet_prompt = builder.create_character_sheet_prompt(protagonist)
    print(f"Character sheet prompt: {char_sheet_prompt}")
