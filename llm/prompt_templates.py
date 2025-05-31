"""
Prompt Templates Module

Houses prompt patterns for different acts, scenes, and dialogue types
in manga story generation.
"""

from typing import Dict, List, Any


# Act-based story prompt templates
ACT_TEMPLATES = {
    "act_1_setup": {
        "template": """
        ACT 1 - SETUP ({title})
        
        Create the opening act for a manga story about: {premise}
        
        This act should:
        - Introduce the main character(s) and their ordinary world
        - Establish the setting and atmosphere
        - Present the inciting incident that starts the adventure
        - Show character motivations and initial conflicts
        
        Genre: {genre}
        Target audience: {audience}
        Tone: {tone}
        
        Structure this as {scenes} distinct scenes with clear visual descriptions for manga panels.
        Include dialogue, character actions, and environmental details.
        """,
        "variables": ["title", "premise", "genre", "audience", "tone", "scenes"]
    },
    
    "act_2_confrontation": {
        "template": """
        ACT 2 - CONFRONTATION ({title})
        
        Continue the manga story: {premise}
        
        Previous context: {previous_context}
        
        This act should:
        - Develop the main conflict and raise stakes
        - Show character growth and challenges
        - Introduce obstacles and complications
        - Build tension toward the climax
        - Develop relationships between characters
        
        Genre: {genre}
        Current mood: {mood}
        
        Create {scenes} scenes that escalate the conflict and deepen character development.
        Focus on visual storytelling suitable for manga panels.
        """,
        "variables": ["title", "premise", "previous_context", "genre", "mood", "scenes"]
    },
    
    "act_3_resolution": {
        "template": """
        ACT 3 - RESOLUTION ({title})
        
        Conclude the manga story: {premise}
        
        Previous story context: {previous_context}
        
        This act should:
        - Reach the climactic confrontation
        - Resolve the main conflict
        - Show character transformation
        - Provide satisfying conclusion
        - Tie up loose plot threads
        
        Genre: {genre}
        Desired ending: {ending_type}
        
        Create {scenes} scenes that bring the story to a compelling conclusion.
        Ensure visual impact for the final manga panels.
        """,
        "variables": ["title", "premise", "previous_context", "genre", "ending_type", "scenes"]
    }
}

# Scene-specific prompt templates
SCENE_TEMPLATES = {
    "action_scene": {
        "template": """
        Create an action scene for a manga:
        
        Context: {context}
        Characters involved: {characters}
        Action type: {action_type}
        
        Focus on:
        - Dynamic movement and poses
        - Impact moments and reactions
        - Environmental interaction
        - Clear sequence of events
        
        Describe the scene with manga panel composition in mind.
        """,
        "variables": ["context", "characters", "action_type"]
    },
    
    "dialogue_scene": {
        "template": """
        Create a dialogue-heavy scene for a manga:
        
        Context: {context}
        Characters: {characters}
        Conversation topic: {topic}
        Emotional tone: {emotion}
        
        Focus on:
        - Character expressions and body language
        - Speech patterns that match personalities
        - Visual subtext and reactions
        - Panel composition for conversation flow
        
        Include both dialogue and visual descriptions.
        """,
        "variables": ["context", "characters", "topic", "emotion"]
    },
    
    "establishing_scene": {
        "template": """
        Create an establishing scene for a manga:
        
        Location: {location}
        Time of day: {time}
        Atmosphere: {atmosphere}
        Purpose: {purpose}
        
        Focus on:
        - Environmental details and mood
        - Character introduction or positioning
        - Setting the tone for upcoming events
        - Visual elements that enhance storytelling
        
        Describe the scene with emphasis on visual composition.
        """,
        "variables": ["location", "time", "atmosphere", "purpose"]
    }
}

# Character dialogue templates
DIALOGUE_TEMPLATES = {
    "protagonist": {
        "determined": "I won't give up! {context}",
        "confused": "I don't understand... {context}",
        "angry": "This isn't right! {context}",
        "hopeful": "Maybe there's still a chance... {context}"
    },
    
    "antagonist": {
        "threatening": "You have no idea what you're dealing with. {context}",
        "mocking": "How naive... {context}",
        "revealing": "The truth is... {context}",
        "defeated": "Impossible... {context}"
    },
    
    "supporting": {
        "encouraging": "You can do this! {context}",
        "worried": "Be careful... {context}",
        "informative": "Listen, {context}",
        "comic_relief": "Well, this is awkward... {context}"
    }
}

# Genre-specific modifiers
GENRE_MODIFIERS = {
    "shonen": {
        "focus": "friendship, growth, determination, action",
        "tone": "energetic, optimistic, adventurous",
        "themes": "overcoming challenges, protecting others, becoming stronger"
    },
    
    "seinen": {
        "focus": "complex characters, moral ambiguity, realistic consequences",
        "tone": "mature, thoughtful, sometimes dark",
        "themes": "responsibility, sacrifice, difficult choices"
    },
    
    "slice_of_life": {
        "focus": "everyday moments, character relationships, small discoveries",
        "tone": "gentle, reflective, heartwarming",
        "themes": "personal growth, friendship, finding meaning in ordinary life"
    },
    
    "fantasy": {
        "focus": "magic systems, world-building, epic quests",
        "tone": "wonder, adventure, mystical",
        "themes": "destiny, power vs responsibility, good vs evil"
    }
}


def get_act_prompt(act_number: int, **kwargs) -> str:
    """
    Get a formatted prompt for a specific act.
    
    Args:
        act_number: Act number (1, 2, or 3)
        **kwargs: Variables to fill in the template
        
    Returns:
        Formatted prompt string
    """
    act_keys = ["act_1_setup", "act_2_confrontation", "act_3_resolution"]
    
    if act_number < 1 or act_number > 3:
        raise ValueError("Act number must be 1, 2, or 3")
    
    act_key = act_keys[act_number - 1]
    template_data = ACT_TEMPLATES[act_key]
    
    return template_data["template"].format(**kwargs)


def get_scene_prompt(scene_type: str, **kwargs) -> str:
    """
    Get a formatted prompt for a specific scene type.
    
    Args:
        scene_type: Type of scene (action_scene, dialogue_scene, establishing_scene)
        **kwargs: Variables to fill in the template
        
    Returns:
        Formatted prompt string
    """
    if scene_type not in SCENE_TEMPLATES:
        raise ValueError(f"Unknown scene type: {scene_type}")
    
    template_data = SCENE_TEMPLATES[scene_type]
    return template_data["template"].format(**kwargs)


def get_dialogue(character_type: str, emotion: str, context: str = "") -> str:
    """
    Get dialogue template for a character type and emotion.
    
    Args:
        character_type: Type of character (protagonist, antagonist, supporting)
        emotion: Emotional state
        context: Context to fill in the dialogue
        
    Returns:
        Formatted dialogue string
    """
    if character_type not in DIALOGUE_TEMPLATES:
        raise ValueError(f"Unknown character type: {character_type}")
    
    if emotion not in DIALOGUE_TEMPLATES[character_type]:
        raise ValueError(f"Unknown emotion '{emotion}' for character type '{character_type}'")
    
    return DIALOGUE_TEMPLATES[character_type][emotion].format(context=context)


def get_genre_modifier(genre: str) -> Dict[str, str]:
    """
    Get genre-specific modifiers for story generation.
    
    Args:
        genre: Genre name
        
    Returns:
        Dictionary with genre modifiers
    """
    return GENRE_MODIFIERS.get(genre, GENRE_MODIFIERS["shonen"])  # Default to shonen
