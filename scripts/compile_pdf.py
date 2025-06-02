#!/usr/bin/env python3
"""
Manga PDF Compiler

Compiles manga panels into a professional PDF with 2x2 grid layout.
"""

import os
import sys
from pathlib import Path
from typing import List, Tuple
from PIL import Image, ImageDraw
import argparse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.utils import ImageReader
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def collect_panel_images(manga_dir: str) -> List[Path]:
    """
    Collect all panel images from chapter directories in order.

    Args:
        manga_dir: Path to manga output directory

    Returns:
        List of panel image paths in order
    """
    manga_path = Path(manga_dir)
    panel_paths = []

    # Look for chapter directories
    chapter_dirs = sorted([d for d in manga_path.iterdir() if d.is_dir() and d.name.startswith('chapter_')])

    for chapter_dir in chapter_dirs:
        # Look for bubble images first, then regular panels
        bubble_dir = chapter_dir / "with_bubbles"
        if bubble_dir.exists():
            # Only collect *_bubble.png files, not the original copies
            chapter_panels = sorted(bubble_dir.glob("*_bubble.png"))
            if not chapter_panels:
                # Fallback to any PNG in bubble dir if no _bubble.png found
                chapter_panels = sorted(bubble_dir.glob("*.png"))
        else:
            # No bubble directory, use regular panels
            chapter_panels = sorted(chapter_dir.glob("scene_*.png"))

        panel_paths.extend(chapter_panels)

    # If no chapter structure, look for panels directly
    if not panel_paths:
        bubble_dir = manga_path / "with_bubbles"
        if bubble_dir.exists():
            panel_paths = sorted(bubble_dir.glob("*_bubble.png"))
            if not panel_paths:
                panel_paths = sorted(bubble_dir.glob("*.png"))
        else:
            panel_paths = sorted(manga_path.glob("panel_*.png"))

    return panel_paths


def create_manga_page(panel_paths: List[Path], page_size: Tuple[int, int] = (1700, 2400)) -> Image.Image:
    """
    Create a manga page with 2x2 grid layout.
    
    Args:
        panel_paths: List of up to 4 panel image paths
        page_size: Page dimensions (width, height)
        
    Returns:
        PIL Image of the composed page
    """
    page_width, page_height = page_size
    margin = 50
    
    # Calculate panel dimensions
    panel_width = (page_width - 3 * margin) // 2
    panel_height = (page_height - 3 * margin) // 2
    
    # Create blank page
    page = Image.new('RGB', page_size, color='white')
    
    # Panel positions in 2x2 grid
    positions = [
        (margin, margin),                                    # Top-left
        (margin + panel_width + margin, margin),             # Top-right
        (margin, margin + panel_height + margin),            # Bottom-left
        (margin + panel_width + margin, margin + panel_height + margin)  # Bottom-right
    ]
    
    # Place panels
    for i, panel_path in enumerate(panel_paths[:4]):  # Max 4 panels per page
        if i >= len(positions):
            break
            
        try:
            # Load and resize panel
            panel = Image.open(panel_path)
            
            # Resize panel to fit grid while maintaining aspect ratio
            panel.thumbnail((panel_width, panel_height), Image.Resampling.LANCZOS)
            
            # Calculate centering position
            panel_w, panel_h = panel.size
            pos_x, pos_y = positions[i]
            
            # Center the panel in its grid cell
            center_x = pos_x + (panel_width - panel_w) // 2
            center_y = pos_y + (panel_height - panel_h) // 2
            
            # Paste panel onto page
            page.paste(panel, (center_x, center_y))
            
            # Draw border around panel
            draw = ImageDraw.Draw(page)
            border_rect = [
                center_x - 2, center_y - 2,
                center_x + panel_w + 2, center_y + panel_h + 2
            ]
            draw.rectangle(border_rect, outline='black', width=1)
            
        except Exception as e:
            print(f"Error processing panel {panel_path}: {e}")
            continue
    
    return page


