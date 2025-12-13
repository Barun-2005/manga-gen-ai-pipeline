#!/usr/bin/env python3
"""
Simple manga page composer - just arranges panels in a 2x2 grid.
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

def compose_manga_page(output_dir: str = "outputs"):
    """Create a simple manga page from 4 panels."""
    
    print("📄 Composing Manga Page...")
    print("=" * 50)
    
    output_dir = Path(output_dir)
    
    # Load panels
    panels = []
    for i in range(1, 5):
        panel_path = output_dir / f"panel_{i:02d}.png"
        if panel_path.exists():
            img = Image.open(panel_path)
            panels.append(img)
            print(f"   ✅ Loaded panel_{i:02d}.png")
        else:
            print(f"   ❌ Missing panel_{i:02d}.png")
            return None
    
    if len(panels) != 4:
        print("   ❌ Need exactly 4 panels!")
        return None
    
    # Page settings
    page_width = 2480  # A4 at 300 DPI
    page_height = 3508
    margin = 50
    gutter = 30
    
    # Calculate panel size
    panel_width = (page_width - 2 * margin - gutter) // 2
    panel_height = (page_height - 2 * margin - gutter) // 2
    
    # Create white page
    page = Image.new("RGB", (page_width, page_height), "white")
    
    # Resize and place panels
    positions = [
        (margin, margin),  # Top left
        (margin + panel_width + gutter, margin),  # Top right
        (margin, margin + panel_height + gutter),  # Bottom left
        (margin + panel_width + gutter, margin + panel_height + gutter)  # Bottom right
    ]
    
    for i, (panel, pos) in enumerate(zip(panels, positions)):
        resized = panel.resize((panel_width, panel_height), Image.LANCZOS)
        page.paste(resized, pos)
        
        # Add black border
        draw = ImageDraw.Draw(page)
        x, y = pos
        draw.rectangle([x, y, x + panel_width, y + panel_height], outline="black", width=3)
    
    # Add title
    draw = ImageDraw.Draw(page)
    try:
        font = ImageFont.truetype("arial.ttf", 60)
    except:
        font = ImageFont.load_default()
    
    title = "NINJA INFILTRATION"
    draw.text((page_width // 2 - 200, 10), title, fill="black", font=font)
    
    # Save
    output_path = output_dir / "manga_page.png"
    page.save(output_path)
    print(f"\n✅ Saved: {output_path}")
    
    # Also save PDF
    pdf_path = output_dir / "manga_page.pdf"
    page.save(pdf_path, "PDF", resolution=300)
    print(f"✅ Saved: {pdf_path}")
    
    print()
    print("🎉 Manga page complete!")
    
    return str(output_path)


if __name__ == "__main__":
    compose_manga_page()
