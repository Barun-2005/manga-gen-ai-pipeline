#!/usr/bin/env python3
"""
MangaGen - Multi-Page Manga Generator

Generates complete manga chapters with:
- Multiple pages
- Consistent characters
- Color or B/W styles
- Chapter structure
"""

import json
import os
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class MangaConfig:
    """Configuration for manga generation."""
    title: str
    style: str = "color_anime"  # "color_anime" or "bw_manga"
    layout: str = "2x2"  # "2x2" (4 panels), "2x3" (6 panels)
    pages: int = 1
    output_dir: str = "outputs"
    
    @property
    def panels_per_page(self) -> int:
        if self.layout == "2x2":
            return 4
        elif self.layout == "2x3":
            return 6
        elif self.layout == "3x3":
            return 9
        return 4


@dataclass
class Character:
    """A character in the manga."""
    name: str
    appearance: str
    personality: str = ""


@dataclass
class Panel:
    """A single manga panel."""
    number: int
    description: str
    shot_type: str = "medium"
    characters_present: List[str] = field(default_factory=list)
    dialogue: List[Dict] = field(default_factory=list)


@dataclass
class MangaPage:
    """A page of manga panels."""
    page_number: int
    panels: List[Panel] = field(default_factory=list)


@dataclass
class MangaChapter:
    """A complete manga chapter."""
    title: str
    chapter_number: int = 1
    characters: List[Character] = field(default_factory=list)
    pages: List[MangaPage] = field(default_factory=list)
    style: str = "color_anime"


