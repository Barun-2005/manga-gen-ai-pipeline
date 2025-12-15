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


@dataclass
class MangaConfig:
    """Configuration for manga generation."""
    title: str
    style: str = "color_anime"  # "color_anime" or "bw_manga"
    layout: str = "2x2"  # "2x2" (4 panels), "2x3" (6 panels)
    pages: int = 1
    output_dir: str = "outputs"
    image_provider: str = "pollinations"  # "pollinations" or "nvidia"
    is_complete_story: bool = False  # If True, wrap up story. If False, leave for continuation.
    
    @property
    def panels_per_page(self) -> int:
        if self.layout == "2x2":
            return 4
        elif self.layout == "2x3":
            return 6
        elif self.layout == "3x3":
            return 9
        return 4


class MangaGenerator:
    """
    Complete manga generation pipeline with intelligent story planning.
    
    Uses:
    - Gemini AI for story planning (Story Director)
    - Pollinations.ai for image generation
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
        
        # Choose image generator based on provider
        if config.image_provider == "nvidia":
            import os
            nvidia_key = os.environ.get("NVIDIA_IMAGE_API_KEY")
            if nvidia_key:
                print(f"📦 Using NVIDIA FLUX.1-dev (sequential mode)")
                self.image_generator = NVIDIAImageGenerator(str(self.output_dir), api_key=nvidia_key)
            else:
                print(f"⚠️ NVIDIA_IMAGE_API_KEY not found, falling back to Pollinations")
                self.image_generator = PollinationsGenerator(str(self.output_dir))
        else:
            print(f"📦 Using Pollinations.ai (parallel mode)")
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
    
    def generate_chapter(
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
                is_complete_story=self.config.is_complete_story
            )
            
            # Register characters with Character DNA Manager
            print("\n🧬 Building Character DNA for visual consistency...")
            self.character_dna.register_characters_from_plan(chapter_plan)
        else:
            # Fallback to Groq (simpler planning)
            print("\n⚡ Using Groq for scene generation (set GEMINI_API_KEY for better results)...")
            chapter_plan = self._generate_with_groq(story_prompt, groq_api_key)
        
        # Step 2: Generate panels and compose pages
        chapter_pages = []
        
        for page_data in chapter_plan.get('pages', []):
            page_num = page_data.get('page_number', len(chapter_pages) + 1)
            
            print(f"\n📄 Processing Page {page_num}/{self.config.pages}")
            print(f"   Beat: {page_data.get('emotional_beat', 'unknown')}")
            
            # Report progress
            if progress_callback:
                # Progress calculation: 20% (planning done) + (80% * page_num / total_pages)
                current_prog = 20 + int(70 * (page_num - 1) / self.config.pages)
                progress_callback(f"Processing page {page_num}/{self.config.pages}...", current_prog, None)
            
            # Generate panel images
            panel_paths = self._generate_page_panels(page_data, page_num, progress_callback)
            
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
                self.config.title
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
                'panels': panel_paths,
                'page_image': page_path,
                'dialogue': dialogue_data  # NEW: Store for canvas editor
            })
        
        # Step 3: Create PDF
        pdf_path = self._create_pdf(chapter_pages)
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✅ Chapter Complete!")
        print("=" * 60)
        print(f"   Pages: {len(chapter_pages)}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   PDF: {pdf_path}")
        
        if chapter_plan.get('cliffhanger'):
            print(f"\n🎬 Cliffhanger: {chapter_plan.get('cliffhanger')}")
        
        return {
            'title': self.config.title,
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
    
    def _generate_page_panels(self, page_data: Dict, page_num: int, progress_callback: Optional[Callable] = None) -> List[str]:
        """Generate panel images for a single page."""
        
        panels = page_data.get('panels', [])
        characters = {c.get('name', ''): c for c in page_data.get('characters', [])}
        
        generated_files = []
        
        for i, panel in enumerate(panels, 1):
            panel_id = f"p{page_num:02d}_panel_{i:02d}"
            filename = f"{panel_id}.png"
            
            # Build detailed prompt
            description = panel.get('description', '')
            shot_type = panel.get('shot_type', 'medium')
            characters_present = panel.get('characters_present', [])
            
            # Use Character DNA to enhance prompt with visual consistency tags
            prompt = self.character_dna.enhance_panel_prompt(
                base_prompt=f"{shot_type} shot, {description}",
                characters_present=characters_present
            )
            
            print(f"   Panel {i}: {description[:40]}...")
            
            result = self.image_generator.generate_image(
                prompt=prompt,
                filename=filename,
                style=self.config.style,
                seed=page_num * 100 + i
            )
            
            if result:
                generated_files.append(result)
                print(f"   ✅ {filename}")
                
                if progress_callback:
                    data = {
                        "event": "panel_complete",
                        "panel_index": (page_num - 1) * 4 + (i - 1),
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
    
    def _compose_page(self, panel_paths: List[str], page_num: int, title: str) -> str:
        """Compose panels into a single manga page."""
        
        from PIL import Image, ImageDraw, ImageFont
        
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
        
        # Page settings
        if self.config.layout == "2x2":
            cols, rows = 2, 2
        elif self.config.layout == "2x3":
            cols, rows = 2, 3
        else:
            cols, rows = 3, 3
        
        page_width = 1240
        margin = 30
        gutter = 20
        title_height = 50
        
        panel_width = (page_width - 2 * margin - (cols - 1) * gutter) // cols
        panel_height = int(panel_width * 1.2)
        page_height = 2 * margin + title_height + rows * panel_height + (rows - 1) * gutter
        
        # Create page
        page = Image.new("RGB", (page_width, page_height), "white")
        draw = ImageDraw.Draw(page)
        
        # Title
        try:
            font = ImageFont.truetype("arial.ttf", 28)
        except:
            font = ImageFont.load_default()
        
        page_title = f"{title} - Page {page_num}"
        draw.text((margin, 15), page_title, fill="black", font=font)
        
        # Place panels
        for idx, panel in enumerate(panels[:cols * rows]):
            row = idx // cols
            col = idx % cols
            
            x = margin + col * (panel_width + gutter)
            y = title_height + margin + row * (panel_height + gutter)
            
            resized = panel.resize((panel_width, panel_height), Image.LANCZOS)
            page.paste(resized, (x, y))
            draw.rectangle([x, y, x + panel_width, y + panel_height], outline="black", width=2)
        
        # Save
        output_path = self.output_dir / f"manga_page_{page_num:02d}.png"
        page.save(output_path)
        print(f"   ✅ Saved: {output_path}")
        
        return str(output_path)
    
    def _create_pdf(self, chapter_pages: List[Dict]) -> str:
        """Combine all pages into a single PDF."""
        
        from PIL import Image
        
        print("\n📄 Creating chapter PDF...")
        
        page_images = []
        for page_data in sorted(chapter_pages, key=lambda x: x['page_number']):
            if os.path.exists(page_data['page_image']):
                img = Image.open(page_data['page_image'])
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                page_images.append(img)
        
        pdf_path = self.output_dir / f"{self.config.title.replace(' ', '_')}_chapter.pdf"
        
        if page_images:
            page_images[0].save(
                pdf_path,
                "PDF",
                resolution=150,
                save_all=True,
                append_images=page_images[1:] if len(page_images) > 1 else []
            )
        
        print(f"   ✅ Saved: {pdf_path}")
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
