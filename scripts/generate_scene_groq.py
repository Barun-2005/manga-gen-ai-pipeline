#!/usr/bin/env python3
"""
MangaGen - Scene Generator with Groq
Uses Groq's fast LLM for story-to-scene conversion.

Groq provides free tier with fast inference!
Models: llama3-8b-8192, llama3-70b-8192, mixtral-8x7b-32768
"""

import json
import os
from typing import Optional
from groq import Groq


def generate_scene_with_groq(
    story_prompt: str,
    style: str = "color_anime",
    layout: str = "2x2",
    api_key: Optional[str] = None
) -> dict:
    """
    Convert a story prompt into structured scene JSON using Groq.
    
    Args:
        story_prompt: The story/scenario to visualize
        style: 'color_anime' or 'bw_manga'
        layout: '2x2' (4 panels) or '2x3' (6 panels)
        api_key: Groq API key (or uses GROQ_API_KEY env var)
    
    Returns:
        Scene plan dictionary
    """
    
    # Get API key
    api_key = api_key or os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found. Set it as environment variable or pass api_key parameter.")
    
    client = Groq(api_key=api_key)
    
    num_panels = 4 if layout == "2x2" else 6
    
    system_prompt = f"""You are a professional manga/anime storyboard artist. 
Convert the user's story prompt into a structured scene plan with exactly {num_panels} panels.

Output ONLY valid JSON (no markdown, no explanation) with this structure:
{{
  "title": "Short catchy title",
  "style": "{style}",
  "layout": "{layout}",
  "characters": [
    {{
      "name": "Character Name",
      "appearance": "Detailed visual description for image generation"
    }}
  ],
  "panels": [
    {{
      "panel_number": 1,
      "shot_type": "wide|medium|close-up|extreme-close-up",
      "description": "Detailed visual description for this panel",
      "characters_present": ["Character Name"],
      "dialogue": [
        {{"character": "Name", "text": "What they say", "style": "speech|thought|shout"}}
      ]
    }}
  ]
}}

Guidelines:
- Make each panel visually distinct
- Vary shot types for visual interest
- Keep dialogues SHORT (max 10 words per line)
- Include visual details (lighting, mood, action)
- Not every panel needs dialogue"""

    print(f"🤖 Generating scene with Groq...")
    print(f"   Model: llama-3.1-8b-instant")
    print(f"   Panels: {num_panels}")
    
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Fast and free!
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": story_prompt}
        ],
        temperature=0.7,
        max_tokens=2000
    )
    
    # Parse JSON response
    content = response.choices[0].message.content
    
    # Try to extract JSON if wrapped in markdown
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0]
    elif "```" in content:
        content = content.split("```")[1].split("```")[0]
    
    try:
        scene_data = json.loads(content.strip())
    except json.JSONDecodeError as e:
        print(f"⚠️ JSON parse error: {e}")
        print(f"Raw content: {content[:500]}...")
        raise
    
    print(f"✅ Generated: '{scene_data.get('title', 'Untitled')}'")
    print(f"   Characters: {len(scene_data.get('characters', []))}")
    print(f"   Panels: {len(scene_data.get('panels', []))}")
    
    return scene_data


def save_scene(scene_data: dict, output_path: str = "scene_plan.json"):
    """Save scene plan to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(scene_data, f, indent=2)
    print(f"💾 Saved: {output_path}")


def main():
    """Test scene generation with Groq."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate scene plan with Groq")
    parser.add_argument("prompt", help="Story prompt")
    parser.add_argument("--style", default="color_anime", choices=["color_anime", "bw_manga"])
    parser.add_argument("--layout", default="2x2", choices=["2x2", "2x3"])
    parser.add_argument("--output", default="scene_plan.json")
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("🎨 MangaGen - Groq Scene Generator")
    print("=" * 50)
    
    try:
        scene = generate_scene_with_groq(
            story_prompt=args.prompt,
            style=args.style,
            layout=args.layout
        )
        save_scene(scene, args.output)
        
        # Print summary
        print("\n📋 Scene Summary:")
        print(f"   Title: {scene.get('title')}")
        for panel in scene.get('panels', []):
            desc = panel.get('description', '')[:50]
            print(f"   Panel {panel.get('panel_number')}: {desc}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