def compile_manga_pdf_reportlab(manga_dir: str, output_path: str = None) -> str:
    """
    Compile manga panels into a PDF using ReportLab (more reliable).

    Args:
        manga_dir: Path to manga output directory
        output_path: Optional output PDF path

    Returns:
        Path to the generated PDF
    """
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader

    manga_path = Path(manga_dir)

    if output_path is None:
        output_path = manga_path / "Final_Manga.pdf"
    else:
        output_path = Path(output_path)

    # Collect all panel images
    panel_paths = collect_panel_images(manga_dir)

    if not panel_paths:
        raise Exception(f"No panel images found in {manga_dir}")

    print(f"📚 Compiling {len(panel_paths)} panels into PDF using ReportLab...")

    # Create PDF with ReportLab
    page_width, page_height = 1700, 2400  # Custom page size
    c = canvas.Canvas(str(output_path), pagesize=(page_width, page_height))

    margin = 50
    panel_width = (page_width - 3 * margin) // 2
    panel_height = (page_height - 3 * margin) // 2

    # Panel positions in 2x2 grid
    positions = [
        (margin, page_height - margin - panel_height),                    # Top-left
        (margin + panel_width + margin, page_height - margin - panel_height),  # Top-right
        (margin, page_height - margin - panel_height - margin - panel_height), # Bottom-left
        (margin + panel_width + margin, page_height - margin - panel_height - margin - panel_height)  # Bottom-right
    ]

    panels_on_page = 0
    page_num = 1

    for i, panel_path in enumerate(panel_paths):
        try:
            # Load image
            img = Image.open(panel_path)

            # Resize to fit panel area while maintaining aspect ratio
            img.thumbnail((panel_width, panel_height), Image.Resampling.LANCZOS)

            # Convert to ImageReader for ReportLab
            img_buffer = io.BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            img_reader = ImageReader(img_buffer)

            # Calculate position
            pos_x, pos_y = positions[panels_on_page]

            # Center the image in its grid cell
            img_w, img_h = img.size
            center_x = pos_x + (panel_width - img_w) // 2
            center_y = pos_y + (panel_height - img_h) // 2

            # Draw image
            c.drawImage(img_reader, center_x, center_y, width=img_w, height=img_h)

            # Draw border
            c.rect(center_x - 2, center_y - 2, img_w + 4, img_h + 4, stroke=1, fill=0)

            panels_on_page += 1

            # Start new page after 4 panels
            if panels_on_page >= 4:
                c.showPage()
                panels_on_page = 0
                page_num += 1
                print(f"   Created page {page_num - 1} with 4 panels")

        except Exception as e:
            print(f"Error processing panel {panel_path}: {e}")
            continue

    # Finish the last page if it has panels
    if panels_on_page > 0:
        print(f"   Created page {page_num} with {panels_on_page} panels")

    # Save PDF
    c.save()

    print(f"✅ PDF compiled successfully: {output_path}")

    # Print statistics
    file_size = output_path.stat().st_size
    print(f"📊 PDF Statistics:")
    print(f"   Pages: {page_num}")
    print(f"   Total panels: {len(panel_paths)}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    return str(output_path)


def compile_panels_to_pdf(panel_paths: list, output_path: str) -> str:
    """
    Compile a list of panel images into a PDF.

    Args:
        panel_paths: List of paths to panel images
        output_path: Output PDF path

    Returns:
        str: Path to generated PDF
    """
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Image, PageBreak
    from reportlab.lib.units import inch
    from PIL import Image as PILImage
    import os

    if not panel_paths:
        print("❌ No panels provided")
        return None

    # Create output directory if needed
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Create PDF document
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    story = []

    # Page dimensions
    page_width, page_height = letter
    margin = 0.5 * inch
    available_width = page_width - 2 * margin
    available_height = page_height - 2 * margin

    panels_per_page = 4
    panel_width = available_width / 2
    panel_height = available_height / 2

    for i, panel_path in enumerate(panel_paths):
        if not os.path.exists(panel_path):
            print(f"⚠️  Panel not found: {panel_path}")
            continue

        try:
            # Add image to story
            img = Image(panel_path, width=panel_width, height=panel_height)
            story.append(img)

            # Add page break after every 4 panels
            if (i + 1) % panels_per_page == 0 and i < len(panel_paths) - 1:
                story.append(PageBreak())

        except Exception as e:
            print(f"⚠️  Error processing panel {panel_path}: {e}")
            continue

    # Build PDF
    doc.build(story)

    # Get file size
    file_size = os.path.getsize(output_path)
    print(f"✅ PDF compiled successfully: {output_path}")
    print(f"   Panels: {len(panel_paths)}")
    print(f"   File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")

    return output_path


def compile_manga_pdf(manga_dir: str, output_path: str = None) -> str:
    """
    Compile manga panels into a PDF using ReportLab (reliable method).

    Args:
        manga_dir: Path to manga output directory
        output_path: Optional output PDF path

    Returns:
        Path to the generated PDF
    """
    # Use ReportLab method by default as it's more reliable
    return compile_manga_pdf_reportlab(manga_dir, output_path)


def create_page_previews(manga_dir: str) -> List[str]:
    """
    Create individual page preview images.
    
    Args:
        manga_dir: Path to manga output directory
        
    Returns:
        List of paths to page preview images
    """
    manga_path = Path(manga_dir)
    panel_paths = collect_panel_images(manga_dir)
    
    if not panel_paths:
        return []
    
    preview_dir = manga_path / "page_previews"
    preview_dir.mkdir(exist_ok=True)
    
    preview_paths = []
    
    for i in range(0, len(panel_paths), 4):
        page_panels = panel_paths[i:i+4]
        page_image = create_manga_page(page_panels)
        
        # Save page preview
        page_num = (i // 4) + 1
        preview_path = preview_dir / f"page_{page_num:02d}.png"
        page_image.save(preview_path)
        preview_paths.append(str(preview_path))
        
        print(f"   Created page preview {page_num}: {preview_path}")
    
    return preview_paths


def main():
    """Main entry point for PDF compilation."""
    parser = argparse.ArgumentParser(
        description="Compile manga panels into PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/compile_pdf.py outputs/manga_phase6_20250601_140000
  python scripts/compile_pdf.py outputs/my_manga --output my_manga.pdf
  python scripts/compile_pdf.py outputs/manga_test --previews
        """
    )
    
    parser.add_argument(
        "manga_dir",
        help="Path to manga output directory containing panels"
    )
    parser.add_argument(
        "--output",
        help="Output PDF path (default: Final_Manga.pdf in manga directory)"
    )
    parser.add_argument(
        "--previews",
        action="store_true",
        help="Also create individual page preview images"
    )
    
    args = parser.parse_args()
    
    try:
        print("Manga PDF Compiler")
        print("=" * 40)
        
        # Compile PDF
        pdf_path = compile_manga_pdf(args.manga_dir, args.output)
        
        # Create previews if requested
        if args.previews:
            print("\n📄 Creating page previews...")
            preview_paths = create_page_previews(args.manga_dir)
            print(f"✅ Created {len(preview_paths)} page previews")
        
        print(f"\n🎉 Manga compilation completed!")
        print(f"📚 PDF: {pdf_path}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
