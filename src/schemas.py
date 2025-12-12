"""
Pydantic Schemas for MangaGen Pipeline

Defines strict data structures for:
- Scene plans (LLM output)
- Panel configurations
- Character definitions
- Bubble placements
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class CharacterAppearance(BaseModel):
    """Defines a character's visual appearance for consistency."""
    name: str = Field(..., description="Character's name")
    hair_color: str = Field(..., description="Hair color and style")
    eye_color: str = Field(default="", description="Eye color")
    clothing: str = Field(..., description="Clothing description")
    distinguishing_features: str = Field(default="", description="Scars, accessories, etc.")
    age_appearance: str = Field(default="young adult", description="Apparent age")
    
    def to_prompt(self) -> str:
        """Convert character appearance to image generation prompt."""
        parts = [
            f"{self.name}",
            f"{self.hair_color} hair",
        ]
        if self.eye_color:
            parts.append(f"{self.eye_color} eyes")
        parts.append(self.clothing)
        if self.distinguishing_features:
            parts.append(self.distinguishing_features)
        parts.append(f"{self.age_appearance}")
        return ", ".join(parts)


class DialogueLine(BaseModel):
    """A single line of dialogue in a panel."""
    speaker: str = Field(..., description="Character name speaking")
    text: str = Field(..., description="Dialogue text")
    emotion: str = Field(default="neutral", description="Emotional tone")
    bubble_type: Literal["speech", "thought", "shout", "whisper", "narration"] = Field(
        default="speech", description="Type of speech bubble"
    )


class PanelScene(BaseModel):
    """Defines a single manga panel."""
    panel_number: int = Field(..., ge=1, le=10, description="Panel number (1-indexed)")
    description: str = Field(..., min_length=10, description="Visual scene description")
    characters_present: List[str] = Field(default_factory=list, description="Characters in this panel")
    character_actions: str = Field(default="", description="What characters are doing")
    background: str = Field(..., description="Background/setting description")
    camera_angle: Literal["close-up", "medium", "wide", "extreme-close-up", "bird-eye", "low-angle"] = Field(
        default="medium", description="Camera perspective"
    )
    mood: str = Field(default="neutral", description="Emotional mood of the scene")
    dialogue: List[DialogueLine] = Field(default_factory=list, description="Dialogue lines in this panel")
    
    def to_image_prompt(self, style: str = "bw_manga", characters: dict = None) -> str:
        """Generate image prompt for this panel."""
        # Style-specific prefixes
        style_prefixes = {
            "bw_manga": "masterpiece, best quality, black and white manga, manga panel, ink drawing, high contrast",
            "color_anime": "masterpiece, best quality, anime style, vibrant colors, detailed artwork, anime illustration"
        }
        
        prefix = style_prefixes.get(style, style_prefixes["bw_manga"])
        
        # Build character descriptions
        char_desc = ""
        if characters and self.characters_present:
            char_parts = []
            for char_name in self.characters_present:
                if char_name in characters:
                    char_parts.append(characters[char_name].to_prompt())
            if char_parts:
                char_desc = ", ".join(char_parts) + ", "
        
        # Compose full prompt
        prompt_parts = [
            prefix,
            char_desc,
            self.description,
            self.character_actions,
            f"{self.background} background",
            f"{self.camera_angle} shot",
            f"{self.mood} atmosphere"
        ]
        
        return ", ".join(filter(None, prompt_parts))


class MangaScenePlan(BaseModel):
    """Complete scene plan for a manga page."""
    title: str = Field(..., description="Story/chapter title")
    style: Literal["bw_manga", "color_anime"] = Field(
        default="bw_manga", description="Visual style"
    )
    layout: Literal["2x2", "vertical_webtoon", "3_panel", "single"] = Field(
        default="2x2", description="Panel layout"
    )
    characters: List[CharacterAppearance] = Field(
        default_factory=list, description="Character definitions"
    )
    panels: List[PanelScene] = Field(..., min_length=1, max_length=10, description="Panel scenes")
    
    @field_validator('panels')
    @classmethod
    def validate_panel_numbers(cls, panels: List[PanelScene]) -> List[PanelScene]:
        """Ensure panel numbers are sequential starting from 1."""
        for i, panel in enumerate(panels):
            if panel.panel_number != i + 1:
                panel.panel_number = i + 1
        return panels
    
    def get_character_dict(self) -> dict:
        """Get characters as a dict keyed by name."""
        return {char.name: char for char in self.characters}
    
    def get_panel_count(self) -> int:
        """Get number of panels based on layout."""
        layout_counts = {
            "2x2": 4,
            "vertical_webtoon": 3,
            "3_panel": 3,
            "single": 1
        }
        return min(len(self.panels), layout_counts.get(self.layout, 4))


class BubblePlacement(BaseModel):
    """Placement information for a dialogue bubble."""
    panel_number: int = Field(..., description="Panel this bubble belongs to")
    x: int = Field(..., description="X position")
    y: int = Field(..., description="Y position")
    width: int = Field(..., description="Bubble width")
    height: int = Field(..., description="Bubble height")
    text: str = Field(..., description="Dialogue text")
    speaker: str = Field(default="", description="Speaker name")
    bubble_type: str = Field(default="speech", description="Bubble type")


class PanelOutput(BaseModel):
    """Output metadata for a generated panel."""
    panel_number: int
    image_path: str
    prompt_used: str
    generation_params: dict = Field(default_factory=dict)
    bubbles: List[BubblePlacement] = Field(default_factory=list)


class MangaOutput(BaseModel):
    """Complete manga generation output."""
    title: str
    style: str
    layout: str
    panels: List[PanelOutput]
    pdf_path: Optional[str] = None
    zip_path: Optional[str] = None
