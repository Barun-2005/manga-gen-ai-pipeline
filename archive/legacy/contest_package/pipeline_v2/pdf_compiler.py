import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from PIL import Image, ImageDraw, ImageFont
import json

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

class MangaPDFCompiler:
    """
    PDF compiler for manga panels with professional layout.
    
    Features:
    - Multi-panel page layouts
    - Title page generation
    - Story information integration
    - Professional manga formatting
    """
    
    def __init__(self):
        """Initialize the PDF compiler."""
        # Page settings (A4 size optimized for manga)
        self.page_width = 1700
        self.page_height = 2400
        self.margin = 50
        self.panel_spacing = 30
        
        # Layout settings
        self.panels_per_page = 2  # 2 panels per page for better readability
        self.title_page_height = 200
        
        print("✅ Manga PDF compiler initialized")
    
    def compile_manga_pdf(
        self,
        manga_dir: str,
        story_data: Dict[str, Any] = None,
        output_filename: str = None
    ) -> str:
        """
        Compile manga panels into a professional PDF.
        
        Args:
            manga_dir: Directory containing manga panels
            story_data: Story structure data
            output_filename: Custom output filename
            
        Returns:
            Path to generated PDF
        """
        manga_path = Path(manga_dir)
        
        if not manga_path.exists():
            raise ValueError(f"Manga directory not found: {manga_dir}")
        
        print(f"📚 Compiling manga PDF from: {manga_path}")
        
        # Find panel images
        panel_files = self._find_panel_images(manga_path)
        
        if not panel_files:
            raise ValueError(f"No panel images found in {manga_dir}")
        
        print(f"   📊 Found {len(panel_files)} panels")
        
        # Load story data if not provided
        if not story_data:
            story_data = self._load_story_data(manga_path)
        
        # Determine output path
        if not output_filename:
            title = story_data.get("title", "Manga").replace(" ", "_")
            output_filename = f"{title}_Complete.pdf"
        
        output_path = manga_path / output_filename
        
        # Create PDF pages
        pages = []
        
        # Create title page
        if story_data:
            title_page = self._create_title_page(story_data)
            pages.append(title_page)
        
        # Create panel pages
        panel_pages = self._create_panel_pages(panel_files, story_data)
        pages.extend(panel_pages)
        
        # Save PDF
        if pages:
            pages[0].save(
                str(output_path),
                save_all=True,
                append_images=pages[1:],
                format='PDF',
                resolution=300.0,
                quality=95
            )
            
            # Get file size
            file_size = os.path.getsize(output_path)
            print(f"✅ PDF compiled successfully: {output_path}")
            print(f"   📄 Pages: {len(pages)}")
            print(f"   📁 File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            return str(output_path)
        else:
            raise ValueError("No pages generated for PDF")
    
    def _find_panel_images(self, manga_path: Path) -> List[Path]:
        """Find and sort panel image files."""
        
        # Look for panel images (panel_01.png, panel_02.png, etc.)
        panel_files = []
        
        for pattern in ["panel_*.png", "panel_*.jpg", "panel_*.jpeg"]:
            panel_files.extend(manga_path.glob(pattern))
        
        # Sort by panel number
        panel_files.sort(key=lambda x: x.name)
        
        return panel_files
    
    def _load_story_data(self, manga_path: Path) -> Dict[str, Any]:
        """Load story data from JSON file."""
        
        story_file = manga_path / "story_structure.json"
        
        if story_file.exists():
            try:
                with open(story_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ Could not load story data: {e}")
        
        # Return minimal story data
        return {
            "title": "Generated Manga",
            "character": {"name": "Protagonist"},
            "panels": []
        }
    
    def _create_title_page(self, story_data: Dict[str, Any]) -> Image.Image:
        """Create a title page for the manga."""
        
        # Create blank page
        page = Image.new('RGB', (self.page_width, self.page_height), 'white')
        draw = ImageDraw.Draw(page)
        
        # Try to load fonts (fallback to default if not available)
        try:
            title_font = ImageFont.truetype("arial.ttf", 72)
            subtitle_font = ImageFont.truetype("arial.ttf", 36)
            text_font = ImageFont.truetype("arial.ttf", 24)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
        
        # Title
        title = story_data.get("title", "Generated Manga")
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (self.page_width - title_width) // 2
        title_y = 300
        
        draw.text((title_x, title_y), title, fill='black', font=title_font)
        
        # Character info
        character = story_data.get("character", {})
        char_name = character.get("name", "Protagonist")
        
        subtitle = f"Featuring: {char_name}"
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (self.page_width - subtitle_width) // 2
        subtitle_y = title_y + 150
        
        draw.text((subtitle_x, subtitle_y), subtitle, fill='black', font=subtitle_font)
        
        # Character description
        char_desc = character.get("personality", "")
        if char_desc:
            desc_text = f"Character: {char_desc}"
            desc_bbox = draw.textbbox((0, 0), desc_text, font=text_font)
            desc_width = desc_bbox[2] - desc_bbox[0]
            desc_x = (self.page_width - desc_width) // 2
            desc_y = subtitle_y + 100
            
            draw.text((desc_x, desc_y), desc_text, fill='black', font=text_font)
        
        # Generation info
        from datetime import datetime
        gen_text = f"Generated: {datetime.now().strftime('%Y-%m-%d')}"
        gen_bbox = draw.textbbox((0, 0), gen_text, font=text_font)
        gen_width = gen_bbox[2] - gen_bbox[0]
        gen_x = (self.page_width - gen_width) // 2
        gen_y = self.page_height - 200
        
        draw.text((gen_x, gen_y), gen_text, fill='gray', font=text_font)
        
        return page
    
    def _create_panel_pages(
        self, 
        panel_files: List[Path], 
        story_data: Dict[str, Any]
    ) -> List[Image.Image]:
        """Create pages with manga panels."""
        
        pages = []
        panels_data = story_data.get("panels", [])
        
        # Group panels by page
        for i in range(0, len(panel_files), self.panels_per_page):
            page_panels = panel_files[i:i + self.panels_per_page]
            page_data = panels_data[i:i + self.panels_per_page] if i < len(panels_data) else []
            
            page = self._create_single_page(page_panels, page_data)
            pages.append(page)
        
        return pages
    
    def _create_single_page(
        self, 
        panel_files: List[Path], 
        panels_data: List[Dict[str, Any]]
    ) -> Image.Image:
        """Create a single page with panels."""
        
        # Create blank page
        page = Image.new('RGB', (self.page_width, self.page_height), 'white')
        
        # Calculate panel dimensions
        available_height = self.page_height - (2 * self.margin)
        available_width = self.page_width - (2 * self.margin)
        
        if len(panel_files) == 1:
            # Single panel - use most of the page
            panel_height = available_height - 100  # Leave space for text
            panel_width = available_width
        else:
            # Multiple panels - stack vertically
            panel_height = (available_height - (len(panel_files) - 1) * self.panel_spacing) // len(panel_files)
            panel_width = available_width
        
        # Place panels
        current_y = self.margin
        
        for i, panel_file in enumerate(panel_files):
            try:
                # Load and resize panel
                panel_img = Image.open(panel_file)
                
                # Maintain aspect ratio
                panel_aspect = panel_img.width / panel_img.height
                
                if panel_width / panel_height > panel_aspect:
                    # Height is limiting factor
                    new_height = panel_height
                    new_width = int(panel_height * panel_aspect)
                else:
                    # Width is limiting factor
                    new_width = panel_width
                    new_height = int(panel_width / panel_aspect)
                
                # Resize panel
                panel_img = panel_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center panel horizontally
                panel_x = self.margin + (panel_width - new_width) // 2
                
                # Paste panel onto page
                page.paste(panel_img, (panel_x, current_y))
                
                # Add panel number/title if available
                if i < len(panels_data):
                    panel_data = panels_data[i]
                    purpose = panel_data.get("narrative_purpose", f"Panel {i+1}")
                    
                    # Add small text below panel
                    draw = ImageDraw.Draw(page)
                    try:
                        font = ImageFont.truetype("arial.ttf", 16)
                    except:
                        font = ImageFont.load_default()
                    
                    text_y = current_y + new_height + 10
                    draw.text((panel_x, text_y), purpose, fill='gray', font=font)
                
                # Move to next panel position
                current_y += panel_height + self.panel_spacing
                
            except Exception as e:
                print(f"⚠️ Error processing panel {panel_file}: {e}")
                continue
        
        return page
