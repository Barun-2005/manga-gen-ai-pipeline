#!/usr/bin/env python3
"""
Full Manga Generation Script

Generates complete manga from vague prompts with automatic:
- Story structuring and chapter planning
- Dialog and narration assignment  
- Panel generation for each scene
- Organized output with metadata

Usage:
    python scripts/generate_full_manga.py "ninja discovers magic"
    python scripts/generate_full_manga.py "robot learns emotions" --chapters 5
    python scripts/generate_full_manga.py "girl finds portal" --output custom_manga
"""

import os
import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from pipeline.manga_automation import MangaPanelPipeline, generate_manga_from_prompt


def main():
    """Main entry point for full manga generation."""
    parser = argparse.ArgumentParser(
        description="Generate complete manga from vague prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/generate_full_manga.py "ninja discovers magic"
  python scripts/generate_full_manga.py "robot learns emotions" --chapters 5
  python scripts/generate_full_manga.py "girl finds portal" --output my_manga
  
This script will:
  1. Generate a complete story structure with chapters
  2. Create dialog and narration for each scene
  3. Generate manga panels automatically
  4. Organize everything in a structured output directory
        """
    )
    
    parser.add_argument(
        "prompt",
        help="Vague story prompt (e.g., 'ninja discovers magic', 'robot learns emotions')"
    )
    parser.add_argument(
        "--chapters",
        type=int,
        default=3,
        help="Number of chapters to generate (default: 3)"
    )
    parser.add_argument(
        "--output",
        help="Custom output directory name (auto-generated if not specified)"
    )
    
    args = parser.parse_args()
    
    try:
        print("Full Manga Generation System")
        print("=" * 50)
        print(f"📝 Story Prompt: '{args.prompt}'")
        print(f"📚 Chapters: {args.chapters}")
        if args.output:
            print(f"📁 Output: {args.output}")
        print()
        
        # Initialize the pipeline
        pipeline = MangaPanelPipeline()
        
        # Generate the complete manga
        results = pipeline.generate_full_manga(
            prompt=args.prompt,
            chapters=args.chapters,
            output_dir=f"outputs/{args.output}" if args.output else None
        )
        
        # Display results summary
        print("\n" + "=" * 50)
        print("📊 Generation Summary:")
        print(f"📖 Story Title: {results['story_structure']['title']}")
        print(f"📚 Chapters Generated: {len(results['chapters'])}")
        print(f"🖼️  Total Panels: {results['total_panels_generated']}")
        print(f"📁 Output Directory: {results['output_directory']}")
        
        # Chapter breakdown
        print("\n📚 Chapter Breakdown:")
        for i, chapter in enumerate(results['chapters'], 1):
            success_count = sum(1 for scene in chapter['scenes'] if scene['generation_success'])
            total_scenes = len(chapter['scenes'])
            print(f"  Chapter {i}: {chapter['title']}")
            print(f"    Scenes: {total_scenes}, Panels: {success_count}/{total_scenes}")
        
        # Show file structure
        output_path = Path(results['output_directory'])
        print(f"\n📁 Generated Files:")
        print(f"  {output_path}/")
        print(f"  ├── story_structure.json")
        print(f"  ├── manga_results.json")
        for i in range(len(results['chapters'])):
            print(f"  └── chapter_{i+1:02d}/")
            chapter_dir = output_path / f"chapter_{i+1:02d}"
            if chapter_dir.exists():
                panel_files = list(chapter_dir.glob("*.png"))
                for panel_file in sorted(panel_files):
                    print(f"      └── {panel_file.name}")
        
        print(f"\n✅ Manga generation completed successfully!")
        print(f"🎨 Check {results['output_directory']} for your generated manga.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  Generation interrupted by user.")
        return 1
    except Exception as e:
        print(f"\n❌ Error during manga generation: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
