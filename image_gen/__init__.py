"""
Image Generation Module

ComfyUI integration and prompt building for manga-style image generation.
"""

from .comfy_client import ComfyUIClient, load_workflow_template, create_basic_txt2img_workflow
from .prompt_builder import (
    PromptBuilder,
    Character,
    Scene,
    create_story_prompts
)
from .image_generator import generate_image, generate_manga_sequence, batch_generate_with_retry

__all__ = [
    "ComfyUIClient",
    "load_workflow_template",
    "create_basic_txt2img_workflow",
    "PromptBuilder",
    "Character",
    "Scene",
    "create_story_prompts",
    "generate_image",
    "generate_manga_sequence",
    "batch_generate_with_retry"
]
