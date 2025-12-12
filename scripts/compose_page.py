#!/usr/bin/env python3
"""
MangaGen - Page Composer

Composes manga panels with dialogue bubbles into a final page and PDF.
Creates a downloadable zip file for easy Kaggle export.

Usage:
    python scripts/compose_page.py --panels outputs/ --bubbles bubbles.json
    python scripts/compose_page.py --panels outputs/ --bubbles bubbles.json --layout 2x2

Features:
    - Multiple layout options (2x2, vertical_webtoon, 3_panel)
    - Renders dialogue bubbles onto panels
    - Creates PDF output
    - Zips everything for easy Kaggle download
"""

import os
import sys
import json
import argparse
import zipfile
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install Pillow reportlab")
    sys.exit(1)

from src.schemas import MangaScenePlan, BubblePlacement


# ============================================
# Configuration
# ============================================

class PageConfig:
    """Page composition configuration."""
    # Page settings
    page_width: int = 2480   # A4 at 300 DPI
    page_height: int = 3508  # A4 at 300 DPI
    margin: int = 60
    gutter: int = 30  # Space between panels
    
    # Bubble styling
    bubble_padding: int = 12
    font_size: int = 24
    tail_size: int = 20
    
    # Style colors
    bw_manga = {
        "bubble_fill": (255, 255, 255),
        "bubble_outline": (0, 0, 0),
        "text_color": (0, 0, 0),
        "outline_width": 3,
    }
    color_anime = {
        "bubble_fill": (255, 255, 255),
        "bubble_outline": (50, 50, 50),
        "text_color": (30, 30, 30),
        "outline_width": 2,
    }


# ============================================
# Bubble Rendering
# ============================================

