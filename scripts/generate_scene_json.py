#!/usr/bin/env python3
"""
MangaGen - Scene JSON Generator

Takes a story prompt and generates a structured scene plan using Google Gemini.

Usage:
    python scripts/generate_scene_json.py "Your story prompt here"
    python scripts/generate_scene_json.py "Your story prompt" --style color_anime --layout 3_panel
    python scripts/generate_scene_json.py "Your story prompt" --output my_scene.json

Environment:
    GEMINI_API_KEY: Your Google Gemini API key (required)
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import google.generativeai as genai
    from pydantic import ValidationError
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install google-generativeai pydantic")
    sys.exit(1)

from src.schemas import MangaScenePlan, CharacterAppearance, PanelScene, DialogueLine


# ============================================
# Gemini Prompt Template
# ============================================

SCENE_GENERATION_PROMPT = '''You are a professional manga storyboard artist and writer. 
Given a story premise, create a detailed scene plan for a manga page.

STORY PREMISE:
{story_prompt}

REQUIREMENTS:
- Style: {style} (either "bw_manga" for black and white manga, or "color_anime" for colorful anime style)
- Layout: {layout} (affects number of panels)
- Generate exactly {panel_count} panels

For each CHARACTER mentioned or implied, define their appearance with:
- name: Character's name
- hair_color: Hair color and style (e.g., "messy silver", "long black ponytail")
- eye_color: Eye color (e.g., "bright blue", "amber")
- clothing: What they're wearing (be specific!)
- distinguishing_features: Scars, accessories, tattoos, etc.
- age_appearance: How old they look (e.g., "young adult", "teenager", "middle-aged")

For each PANEL, provide:
- panel_number: Sequential number (1, 2, 3, ...)
- description: Detailed visual description of what's happening
- characters_present: List of character names in this panel
- character_actions: What the characters are doing
- background: Background/environment description
- camera_angle: One of: "close-up", "medium", "wide", "extreme-close-up", "bird-eye", "low-angle"
- mood: Emotional tone (e.g., "tense", "peaceful", "exciting", "mysterious")
- dialogue: List of dialogue lines with speaker, text, emotion, and bubble_type

DIALOGUE bubble_type OPTIONS:
- "speech": Normal talking
- "thought": Internal thoughts (cloud bubble)
- "shout": Yelling/excitement (jagged bubble)
- "whisper": Quiet speech (dotted bubble)
- "narration": Story narration (rectangular box)

OUTPUT STRICT JSON matching this exact structure:
{{
  "title": "Chapter/Story Title",
  "style": "{style}",
  "layout": "{layout}",
  "characters": [
    {{
      "name": "Character Name",
      "hair_color": "description",
      "eye_color": "color",
      "clothing": "detailed clothing description",
      "distinguishing_features": "any notable features",
      "age_appearance": "apparent age"
    }}
  ],
  "panels": [
    {{
      "panel_number": 1,
      "description": "What is visually shown",
      "characters_present": ["Character1", "Character2"],
      "character_actions": "What they are doing",
      "background": "Environment description",
      "camera_angle": "medium",
      "mood": "mysterious",
      "dialogue": [
        {{
          "speaker": "Character1",
          "text": "What they say",
          "emotion": "curious",
          "bubble_type": "speech"
        }}
      ]
    }}
  ]
}}

IMPORTANT:
- Output ONLY valid JSON, no markdown formatting, no code blocks
- Be specific and visual in descriptions
- Keep dialogue concise (manga bubbles are small!)
- Ensure character appearances are consistent across panels
- Make the story flow naturally from panel to panel
'''


def get_panel_count(layout: str) -> int:
    """Get recommended panel count for a layout."""
    layout_counts = {
        "2x2": 4,
        "vertical_webtoon": 3,
        "3_panel": 3,
        "single": 1
    }
    return layout_counts.get(layout, 4)


def generate_scene_plan(
    story_prompt: str,
    style: str = "bw_manga",
    layout: str = "2x2",
    api_key: Optional[str] = None,
    model_name: str = "gemini-2.0-flash"
) -> MangaScenePlan:
    """
    Generate a scene plan from a story prompt using Gemini.
    
    Args:
        story_prompt: The story/scene description
        style: Visual style ("bw_manga" or "color_anime")
        layout: Panel layout ("2x2", "vertical_webtoon", "3_panel", "single")
        api_key: Gemini API key (or use GEMINI_API_KEY env var)
        model_name: Gemini model to use
        
    Returns:
        MangaScenePlan: Validated scene plan
        
    Raises:
        ValueError: If API key missing or generation fails
    """
    # Get API key
    api_key = api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY not found. Set it as environment variable or pass api_key parameter.\n"
            "Get your key at: https://aistudio.google.com/app/apikey"
        )
    
    # Configure Gemini
    genai.configure(api_key=api_key)
    
    # Get panel count for layout
    panel_count = get_panel_count(layout)
    
    # Build prompt
    prompt = SCENE_GENERATION_PROMPT.format(
        story_prompt=story_prompt,
        style=style,
        layout=layout,
        panel_count=panel_count
    )
    
    print(f"🤖 Generating scene plan with Gemini ({model_name})...")
    print(f"   Style: {style}")
    print(f"   Layout: {layout} ({panel_count} panels)")
    
    # Generate
    try:
        model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.9,
                "max_output_tokens": 4096,
            }
        )
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
    except Exception as e:
        raise ValueError(f"Gemini API error: {e}")
    
    # Clean response (remove markdown code blocks if present)
    if response_text.startswith("```"):
        # Remove ```json and ``` markers
        lines = response_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        response_text = "\n".join(lines)
    
    # Parse JSON
    try:
        scene_data = json.loads(response_text)
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parsing error: {e}")
        print(f"Raw response:\n{response_text[:500]}...")
        raise ValueError(f"Failed to parse Gemini response as JSON: {e}")
    
    # Validate with Pydantic
    try:
        scene_plan = MangaScenePlan(**scene_data)
    except ValidationError as e:
        print(f"⚠️ Schema validation error: {e}")
        print(f"Attempting to fix common issues...")
        
        # Try to fix common issues
        if "panels" in scene_data:
            for i, panel in enumerate(scene_data["panels"]):
                panel["panel_number"] = i + 1
                if "dialogue" not in panel:
                    panel["dialogue"] = []
        
        if "characters" not in scene_data:
            scene_data["characters"] = []
        
        scene_data["style"] = style
        scene_data["layout"] = layout
        
        # Try validation again
        scene_plan = MangaScenePlan(**scene_data)
    
    print(f"✅ Generated scene plan: '{scene_plan.title}'")
    print(f"   Characters: {[c.name for c in scene_plan.characters]}")
    print(f"   Panels: {len(scene_plan.panels)}")
    
    return scene_plan


def save_scene_plan(scene_plan: MangaScenePlan, output_path: Path) -> None:
    """Save scene plan to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(scene_plan.model_dump(), f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved scene plan to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate manga scene plan from story prompt using Gemini",
        epilog="Example: python generate_scene_json.py 'A ninja discovers a secret temple'"
    )
    parser.add_argument(
        "prompt",
        type=str,
        help="Story prompt describing the manga scene"
    )
    parser.add_argument(
        "--style",
        type=str,
        choices=["bw_manga", "color_anime"],
        default="bw_manga",
        help="Visual style (default: bw_manga)"
    )
    parser.add_argument(
        "--layout",
        type=str,
        choices=["2x2", "vertical_webtoon", "3_panel", "single"],
        default="2x2",
        help="Panel layout (default: 2x2)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="scene_plan.json",
        help="Output JSON file path (default: scene_plan.json)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gemini-2.0-flash",
        help="Gemini model to use (default: gemini-2.0-flash)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🎨 MangaGen - Scene Generator")
    print("=" * 50)
    print(f"📝 Prompt: {args.prompt[:100]}{'...' if len(args.prompt) > 100 else ''}")
    print()
    
    try:
        # Generate scene plan
        scene_plan = generate_scene_plan(
            story_prompt=args.prompt,
            style=args.style,
            layout=args.layout,
            model_name=args.model
        )
        
        # Save to file
        save_scene_plan(scene_plan, Path(args.output))
        
        # Print summary
        print()
        print("=" * 50)
        print("📋 Scene Plan Summary")
        print("=" * 50)
        print(f"Title: {scene_plan.title}")
        print(f"Style: {scene_plan.style}")
        print(f"Layout: {scene_plan.layout}")
        print()
        
        print("Characters:")
        for char in scene_plan.characters:
            print(f"  • {char.name}: {char.hair_color} hair, {char.clothing}")
        print()
        
        print("Panels:")
        for panel in scene_plan.panels:
            dialogue_count = len(panel.dialogue)
            print(f"  {panel.panel_number}. [{panel.camera_angle}] {panel.description[:60]}...")
            if dialogue_count:
                print(f"     💬 {dialogue_count} dialogue line(s)")
        print()
        
        print("✅ Scene generation complete!")
        print(f"📄 Output: {args.output}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
