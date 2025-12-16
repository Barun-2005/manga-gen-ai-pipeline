#!/usr/bin/env python3
"""
MangaGen - Intelligent Story Director

Uses FallbackLLM for sophisticated story planning:
- Groq (primary) -> NVIDIA NIM (fallback) -> others
- Understands page count and paces story accordingly
- Adds supporting characters beyond user input
- Creates meaningful dialogue that advances the plot
- Generates detailed scene descriptions for image AI

This is the BRAIN of MangaGen - makes stories that make sense!
"""

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class StoryDirector:
    """
    Intelligent story planning with FallbackLLM.
    
    Key Philosophy:
    - Story pacing matters: 1 page = intro only, 5 pages = act 1, 10+ = full arc
    - Characters need depth: AI adds supporting cast automatically
    - Dialogue tells the story: readers should understand plot from dialogue
    - Chapters continue: unless user says "complete", leave room for more
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with FallbackLLM (ignores api_key, uses env vars)."""
        from src.ai.llm_factory import get_llm
        self.llm = get_llm()  # Auto-selects best provider with fallback!
        print(f"🧠 Story Director initialized with: {self.llm.name}")
    
    def plan_chapter(
        self,
        story_prompt: str,
        characters: List[Dict],
        chapter_title: str,
        page_count: int,
        panels_per_page: int,
        style: str,
        is_complete_story: bool = False
    ) -> Dict:
        """
        Plan an entire chapter with intelligent story pacing.
        
        Args:
            story_prompt: User's story idea
            characters: List of user-defined characters [{name, appearance, personality}]
            chapter_title: Title for this chapter
            page_count: Number of pages to generate
            panels_per_page: Panels per page (4 for 2x2, 6 for 2x3)
            style: 'color_anime' or 'bw_manga'
            is_complete_story: If True, wrap up story. If False, leave for continuation.
        
        Returns:
            Complete chapter plan with all pages, panels, and dialogue
        """
        
        total_panels = page_count * panels_per_page
        
        # Format character info
        char_info = "\n".join([
            f"- {c['name']}: {c.get('appearance', 'no description')} | Personality: {c.get('personality', 'not specified')}"
            for c in characters
        ]) if characters else "No characters specified - create main characters based on the story."
        
        # Determine story pacing based on page count
        if page_count == 1:
            pacing_guide = """
SINGLE PAGE (4-6 panels): This is an INTRODUCTION only.
- Panel 1-2: Establish setting and mood
- Panel 3-4: Introduce main character(s) and hint at conflict
- Panel 5-6: End with intrigue/cliffhanger (NOT resolution!)
DO NOT try to complete the story. This is just the HOOK."""
        elif page_count <= 3:
            pacing_guide = f"""
SHORT CHAPTER ({page_count} pages, {total_panels} panels): Show Act 1 only.
- Page 1: Opening - establish world and characters
- Page 2: Rising action - introduce the conflict/problem
- Page 3: Tension peak - major obstacle or revelation
END with a dramatic moment, NOT a resolution. Leave readers wanting more."""
        elif page_count <= 5:
            pacing_guide = f"""
MEDIUM CHAPTER ({page_count} pages, {total_panels} panels): Show Act 1 + Act 2 beginning.
- Pages 1-2: Opening - world building, character introduction
- Pages 3-4: Rising action - conflict develops, stakes increase
- Page 5: Major turning point or confrontation
{"END with resolution and setup for next adventure." if is_complete_story else "END at the climax moment - leave the outcome uncertain."}"""
        else:
            pacing_guide = f"""
FULL CHAPTER ({page_count} pages, {total_panels} panels): Complete story arc possible.
- Pages 1-2: Opening - immersive world building, all characters introduced
- Pages 3-{page_count//2}: Rising action - conflict escalates, relationships develop
- Pages {page_count//2+1}-{page_count-1}: Climax - major confrontation, emotional peaks
- Page {page_count}: {"Resolution - satisfying conclusion" if is_complete_story else "Aftermath - show consequences but leave threads open for continuation"}"""

        prompt = f"""You are a MASTER MANGA STORYTELLER. Create a complete chapter plan for a manga.

## STORY CONCEPT
{story_prompt}

## USER-PROVIDED CHARACTERS
{char_info}

## CHAPTER INFO
- Title: "{chapter_title}"
- Pages: {page_count}
- Panels per page: {panels_per_page}
- Total panels: {total_panels}
- Style: {style}
- Complete story: {"Yes, wrap it up" if is_complete_story else "No, this is chapter of an ongoing series"}

## STORY PACING REQUIREMENTS
{pacing_guide}

## YOUR TASKS

1. **EXPAND THE CAST**: Add 1-3 supporting characters if the story needs them (mentors, rivals, sidekicks). Give them names, appearances, and roles.

2. **PLAN EACH PAGE**: For every page, describe:
   - What happens on this page (2-3 sentences)
   - The emotional beat (tense, sad, exciting, mysterious, etc.)

3. **DESIGN EACH PANEL**: For every panel, provide:
   - Panel number (1 to {total_panels})
   - **Camera shot**: Choose ONE: wide shot | medium shot | close-up | extreme close-up | over-the-shoulder | bird's eye view | worm's eye view
   - **Camera angle**: Choose ONE: straight-on | dutch angle (tilted) | low angle (looking up) | high angle (looking down)
   - **Composition**: Choose ONE: rule of thirds | center frame | dynamic diagonal | symmetrical
   - **Lighting/Mood**: dramatic shadows | soft lighting | harsh contrast | backlit | rim light | moody | bright
   - **Visual description**: Use COMMA-SEPARATED TAGS for image generation, NOT prose sentences!
     * Format: "character action, environment detail, mood/atmosphere, visual style tags"
     * Example GOOD: "Akira running through alley, neon signs, rain, motion blur, dramatic shadows{', grayscale, screentone' if style == 'bw_manga' else ', vibrant colors, cel shading'}"
     * Example BAD: "Akira is running through a dark alley while it's raining"
   - Characters present: List character names
   - Dialogue: MEANINGFUL lines that tell the story (max 2 speech bubbles per panel)

4. **VISUAL DESCRIPTION RULES**:
   - **USE TAGS, NOT SENTENCES**: Comma-separated keywords only
   - **Always include style tags**: {'"manga style, monochrome, ink lineart, screentone, high contrast"' if style == 'bw_manga' else '"anime style, vibrant colors, cel shading, studio quality"'}
   - **Include camera info**: Start with shot type + angle (e.g., "close-up, dutch angle")
   - **Add mood/lighting**: "dramatic shadows", "rim light", "moody atmosphere", etc.
   - **Specify action clearly**: "character running", "character shocked expression", "character reaching out"
   - **Include environment**: "urban alley", "rooftop at sunset", "classroom interior", etc.
   - **Avoid THESE in descriptions**: text, dialogue bubbles, watermarks (those go in negative prompts)

5. **DIALOGUE RULES**:
   - Dialogue should tell the story - a reader should understand the plot from dialogue alone
   - Keep lines SHORT (max 15 words)
   - Vary styles: speech, thought, shout, whisper
   - Not every panel needs dialogue - let some visuals speak
   - {"For B/W manga: describe in grayscale terms, no colors" if style == "bw_manga" else "For color anime: include vivid color descriptions"}

## OUTPUT FORMAT (JSON only, no markdown)
{{
  "chapter_title": "{chapter_title}",
  "summary": "2-3 sentence chapter summary",
  "characters": [
    {{
      "name": "Character Name",
      "appearance": "Detailed visual description for consistent image generation",
      "personality": "Brief personality traits",
      "role": "protagonist/antagonist/mentor/sidekick/etc"
    }}
  ],
  "pages": [
    {{
      "page_number": 1,
      "page_summary": "What happens on this page",
      "emotional_beat": "tense/exciting/sad/mysterious/hopeful/etc",
      "panels": [
        {{
          "panel_number": 1,
          "shot_type": "wide shot|medium shot|close-up|extreme close-up|over-the-shoulder|bird's eye|worm's eye",
          "camera_angle": "straight-on|dutch angle|low angle|high angle",
          "composition": "rule of thirds|center frame|dynamic diagonal|symmetrical",
          "lighting_mood": "dramatic shadows|soft lighting|harsh contrast|backlit|rim light|moody|bright",
          "description": "COMMA-SEPARATED TAGS (not prose!), character action, environment, mood, style tags",
          "characters_present": ["Character Name"],
          "dialogue": [
            {{"character": "Name", "text": "What they say", "style": "speech|thought|shout|whisper"}}
          ]
        }}
      ]
    }}
  ],
  "cliffhanger": "How this chapter ends - tease what's next (only if not complete story)",
  "next_chapter_hook": "Brief idea for next chapter continuation"
}}

Create a compelling, well-paced manga chapter now:"""

        print(f"🧠 Story Director: Planning chapter...")
        print(f"   Pages: {page_count}, Panels: {total_panels}")
        print(f"   Story: {story_prompt[:100]}...")
        
        try:
            # Use FallbackLLM - auto-switches on rate limit!
            content = self.llm.generate(prompt, max_tokens=8000)
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            chapter_plan = json.loads(content.strip())
            
            print(f"✅ Chapter planned: '{chapter_plan.get('chapter_title', chapter_title)}'")
            print(f"   Characters: {len(chapter_plan.get('characters', []))}")
            print(f"   Pages: {len(chapter_plan.get('pages', []))}")
            
            return chapter_plan
            
        except Exception as e:
            print(f"❌ Story Director error: {e}")
            raise
    
    def enhance_prompt(self, user_prompt: str) -> str:
        """
        Use AI to improve a user's story prompt.
        Makes it more detailed and suitable for manga.
        """
        
        prompt = f"""You are a manga story consultant. The user has this story idea:

"{user_prompt}"

Enhance this into a BETTER manga story premise by:
1. Adding specific setting details (time, place, atmosphere)
2. Suggesting clear character archetypes
3. Adding a central conflict or mystery
4. Making it more visual/dramatic for manga format

Return ONLY the enhanced prompt (2-4 sentences), no explanation."""

        enhanced = self.llm.generate(prompt, max_tokens=500)
        enhanced = enhanced.strip()
        
        # Remove quotes if present
        if enhanced.startswith('"') and enhanced.endswith('"'):
            enhanced = enhanced[1:-1]
        
        return enhanced
    
    def generate_blueprint(
        self,
        story_prompt: str,
        characters: List[Dict],
        style: str,
        estimated_chapters: int = 3
    ) -> Dict:
        """
        Generate a complete story blueprint for multi-chapter continuation.
        
        This is called ONCE when creating a new manga. The blueprint stores:
        - Full story arc overview
        - All character details with visual DNA
        - Chapter-by-chapter outlines
        - World/setting details
        
        This enables seamless continuation without losing consistency.
        """
        
        char_info = "\n".join([
            f"- {c['name']}: {c.get('appearance', 'no description')} | Personality: {c.get('personality', 'not specified')}"
            for c in characters
        ]) if characters else "Create main characters based on the story."
        
        prompt = f"""You are a MASTER MANGA STORY ARCHITECT. Create a complete STORY BLUEPRINT.

## USER'S STORY CONCEPT
{story_prompt}

## USER-PROVIDED CHARACTERS
{char_info}

## REQUIREMENTS
- Plan for approximately {estimated_chapters} chapters
- Each chapter should be 3-5 pages worth of content
- Create a complete story arc with beginning, middle, and end
- BUT leave room for potential continuation beyond these chapters

## YOUR TASK
Create a comprehensive story blueprint that will guide all future page generation.

## OUTPUT FORMAT (JSON only, no markdown)
{{
  "title": "Manga Title",
  "genre": "action/romance/fantasy/sci-fi/horror/slice-of-life",
  "overall_arc": "2-3 sentence description of the complete story journey",
  "theme": "Core theme or message of the story",
  
  "characters": [
    {{
      "id": "char_001",
      "name": "Character Name",
      "appearance": "DETAILED visual description for consistent image generation - hair color/style, eye color, clothing, distinguishing features",
      "personality": "Key personality traits",
      "role": "protagonist/antagonist/mentor/sidekick/rival",
      "arc": "How this character changes through the story"
    }}
  ],
  
  "world_details": {{
    "setting": "Where the story takes place",
    "time_period": "When (modern, future, fantasy era, etc)",
    "atmosphere": "Overall mood/tone",
    "key_locations": ["Location 1", "Location 2", "Location 3"],
    "visual_style": "{style}"
  }},
  
  "chapter_outlines": [
    {{
      "chapter": 1,
      "title": "Chapter Title",
      "summary": "What happens in this chapter (3-4 sentences)",
      "key_events": ["Event 1", "Event 2", "Event 3"],
      "emotional_arc": "How emotions progress (e.g., 'hopeful to desperate to determined')",
      "cliffhanger": "How this chapter ends to hook readers",
      "estimated_pages": 4
    }}
  ],
  
  "continuation_hooks": [
    "Potential future story thread 1",
    "Potential future story thread 2"
  ]
}}"""

        content = self.llm.generate(prompt, max_tokens=4000)
        
        # Parse JSON from response
        import re
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        try:
            blueprint = json.loads(content.strip())
            
            # Ensure required fields exist
            if "characters" not in blueprint:
                blueprint["characters"] = characters
            if "world_details" not in blueprint:
                blueprint["world_details"] = {"visual_style": style}
            if "chapter_outlines" not in blueprint:
                blueprint["chapter_outlines"] = []
            
            print(f"📘 Generated blueprint: {blueprint.get('title', 'Untitled')} with {len(blueprint.get('chapter_outlines', []))} chapters")
            return blueprint
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Blueprint JSON parse failed: {e}")
            # Return minimal blueprint
            return {
                "title": "Untitled Manga",
                "genre": "action",
                "overall_arc": story_prompt,
                "characters": characters,
                "world_details": {"visual_style": style},
                "chapter_outlines": [],
                "continuation_hooks": []
            }
    
    def plan_continuation(
        self,
        blueprint: Dict,
        previous_pages_summary: str,
        last_panel_description: str,
        new_page_count: int,
        user_direction: str = None
    ) -> Dict:
        """
        Generate next pages continuing from where we left off.
        
        Uses the stored blueprint + previous progress to maintain consistency.
        """
        
        characters = blueprint.get("characters", [])
        char_info = "\n".join([
            f"- {c['name']}: {c.get('appearance', '')} | {c.get('personality', '')}"
            for c in characters
        ])
        
        chapter_outlines = blueprint.get("chapter_outlines", [])
        outline_info = "\n".join([
            f"Chapter {c['chapter']}: {c['title']} - {c['summary']}"
            for c in chapter_outlines
        ])
        
        user_note = f"\n## USER'S DIRECTION\n{user_direction}" if user_direction else ""
        
        prompt = f"""You are continuing a manga story. Generate the NEXT {new_page_count} pages.

## STORY BLUEPRINT
Title: {blueprint.get('title', 'Untitled')}
Overall Arc: {blueprint.get('overall_arc', '')}
Theme: {blueprint.get('theme', '')}

## CHARACTERS (Use EXACT appearances for image prompts!)
{char_info}

## CHAPTER OUTLINES
{outline_info}

## PREVIOUS PROGRESS
Pages generated so far: {previous_pages_summary}
Last panel showed: {last_panel_description}
{user_note}

## VISUAL PROMPT ENGINEERING RULES
For EVERY panel, the visual_prompt MUST follow these rules:

1. **USE COMMA-SEPARATED TAGS, NOT SENTENCES**
   - GOOD: "Akira close-up, shocked expression, rain, neon lights, dutch angle, dramatic shadows, manga style"
   - BAD: "Akira looks shocked while standing in the rain"

2. **ALWAYS INCLUDE THESE ELEMENTS**:
   - Character name + EXACT appearance from their description above
   - Camera shot: wide shot | medium shot | close-up | extreme close-up | over-the-shoulder
   - Camera angle: straight-on | dutch angle | low angle | high angle
   - Lighting/mood: dramatic shadows | soft lighting | rim light | backlit | moody
   - Style tags: manga style, monochrome, ink lineart, screentone, high contrast

3. **CHARACTER CONSISTENCY IS CRITICAL**
   - Copy the character's appearance EXACTLY from the CHARACTERS section above
   - Include hair color, eye color, clothing, distinguishing features

4. **PANEL VARIETY**
   - Mix shot types: don't use same camera for every panel
   - Vary composition: rule of thirds, center frame, dynamic diagonal
   - Emotional progression: match lighting to emotional beat

## YOUR TASK
Generate EXACTLY {new_page_count} new pages that:
1. Continue EXACTLY from where we left off
2. Use the SAME characters with their EXACT appearance descriptions
3. Follow the chapter outlines but adapt pacing to page count
4. DO NOT repeat any scenes already shown
5. End with a hook for further continuation

## OUTPUT FORMAT (JSON only, no markdown)
{{
  "pages": [
    {{
      "page_number": 1,
      "page_summary": "What happens on this page",
      "emotional_beat": "tense/exciting/sad/mysterious/hopeful",
      "panels": [
        {{
          "panel_number": 1,
          "shot_type": "wide shot/medium shot/close-up/extreme close-up/over-the-shoulder",
          "camera_angle": "straight-on/dutch angle/low angle/high angle",
          "lighting_mood": "dramatic shadows/soft lighting/rim light/backlit/moody",
          "visual_prompt": "COMMA-SEPARATED TAGS: [character name + appearance], [action], [camera], [setting], [mood], manga style, monochrome, ink lineart, screentone",
          "characters_present": ["Character Name"],
          "dialogue": [
            {{"character": "Name", "text": "Dialogue line", "style": "speech/thought/shout/narrator"}}
          ]
        }}
      ]
    }}
  ],
  "progress_summary": "What was accomplished in these pages",
  "last_panel_description": "Description of the final panel for next continuation"
}}"""

        content = self.llm.generate(prompt, max_tokens=4000)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"⚠️ Continuation parse failed: {e}")
            return {"pages": [], "progress_summary": "", "last_panel_description": ""}
    
    def generate_gallery_images(self, count: int = 6) -> List[Dict]:
        """
        Generate random anime scene ideas for the gallery.
        Returns prompts that can be used with Pollinations.
        """
        
        prompt = f"""Generate {count} diverse anime/manga scene prompts for a gallery.
Each should be a different genre: action, romance, fantasy, sci-fi, slice-of-life, horror.

Return JSON array only:
[
  {{
    "title": "Scene title",
    "prompt": "Detailed image generation prompt (50+ words)",
    "genre": "action/romance/fantasy/sci-fi/slice-of-life/horror"
  }}
]"""
        
        content = self.llm.generate(prompt, max_tokens=2000)
        
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content.strip())


def test_story_director():
    """Test the Story Director."""
    
    director = StoryDirector()
    
    # Test prompt enhancement
    original = "ninja girl fights evil empire"
    enhanced = director.enhance_prompt(original)
    print(f"\n📝 Original: {original}")
    print(f"📝 Enhanced: {enhanced}")


if __name__ == "__main__":
    test_story_director()
