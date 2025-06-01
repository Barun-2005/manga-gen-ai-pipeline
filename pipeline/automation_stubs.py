"""
Automation Helper Functions

This module contains helper functions for automated manga generation:
1. Pose generation from text descriptions
2. Style assignment based on content analysis
3. Text-to-panel pipeline utilities

These functions provide basic automation for the manga generation pipeline.
"""

from typing import Dict, Any


def generate_pose_from_text(text_description: str) -> Dict[str, Any]:
    """
    Generate pose/composition data from text description.

    Analyzes text for character positions, actions, and emotions to suggest
    appropriate pose and composition settings for manga panel generation.

    Args:
        text_description: Natural language description of the scene

    Returns:
        Dictionary containing pose/composition data
    """
    # Basic keyword analysis for pose detection
    text_lower = text_description.lower()

    # Detect action types
    action_keywords = {
        "running": "dynamic_run",
        "jumping": "mid_jump",
        "fighting": "combat_stance",
        "sitting": "seated",
        "standing": "standing",
        "walking": "walking",
        "flying": "airborne",
        "falling": "falling",
        "dodging": "evasive",
        "attacking": "attack_pose"
    }

    pose_type = "standing"  # default
    for keyword, pose in action_keywords.items():
        if keyword in text_lower:
            pose_type = pose
            break

    # Detect composition based on scene description
    composition = "medium_shot"
    if any(word in text_lower for word in ["close", "face", "eyes", "expression"]):
        composition = "close_up"
    elif any(word in text_lower for word in ["landscape", "city", "background", "distance"]):
        composition = "wide_shot"

    return {
        "pose_type": pose_type,
        "composition": composition,
        "suggested_angle": "eye_level",
        "dynamic_level": "medium" if "action" in text_lower else "low",
        "character_count": 1,  # simplified for now
        "notes": f"Auto-detected from: {text_description[:50]}..."
    }


def assign_style_automatically(text_prompt: str) -> Dict[str, str]:
    """
    Automatically assign visual style based on text content.

    Analyzes the text prompt to determine appropriate manga style,
    art parameters, and visual treatment for the panel.

    Args:
        text_prompt: Text description of the scene

    Returns:
        Dictionary containing style assignments
    """
    text_lower = text_prompt.lower()

    # Detect genre based on keywords
    genre_keywords = {
        "shonen": ["fight", "battle", "power", "training", "tournament", "hero"],
        "seinen": ["dark", "mature", "complex", "psychological", "adult"],
        "shoujo": ["romance", "love", "school", "friendship", "emotion"],
        "slice_of_life": ["daily", "ordinary", "peaceful", "home", "family"],
        "fantasy": ["magic", "dragon", "spell", "wizard", "mystical"],
        "horror": ["scary", "ghost", "monster", "fear", "nightmare"]
    }

    detected_genre = "shonen"  # default
    for genre, keywords in genre_keywords.items():
        if any(keyword in text_lower for keyword in keywords):
            detected_genre = genre
            break

    # Assign style based on detected genre
    style_configs = {
        "shonen": {
            "line_weight": "bold",
            "shading_style": "dramatic",
            "background_detail": "high",
            "color_palette": "high_contrast"
        },
        "seinen": {
            "line_weight": "fine",
            "shading_style": "realistic",
            "background_detail": "detailed",
            "color_palette": "muted"
        },
        "shoujo": {
            "line_weight": "delicate",
            "shading_style": "soft",
            "background_detail": "decorative",
            "color_palette": "pastel"
        },
        "slice_of_life": {
            "line_weight": "clean",
            "shading_style": "simple",
            "background_detail": "moderate",
            "color_palette": "natural"
        }
    }

    style_config = style_configs.get(detected_genre, style_configs["shonen"])
    style_config["manga_genre"] = detected_genre
    style_config["notes"] = f"Auto-detected genre: {detected_genre}"

    return style_config


# Additional helper functions can be added here as needed


# Configuration presets for different automation levels
AUTOMATION_PRESETS = {
    "full_auto": {
        "description": "Fully automated text-to-panel generation",
        "pose_generation": True,
        "style_assignment": True,
        "quality_control": True,
        "human_review": False
    },
    "assisted": {
        "description": "Semi-automated with human review points",
        "pose_generation": True,
        "style_assignment": True,
        "quality_control": True,
        "human_review": True
    },
    "manual": {
        "description": "Manual control with automated suggestions",
        "pose_generation": False,
        "style_assignment": False,
        "quality_control": True,
        "human_review": True
    }
}



