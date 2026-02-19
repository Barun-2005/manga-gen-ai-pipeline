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
import uuid
from pathlib import Path
from typing import Dict, List, Optional

# Add project root for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class StoryDirector:
    """
    Intelligent story planning with FallbackLLM.
    
    Key Philosophy:
    - Story pacing is DYNAMIC: LLM analyzes story content to decide pacing
    - Characters need depth: AI adds supporting cast automatically
    - Dialogue tells the story: readers should understand plot from dialogue
    - Chapters continue: unless user says "complete", leave room for more
    - Stable IDs: All entities use UUIDs for save/continue support
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
        panels_per_page: int,  # Can be None for V4 dynamic mode
        style: str,
        is_complete_story: bool = False,
        engine: str = "z_image"  # NEW: "z_image", "flux_dev", "flux_schnell"
    ) -> Dict:
        """
        Plan an entire chapter with intelligent story pacing.
        
        Args:
            story_prompt: User's story idea
            characters: List of user-defined characters [{name, appearance, personality}]
            chapter_title: Title for this chapter
            page_count: Number of pages to generate
            panels_per_page: Panels per page (4 for 2x2, 6 for 2x3), or None for V4 DYNAMIC mode
            style: 'color_anime' or 'bw_manga'
            is_complete_story: If True, wrap up story. If False, leave for continuation.
            engine: Image engine - "z_image" (tags), "flux_dev" or "flux_schnell" (sentences)
        
        Returns:
            Complete chapter plan with all pages, panels, and dialogue
        """
        
        # V4 Dynamic Mode: LLM decides panel count based on archetypes
        is_dynamic_layout = panels_per_page is None
        if is_dynamic_layout:
            total_panels = None  # LLM will decide
            panels_per_page_text = "DYNAMIC (You decide 1-6 panels per page based on the archetype you choose)"
            total_panels_text = "DYNAMIC (Varies by archetype - see ARCHETYPE rules below)"
        else:
            total_panels = page_count * panels_per_page
            panels_per_page_text = str(panels_per_page)
            total_panels_text = str(total_panels)
        
        # ENGINE MODE: Flux uses sentence prompts, Z-Image uses tags
        is_flux_mode = engine.startswith("flux")
        if is_flux_mode:
            # FLUX PRO MODE: Cinematographer approach
            print(f"")
            print(f"🚀 ═══════════════════════════════════════════════════════")
            print(f"🚀 MODE: FLUX PRO (Natural Language + IP-Adapter)")
            print(f"🚀 Engine: {engine.upper()} | Style: Cinematographer")
            print(f"🚀 ═══════════════════════════════════════════════════════")
            print(f"")
            
            visual_prompt_instruction = """
   - **Visual description**: DESCRIPTIVE CINEMATIC SENTENCE (Flux Premium)
     * You are a CINEMATOGRAPHER describing each panel as a film shot
     * Format: "[Camera angle] of [subject] in [setting], [lighting], [atmosphere]"
     * Example: "Low angle shot of a determined samurai with wild black hair unsheathing his katana in a rain-soaked alley, dramatic neon reflections on wet pavement, cyberpunk noir atmosphere"
     * Include: character details, pose, expression, environment, lighting quality
     * FORBIDDEN: Danbooru tags, parentheses weights like (masterpiece:1.2), comma-separated keywords
     * Write like a film director describing a shot - rich, atmospheric, visual
