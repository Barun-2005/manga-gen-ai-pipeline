"""
Prompt Builder Module

Converts story paragraphs into descriptive image prompts for manga panel generation.
Uses predefined rules and templates to create optimized prompts for image generation.
"""

import re
from typing import List, Dict, Any, Optional


def build_image_prompts(story_paragraphs: List[str]) -> List[str]:
    """
    Converts each story paragraph into a descriptive image prompt using predefined rules or templates.
    
    Args:
        story_paragraphs: List of story paragraphs, each representing a scene/panel
        
    Returns:
        List of image generation prompts optimized for manga-style art
    """
    image_prompts = []
    
    for i, paragraph in enumerate(story_paragraphs):
        # Build the image prompt for this paragraph
        prompt = _build_single_image_prompt(paragraph, i + 1)
        image_prompts.append(prompt)
    
    return image_prompts


def _build_single_image_prompt(paragraph: str, panel_number: int) -> str:
    """
    Build a single image prompt from a story paragraph.
    
    Args:
        paragraph: Story paragraph describing a scene
        panel_number: Panel number (1-6)
        
    Returns:
        Optimized image generation prompt
    """
    # Base manga style elements
    base_style = "manga style, anime art, black and white, high contrast, detailed line art"
    quality_tags = "masterpiece, best quality, highly detailed, professional manga artwork"
    
    # Extract key elements from the paragraph
    scene_elements = _extract_scene_elements(paragraph)
    
    # Determine panel composition based on content and position
    composition = _determine_panel_composition(paragraph, panel_number)
    
    # Build character descriptions
    character_desc = _extract_character_descriptions(paragraph)
    
    # Build environment/setting description
    environment_desc = _extract_environment_description(paragraph)
    
    # Build action/emotion description
    action_desc = _extract_action_description(paragraph)
    
    # Combine all elements into a cohesive prompt
    prompt_parts = [
        quality_tags,
        base_style,
        composition,
        character_desc,
        environment_desc,
        action_desc,
        scene_elements
    ]
    
    # Filter out empty parts and join
    prompt = ", ".join([part for part in prompt_parts if part.strip()])
    
    # Add negative prompt elements
    negative_elements = "blurry, low quality, distorted, ugly, bad anatomy, extra limbs, text, watermark"
    
    return f"{prompt} | NEGATIVE: {negative_elements}"


def _extract_scene_elements(paragraph: str) -> str:
    """Extract key visual elements from the paragraph."""
    # Keywords that indicate specific visual elements
    visual_keywords = {
        'magic': 'magical effects, glowing energy, mystical aura',
        'fight': 'dynamic action, motion lines, impact effects',
        'city': 'urban background, buildings, modern setting',
        'school': 'school uniform, classroom, educational setting',
        'night': 'dark atmosphere, moonlight, shadows',
        'day': 'bright lighting, clear sky, daylight',
        'forest': 'trees, natural setting, outdoor environment',
        'dramatic': 'dramatic lighting, intense shadows, emotional atmosphere'
    }
    
    elements = []
    paragraph_lower = paragraph.lower()
    
    for keyword, description in visual_keywords.items():
        if keyword in paragraph_lower:
            elements.append(description)
    
    return ", ".join(elements) if elements else "detailed background"


def _determine_panel_composition(paragraph: str, panel_number: int) -> str:
    """Determine the best panel composition based on content and position."""
    paragraph_lower = paragraph.lower()
    
    # Panel composition based on story position
    if panel_number == 1:
        base_comp = "establishing shot, wide view"
    elif panel_number == 6:
        base_comp = "dramatic close-up, emotional finale"
    else:
        base_comp = "medium shot, balanced composition"
    
    # Modify based on content
    if any(word in paragraph_lower for word in ['dialogue', 'said', 'spoke', 'whispered']):
        return "close-up shot, detailed facial expressions, speech bubble composition"
    elif any(word in paragraph_lower for word in ['action', 'fight', 'battle', 'attack']):
        return "dynamic angle, action shot, motion blur effects"
    elif any(word in paragraph_lower for word in ['landscape', 'city', 'building', 'environment']):
        return "wide establishing shot, detailed background, environmental focus"
    
    return base_comp


def _extract_character_descriptions(paragraph: str) -> str:
    """Extract and enhance character descriptions."""
    # Common character archetypes and their visual descriptions
    character_types = {
        'ninja': 'ninja outfit, athletic build, determined expression',
        'student': 'school uniform, youthful appearance, backpack',
        'warrior': 'armor, strong physique, battle-ready stance',
        'mage': 'robes, magical staff, mystical appearance',
        'protagonist': 'main character, heroic pose, distinctive features'
    }
    
    paragraph_lower = paragraph.lower()
    descriptions = []
    
    # Check for character types
    for char_type, desc in character_types.items():
        if char_type in paragraph_lower:
            descriptions.append(desc)
    
    # Extract age/gender indicators
    if any(word in paragraph_lower for word in ['young', 'teenager', 'student']):
        descriptions.append('teenage character')
    elif any(word in paragraph_lower for word in ['adult', 'man', 'woman']):
        descriptions.append('adult character')
    
    # Extract emotional states
    emotions = {
        'angry': 'angry expression, clenched fists',
        'sad': 'sad expression, downcast eyes',
        'happy': 'smiling, cheerful expression',
        'determined': 'determined expression, focused eyes',
        'surprised': 'surprised expression, wide eyes'
    }
    
    for emotion, desc in emotions.items():
        if emotion in paragraph_lower:
            descriptions.append(desc)
    
    return ", ".join(descriptions) if descriptions else "manga character, expressive features"