class MangaGenerator:
    """
    Complete manga generation pipeline.
    
    Supports:
    - Multi-page chapters
    - Color and B/W styles
    - Multiple characters
    - Smart dialogue placement
    """
    
    def __init__(self, config: MangaConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Import generation modules
        from scripts.generate_scene_groq import generate_scene_with_groq
        from scripts.generate_panels_api import PollinationsGenerator
        from src.dialogue.smart_bubbles import SmartBubblePlacer
        
        self.scene_generator = generate_scene_with_groq
        self.image_generator = PollinationsGenerator(str(self.output_dir))
        self.bubble_placer = SmartBubblePlacer()
    
    def generate_chapter_scenes(
        self,
        story_prompt: str,
        groq_api_key: str
    ) -> List[Dict]:
        """Generate scene plans for all pages in the chapter."""
        
        scenes = []
        total_panels = self.config.pages * self.config.panels_per_page
        
        print(f"\n📖 Generating {self.config.pages} page(s), {total_panels} panels total")
        
        # For multi-page, we expand the story across pages
        for page_num in range(1, self.config.pages + 1):
            print(f"\n📄 Page {page_num}/{self.config.pages}")
            
            # Adjust prompt for page context
            if self.config.pages > 1:
                page_prompt = f"{story_prompt}\n\n[This is page {page_num} of {self.config.pages}. "
                if page_num == 1:
                    page_prompt += "Start the story, introduce characters.]"
                elif page_num == self.config.pages:
                    page_prompt += "Conclude the story with a satisfying ending.]"
                else:
                    page_prompt += "Continue the action, build tension.]"
            else:
                page_prompt = story_prompt
            
            scene = self.scene_generator(
                story_prompt=page_prompt,
                style=self.config.style,
                layout=self.config.layout,
                api_key=groq_api_key
            )
            
            scene['page_number'] = page_num
            scenes.append(scene)
        
        return scenes
    
    def generate_page_panels(
        self,
        scene: Dict,
        page_num: int
    ) -> List[str]:
        """Generate panel images for a single page."""
        
        print(f"\n🎨 Generating panels for page {page_num}...")
        
        panels = scene.get('panels', [])
        characters = {c['name']: c for c in scene.get('characters', [])}
        
        generated_files = []
        
        for i, panel in enumerate(panels, 1):
            panel_id = f"p{page_num:02d}_panel_{i:02d}"
            filename = f"{panel_id}.png"
            
            # Build prompt
            description = panel.get('description', '')
            shot_type = panel.get('shot_type', 'medium')
            
            # Add character details
            char_details = []
            for char_name in panel.get('characters_present', []):
                if char_name in characters:
                    char_details.append(characters[char_name].get('appearance', ''))
            
            prompt_parts = [
                f"{shot_type} shot",
                description,
                ", ".join(char_details) if char_details else ""
            ]
            prompt = ", ".join(p for p in prompt_parts if p)
            
            print(f"   Panel {i}: {description[:40]}...")
            
            result = self.image_generator.generate_image(
                prompt=prompt,
                filename=filename,
                style=self.config.style
            )
            
            if result:
                generated_files.append(result)
                print(f"   ✅ {filename}")
            
            time.sleep(1)  # Rate limiting
        
        return generated_files
    
    def add_dialogue_to_panels(
        self,
        panel_paths: List[str],
        scene: Dict,
        page_num: int
    ) -> List[str]:
        """Add dialogue bubbles to panels."""
        
        print(f"\n💬 Adding dialogue to page {page_num}...")
        
        panels = scene.get('panels', [])
        output_files = []
        
        for i, (panel_path, panel_data) in enumerate(zip(panel_paths, panels), 1):
            dialogues = panel_data.get('dialogue', [])
            
            if dialogues:
                output_path = panel_path.replace('.png', '_bubbles.png')
                self.bubble_placer.place_dialogue(
                    panel_path,
                    dialogues,
                    output_path
                )
                output_files.append(output_path)
                print(f"   ✅ Added {len(dialogues)} bubble(s) to panel {i}")
            else:
                output_files.append(panel_path)
        
        return output_files
    
    def compose_page(
        self,
        panel_paths: List[str],
        page_num: int,
        title: str
    ) -> str:
        """Compose panels into a single manga page."""
        
        from PIL import Image, ImageDraw, ImageFont
        
        print(f"\n📐 Composing page {page_num}...")
        
        # Load panels
        panels = [Image.open(p) for p in panel_paths]
        
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
    
    def generate_chapter(
        self,
        story_prompt: str,
        groq_api_key: str
    ) -> Dict:
        """Generate a complete manga chapter."""
        
        print("=" * 60)
        print(f"📚 MangaGen - Chapter Generation")
        print("=" * 60)
        print(f"   Title: {self.config.title}")
        print(f"   Style: {self.config.style}")
        print(f"   Pages: {self.config.pages}")
        print(f"   Layout: {self.config.layout}")
        
        start_time = time.time()
        
        # Step 1: Generate scenes for all pages
        scenes = self.generate_chapter_scenes(story_prompt, groq_api_key)
        
        # Step 2: Generate panels and compose pages
        chapter_pages = []
        
        for scene in scenes:
            page_num = scene['page_number']
            
            # Generate panel images
            panel_paths = self.generate_page_panels(scene, page_num)
            
            # Add dialogue
            bubble_paths = self.add_dialogue_to_panels(panel_paths, scene, page_num)
            
            # Compose page
            page_path = self.compose_page(
                bubble_paths,
                page_num,
                self.config.title
            )
            
            chapter_pages.append({
                'page_number': page_num,
                'scene': scene,
                'panels': panel_paths,
                'page_image': page_path
            })
        
        # Step 3: Create PDF with all pages
        pdf_path = self.create_chapter_pdf(chapter_pages)
        
        elapsed = time.time() - start_time
        
        print("\n" + "=" * 60)
        print(f"✅ Chapter Complete!")
        print("=" * 60)
        print(f"   Pages: {len(chapter_pages)}")
        print(f"   Time: {elapsed/60:.1f} minutes")
        print(f"   PDF: {pdf_path}")
        
        return {
            'title': self.config.title,
            'pages': chapter_pages,
            'pdf': pdf_path,
            'elapsed_seconds': elapsed
        }
    
    def create_chapter_pdf(self, chapter_pages: List[Dict]) -> str:
        """Combine all pages into a single PDF."""
        
        from PIL import Image
        
        print("\n📄 Creating chapter PDF...")
        
        page_images = []
        for page_data in sorted(chapter_pages, key=lambda x: x['page_number']):
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
    
    args = parser.parse_args()
    
    config = MangaConfig(
        title=args.title,
        style=args.style,
        layout=args.layout,
        pages=args.pages,
        output_dir=args.output
    )
    
    generator = MangaGenerator(config)
    
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        print("❌ Set GROQ_API_KEY environment variable")
        return 1
    
    result = generator.generate_chapter(args.prompt, groq_key)
    
    print(f"\n🎉 Your manga is ready!")
    print(f"   PDF: {result['pdf']}")
    
    return 0


if __name__ == "__main__":
    exit(main())
