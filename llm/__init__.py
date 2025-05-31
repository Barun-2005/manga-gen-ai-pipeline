"""
LLM Module

Large Language Model integration for manga story generation.
"""

from .story_generator import StoryGenerator, generate_manga_story, generate_story
from .prompt_templates import (
    ACT_TEMPLATES,
    SCENE_TEMPLATES,
    DIALOGUE_TEMPLATES,
    GENRE_MODIFIERS,
    get_act_prompt,
    get_scene_prompt,
    get_dialogue,
    get_genre_modifier
)

__all__ = [
    "StoryGenerator",
    "generate_manga_story",
    "generate_story",
    "ACT_TEMPLATES",
    "SCENE_TEMPLATES",
    "DIALOGUE_TEMPLATES",
    "GENRE_MODIFIERS",
    "get_act_prompt",
    "get_scene_prompt",
    "get_dialogue",
    "get_genre_modifier"
]