class BubbleRenderer:
    """Renders dialogue bubbles onto panel images."""
    
    def __init__(self, style: str = "bw_manga"):
        self.style = style
        self.colors = PageConfig.bw_manga if style == "bw_manga" else PageConfig.color_anime
        
        # Try to load a font
        self.font = self._load_font()
    
    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load a suitable font for bubble text."""
        font_paths = [
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ]
        
        for path in font_paths:
            if os.path.exists(path):
                try:
                    return ImageFont.truetype(path, PageConfig.font_size)
                except:
                    continue
        
        # Fallback to default
        return ImageFont.load_default()
    
    def _wrap_text(self, text: str, max_width: int) -> List[str]:
        """Wrap text to fit within bubble width."""
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        
        # Approximate character width
        char_width = PageConfig.font_size * 0.5
        
        for word in words:
            word_width = len(word) * char_width
            
            if current_width + word_width > max_width - PageConfig.bubble_padding * 2:
                if current_line:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_width = word_width
                else:
                    lines.append(word)
                    current_width = 0
            else:
                current_line.append(word)
                current_width += word_width + char_width
        
        if current_line:
            lines.append(" ".join(current_line))
        
        return lines
    
    def _draw_speech_bubble(
        self,
        draw: ImageDraw.Draw,
        x: int, y: int,
        width: int, height: int,
        bubble_type: str = "speech"
    ):
        """Draw a speech bubble shape."""
        fill = self.colors["bubble_fill"]
        outline = self.colors["bubble_outline"]
        outline_width = self.colors["outline_width"]
        
        if bubble_type == "thought":
            # Cloud-like thought bubble
            radius = min(width, height) // 4
            for dx, dy in [(-10, -5), (10, -5), (15, 5), (-15, 5)]:
                draw.ellipse(
                    [x + width//2 + dx - radius, y + height//2 + dy - radius,
                     x + width//2 + dx + radius, y + height//2 + dy + radius],
                    fill=fill, outline=outline, width=outline_width
                )
            draw.ellipse(
                [x + 5, y + 5, x + width - 5, y + height - 5],
                fill=fill, outline=outline, width=outline_width
            )
        elif bubble_type == "shout":
            # Jagged/starburst bubble
            points = []
            cx, cy = x + width // 2, y + height // 2
            for i in range(12):
                angle = i * 30
                import math
                r = (width // 2) if i % 2 == 0 else (width // 2 - 15)
                px = cx + r * math.cos(math.radians(angle))
                py = cy + (r * 0.7) * math.sin(math.radians(angle))
                points.append((px, py))
            draw.polygon(points, fill=fill, outline=outline, width=outline_width)
        elif bubble_type == "whisper":
            # Dotted bubble
            draw.rounded_rectangle(
                [x, y, x + width, y + height],
                radius=15,
                fill=fill
            )
            # Draw dotted outline
            for i in range(0, width + height, 10):
                if i < width:
                    draw.ellipse([x + i - 2, y - 2, x + i + 2, y + 2], fill=outline)
                    draw.ellipse([x + i - 2, y + height - 2, x + i + 2, y + height + 2], fill=outline)
        elif bubble_type == "narration":
            # Rectangle with sharp corners
            draw.rectangle(
                [x, y, x + width, y + height],
                fill=fill, outline=outline, width=outline_width
            )
        else:  # speech
            # Standard rounded rectangle
            draw.rounded_rectangle(
                [x, y, x + width, y + height],
                radius=20,
                fill=fill, outline=outline, width=outline_width
            )
    
    def render_bubble(
        self,
        image: Image.Image,
        bubble: Dict[str, Any]
    ) -> Image.Image:
        """Render a single bubble onto an image."""
        draw = ImageDraw.Draw(image)
        
        x = bubble["x"]
        y = bubble["y"]
        width = bubble["width"]
        height = bubble["height"]
        text = bubble["text"]
        bubble_type = bubble.get("bubble_type", "speech")
        
        # Draw bubble shape
        self._draw_speech_bubble(draw, x, y, width, height, bubble_type)
        
        # Wrap and draw text
        lines = self._wrap_text(text, width)
        text_color = self.colors["text_color"]
        
        line_height = PageConfig.font_size + 4
        total_text_height = len(lines) * line_height
        start_y = y + (height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            # Center text horizontally
            try:
                bbox = draw.textbbox((0, 0), line, font=self.font)
                text_width = bbox[2] - bbox[0]
            except:
                text_width = len(line) * PageConfig.font_size * 0.5
            
            text_x = x + (width - text_width) // 2
            text_y = start_y + i * line_height
            
            draw.text((text_x, text_y), line, fill=text_color, font=self.font)
        
        return image
    
    def render_panel_with_bubbles(
        self,
        panel_path: Path,
        bubbles: List[Dict[str, Any]]
    ) -> Image.Image:
        """Render all bubbles onto a panel image."""
        image = Image.open(panel_path).convert("RGB")
        
        for bubble in bubbles:
            image = self.render_bubble(image, bubble)
        
        return image


# ============================================
# Page Composer
# ============================================

class PageComposer:
    """Composes panels into manga page layouts."""
    
    def __init__(self, layout: str = "2x2", style: str = "bw_manga"):
        self.layout = layout
        self.style = style
        self.config = PageConfig()
        self.renderer = BubbleRenderer(style)
    
    def _get_layout_positions(self, num_panels: int) -> List[Tuple[int, int, int, int]]:
        """
        Get panel positions (x, y, width, height) based on layout.
        Returns list of (x, y, w, h) tuples.
        """
        w = self.config.page_width
        h = self.config.page_height
        m = self.config.margin
        g = self.config.gutter
        
        usable_w = w - 2 * m
        usable_h = h - 2 * m
        
        if self.layout == "2x2":
            panel_w = (usable_w - g) // 2
            panel_h = (usable_h - g) // 2
            return [
                (m, m, panel_w, panel_h),                         # Top-left
                (m + panel_w + g, m, panel_w, panel_h),           # Top-right
                (m, m + panel_h + g, panel_w, panel_h),           # Bottom-left
                (m + panel_w + g, m + panel_h + g, panel_w, panel_h),  # Bottom-right
            ][:num_panels]
        
        elif self.layout == "vertical_webtoon":
            panel_h = (usable_h - 2 * g) // 3
            return [
                (m, m, usable_w, panel_h),
                (m, m + panel_h + g, usable_w, panel_h),
                (m, m + 2 * (panel_h + g), usable_w, panel_h),
            ][:num_panels]
        
        elif self.layout == "3_panel":
            # Top wide, bottom two smaller
            top_h = usable_h // 2
            bottom_h = usable_h // 2 - g
            panel_w = (usable_w - g) // 2
            return [
                (m, m, usable_w, top_h),                          # Top (wide)
                (m, m + top_h + g, panel_w, bottom_h),            # Bottom-left
                (m + panel_w + g, m + top_h + g, panel_w, bottom_h),  # Bottom-right
            ][:num_panels]
        
        elif self.layout == "single":
            return [(m, m, usable_w, usable_h)]
        
        else:
            # Default to 2x2
            return self._get_layout_positions("2x2", num_panels)
    
    def compose_page(
        self,
        panel_images: List[Image.Image]
    ) -> Image.Image:
        """Compose panels into a single page image."""
        # Create page
        if self.style == "bw_manga":
            page = Image.new("RGB", (self.config.page_width, self.config.page_height), (255, 255, 255))
        else:
            page = Image.new("RGB", (self.config.page_width, self.config.page_height), (250, 250, 255))
        
        # Get layout positions
        positions = self._get_layout_positions(len(panel_images))
        
        # Place panels
        for i, (panel, pos) in enumerate(zip(panel_images, positions)):
            x, y, w, h = pos
            
            # Resize panel to fit position
            resized = panel.resize((w, h), Image.Resampling.LANCZOS)
            
            # Optional: Add border
            border = Image.new("RGB", (w + 4, h + 4), (0, 0, 0))
            border.paste(resized, (2, 2))
            
            page.paste(border, (x - 2, y - 2))
        
        return page
    
    def create_pdf(
        self,
        pages: List[Image.Image],
        output_path: Path,
        title: str = "Manga"
    ):
        """Create a PDF from page images."""
        output_path = Path(output_path)
        
        # Create PDF
        c = canvas.Canvas(str(output_path), pagesize=A4)
        pdf_width, pdf_height = A4
        
        for i, page_img in enumerate(pages):
            # Save temp image
            temp_path = output_path.parent / f"_temp_page_{i}.png"
            page_img.save(temp_path)
            
            # Add to PDF
            c.drawImage(
                str(temp_path),
                0, 0,
                width=pdf_width,
                height=pdf_height,
                preserveAspectRatio=True
            )
            
            if i < len(pages) - 1:
                c.showPage()
            
            # Clean up temp
            temp_path.unlink()
        
        c.save()
        print(f"📄 Created PDF: {output_path}")


# ============================================
# Zip Creator
# ============================================

def create_output_zip(output_dir: Path, zip_name: str = "manga_output.zip") -> Path:
    """
    Create a zip file of all outputs for easy Kaggle download.
    
    Args:
        output_dir: Directory containing outputs
        zip_name: Name of the zip file
        
    Returns:
        Path to the created zip file
    """
    output_dir = Path(output_dir)
    zip_path = output_dir.parent / zip_name
    
    # Remove existing zip
    if zip_path.exists():
        zip_path.unlink()
    
    print(f"📦 Creating output zip: {zip_path}")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(output_dir.parent)
                zf.write(file_path, arcname)
                print(f"   + {arcname}")
    
    size_mb = zip_path.stat().st_size / 1024 / 1024
    print(f"✅ Created zip: {zip_path} ({size_mb:.2f} MB)")
    
    return zip_path


# ============================================
# Main Pipeline
# ============================================

def compose_manga(
    panels_dir: Path,
    bubbles_path: Path,
    scene_plan: MangaScenePlan,
    output_dir: Path
) -> Dict[str, Path]:
    """
    Compose final manga page with bubbles.
    
    Returns:
        Dictionary with paths to output files (page, pdf, zip)
    """
    panels_dir = Path(panels_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load bubbles
    with open(bubbles_path, "r", encoding="utf-8") as f:
        all_bubbles = json.load(f)
    
    # Initialize components
    renderer = BubbleRenderer(style=scene_plan.style)
    composer = PageComposer(layout=scene_plan.layout, style=scene_plan.style)
    
    # Render panels with bubbles
    print("\n🎨 Rendering panels with bubbles...")
    panel_images = []
    
    for panel in scene_plan.panels:
        panel_key = f"panel_{panel.panel_number:02d}"
        panel_path = panels_dir / f"{panel_key}.png"
        
        if not panel_path.exists():
            print(f"   ⚠️ Panel not found: {panel_path}")
            continue
        
        bubbles = all_bubbles.get(panel_key, [])
        
        print(f"   {panel_key}: {len(bubbles)} bubble(s)")
        
        if bubbles:
            rendered = renderer.render_panel_with_bubbles(panel_path, bubbles)
        else:
            rendered = Image.open(panel_path).convert("RGB")
        
        # Save rendered panel
        rendered_path = output_dir / f"{panel_key}_with_bubbles.png"
        rendered.save(rendered_path)
        
        panel_images.append(rendered)
    
    # Compose page
    print("\n📐 Composing page layout...")
    page = composer.compose_page(panel_images)
    
    page_path = output_dir / "manga_page.png"
    page.save(page_path)
    print(f"   Saved page: {page_path}")
    
    # Create PDF
    print("\n📄 Creating PDF...")
    pdf_path = output_dir / "manga_page.pdf"
    composer.create_pdf([page], pdf_path, title=scene_plan.title)
    
    # Create zip
    print("\n📦 Creating output zip...")
    zip_path = create_output_zip(output_dir)
    
    return {
        "page": page_path,
        "pdf": pdf_path,
        "zip": zip_path
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compose manga page with dialogue bubbles",
        epilog="Example: python compose_page.py --panels outputs/ --bubbles bubbles.json"
    )
    parser.add_argument(
        "--panels",
        type=str,
        required=True,
        help="Directory containing panel images"
    )
    parser.add_argument(
        "--bubbles",
        type=str,
        required=True,
        help="Path to bubbles.json"
    )
    parser.add_argument(
        "--scene",
        type=str,
        default="scene_plan.json",
        help="Path to scene_plan.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="outputs",
        help="Output directory (default: outputs)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("📄 MangaGen - Page Composer")
    print("=" * 50)
    
    # Load scene plan
    scene_path = Path(args.scene)
    if not scene_path.exists():
        print(f"❌ Scene plan not found: {scene_path}")
        sys.exit(1)
    
    with open(scene_path, "r", encoding="utf-8") as f:
        scene_data = json.load(f)
    scene_plan = MangaScenePlan(**scene_data)
    
    print(f"📄 Scene: {scene_plan.title}")
    print(f"   Style: {scene_plan.style}")
    print(f"   Layout: {scene_plan.layout}")
    
    # Check bubbles file
    bubbles_path = Path(args.bubbles)
    if not bubbles_path.exists():
        print(f"❌ Bubbles file not found: {bubbles_path}")
        sys.exit(1)
    
    # Compose
    outputs = compose_manga(
        panels_dir=Path(args.panels),
        bubbles_path=bubbles_path,
        scene_plan=scene_plan,
        output_dir=Path(args.output)
    )
    
    # Summary
    print()
    print("=" * 50)
    print("✅ Composition Complete!")
    print("=" * 50)
    print(f"📄 Page: {outputs['page']}")
    print(f"📄 PDF: {outputs['pdf']}")
    print(f"📦 Zip: {outputs['zip']}")
    print()
    print("🎉 Your manga is ready!")


if __name__ == "__main__":
    main()
