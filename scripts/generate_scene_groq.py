#!/usr/bin/env python3
"""
MangaGen - Scene Generator with Smart LLM Fallback

Uses FallbackLLM for automatic provider switching:
- Groq (primary, fast)
- NVIDIA NIM (fallback, 40 req/min)
- Gemini/OpenRouter (additional fallbacks)

If Groq hits rate limit, automatically switches to NVIDIA!
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def generate_scene_with_groq(
    story_prompt: str,
    style: str = "color_anime",
    layout: str = "2x2",
    page_number: int = 1,
    total_pages: int = 1,
    api_key: Optional[str] = None  # Kept for backwards compat, not used
) -> dict:
    """
    Convert a story prompt into structured scene JSON.
    
    Uses FallbackLLM: Groq -> NVIDIA NIM -> Gemini -> OpenRouter
    
    Args:
        story_prompt: The story/scenario to visualize
        style: 'color_anime' or 'bw_manga'
        layout: '2x2' (4 panels) or '2x3' (6 panels)
        page_number: Current page number (1-indexed)
        total_pages: Total number of pages in the chapter
        api_key: Deprecated, uses env vars now
    
    Returns:
        Scene plan dictionary
    """
    
    # Import our smart fallback LLM
    from src.ai.llm_factory import get_llm
    
    llm = get_llm()  # Auto-selects with fallback!
    num_panels = 4 if layout == "2x2" else 6
    
    # Add page context for story pacing
    if total_pages > 1:
        if page_number == 1:
            page_context = f"This is PAGE {page_number} of {total_pages} (OPENING). Introduce characters and setting. Build intrigue."
        elif page_number == total_pages:
            page_context = f"This is PAGE {page_number} of {total_pages} (FINALE). Resolve the conflict. Provide a satisfying conclusion or cliffhanger."
        elif page_number <= total_pages // 2:
            page_context = f"This is PAGE {page_number} of {total_pages} (RISING ACTION). Build tension and develop the conflict."
        else:
            page_context = f"This is PAGE {page_number} of {total_pages} (CLIMAX BUILDING). Increase stakes, move toward the resolution."
    else:
        page_context = "This is a single-page manga. Tell a complete mini-story with setup, conflict, and resolution."

    prompt = f"""You are a professional manga/anime storyboard artist. 
Convert the following story into a structured scene plan with exactly {num_panels} panels.

IMPORTANT STORY CONTEXT: {page_context}

STORY: {story_prompt}

Output ONLY valid JSON (no markdown, no explanation) with this structure:
{{
  "title": "Short catchy title",
  "style": "{style}",
  "layout": "{layout}",
  "characters": [
    {{
      "name": "Character Name",
      "appearance": "Detailed visual description for image generation (no colors if style is bw_manga)"
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
- Not every panel needs dialogue
- {"NO COLORS in descriptions - this is BLACK AND WHITE manga" if style == "bw_manga" else "Use vibrant colors for color anime style"}"""

    print(f"📝 Generating scene plan...")
    print(f"   Panels: {num_panels}")
    
    # Use FallbackLLM - will auto-switch providers if rate limited!
    content = llm.generate(prompt, max_tokens=2000)
    
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
