import os
import sys
import requests
from typing import Optional

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def generate_dialogue_for_panel(prompt: str, output_path: str) -> str:
    """
    Generate dialogue text for a manga panel based on the prompt.
    
    Args:
        prompt: Description of the character/scene
        output_path: Path to save the dialogue text
        
    Returns:
        Generated dialogue text
    """
    # Simple dialogue generation based on emotion and pose keywords
    dialogue_map = {
        "happy": [
            "This is amazing!",
            "I can't believe it!",
            "Everything is perfect!",
            "What a wonderful day!"
        ],
        "angry": [
            "I won't forgive this!",
            "How dare you!",
            "This is unacceptable!",
            "I've had enough!"
        ],
        "surprised": [
            "What?! No way!",
            "I can't believe my eyes!",
            "This is impossible!",
            "How did this happen?!"
        ],
        "sad": [
            "Why did this happen?",
            "I feel so alone...",
            "Nothing will ever be the same.",
            "I wish things were different."
        ],
        "neutral": [
            "I see.",
            "Understood.",
            "Let's proceed.",
            "What should we do next?"
        ]
    }
    
    # Extract emotion from prompt
    emotion = "neutral"
    for key in dialogue_map.keys():
        if key in prompt.lower():
            emotion = key
            break
    
    # Select dialogue based on emotion
    import random
    dialogue_options = dialogue_map.get(emotion, dialogue_map["neutral"])
    selected_dialogue = random.choice(dialogue_options)
    
    # Add pose-based context
    if "arms_crossed" in prompt.lower():
        if emotion == "angry":
            selected_dialogue = f"*crosses arms* {selected_dialogue}"
        else:
            selected_dialogue = f"*stands with arms crossed* {selected_dialogue}"
    elif "openpose" in prompt.lower() or "standing" in prompt.lower():
        selected_dialogue = f"*stands confidently* {selected_dialogue}"
    
    # Save to file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"Panel Dialogue:\n")
        f.write(f"Scene: {prompt}\n")
        f.write(f"Emotion: {emotion}\n")
        f.write(f"Dialogue: \"{selected_dialogue}\"\n")
    
    print(f"Generated dialogue: {output_path}")
    return selected_dialogue