def _extract_environment_description(paragraph: str) -> str:
    """Extract environment and setting descriptions."""
    environments = {
        'city': 'urban environment, city buildings, modern architecture',
        'school': 'school building, classroom, educational environment',
        'forest': 'forest setting, trees, natural environment',
        'home': 'indoor setting, residential, comfortable atmosphere',
        'street': 'street scene, urban setting, public space',
        'rooftop': 'rooftop setting, city skyline, elevated view',
        'park': 'park setting, outdoor, peaceful environment'
    }
    
    paragraph_lower = paragraph.lower()
    
    for env_type, desc in environments.items():
        if env_type in paragraph_lower:
            return desc
    
    # Time of day
    if any(word in paragraph_lower for word in ['night', 'evening', 'dark']):
        return "nighttime setting, dark atmosphere, artificial lighting"
    elif any(word in paragraph_lower for word in ['morning', 'dawn', 'sunrise']):
        return "morning setting, soft lighting, peaceful atmosphere"
    
    return "detailed background, atmospheric setting"


def _extract_action_description(paragraph: str) -> str:
    """Extract action and movement descriptions."""
    actions = {
        'running': 'running pose, motion lines, dynamic movement',
        'jumping': 'jumping action, airborne pose, dynamic angle',
        'fighting': 'combat pose, action lines, intense movement',
        'walking': 'walking pose, casual movement, natural stance',
        'standing': 'standing pose, confident stance, stable composition',
        'sitting': 'sitting pose, relaxed position, calm composition'
    }
    
    paragraph_lower = paragraph.lower()
    
    for action, desc in actions.items():
        if action in paragraph_lower:
            return desc
    
    # Check for general movement indicators
    if any(word in paragraph_lower for word in ['moved', 'motion', 'speed', 'fast']):
        return "dynamic movement, motion effects, speed lines"
    
    return "natural pose, balanced composition"


def enhance_prompt_for_style(prompt: str, style: str = "shonen") -> str:
    """
    Enhance the prompt based on manga style.
    
    Args:
        prompt: Base image prompt
        style: Manga style (shonen, seinen, slice_of_life, fantasy)
        
    Returns:
        Style-enhanced prompt
    """
    style_enhancements = {
        "shonen": "energetic, action-packed, heroic, bright colors, dynamic poses",
        "seinen": "mature, realistic, detailed, sophisticated, complex emotions",
        "slice_of_life": "peaceful, everyday, warm atmosphere, gentle expressions, natural lighting",
        "fantasy": "magical, mystical, otherworldly, fantasy elements, epic scale"
    }
    
    enhancement = style_enhancements.get(style, style_enhancements["shonen"])
    return f"{prompt}, {enhancement}"


def create_panel_sequence_prompts(story_paragraphs: List[str], style: str = "shonen") -> List[Dict[str, Any]]:
    """
    Create a complete sequence of panel prompts with metadata.
    
    Args:
        story_paragraphs: List of story paragraphs
        style: Manga style
        
    Returns:
        List of prompt dictionaries with metadata
    """
    base_prompts = build_image_prompts(story_paragraphs)
    
    panel_prompts = []
    for i, (paragraph, prompt) in enumerate(zip(story_paragraphs, base_prompts)):
        enhanced_prompt = enhance_prompt_for_style(prompt, style)
        
        panel_data = {
            "panel_number": i + 1,
            "story_text": paragraph,
            "image_prompt": enhanced_prompt,
            "style": style,
            "composition_type": _determine_panel_composition(paragraph, i + 1),
            "estimated_complexity": _estimate_complexity(paragraph)
        }
        
        panel_prompts.append(panel_data)
    
    return panel_prompts


def _estimate_complexity(paragraph: str) -> str:
    """Estimate the visual complexity of a scene."""
    paragraph_lower = paragraph.lower()
    
    # Count complexity indicators
    complexity_indicators = [
        'multiple', 'crowd', 'many', 'several', 'background', 'detailed',
        'complex', 'intricate', 'elaborate', 'busy', 'chaotic'
    ]
    
    action_indicators = [
        'fight', 'battle', 'action', 'explosion', 'magic', 'effects'
    ]
    
    complexity_count = sum(1 for indicator in complexity_indicators if indicator in paragraph_lower)
    action_count = sum(1 for indicator in action_indicators if indicator in paragraph_lower)
    
    total_score = complexity_count + action_count
    
    if total_score >= 3:
        return "high"
    elif total_score >= 1:
        return "medium"
    else:
        return "low"


if __name__ == "__main__":
    # Example usage
    test_paragraphs = [
        "A young ninja student stands on a school rooftop, looking out over the bustling city below.",
        "Suddenly, magical energy begins to glow around his hands, surprising him greatly.",
        "A mysterious figure appears in the shadows, watching the young ninja with interest.",
        "The ninja faces a difficult choice between using his newfound powers or staying hidden.",
        "An intense magical battle erupts on the rooftop with dramatic lighting and effects.",
        "The story concludes with the ninja accepting his destiny, determined to protect the city."
    ]
    
    # Test basic prompt building
    prompts = build_image_prompts(test_paragraphs)
    print("Generated Image Prompts:")
    for i, prompt in enumerate(prompts, 1):
        print(f"Panel {i}: {prompt[:100]}...")
    
    # Test enhanced sequence creation
    print("\nEnhanced Panel Sequence:")
    panel_sequence = create_panel_sequence_prompts(test_paragraphs, "shonen")
    for panel in panel_sequence:
        print(f"Panel {panel['panel_number']}: {panel['composition_type']} - {panel['estimated_complexity']} complexity")
