"""
Prompt Builder Module

Converts story data into Stable Diffusion prompts optimized for manga-style image generation.
Handles character consistency, scene composition, and visual style.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


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
    
    def __init__(self):
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
        Build prompt for a specific manga panel.
        
        Args:
            story_data: Complete story data
            scene_index: Index of the scene
            panel_index: Index of the panel within the scene
            
        Returns:
            Tuple of (positive_prompt, negative_prompt)
        """
        # Extract scene information (placeholder implementation)
        # TODO: Implement proper story data parsing
        
        scene_description = f"manga panel {panel_index + 1}"
        if "scenes" in story_data and scene_index < len(story_data["scenes"]):
            scene_description = story_data["scenes"][scene_index]
        
        # Create basic scene object
        scene = Scene(
            description=scene_description,
            location="generic location",
            time_of_day="day",
            mood="neutral",
            characters=["main character"],
            action="standing"
        )
        
        positive_prompt = self.build_scene_prompt(scene)
        negative_prompt = self.get_negative_prompt()
        
        return positive_prompt, negative_prompt
    
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


def create_story_prompts(story_data: Dict[str, Any]) -> List[Tuple[str, str]]:
    """
    Create prompts for all scenes in a story.
    
    Args:
        story_data: Complete story data
        
    Returns:
        List of (positive_prompt, negative_prompt) tuples
    """
    builder = PromptBuilder()
    prompts = []
    
    # TODO: Parse story_data properly and extract scenes
    # For now, create placeholder prompts
    
    num_scenes = story_data.get("scenes_count", 6)
    
    for i in range(num_scenes):
        positive, negative = builder.build_manga_panel_prompt(story_data, i)
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
