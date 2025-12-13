#!/usr/bin/env python3
"""
MangaGen - Final Page Composer
Composes panels with dialogue into a complete manga page.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys


def compose_final_manga(
    panels_with_bubbles: bool = True,
    output_dir: str = "outputs",
    title: str = "NINJA INFILTRATION"
):
    """Create final manga page from panels (with or without bubbles)."""
    
    print("📄 Composing Final Manga Page")
    print("=" * 50)
    
    output_dir = Path(output_dir)
    
    # Choose panel files (with bubbles if available)
    panels = []
    for i in range(1, 5):
        if panels_with_bubbles:
            bubble_path = output_dir / f"panel_{i:02d}_bubbles.png"
            if bubble_path.exists():
                panels.append(Image.open(bubble_path))
                print(f"   ✅ panel_{i:02d}_bubbles.png")
                continue
        
        # Fallback to regular panel
        panel_path = output_dir / f"panel_{i:02d}.png"
        if panel_path.exists():
            panels.append(Image.open(panel_path))
            print(f"   ✅ panel_{i:02d}.png")
        else:
            print(f"   ❌ Missing panel_{i:02d}")
            return None
    
    if len(panels) != 4:
        print("   ❌ Need exactly 4 panels!")
        return None
    
    # Page settings (A4 at ~150 DPI for web)
    page_width = 1240
    page_height = 1754
    margin = 30
    gutter = 20
    title_height = 50
    
    # Calculate panel size
    panel_width = (page_width - 2 * margin - gutter) // 2
    panel_height = (page_height - 2 * margin - gutter - title_height) // 2
    
    # Create white page
    page = Image.new("RGB", (page_width, page_height), "white")
    draw = ImageDraw.Draw(page)
    
    # Add title
    try:
        title_font = ImageFont.truetype("arial.ttf", 36)
    except:
        title_font = ImageFont.load_default()
    
    # Center title
    try:
        bbox = draw.textbbox((0, 0), title, font=title_font)
        title_w = bbox[2] - bbox[0]
    except:
        title_w = len(title) * 20
    
    draw.text(
        ((page_width - title_w) // 2, 10),
        title,
        fill="black",
        font=title_font
    )
    
    # Panel positions (2x2 grid below title)
    positions = [
        (margin, title_height + margin),  # Top left
        (margin + panel_width + gutter, title_height + margin),  # Top right
        (margin, title_height + margin + panel_height + gutter),  # Bottom left
        (margin + panel_width + gutter, title_height + margin + panel_height + gutter)  # Bottom right
    ]
    
    # Place panels
    for i, (panel, pos) in enumerate(zip(panels, positions)):
        resized = panel.resize((panel_width, panel_height), Image.LANCZOS)
        page.paste(resized, pos)
        
        # Add black border
        x, y = pos
        draw.rectangle([x, y, x + panel_width, y + panel_height], outline="black", width=3)
    
    # Save PNG
    output_path = output_dir / "manga_final.png"
    page.save(output_path, quality=95)
    print(f"\n✅ Saved: {output_path}")
    
    # Save PDF
    pdf_path = output_dir / "manga_final.pdf"
    page.save(pdf_path, "PDF", resolution=150)
    print(f"✅ Saved: {pdf_path}")
    
    print("\n🎉 Your complete manga is ready!")
    
    return str(output_path)


if __name__ == "__main__":
    compose_final_manga()
