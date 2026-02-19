#!/usr/bin/env python3
"""
MangaGen - Multi-Page Manga Generator (Intelligent Version)

Uses Story Director AI for:
- Proper story pacing based on page count
- Character expansion (adds supporting cast)
- Meaningful dialogue that tells the story
- Chapter continuation (doesn't rush endings)
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field

# V4: Layout templates for dynamic panel composition
from scripts.layout_templates import LAYOUT_TEMPLATES, validate_template
import inspect
import asyncio


@dataclass
class MangaConfig:
    """Configuration for manga generation."""
    title: str
    style: str = "color_anime"  # "color_anime" or "bw_manga"
    layout: str = "2x2"  # "2x2" (4 panels), "2x3" (6 panels)
    pages: int = 1
    output_dir: str = "outputs"
    engine: str = "z_image"  # "z_image", "flux_dev", or "flux_schnell"
    is_complete_story: bool = False  # If True, wrap up story. If False, leave for continuation.
    starting_page_number: int = 1  # For continuations: start at page N+1 to avoid overwriting
    
    @property
    def panels_per_page(self) -> int:
        """
        Returns panels per page, or None for dynamic (V4 archetype-based) layouts.
        When None, the LLM decides panel count based on page archetype.
        """
        if self.layout == "dynamic":
            return None  # V4: Let LLM decide based on archetypes
        elif self.layout == "2x2":
            return 4
        elif self.layout == "2x3":
            return 6
        elif self.layout == "3x3":
            return 9
        elif self.layout == "full":
            return 1
        return None  # Default to dynamic for unknown layouts


class ComfyUIGeneratorWrapper:
    """
    Wrapper to adapt async ComfyUI ImageProvider to sync generator interface.
    
    This enables local ComfyUI generation using our tested Hybrid Z-Image workflow.
    The wrapper converts async generate() calls to sync and handles file saving.
    """
    
    def __init__(self, provider, output_dir: str):
        self.provider = provider
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._panel_counter = 0
    
    # Action keywords for Animagine pass (future feature)
    ACTION_KEYWORDS = ['fight', 'battle', 'attack', 'explosion', 'running', 
                       'jumping', 'punch', 'kick', 'dodge', 'clash', 'combat',
                       'sword', 'weapon', 'action', 'charging', 'flying']
    
    def _is_action_scene(self, prompt: str) -> bool:
        """Detect if prompt describes an action scene."""
        prompt_lower = prompt.lower()
        return any(kw in prompt_lower for kw in self.ACTION_KEYWORDS)
    
    def _strip_color_words(self, prompt: str) -> str:
        """Remove color words from prompt for B/W mode."""
        import re
        # Replace color words with grayscale alternatives
        color_patterns = [
            (r'\b(pink|magenta)\s*(hair|haired)', 'light grey hair'),
            (r'\b(blue|azure|cyan)\s*(hair|haired)', 'dark grey hair'),
            (r'\b(red|crimson|scarlet)\s*(hair|haired)', 'dark hair'),
            (r'\b(green|emerald)\s*(hair|haired)', 'grey hair'),
            (r'\b(purple|violet)\s*(hair|haired)', 'grey hair'),
            (r'\b(yellow|blonde|golden)\s*(hair|haired)', 'light hair'),
            (r'\b(orange)\s*(hair|haired)', 'light grey hair'),
            (r'\b(pink|blue|red|green|purple|yellow|orange|cyan|magenta)\s*(eyes)', r'grey \2'),
            # Remove standalone color words
            (r'\b(vibrant|colorful|colored|coloured)\b', ''),
        ]
        result = prompt
        for pattern, replacement in color_patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    
    async def generate_image(
        self,
        prompt: str,
        filename: str,
        width: int = 1024,
        height: int = 1024,
        style: str = "anime",
        max_retries: int = 3,
        seed: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate a single image using ComfyUI Z-Image Hybrid workflow.
        
        Compatible with PollinationsGenerator/NVIDIAImageGenerator interface.
        """
        import asyncio
        
        # For B/W mode: strip color words and add strong B/W enforcement
        if style == "bw_manga":
            prompt = self._strip_color_words(prompt)
            style_suffix = ", manga style, monochrome, ink drawing, high contrast, screentone, BLACK AND WHITE ONLY, grayscale, NO COLOR"
        else:
            style_suffix = ", anime style, vibrant colors, studio quality"
        
        # Check for action scene (log for now, Animagine pass is future feature)
        if self._is_action_scene(prompt):
            print(f"   ⚡ Action scene detected: {prompt[:50]}...")
        
        full_prompt = f"{prompt}{style_suffix}"
        actual_seed = seed if seed is not None else 42 + self._panel_counter
        
        for attempt in range(max_retries):
            try:
                print(f"   🖼️ ComfyUI generating (attempt {attempt + 1})...")
                
                # Direct async await - no manual loop!
                image_bytes = await self.provider.generate(
                    prompt=full_prompt, 
                    width=width, 
                    height=height, 
                    seed=actual_seed, 
                    panel_id=f"panel_{self._panel_counter}"
                )
                
                # Save to file
                output_path = self.output_dir / filename
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                
                self._panel_counter += 1
                print(f"   ✅ Saved: {filename}")
                return str(output_path)
                
            except Exception as e:
                print(f"   ⚠️ ComfyUI attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    print(f"   ❌ All retries failed for: {filename}")
                    return None
                await asyncio.sleep(2)
        
        return None
    
    async def generate_cover(
        self,
        prompt: str,
        style: str = "anime",
        width: int = 768,
        height: int = 1024,  # Taller for cover
        seed: int = 12345
    ) -> Optional[str]:
        """
        Generate a cover image for the manga.
        Uses the same workflow as panel generation but saves as cover.png
        """
        filename = "cover.png"
        
        print(f"   🎨 Generating Cover Art: {prompt[:50]}...")
        
        return await self.generate_image(
            prompt=prompt,
            filename=filename,
            width=width,
            height=height,
            style=style,
            seed=seed
        )
    
    def generate_panels(self, prompts: list, seeds: list = None) -> list:
        """
        Generate multiple panels using ComfyUI.
        
        Compatible with PollinationsGenerator.generate_panels() interface.
        """
        results = []
        seeds = seeds or [42 + i for i in range(len(prompts))]
        
        for i, (prompt, seed) in enumerate(zip(prompts, seeds)):
            filename = f"panel_{self._panel_counter:04d}.png"
            result = self.generate_image(prompt, filename, seed=seed)
            if result:
                results.append({
                    "path": result,
                    "prompt": prompt,
                    "seed": seed
                })
            else:
                results.append({"error": "Generation failed", "prompt": prompt})
        
        return results


class MangaGenerator:
    """
    Complete manga generation pipeline with intelligent story planning.
    
    Uses:
    - Gemini AI for story planning (Story Director)
    - Pollinations.ai OR ComfyUI for image generation
    - Smart bubble placement for dialogue
    """
    
    def __init__(self, config: MangaConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # Import generation modules
        from scripts.generate_panels_api import PollinationsGenerator, NVIDIAImageGenerator
        from src.dialogue.smart_bubbles import SmartBubblePlacer
        from src.ai.character_dna import CharacterDNAManager
        
        # Choose image generator based on engine
        if config.engine == "z_image":
            # Use local ComfyUI with Z-Image workflow
            from src.ai.image_factory import get_image_provider
            comfyui = get_image_provider("z_image")
            if comfyui.is_available():
                print(f"📦 Using Z-Image Engine (ComfyUI local) - Start with: py -3.10 ComfyUI/main.py --novram")
                self.image_generator = ComfyUIGeneratorWrapper(comfyui, str(self.output_dir))
            else:
                print(f"⚠️ ComfyUI not available, falling back to Pollinations")
                self.image_generator = PollinationsGenerator(str(self.output_dir))
        elif config.engine in ("flux_dev", "flux_schnell"):
            # Use local ComfyUI with Flux workflow - PREMIUM MODE
            print(f"")
            print(f"🚀 ═══════════════════════════════════════════════════════")
            print(f"🚀 FLUX PRO ENGINE ACTIVATED")
            print(f"🚀 Engine: {config.engine.upper()} | IP-Adapter: ENABLED")
            print(f"🚀 ═══════════════════════════════════════════════════════")
            print(f"")
            from src.ai.image_factory import get_image_provider
            flux = get_image_provider(config.engine)
            if flux.is_available():
                print(f"📦 Flux Provider: {flux.name}")
                self.image_generator = ComfyUIGeneratorWrapper(flux, str(self.output_dir))
            else:
                print(f"⚠️ ComfyUI not available for Flux, falling back to Pollinations")
                self.image_generator = PollinationsGenerator(str(self.output_dir))
        else:
            # Default: Pollinations cloud
            print(f"📦 Using Pollinations.ai Cloud (parallel mode)")
            self.image_generator = PollinationsGenerator(str(self.output_dir))
        
        # Character DNA Manager for visual consistency
        self.character_dna = CharacterDNAManager(style=config.style)
        print(f"🧬 Character DNA Manager initialized ({config.style})")
        
        self.bubble_placer = SmartBubblePlacer()
        
        # Story Director (Gemini) - will be initialized when needed
        self._story_director = None
    
    @property
    def story_director(self):
        """Lazy load Story Director to avoid import issues."""
        if self._story_director is None:
            from src.ai.story_director import StoryDirector
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if gemini_key:
                self._story_director = StoryDirector(gemini_key)
            else:
                print("⚠️ GEMINI_API_KEY not set, using fallback Groq")
                self._story_director = None
        return self._story_director
    
    def _extract_chapters_from_plan(self, chapter_plan: Dict) -> List[Dict]:
        """
        Extract chapter structure from LLM plan.
        Groups pages by chapter_number for multi-chapter stories.
        """
        import uuid
        
        pages = chapter_plan.get('pages', [])
        
        # Group pages by chapter_number
        chapters_dict = {}
        for page in pages:
            chapter_num = page.get('chapter_number', 1)
            if chapter_num not in chapters_dict:
                chapters_dict[chapter_num] = {
                    "chapter_id": f"ch_{uuid.uuid4().hex[:8]}",
                    "chapter_number": chapter_num,
                    "title": chapter_plan.get('chapter_title', self.config.title),
                    "summary": chapter_plan.get('summary', ''),
                    "pages": []
                }
            chapters_dict[chapter_num]["pages"].append(page.get('page_id'))
        
        # If only one chapter, use the LLM's chapter title
        if len(chapters_dict) == 1:
            chapter = list(chapters_dict.values())[0]
            chapter["chapter_id"] = chapter_plan.get('chapter_id', chapter["chapter_id"])
            chapter["title"] = chapter_plan.get('chapter_title', self.config.title)
        
        # Convert to sorted list
        return sorted(chapters_dict.values(), key=lambda c: c["chapter_number"])
    
    def _count_chapters(self, chapter_plan: Dict) -> int:
        """Count number of unique chapters in the plan."""
        pages = chapter_plan.get('pages', [])
        chapter_nums = set(p.get('chapter_number', 1) for p in pages)
        return len(chapter_nums) if chapter_nums else 1
    
    def _save_story_blueprint(self, chapter_plan: Dict, story_prompt: str, characters: Optional[List[Dict]]):
        """
        Save complete story state for save/continue/edit flows.
        
        Creates story_state.json with:
        - Stable UUIDs for all entities
        - Character DNA for visual consistency
        - Continuation state for "continue story" feature
        """
        from datetime import datetime
        import json
        import uuid
        
        try:
            # Generate manga-level UUID if not exists
            manga_id = f"manga_{uuid.uuid4().hex[:12]}"
            
            story_state = {
                # Schema version for future migrations
                "$schema": "MangaGen Story State v1.0",
                "manga_id": manga_id,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                
                # Metadata
                "metadata": {
                    "manga_title": chapter_plan.get("manga_title", self.config.title),
                    "title": self.config.title,  # Keep original chapter title
                    "cover_prompt": chapter_plan.get("cover_prompt", ""),
                    "style": self.config.style,
                    "total_pages": self.config.pages,
                    "layout_template": self.config.layout,
                    "status": "complete" if self.config.is_complete_story else "in_progress"
                },
                
                # Story context (for understanding and continuation)
                "story_context": {
                    "original_prompt": story_prompt,
                    "llm_interpretation": chapter_plan.get('summary', ''),
                    "genre": "manga",  # Could be detected by LLM
                    "target_scope": "complete" if self.config.is_complete_story else "chapter"
                },
                
                # Characters with DNA for visual consistency
                "characters": chapter_plan.get('characters', []),
                
                # Extract chapters from pages (multi-chapter detection)
                "chapters": self._extract_chapters_from_plan(chapter_plan),
                
                # Pages and panels (full data)
                "pages": chapter_plan.get('pages', []),
                
                # Continuation state (for "continue story" feature)
                "continuation_state": {
                    "cliffhanger": chapter_plan.get('cliffhanger', ''),
                    "next_chapter_hook": chapter_plan.get('next_chapter_hook', ''),
                    "unresolved_threads": [],  # Could be extracted by LLM
                    "chapter_count": self._count_chapters(chapter_plan)
                },
                
                # Legacy format (for backwards compatibility)
                "chapter_plan": chapter_plan,
                "panel_prompts": []
            }
            
            # Extract panel prompts for debugging (with stable IDs)
            for page in chapter_plan.get('pages', []):
                for panel in page.get('panels', []):
                    story_state["panel_prompts"].append({
                        "panel_id": panel.get('panel_id'),
                        "page_id": page.get('page_id'),
                        "panel_number": panel.get('panel_number'),
                        "description": panel.get('description'),
                        "dialogue": panel.get('dialogue', [])
                    })
            
            # Save to output directory
            state_path = self.output_dir / "story_state.json"
            with open(state_path, 'w', encoding='utf-8') as f:
                json.dump(story_state, f, indent=2, ensure_ascii=False)
            
            # Also save legacy format for backwards compatibility
            legacy_path = self.output_dir / "story_blueprint.json"
            with open(legacy_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "timestamp": story_state["created_at"],
                    "original_prompt": story_prompt,
                    "provided_characters": characters or [],
                    "config": story_state["metadata"],
                    "chapter_plan": chapter_plan,
                    "panel_prompts": story_state["panel_prompts"]
                }, f, indent=2, ensure_ascii=False)
            
            print(f"📝 Story state saved: {state_path}")
            print(f"📝 Legacy blueprint saved: {legacy_path}")
            
        except Exception as e:
            print(f"⚠️ Failed to save story state: {e}")
    

    async def generate_chapter(
        self,
        story_prompt: str,
        groq_api_key: str,
        characters: Optional[List[Dict]] = None,
        progress_callback: Optional[Callable[[str, int, Optional[Dict]], None]] = None
    ) -> Dict:
        """
        Generate a complete manga chapter with intelligent story planning.
        
        Args:
            story_prompt: The story concept
            groq_api_key: Groq API key (fallback if no Gemini)
            characters: Optional list of user-defined characters
        
        Returns:
            Chapter result with all pages and PDF
        """
        
        print("=" * 60)
        print(f"📚 MangaGen - Intelligent Chapter Generation")
        print("=" * 60)
        print(f"   Title: {self.config.title}")
        print(f"   Style: {self.config.style}")
        print(f"   Pages: {self.config.pages}")
        print(f"   Layout: {self.config.layout}")
        print(f"   Complete Story: {self.config.is_complete_story}")
        
        start_time = time.time()
        
        # Step 1: Plan the chapter with Story Director (Gemini)
        if self.story_director:
            print("\n🧠 Using Gemini Story Director for intelligent planning...")
            chapter_plan = self.story_director.plan_chapter(
                story_prompt=story_prompt,
                characters=characters or [],
                chapter_title=self.config.title,
                page_count=self.config.pages,
                panels_per_page=self.config.panels_per_page,
                style=self.config.style,
                is_complete_story=self.config.is_complete_story,
                engine=self.config.engine  # DUAL ENGINE: z_image, flux_dev, flux_schnell
            )
            
            # Register characters with Character DNA Manager
            print("\n🧬 Building Character DNA for visual consistency...")
            self.character_dna.register_characters_from_plan(chapter_plan)
            
            # Save story blueprint for debugging/analysis
            self._save_story_blueprint(chapter_plan, story_prompt, characters)
        else:
            # Fallback to Groq (simpler planning)
            print("\n⚡ Using Groq for scene generation (set GEMINI_API_KEY for better results)...")
            chapter_plan = self._generate_with_groq(story_prompt, groq_api_key)
            
            # Save story blueprint for debugging/analysis
            self._save_story_blueprint(chapter_plan, story_prompt, characters)
        
        # Calculate actual total panels from the plan
        actual_total_panels = sum(len(page.get('panels', [])) for page in chapter_plan.get('pages', []))
        
        # Report plan completion with actual panel count
        if progress_callback:
            progress_callback("Planning complete", 20, {
                "event": "plan_complete",
                "total_panels": actual_total_panels,
                "pages": len(chapter_plan.get('pages', []))
            })
        
        # Step 2: Generate panels and compose pages
        chapter_pages = []
        
        # Track running panel count for accurate indexing in dynamic layouts
        total_panels_generated = 0
        
        for page_data in chapter_plan.get('pages', []):
            # Offset page number for continuations (e.g., page 1 becomes page 4 if starting_page_number=4)
            original_page_num = page_data.get('page_number', len(chapter_pages) + 1)
            page_num = original_page_num + (self.config.starting_page_number - 1)
            
            print(f"\n📄 Processing Page {page_num}/{self.config.starting_page_number + self.config.pages - 1}")
            print(f"   Beat: {page_data.get('emotional_beat', 'unknown')}")
            
            # Report progress - use original_page_num (1,2,3) not offset page_num (7,8,9)
            if progress_callback:
                # Progress calculation: 20% (planning done) + 70% for pages
                current_prog = 20 + int(70 * (original_page_num - 1) / self.config.pages)
                # Display relative progress (1/3) that matches percentage
                progress_callback(f"Processing page {original_page_num}/{self.config.pages}...", current_prog, None)
            
            # Generate panel images (pass base_panel_index for correct indexing)
            panel_paths = await self._generate_page_panels(page_data, page_num, progress_callback, total_panels_generated)
            total_panels_generated += len(page_data.get('panels', []))  # Update running count
            
            # Extract dialogue data (no rendering - just JSON)
            if progress_callback:
                progress_callback(f"Extracting dialogue for page {page_num}...", -1, {"event": "step_started", "step": "dialogue"})
            
            panel_paths, dialogue_data = self._add_dialogue(panel_paths, page_data, page_num)
            
            # Compose page (panels only, no dialogue bubbles)
            if progress_callback:
                progress_callback(f"Composing page {page_num}...", -1, {"event": "step_started", "step": "composition"})
            page_path = self._compose_page(
                panel_paths,
                page_num,
                self.config.title,
                page_data  # V4.2: Pass page_data for layout template
            )
            
            if progress_callback:
                # Page complete - Send path for live preview
                current_prog = 20 + int(70 * page_num / self.config.pages)
                data = {
                    "event": "page_complete",
                    "page_num": page_num,
                    "image_path": str(page_path),
                    "panels": [str(p) for p in panel_paths],
                    "dialogue": dialogue_data  # NEW: Include dialogue JSON
                }
                progress_callback(f"Finished page {page_num}...", current_prog, data)
            
            chapter_pages.append({
                'page_number': page_num,
                'summary': page_data.get('page_summary', ''),
                'archetype': page_data.get('archetype', 'DEFAULT'),
                'layout_template': page_data.get('layout_template', '2x2_grid'),
                # V4 FIX: Include panel data with x,y,w,h geometry for frontend
                'panels': page_data.get('panels', []),  # Full panel objects with geometry!
                'panel_paths': [str(p) for p in panel_paths],  # Legacy: file paths
                'page_image': page_path,
                'dialogue': dialogue_data  # Store for canvas editor
            })
        
        # Step 3: Generate Cover Image
        # V4.7: Progress feedback so frontend doesn't appear stuck
        if progress_callback:
            progress_callback("Generating cover image...", 95, {"event": "cover_start"})
        
        cover_url = None
        cover_prompt = chapter_plan.get('cover_prompt', '')
        manga_title = chapter_plan.get('manga_title', self.config.title)
        
        if cover_prompt and self.image_generator and hasattr(self.image_generator, 'generate_cover'):
            try:
                print(f"\n🎨 Generating cover image for '{manga_title}'...")
                cover_result = self.image_generator.generate_cover(
                    prompt=cover_prompt,
                    style=self.config.style,
                    width=768,
                    height=1024
                )
                
                if cover_result:
                    cover_url = f"/outputs/{self.output_dir.name}/cover.png"
                    print(f"✅ Cover generated: {cover_url}")
                    if progress_callback:
                        progress_callback("Cover complete!", 98, {"event": "cover_complete", "cover_url": cover_url})
                else:
                    # Fallback to first page
                    if chapter_pages:
                        cover_url = f"/outputs/{self.output_dir.name}/manga_page_01.png"
                        print(f"📘 Fallback: Using first page as cover")
            except Exception as e:
                print(f"⚠️ Cover generation failed: {e}")
                if chapter_pages:
                    cover_url = f"/outputs/{self.output_dir.name}/manga_page_01.png"
        else:
            # No cover prompt or method - use first page as cover
            if chapter_pages:
                cover_url = f"/outputs/{self.output_dir.name}/manga_page_01.png"
                print(f"📘 Cover: Using first page as cover for '{manga_title}'")
        
        # Step 4: Create PDF
        pdf_path = self._create_pdf(chapter_pages)
        
        # Step 4.5: Update story_state.json with final panel geometry
        # This ensures x,y,w,h data is saved for canvas panel selection
        try:
            import json
            state_path = self.output_dir / "story_state.json"
            if state_path.exists():
                with open(state_path, 'r', encoding='utf-8') as f:
                    story_state = json.load(f)
                
                # MERGE chapters: Get existing chapters and append/update pages
                existing_chapters = story_state.get("chapters", [])
                
                if existing_chapters and isinstance(existing_chapters, list):
                    # Get existing pages from all chapters
                    existing_pages = []
                    for ch in existing_chapters:
                        if isinstance(ch, dict):
                            existing_pages.extend(ch.get("pages", []))
                    
                    # Merge: Append new pages to existing (avoid duplicates by page_number)
                    existing_page_nums = {p.get("page_number") for p in existing_pages if isinstance(p, dict)}
                    for page in chapter_pages:
                        if page.get("page_number") not in existing_page_nums:
                            existing_pages.append(page)
                        else:
                            # Update existing page with new data (geometry fix for overwrites)
                            for i, ep in enumerate(existing_pages):
                                if ep.get("page_number") == page.get("page_number"):
                                    existing_pages[i] = page
                                    break
                    
                    # Save as single merged chapter
                    story_state["chapters"] = [{
                        "chapter_number": 1,
                        "title": self.config.title,
                        "pages": existing_pages  # All pages with geometry!
                    }]
                else:
                    # First generation - just save new pages
                    story_state["chapters"] = [{
                        "chapter_number": 1,
                        "title": self.config.title,
                        "pages": chapter_pages
                    }]
                
                with open(state_path, 'w', encoding='utf-8') as f:
                    json.dump(story_state, f, indent=2, ensure_ascii=False)
                print(f"📝 Updated story_state with panel geometry ({len(story_state['chapters'][0]['pages'])} pages)")
        except Exception as e:
            print(f"⚠️ Failed to update story_state with geometry: {e}")
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✅ Chapter Complete!")
        print("=" * 60)
        print(f"   Manga: {manga_title}")
        print(f"   Chapter: {self.config.title}")
        print(f"   Pages: {len(chapter_pages)}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   PDF: {pdf_path}")
        print(f"   Cover: {cover_url}")
        
        if chapter_plan.get('cliffhanger'):
            print(f"\n🎬 Cliffhanger: {chapter_plan.get('cliffhanger')}")
        
        return {
            'manga_title': manga_title,  # NEW: Series name
            'title': self.config.title,   # Chapter title
            'cover_url': cover_url,       # NEW: Cover image URL
            'summary': chapter_plan.get('summary', ''),
            'characters': chapter_plan.get('characters', []),
            'pages': chapter_pages,
            'pdf': pdf_path,
            'elapsed_seconds': elapsed,
            'next_chapter_hook': chapter_plan.get('next_chapter_hook', '')
        }
    
    def _generate_with_groq(self, story_prompt: str, api_key: str) -> Dict:
        """Fallback: Generate chapter plan with Groq (simpler approach)."""
        from scripts.generate_scene_groq import generate_scene_with_groq
        
        pages = []
        for page_num in range(1, self.config.pages + 1):
            scene = generate_scene_with_groq(
                story_prompt=story_prompt,
                style=self.config.style,
                layout=self.config.layout,
                page_number=page_num,
                total_pages=self.config.pages,
                api_key=api_key
            )
            
            # Convert to chapter plan format
            pages.append({
                'page_number': page_num,
                'page_summary': scene.get('title', 'Untitled'),
                'emotional_beat': 'action',
                'panels': scene.get('panels', [])
            })
        
        return {
            'chapter_title': self.config.title,
            'summary': story_prompt[:200],
            'characters': pages[0].get('characters', []) if pages else [],
            'pages': pages
        }
    
    async def _generate_page_panels(self, page_data: Dict, page_num: int, progress_callback: Optional[Callable] = None, base_panel_index: int = 0) -> List[str]:
        """Generate panel images for a single page.
        
        Args:
            page_data: Panel data for this page
            page_num: Page number (1-indexed)
            progress_callback: Optional callback for progress updates
            base_panel_index: Running count of panels generated so far (for accurate indexing)
        """
        
        panels = page_data.get('panels', [])
        characters = {c.get('name', ''): c for c in page_data.get('characters', [])}
        
        # V4 GEOMETRY: Merge layout template dimensions into panels
        # Get template info from page_data (set by LLM or _compose_page fallback)
        layout_template_name = page_data.get('layout_template', '2x2_grid')
        template = LAYOUT_TEMPLATES.get(layout_template_name, LAYOUT_TEMPLATES.get('2x2_grid', {}))
        template_layout = template.get('layout', [])
        
        # Merge w,h from template into each panel (if available)
        for idx, panel in enumerate(panels):
            if idx < len(template_layout):
                template_panel = template_layout[idx]
                panel['w'] = template_panel.get('w', 50)
                panel['h'] = template_panel.get('h', 50)
                panel['x'] = template_panel.get('x', 0)
                panel['y'] = template_panel.get('y', 0)
        
        generated_files = []
        
        for i, panel in enumerate(panels, 1):
            panel_id = f"p{page_num:02d}_panel_{i:02d}"
            filename = f"{panel_id}.png"
            
            # Build enhanced prompt with cinematography parameters
            description = panel.get('description', '')
            shot_type = panel.get('shot_type', 'medium shot')
            camera_angle = panel.get('camera_angle', 'straight-on')
            composition = panel.get('composition', 'rule of thirds')
            lighting_mood = panel.get('lighting_mood', 'soft lighting')
            characters_present = panel.get('characters_present', [])
            
            # Construct base visual prompt with cinematography
            cinematography = f"{shot_type}, {camera_angle}, {composition}, {lighting_mood}"
            
            # Use Character DNA to enhance prompt with visual consistency tags
            prompt = self.character_dna.enhance_panel_prompt(
                base_prompt=f"{cinematography}, {description}",
                characters_present=characters_present
            )
            
            # V4 GEOMETRY FIX: Calculate aspect ratio from panel dimensions
            # Panel dimensions come from layout template (w, h as percentages)
            panel_w_pct = panel.get('w', 50)  # Width percentage from layout
            panel_h_pct = panel.get('h', 50)  # Height percentage from layout
            
            # Convert percentage-based aspect to actual pixel dimensions
            # Base: 1024x1024 at 1:1, adjust based on panel shape
            if panel_w_pct > panel_h_pct:
                # Wide panel (e.g., panorama 100x35 = 2.86:1)
                aspect = panel_w_pct / panel_h_pct
                img_width = 1024
                img_height = max(512, int(1024 / aspect))  # Min 512 for quality
            elif panel_h_pct > panel_w_pct:
                # Tall panel (e.g., portrait 33x70 = 0.47:1)
                aspect = panel_h_pct / panel_w_pct
                img_height = 1024
                img_width = max(512, int(1024 / aspect))
            else:
                # Square panel
                img_width = 1024
                img_height = 1024
            
            print(f"   Panel {i}: {description[:40]}... ({img_width}x{img_height})")
            
            # Hybrid Sync/Async Handler
            gen_func = self.image_generator.generate_image
            if inspect.iscoroutinefunction(gen_func):
                result = await gen_func(
                    prompt=prompt,
                    filename=filename,
                    width=img_width,
                    height=img_height,
                    style=self.config.style,
                    seed=page_num * 100 + i
                )
            else:
                result = gen_func(
                    prompt=prompt,
                    filename=filename,
                    width=img_width,
                    height=img_height,
                    style=self.config.style,
                    seed=page_num * 100 + i
                )
            
            if result:
                generated_files.append(result)
                print(f"   ✅ {filename}")
                
                if progress_callback:
                    # Use base_panel_index for correct dynamic layout indexing
                    global_panel_idx = base_panel_index + (i - 1)
                    data = {
                        "event": "panel_complete",
                        "panel_index": global_panel_idx,
                        "image_path": str(result)
                    }
                    progress_callback(f"Generated Panel {i} on Page {page_num}", -1, data)
            else:
                print(f"   ❌ Failed: {filename}")
            
            time.sleep(1)  # Rate limiting
        
        return generated_files
    
    def _add_dialogue(self, panel_paths: List[str], page_data: Dict, page_num: int) -> tuple[List[str], List[Dict]]:
        """
        Extract dialogue data WITHOUT rendering bubbles.
        
        Returns:
            tuple: (panel_paths_unchanged, dialogue_data_per_panel)
        """
        
        print(f"\n💬 Extracting dialogue data for page {page_num}...")
        
        panels = page_data.get('panels', [])
        dialogue_per_panel = []
        
        for i, panel_data in enumerate(panels, 1):
            dialogues = panel_data.get('dialogue', [])
            
            if dialogues:
                print(f"   📝 Panel {i}: {len(dialogues)} dialogue(s)")
                dialogue_per_panel.append({
                    'panel_index': i - 1,
                    'dialogues': dialogues
                })
            else:
                dialogue_per_panel.append({
                    'panel_index': i - 1,
                    'dialogues': []
                })
        
        print(f"   ℹ️  Dialogue will be composited in canvas editor")
        return panel_paths, dialogue_per_panel
    
    def _compose_page(self, panel_paths: List[str], page_num: int, title: str, page_data: Optional[Dict] = None) -> str:
        """
        Compose panels into a single manga page.
        
        V4.2: Uses layout templates for dynamic composition.
        V4.6: Safety Valve auto-corrects template/panel count mismatches.
        """
        from PIL import Image, ImageDraw, ImageFont
        from scripts.layout_templates import LAYOUT_TEMPLATES, validate_template
        
        print(f"\n📐 Composing page {page_num}...")
        
        # Filter out non-existent files
        valid_panels = [p for p in panel_paths if os.path.exists(p)]
        
        if not valid_panels:
            print("   ⚠️ No valid panels to compose")
            # Create placeholder
            page = Image.new("RGB", (1240, 1754), "white")
            draw = ImageDraw.Draw(page)
            draw.text((620, 877), f"Page {page_num} - Generation Failed", fill="gray", anchor="mm")
            output_path = self.output_dir / f"manga_page_{page_num:02d}.png"
            page.save(output_path)
            return str(output_path)
        
        # Load panels
        panels = [Image.open(p) for p in valid_panels]
        panel_count = len(panels)
        
        # V4.2: Get layout template from page_data
        # Priority: LLM layout_template > config.layout (only if not "dynamic") > 2x2_grid default
        template_name = "2x2_grid"  # Default fallback
        
        if page_data and isinstance(page_data, dict) and page_data.get('layout_template'):
            # Best case: LLM specified a layout template
            template_name = page_data.get('layout_template')
            print(f"   🤖 Using LLM-specified template: {template_name}")
        elif self.config.layout and self.config.layout != "dynamic":
            # User forced a specific layout (not using AI mode)
            layout_map = {"2x2": "2x2_grid", "2x3": "talk_6panel_grid", "full": "reveal_fullpage", "3x3": "2x2_grid"}
            template_name = layout_map.get(self.config.layout, "2x2_grid")
            print(f"   📐 Using user-specified layout: {template_name}")
        else:
            # Dynamic mode without LLM template - use default
            print(f"   ⚠️ No LLM template found, using default: {template_name}")
        
        # V4.6 Safety Valve: Validate template matches actual panel count
        template_name = validate_template(template_name, panel_count)
        template = LAYOUT_TEMPLATES.get(template_name, LAYOUT_TEMPLATES["2x2_grid"])
        
        print(f"   📐 Final template: {template_name} ({template['panel_count']} panels)")
        
        # Page settings
        page_width = 1240
        page_height = 1754  # Standard manga page ratio
        margin = 30
        gutter = 10  # Gap between panels
        
        # Calculate usable area (no title - pure art!)
        usable_width = page_width - (2 * margin)
        usable_height = page_height - (2 * margin)
        
        # Create page
        page = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(page)
        
        # V4: No baked title - pages are pure art!
        # Title/metadata will be handled by the canvas editor or PDF generator
        
        # Place panels according to template layout
        layout = template.get("layout", [])
        for idx, panel_def in enumerate(layout):
            if idx >= len(panels):
                break
            
            # Calculate pixel positions from percentage-based template
            x = margin + int(usable_width * panel_def["x"] / 100)
            y = margin + int(usable_height * panel_def["y"] / 100)  # No title offset!
            w = int(usable_width * panel_def["w"] / 100) - gutter
            h = int(usable_height * panel_def["h"] / 100) - gutter
            
            # Ensure minimum size
            w = max(w, 100)
            h = max(h, 100)
            
            # Resize and paste panel
            panel = panels[idx]
            resized = panel.resize((w, h), Image.LANCZOS)
            page.paste(resized, (x, y))
            
            # Draw panel border
            draw.rectangle([x, y, x + w, y + h], outline="black", width=2)
        
        # V4.4: Apply screentone filter for B/W manga (creates halftone dot pattern)
        if self.config.style == "bw_manga":
            page = self._apply_screentone_filter(page)
        
        # Save
        output_path = self.output_dir / f"manga_page_{page_num:02d}.png"
        page.save(output_path)
        print(f"   ✅ Saved: {output_path}")
        
        return str(output_path)
    
    def _apply_screentone_filter(self, page: 'Image.Image') -> 'Image.Image':
        """
        Apply screentone effect (Floyd-Steinberg dithering) for authentic B/W manga look.
        This creates halftone dot patterns like professionally printed manga.
        """
        import cv2
        import numpy as np
        from PIL import Image
        
        print("   🎨 Applying screentone filter...")
        
        # Convert PIL Image to numpy array
        page_array = np.array(page)
        
        # Convert to grayscale
        if len(page_array.shape) == 3:
            gray = cv2.cvtColor(page_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = page_array
        
        # Apply Floyd-Steinberg dithering
        # This algorithm distributes quantization error to neighboring pixels
        # creating the characteristic manga "dot" pattern
        h, w = gray.shape
        dithered = gray.astype(np.float32)
        
        for y in range(h - 1):
            for x in range(1, w - 1):
                old_pixel = dithered[y, x]
                new_pixel = 255 if old_pixel > 127 else 0
                dithered[y, x] = new_pixel
                error = old_pixel - new_pixel
                
                # Distribute error to neighbors (Floyd-Steinberg weights)
                dithered[y, x + 1] += error * 7 / 16
                dithered[y + 1, x - 1] += error * 3 / 16
                dithered[y + 1, x] += error * 5 / 16
                dithered[y + 1, x + 1] += error * 1 / 16
        
        # Clip values and convert back to uint8
        dithered = np.clip(dithered, 0, 255).astype(np.uint8)
        
        # Convert back to RGB (3-channel grayscale for consistency)
        dithered_rgb = cv2.cvtColor(dithered, cv2.COLOR_GRAY2RGB)
        
        print("   ✅ Screentone applied")
        return Image.fromarray(dithered_rgb)
    
    def _create_pdf(self, chapter_pages: List[Dict]) -> str:
        """Create high-quality PDF from manga pages with proper metadata."""
        
        from PIL import Image
        from datetime import datetime
        
        print("\n📄 Creating chapter PDF...")
        
        page_images = []
        for page_data in sorted(chapter_pages, key=lambda x: x['page_number']):
            if os.path.exists(page_data['page_image']):
                try:
                    img = Image.open(page_data['page_image'])
                    # Convert RGBA to RGB if needed (PDF doesn't support RGBA)
                    if img.mode == 'RGBA':
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        rgb_img.paste(img, mask=img.split()[3])  # Use alpha as mask
                        img = rgb_img
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    page_images.append(img)
                except Exception as e:
                    print(f"   ⚠️ Error loading page {page_data['page_number']}: {e}")
        
        pdf_path = self.output_dir / f"{self.config.title.replace(' ', '_')}_chapter.pdf"
        
        if page_images:
            try:
                page_images[0].save(
                    pdf_path,
                    "PDF",
                    resolution=300.0,  # High resolution for quality
                    quality=95,  # High JPEG quality inside PDF
                    save_all=True,
                    append_images=page_images[1:] if len(page_images) > 1 else [],
                    # PDF metadata
                    title=self.config.title,
                    author="MangaGen AI",
                    creator=f"MangaGen v2.0 | {datetime.now().strftime('%Y-%m-%d')}"
                )
                print(f"   ✅ Saved: {pdf_path} ({len(page_images)} pages, 300 DPI)")
            except Exception as e:
                print(f"   ❌ PDF creation error: {e}")
                return ""
        
        return str(pdf_path)


def main():
    """Test multi-page generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate multi-page manga")
    parser.add_argument("prompt", help="Story prompt")
    parser.add_argument("--title", default="My Manga", help="Chapter title")
    parser.add_argument("--pages", type=int, default=2, help="Number of pages")
    parser.add_argument("--style", default="color_anime", choices=["color_anime", "bw_manga"])
    parser.add_argument("--layout", default="2x2", choices=["2x2", "2x3", "3x3"])
    parser.add_argument("--output", default="outputs")
    parser.add_argument("--complete", action="store_true", help="Complete story in this chapter")
    
    args = parser.parse_args()
    
    config = MangaConfig(
        title=args.title,
        style=args.style,
        layout=args.layout,
        pages=args.pages,
        output_dir=args.output,
        is_complete_story=args.complete
    )
    
    generator = MangaGenerator(config)
    
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("❌ Set GROQ_API_KEY environment variable")
        return 1
    
    result = generator.generate_chapter(args.prompt, groq_key)
    
    print(f"\n🎉 Your manga is ready!")
    print(f"   PDF: {result['pdf']}")
    if result.get('next_chapter_hook'):
        print(f"   Next: {result['next_chapter_hook']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