"""
        else:
            # Z-IMAGE MODE: Tag-based for consistency
            print(f"📷 MODE: Z-IMAGE STANDARD (Tag-Based Prompts)")
            visual_prompt_instruction = """
   - **Visual description**: COMMA-SEPARATED TAGS for image generation
     * Z-Image format: "1boy, spiky_hair, katana, cherry_blossoms, sunset, dramatic_lighting"
     * Include: character tags, action, setting, mood
     * Include style: """ + ("'monochrome, manga, ink lineart'" if style == 'bw_manga' else "'anime style, vibrant colors'")
        
        # Format character info
        char_info = "\n".join([
            f"- {c['name']}: {c.get('appearance', 'no description')} | Personality: {c.get('personality', 'not specified')}"
            for c in characters
        ]) if characters else "No characters specified - create main characters based on the story."
        
        # DYNAMIC PACING - Let LLM analyze the story prompt to decide pacing
        # (Removed hardcoded "1 page = intro only" type templates)

        
        # Multi-chapter detection for 10+ pages
        is_multi_chapter = page_count >= 10
        chapter_guidance = ""
        if is_multi_chapter:
            estimated_chapters = max(2, page_count // 5)  # ~5 pages per chapter
            chapter_guidance = f"""
## 📚 MULTI-CHAPTER STORY (IMPORTANT!)

You have {page_count} pages - this is enough for {estimated_chapters} chapters!

**STRUCTURE YOUR RESPONSE AS MULTIPLE CHAPTERS:**
1. Divide the story into {estimated_chapters} logical chapters
2. Each chapter should have its own:
   - **Dynamic chapter name** (NOT just "Chapter 1" - use descriptive names like "The Awakening", "First Blood", "Shadows Rising")
   - Summary
   - Cliffhanger ending (except final if complete)
3. Pages should be grouped by chapter

