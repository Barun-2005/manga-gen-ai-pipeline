#!/usr/bin/env python3
"""
Character DNA System - For Visual Consistency

Builds and maintains "Visual DNA" tags for each character that get injected
into every panel prompt to ensure consistent appearance across all panels.

Works with ANY image model (Pollinations, FLUX, SD, Z-Image) by using smart
prompt engineering instead of requiring LoRAs or IP-Adapters.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class CharacterDNA:
    """Visual DNA for a character - consistent tags for all panels."""
    name: str
    appearance: str  # Raw description from Story Director
    visual_tags: List[str] = field(default_factory=list)  # Comma-separated tags for prompts
    personality: str = ""
    role: str = ""
    
    def build_visual_tags(self, style: str = "bw_manga") -> List[str]:
        """
        Convert appearance description to visual tags for image prompts.
        
        Args:
            style: 'bw_manga' or 'color_anime'
        
        Returns:
            List of visual tags to inject into prompts
        """
        tags = []
        
        # Parse appearance for key features
        appearance_lower = self.appearance.lower()
        
        # Hair features
        if "hair" in appearance_lower:
            # Extract hair color/style
            hair_parts = []
            for word in appearance_lower.split():
                if word in ["black", "white", "silver", "gray", "grey", "blonde", "brown", "red", "pink", "blue", "purple", "green"]:
                    hair_parts.append(word)
                if word in ["short", "long", "messy", "spiky", "straight", "curly", "wavy"]:
                    hair_parts.append(word)
            
            if hair_parts:
                tags.append(f"{' '.join(hair_parts)} hair")
        
        # Eye features
        if "eye" in appearance_lower:
            for word in appearance_lower.split():
                if word in ["blue", "green", "brown", "gray", "grey", "red", "golden", "emerald", "amber"]:
                    tags.append(f"{word} eyes")
                    break
        
        # Special features (scars, marks, etc.)
        if "scar" in appearance_lower:
            tags.append("facial scar")
        if "glasses" in appearance_lower or "spectacles" in appearance_lower:
            tags.append("wearing glasses")
        
        # Age/build indicators
        if any(word in appearance_lower for word in ["young", "teen", "adolescent"]):
            tags.append("young")
        elif any(word in appearance_lower for word in ["old", "elder", "elderly"]):
            tags.append("elderly")
        
        if any(word in appearance_lower for word in ["tall", "large", "muscular", "strong"]):
            tags.append("athletic build")
        elif any(word in appearance_lower for word in ["small", "petite", "slim", "thin"]):
            tags.append("slim build")
        
        # Style-specific additions
        if style == "bw_manga":
            # For B/W manga, emphasize line work
            base_tags = ["manga style", "monochrome", "ink lineart", "screentone", "high contrast"]
        else:
            # For color anime, keep vibrant
            base_tags = ["anime style", "vibrant", "cel shading", "studio quality"]
        
        self.visual_tags = base_tags + tags
        return self.visual_tags
    
    def get_prompt_injection(self) -> str:
        """Get the visual tags as a comma-separated string to inject in prompts."""
        if not self.visual_tags:
            return ""
        return ", ".join(self.visual_tags)


class CharacterDNAManager:
    """Manages Character DNA for consistent visual prompts across all panels."""
    
    def __init__(self, style: str = "bw_manga"):
        self.style = style
        self.characters: Dict[str, CharacterDNA] = {}
    
    def register_character(self, name: str, appearance: str, personality: str = "", role: str = "") -> CharacterDNA:
        """
        Register a new character and build their visual DNA.
        
        Args:
            name: Character name
            appearance: Raw appearance description from Story Director
            personality: Character personality
            role: Character role (protagonist, antagonist, etc.)
        
        Returns:
            CharacterDNA instance
        """
        dna = CharacterDNA(
            name=name,
            appearance=appearance,
            personality=personality,
            role=role
        )
        dna.build_visual_tags(self.style)
        self.characters[name] = dna
        print(f"   🧬 Character DNA registered: {name}")
        print(f"      Visual Tags: {dna.get_prompt_injection()}")
        return dna
    
    def get_character_tags(self, name: str) -> str:
        """Get visual tags for a specific character."""
        if name in self.characters:
            return self.characters[name].get_prompt_injection()
        return ""
    
    def enhance_panel_prompt(self, base_prompt: str, characters_present: List[str]) -> str:
        """
        Inject character DNA into a panel prompt for consistency.
        
        Args:
            base_prompt: Base scene description from Story Director
            characters_present: List of character names in this panel
        
        Returns:
            Enhanced prompt with character DNA injected
        """
        # Collect DNA tags for all characters in this panel
        char_tags = []
        for char_name in characters_present:
            tags = self.get_character_tags(char_name)
            if tags:
                char_tags.append(tags)
        
        if not char_tags:
            # No characters or no DNA - add base style tags only
            if self.style == "bw_manga":
                return f"{base_prompt}, manga style, monochrome, ink lineart, screentone, high contrast"
            else:
                return f"{base_prompt}, anime style, vibrant, cel shading, studio quality"
        
        # Inject character DNA into prompt
        # Strategy: Base description + character-specific tags
        dna_injection = ", ".join(set(", ".join(char_tags).split(", ")))  # Deduplicate tags
        enhanced = f"{base_prompt}, {dna_injection}"
        
        return enhanced
    
    def register_characters_from_plan(self, chapter_plan: Dict) -> None:
        """Register all characters from a Story Director chapter plan."""
        characters = chapter_plan.get('characters', [])
        for char in characters:
            self.register_character(
                name=char.get('name', 'Unknown'),
                appearance=char.get('appearance', ''),
                personality=char.get('personality', ''),
                role=char.get('role', '')
            )