**CHAPTER PACING:**
- Chapter 1: Introduction + inciting incident (~{page_count // estimated_chapters} pages)
- Middle chapters: Rising action + complications
- Final chapter: Climax + resolution (or major cliffhanger)
"""
        else:
            chapter_guidance = f"""
## 📖 SINGLE CHAPTER STORY

This is a {page_count}-page chapter. Give it a **compelling, descriptive chapter name** that hints at the content.

**DO NOT use generic names like:**
- "Chapter 1" ❌
- "The Beginning" ❌
- "Introduction" ❌

**USE evocative names like:**
- "The Sage's Second Life" ✓
- "Awakening in Shadows" ✓
- "When Stars Fall" ✓
"""

        pacing_analysis = f"""
## 📊 YOUR PACING TASK

You have {page_count} pages ({total_panels} panels) to tell this story.
{chapter_guidance}

**ANALYZE the story prompt** and decide:
1. What is the NATURAL SCOPE of this story segment?
   - Is it a moment, a scene, a chapter, or an arc?
2. Where should this segment END?
   - Cliffhanger? Resolution? Mid-action? Emotional beat?
3. How much can realistically FIT in {total_panels} panels?
   - Don't cram 10 events into 5 pages
   - Don't stretch 1 event across 10 pages

**DO NOT follow rigid formulas.** Each story has unique pacing needs.
- A 1-page story CAN be complete (slice of life moment)
- A 10-page story CAN be just setup (epic fantasy prologue)
- YOU decide based on the STORY CONTENT, not the PAGE COUNT.

**IS THIS A CONTINUATION?** {"No - this is a fresh start." if not is_complete_story else "No - user wants a complete story arc."}
"""

        # Professional Manga Techniques (as GUIDANCE, not rigid rules)
        manga_techniques = f"""
## 🎨 MANGA STORYTELLING TECHNIQUES (Use as guidance)

### Kishōtenketsu Framework (Flexible, not rigid!)
Consider this Japanese 4-act structure:
- **Ki (起)** Introduction: Set the scene
- **Shō (承)** Development: Build on the introduction  
- **Ten (転)** Twist: Something unexpected
- **Ketsu (結)** Conclusion: Show result or leave hook

For {total_panels_text} panels, you might allocate ~{page_count} panels per act (dynamic adjusts automatically).
**BUT** - adapt this to YOUR story. Action may need more Ten. Drama may need more Shō.

### "Ma" (間) - The Power of Pause
- Include 1-2 quiet panels per page (no dialogue)
- Use for: reactions, scenery, dramatic pauses
- These let readers FEEL the emotions

### Panel Density Guidance
- Action scenes: MORE panels (creates urgency)
- Emotional beats: FEWER panels (creates impact)
- Dialogue exchanges: Medium density
- Big reveals: Single large panel possible

### What Makes a Page "Work"
- Each page should have ONE clear focus/event
- End pages on mini-cliffhangers when possible
- Vary panel sizes for visual interest
"""

        # Context Reset (prevent ghost characters)
        context_reset = """
## ⚠️ FRESH STORY RULES (CRITICAL)
- This is a BRAND NEW story. There is NO previous context.
- ONLY use characters defined in "USER-PROVIDED CHARACTERS" below
- If a scene seems familiar from another story, DISCARD IT
- Create fresh scenes that match THIS story prompt ONLY
- Any character not explicitly listed does NOT exist

## 🎭 CHARACTER VISUAL DISTINCTION (CRITICAL!)
Heroes and Villains/Antagonists MUST look visually distinct:

**PROTAGONIST Visual Tags:**
- Warm or neutral colors (if color): brown, blue, warm red
- "Heroic" features: clear eyes, determined expression, dynamic pose
- Practical outfit, relatable design

**ANTAGONIST/VILLAIN Visual Tags (MUST DIFFER FROM HERO!):**
- Cold or dark colors: silver, pale, dark purple, sickly green
- Menacing features: sharp eyes, angular face, intimidating presence
- Elaborate/sinister outfit, asymmetric design, scars, unusual markings
- DIFFERENT hair style/color than protagonist!

Example Distinction:
- Hero: "spiky black hair, warm brown eyes, school uniform"
- Villain: "slicked silver hair, cold red eyes, dark military coat, scar across face"

## 💡 CREATIVITY BOOSTER (For Vague Prompts)
If the user's prompt is SHORT or VAGUE (under 50 words), YOU must:
1. INVENT a compelling setting (cyberpunk city, fantasy kingdom, modern academy)
2. CREATE interesting character names and backstories
3. ADD a twist or mystery element
4. DEVELOP the conflict from vague hints

Example:
- User says: "A ninja story"
- You create: "In Neo-Edo 2185, rogue cyber-ninja Hayate must steal data from the Shogun AI, but discovers his missing sister is a guard. Setting: neon-lit temple rooftop."

NEVER be boring. ALWAYS add creative details!"""

        # PHASE 1 DIRECTOR: Minimal dialogue rules (Writer handles the rest)
        dialogue_rules = """
## 💬 DIALOGUE (Basic placeholders - will be refined by Script Doctor)

### PLACEHOLDER DIALOGUE ONLY
- Include basic dialogue to show WHAT characters discuss
- The Script Doctor will refine these into polished lines later
- Focus on WHO speaks, not exact wording

### VISUAL CONTINUITY (CRITICAL for image generation!)
In each panel description, include:
- What the character is HOLDING (weapon, item, bag)
- What they are WEARING (if it changed)
- Their POSITION (standing, sitting, running)
- Previous panel context if relevant

Example: "Kenji, still holding the glowing sword, faces the enemy directly"

### BASIC FORMAT
- speech: {{"character": "Name", "text": "placeholder", "type": "speech"}}
- narrator: {{"type": "narrator", "text": "Scene context"}}
- thought: {{"type": "thought", "character": "Name", "text": "thinking"}}"""

        prompt = f"""You are a PROFESSIONAL MANGA STORYTELLER trained in Japanese manga techniques.

{context_reset}

## STORY CONCEPT
{story_prompt}

## USER-PROVIDED CHARACTERS (USE ONLY THESE)
{char_info}

## CHAPTER INFO
- Title: "{chapter_title}"
- Pages: {page_count}
- Panels per page: {panels_per_page_text}
- Total panels: {total_panels_text}
- Style: {style}
- Complete story: {"Yes, wrap it up" if is_complete_story else "No, this is Chapter 1 of an ongoing series"}

## STORY PACING
{pacing_analysis}

{manga_techniques}

{dialogue_rules}

## YOUR TASKS

1. **EXPAND THE CAST**: Add 1-3 supporting characters if the story needs them. Give them names, appearances, and roles.

2. **PLAN EACH PAGE**: For every page, describe:
   - What happens (2-3 sentences focusing on ONE main event)
   - The emotional beat (tense, sad, exciting, mysterious, etc.)

3. **DESIGN EACH PANEL**: For every panel, provide:
   - Panel number (1 to {total_panels})
   - **Camera shot**: wide shot | medium shot | close-up | extreme close-up | over-the-shoulder | bird's eye view | worm's eye view
   - **Camera angle**: straight-on | dutch angle | low angle | high angle
   - **Composition**: rule of thirds | center frame | dynamic diagonal | symmetrical
   - **Lighting/Mood**: dramatic shadows | soft lighting | harsh contrast | backlit | rim light | moody | bright
{visual_prompt_instruction}
   - Characters present: List character names
   - Dialogue: Use the format specified above (speech/thought/narrator)

4. **INCLUDE "MA" PANELS**: At least 1 per page should be quiet (no dialogue) for emotional impact.

## PAGE ARCHETYPES (CRITICAL - USE THESE!)
Each page MUST have an archetype that determines its layout:

- **EXPOSITION**: World building, establishing shots, new locations
  → Use templates: expo_1splash (1 panel), expo_1big_3small (4 panels), expo_2wide_2small (4 panels)
  → MUST use WIDE or SPLASH panels for big environments - no tiny panels for cities!
  
- **DIALOGUE**: Character conversations, emotional exchanges  
  → Use templates: talk_5panel (5 panels), talk_6panel_grid (6 panels), talk_4panel_focus (4 panels)
  
- **ACTION**: Fights, chases, intense moments
  → Use templates: action_2slant (2 panels), action_3dynamic (3 panels), action_panorama (3 panels)
  
- **REVEAL**: Plot twists, dramatic reveals
  → Use templates: reveal_fullpage (1 panel), reveal_buildup (4 panels)
  
- **CLIFFHANGER**: Chapter ending, suspense
  → Use templates: cliff_fade (3 panels), cliff_split (3 panels)

**Panel count MUST match the template requirement!**

## OUTPUT FORMAT (JSON only, no markdown)
{{
  "manga_title": "A catchy, marketable manga series name (2-5 words, like 'Starbound Chronicles', 'Shadow Academy', 'Crimson Hearts')",
  "chapter_title": "{chapter_title}",
  "summary": "2-3 sentence chapter summary",
  "cover_prompt": "COMMA-SEPARATED TAGS for cover page image: main character(s) in dramatic pose, key visual element from story, title area at top, {'manga style, monochrome, high contrast' if style == 'bw_manga' else 'anime style, vibrant colors'}, cover art quality",
  "characters": [
    {{
      "name": "Character Name",
      "appearance": "Detailed visual description for consistent image generation - NO COLOR WORDS for B/W style",
      "personality": "Brief personality traits",
      "role": "protagonist/antagonist/mentor/sidekick/etc",
      "visual_prompt": "COMMA-SEPARATED TAGS for image gen: age, hair, eyes, outfit, key features",
      "locked_traits": ["hair_color", "eye_color", "age_appearance"],
      "arc_state": "Current emotional/story state of this character"
    }}
  ],
  "pages": [
    {{
      "page_number": 1,
      "chapter_number": 1,
      "archetype": "EXPOSITION",
      "layout_template": "expo_1big_3small",
      "page_summary": "ONE main event that happens on this page",
      "emotional_beat": "tense/exciting/sad/mysterious/hopeful/etc",
      "panels": [
        {{
          "panel_number": 1,
          "shot_type": "wide shot",
          "camera_angle": "straight-on",
          "composition": "rule of thirds",
          "lighting_mood": "moody",
          "description": "A weathered samurai with spiky black hair stands in a rain-soaked alley, dramatic shadows, black and white manga style",
          "style_tags": "1boy, spiky_hair, samurai, rain, alley, dramatic_lighting, monochrome",
          "characters_present": ["Character Name"],
          "dialogue": [
            {{"character": "Name", "text": "placeholder dialogue", "type": "speech", "style": "speech", "speaker_position": "left"}},
            {{"type": "narrator", "text": "Scene context", "style": "narrator", "speaker_position": "center"}}
          ]
        }}
      ]
    }}
  ],
  "cliffhanger": "How this chapter ends - tease what's next",
  "next_chapter_hook": "Brief idea for next chapter"
}}

Remember:
- MAX 3 plot beats for {page_count} pages
- Include narrator boxes for time/place/context
- Multiple characters should CONVERSE, not just monologue
- Include 1 "Ma" (quiet) panel per page
- Make dialogue reveal CHARACTER and PLOT, not just state facts
- SPEAKER_POSITION: "left" if character is on left of panel, "right" if on right, "center" if centered

## CRITICAL COACHING (LAYOUT FOCUS):

**VARIETY RULE**: Do NOT use the same layout_template two pages in a row!
  - If Page 1 uses "expo_1big_3small", Page 2 MUST use something different
  - High-energy ACTION scenes should PREFER dynamic layouts (action_2slant, action_panorama)
  - All layouts MUST use 100% of the page space - NO GAPS!

**PANEL COUNT**: Match the template's panel_count exactly.

Create a visually compelling manga chapter now (dialogue will be polished by Script Doctor):"""


        print(f"🧠 Story Director: Planning chapter...")
        print(f"   Pages: {page_count}, Layout: {'DYNAMIC' if is_dynamic_layout else f'{panels_per_page} panels/page'}")
        print(f"   Story: {story_prompt[:100]}...")
        
        try:
            # ═══════════════════════════════════════════════════════════════
            # HARDCODED MODEL SWITCH - USER PROVIDED VISUAL PROOF
            # ═══════════════════════════════════════════════════════════════
            if is_flux_mode:
                # FLUX PRO MODE: Use GPT-OSS-120b (Best Reasoning on Groq Free)
                model_id = "openai/gpt-oss-120b"
                print(f"")
                print(f"   🧠 ════════════════════════════════════════════════════════")
                print(f"   🧠 FLUX PRO BRAIN: {model_id}")
                print(f"   🧠 Mode: Cinematographer (Natural Language Prompts)")
                print(f"   🧠 ════════════════════════════════════════════════════════")
                print(f"")
                
                # DEBUG: Print first 500 chars of prompt to verify cinematographer style
                print(f"   📝 DEBUG: Prompt Preview (first 500 chars):")
                print(f"   {prompt[:500]}...")
                print(f"")
                
                try:
                    content = self.llm.generate(prompt, max_tokens=8000, model=model_id)
                except Exception as llm_error:
                    print(f"")
                    print(f"   ❌ ════════════════════════════════════════════════════════")
                    print(f"   ❌ LLM ERROR: {model_id} FAILED!")
                    print(f"   ❌ Error: {llm_error}")
                    print(f"   ❌ Falling back to mixtral-8x7b-32768...")
                    print(f"   ❌ ════════════════════════════════════════════════════════")
                    print(f"")
                    # Fallback to mixtral
                    model_id = "mixtral-8x7b-32768"
                    content = self.llm.generate(prompt, max_tokens=8000, model=model_id)
            else:
                # Z-IMAGE MODE: Standard Llama for tag-based prompts
                model_id = "llama-3.3-70b-versatile"
                print(f"   🧠 Z-Image Brain: {model_id}")
                content = self.llm.generate(prompt, max_tokens=8000, model=model_id)
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            chapter_plan = json.loads(content.strip())
            
            # Assign stable UUIDs to all entities (for save/continue support)
            chapter_plan = self._assign_stable_ids(chapter_plan)
            
            print(f"✅ Chapter planned: '{chapter_plan.get('chapter_title', chapter_title)}'")
            print(f"   Characters: {len(chapter_plan.get('characters', []))}")
            print(f"   Pages: {len(chapter_plan.get('pages', []))}")
            
            # V4 DEBUG: Show LLM's archetype/layout choices
            if is_dynamic_layout:
                print(f"\n📐 V4 DYNAMIC LAYOUT - LLM's choices:")
                for page in chapter_plan.get('pages', []):
                    pg_num = page.get('page_number', '?')
                    archetype = page.get('archetype', 'NOT SET')
                    template = page.get('layout_template', 'NOT SET')
                    panel_count = len(page.get('panels', []))
                    print(f"   Page {pg_num}: {archetype} → {template} ({panel_count} panels)")
            
            # PHASE 2: THE WRITER (Script Doctor)
            # Refine dialogue without touching visual fields
            chapter_plan = self.refine_dialogue(chapter_plan)
            
            # PRO MODE: Generate cover art for Flux engine
            if is_flux_mode:
                chapter_plan = self._add_pro_features(chapter_plan, story_prompt, characters)
            
            return chapter_plan
            
        except Exception as e:
            print(f"❌ Story Director error: {e}")
            raise
    
    def _assign_stable_ids(self, chapter_plan: Dict) -> Dict:
        """
        Assign stable UUIDs to all entities in the chapter plan.
        
        This enables save/continue functionality by giving each
        chapter, page, panel, and dialogue a unique identifier.
        """
        # Chapter-level ID
        chapter_plan['chapter_id'] = str(uuid.uuid4())[:8]
        
        # Character IDs
        for char in chapter_plan.get('characters', []):
            char['character_id'] = f"char_{uuid.uuid4().hex[:8]}"
        
        # Page and panel IDs
        for page in chapter_plan.get('pages', []):
            page['page_id'] = f"page_{uuid.uuid4().hex[:8]}"
            
            for panel in page.get('panels', []):
                panel['panel_id'] = f"panel_{uuid.uuid4().hex[:8]}"
                
                # Dialogue IDs
                for dialogue in panel.get('dialogue', []):
                    dialogue['dialogue_id'] = f"dlg_{uuid.uuid4().hex[:8]}"
        
        return chapter_plan
    
    def _add_pro_features(self, chapter_plan: Dict, story_prompt: str, characters: List[Dict]) -> Dict:
        """
        PRO MODE: Add premium features for Flux engine.
        
        Features:
        - Cover art prompt (for Page 0 / Volume Cover)
        - Chapter title styling
        - Arc name if multi-chapter
        """
        chapter_title = chapter_plan.get('chapter_title', 'Untitled Chapter')
        char_names = [c.get('name', 'Character') for c in characters[:3]]  # Top 3 chars
        char_appearances = [c.get('appearance', '') for c in characters[:2]]  # Top 2 for cover
        
        # DEBUG: Print what we're working with
        print(f"")
        print(f"   📖 ════════════════════════════════════════════════════════")
        print(f"   📖 GENERATING COVER ART FOR: {chapter_title}")
        print(f"   📖 Characters: {char_names}")
        print(f"   📖 ════════════════════════════════════════════════════════")
        print(f"")
        
        # Generate cover art prompt (descriptive sentence for Flux)
        cover_prompt = f"A dramatic manga volume cover illustration: {chapter_title}. "
        if char_appearances:
            cover_prompt += f"Featuring {', '.join(char_names)}. "
            cover_prompt += f"{char_appearances[0][:100]}. "
        cover_prompt += "Dynamic composition, professional manga cover art style, bold title typography space at top, dramatic lighting, high quality illustration."
        
        # DEBUG: Print the exact cover prompt
        print(f"   📖 COVER PROMPT:")
        print(f"   {cover_prompt}")
        print(f"")
        
        # Add cover_art to chapter plan
        chapter_plan['cover_art'] = {
            'prompt': cover_prompt,
            'width': 1024,
            'height': 1440,  # Manga cover aspect ratio (taller)
            'is_cover': True
        }
        
        # INSERT PAGE 0: Cover Art Page (prepend to pages array)
        cover_page = {
            'page_id': f"page_cover_{uuid.uuid4().hex[:8]}",
            'page_number': 0,
            'archetype': 'cover',
            'layout_template': 'full',
            'is_cover': True,
            'panels': [{
                'panel_id': f"panel_cover_{uuid.uuid4().hex[:8]}",
                'panel_number': 1,
                'visual_prompt': cover_prompt,
                'dialogue': [],
                'is_cover': True
            }]
        }
        
        # Prepend cover page and renumber existing pages
        existing_pages = chapter_plan.get('pages', [])
        for page in existing_pages:
            page['page_number'] = page.get('page_number', 1) + 1  # Shift by 1
        
        chapter_plan['pages'] = [cover_page] + existing_pages
        
        # Add Pro metadata
        chapter_plan['pro_mode'] = True
        chapter_plan['engine'] = 'flux_dev'  # Mark which engine was used
        
        print(f"")
        print(f"   📖 ═══════════════════════════════════════════════════")
        print(f"   📖 COVER ART: Page 0 inserted with volume cover prompt")
        print(f"   📖 Chapter: '{chapter_title}'")
        print(f"   📖 Total Pages: {len(chapter_plan['pages'])} (including cover)")
        print(f"   📖 ═══════════════════════════════════════════════════")
        print(f"")
        
        return chapter_plan

    
    def refine_dialogue(self, chapter_plan: Dict) -> Dict:
        """
        PHASE 2: THE WRITER (Script Doctor)
        
        Takes the visual-focused chapter plan from Phase 1 and refines ONLY the dialogue.
        
        CONSTRAINTS (Strictly Enforced):
        - CANNOT add/remove panels
        - CANNOT change layout_template
        - CANNOT change visual_tags or character DNA
        - CAN ONLY modify dialogue[] arrays
        
        Returns:
            Same chapter_plan with refined dialogue
        """
        
        # Extract essential info for the Writer
        story_context = chapter_plan.get('summary', '')
        characters = chapter_plan.get('characters', [])
        pages = chapter_plan.get('pages', [])
        
        if not pages:
            return chapter_plan
        
        # Format character voices for the Writer
        char_voices = "\n".join([
            f"- {c.get('name', 'Unknown')}: {c.get('personality', 'no personality defined')} | Role: {c.get('role', 'unknown')}"
            for c in characters
        ])
        
        # Build the minimal scene context for dialogue refinement
        scene_summaries = []
        for page in pages:
            pg_num = page.get('page_number', '?')
            pg_summary = page.get('page_summary', 'No summary')
            panels_info = []
            for panel in page.get('panels', []):
                panel_num = panel.get('panel_number', '?')
                desc = panel.get('description', '')[:100]
                chars = panel.get('characters_present', [])
                current_dialogue = panel.get('dialogue', [])
                panels_info.append({
                    'panel_number': panel_num,
                    'description': desc,
                    'characters': chars,
                    'dialogue_count': len(current_dialogue)
                })
            scene_summaries.append({
                'page': pg_num,
                'summary': pg_summary,
                'panels': panels_info
            })
        
        writer_prompt = f"""You are a MANGA SCRIPT DOCTOR specializing in dialogue.

## STORY CONTEXT
{story_context}

## CHARACTER VOICES (Give each distinct personality!)
{char_voices}

## SCENE BREAKDOWN
{json.dumps(scene_summaries, indent=2)}

## YOUR TASK: REWRITE ALL DIALOGUE

You must return a JSON object with ONLY the dialogue arrays for each panel.

### RULES (CRITICAL - READ CAREFULLY!):

1. **DISTINCT VOICES**: Each character speaks differently
   - A hot-headed fighter uses short, punchy sentences
   - A wise mentor speaks in metaphors and measured tones
   - A nervous sidekick stutters and asks questions
   - NO GENERIC "AI SPEAK" - make it feel human!

2. **SHOW, DON'T TELL**: Never summarize emotions
   ❌ BAD: "I'm so angry right now!"
   ✅ GOOD: "You... you DARE?!" (style: "shout")

3. **BUBBLE STYLE IS MANDATORY**: Every dialogue MUST have a style field
   - "speech" = normal talking
   - "shout" = yelling/anger/commands (spiky bubble)
   - "thought" = inner thoughts (cloud bubble)
   - "whisper" = secrets/quiet (dashed bubble)
   - "narrator" = scene setting (caption box)

4. **NARRATOR BOXES REQUIRED**: Each page MUST have at least ONE narrator
   - Page 1: Establish location/time
   - Other pages: Transitions, time skips, internal context

5. **SPEAKER POSITION**: Set based on character placement
   - "left" if character is on left of panel
   - "right" if character is on right
   - "center" for narrators or centered characters

6. **3-5 EXCHANGES MINIMUM**: Real conversations, not monologues!

## OUTPUT FORMAT (JSON ONLY)

Return EXACTLY this structure:
{{
  "pages": [
    {{
      "page_number": 1,
      "panels": [
        {{
          "panel_number": 1,
          "dialogue": [
            {{"character": "Name", "text": "Actual line", "type": "speech", "style": "speech", "speaker_position": "left"}},
            {{"type": "narrator", "text": "Scene context", "style": "narrator", "speaker_position": "center"}}
          ]
        }}
      ]
    }}
  ]
}}

CRITICAL: Return ONLY valid JSON. No markdown, no explanation. Just the dialogue data."""

        print(f"\n✍️ Script Doctor: Refining dialogue...")
        
        try:
            # Use LLM for dialogue refinement
            content = self.llm.generate(writer_prompt, max_tokens=4000)
            
            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            dialogue_data = json.loads(content.strip())
            
            # Merge refined dialogue back into chapter_plan (preserving all visual fields!)
            refined_pages = dialogue_data.get('pages', [])
            for refined_page in refined_pages:
                pg_num = refined_page.get('page_number')
                # Find matching page in original
                for orig_page in chapter_plan.get('pages', []):
                    if orig_page.get('page_number') == pg_num:
                        for refined_panel in refined_page.get('panels', []):
                            panel_num = refined_panel.get('panel_number')
                            # Find matching panel
                            for orig_panel in orig_page.get('panels', []):
                                if orig_panel.get('panel_number') == panel_num:
                                    # ONLY update dialogue - preserve everything else!
                                    if 'dialogue' in refined_panel:
                                        orig_panel['dialogue'] = refined_panel['dialogue']
                                    break
                        break
            
            # Count results
            total_dialogues = 0
            narrator_count = 0
            style_count = {'speech': 0, 'shout': 0, 'thought': 0, 'whisper': 0, 'narrator': 0}
            for page in chapter_plan.get('pages', []):
                for panel in page.get('panels', []):
                    for dlg in panel.get('dialogue', []):
                        total_dialogues += 1
                        style = dlg.get('style', 'speech')
                        if style in style_count:
                            style_count[style] += 1
                        if dlg.get('type') == 'narrator':
                            narrator_count += 1
            
            print(f"✅ Dialogue refined: {total_dialogues} bubbles")
            print(f"   Styles: {style_count}")
            print(f"   Narrators: {narrator_count}")
            
            return chapter_plan
            
        except Exception as e:
            print(f"⚠️ Script Doctor failed (using original dialogue): {e}")
            # Return original plan unchanged if refinement fails
            return chapter_plan
    
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
