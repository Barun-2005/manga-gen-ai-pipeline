import os
import sys
from pathlib import Path

# Add pipeline_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))

from generate_panel import generate_panel
from dialogue_generator import generate_dialogue_for_panel

def main():
    """
    Integrated test that generates both image and dialogue for a manga panel.
    """
    print("=== MANGAGEN INTEGRATED GENERATION TEST ===")
    
    # Define output paths
    img_path = "contest_package/output/integrated_panel.png"
    txt_path = "contest_package/output/integrated_panel_dialogue.txt"
    
    # Ensure output directory exists
    os.makedirs("contest_package/output", exist_ok=True)
    
    try:
        print("\n1. Generating B&W panel with emotion & pose...")
        # Generate a B&W panel with emotion & pose (color workflow has issues)
        generate_panel(
            output_image=img_path,
            style="bw",
            emotion="surprised",
            pose="arms_crossed"
        )
        print(f"✅ Panel generated: {img_path}")
        
        print("\n2. Generating matching dialogue...")
        # Generate matching dialogue
        dialogue = generate_dialogue_for_panel(
            prompt="A surprised character with arms crossed",
            output_path=txt_path
        )
        print(f"✅ Dialogue generated: {txt_path}")
        print(f"   Content: \"{dialogue}\"")
        
        print("\n3. Writing STATUS.md...")
        # Write STATUS.md
        with open("contest_package/STATUS.md", "w", encoding='utf-8') as f:
            f.write("# MangaGen Integrated Pipeline Status\n\n")
            f.write("| Feature                   | Result | Path |\n")
            f.write("|---------------------------|:------:|------|\n")
            f.write(f"| Integrated Image Gen      |  PASS  | {img_path} |\n")
            f.write(f"| Dialogue Generation       |  PASS  | {txt_path} |\n")
            f.write("\n## Test Details\n")
            f.write("- **Style**: Black & White manga panel\n")
            f.write("- **Emotion**: Surprised\n")
            f.write("- **Pose**: Arms crossed\n")
            f.write(f"- **Generated Dialogue**: \"{dialogue}\"\n")
            f.write("\n**READY FOR REVIEW**\n")
        
        print("✅ STATUS.md created: contest_package/STATUS.md")
        
        print("\n=== INTEGRATION TEST COMPLETE ===")
        print("✅ All components working successfully!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        
        # Write failure status
        with open("contest_package/STATUS.md", "w", encoding='utf-8') as f:
            f.write("# MangaGen Integrated Pipeline Status\n\n")
            f.write("| Feature                   | Result | Path |\n")
            f.write("|---------------------------|:------:|------|\n")
            f.write(f"| Integrated Image Gen      |  FAIL  | {img_path} |\n")
            f.write(f"| Dialogue Generation       |  FAIL  | {txt_path} |\n")
            f.write(f"\n**ERROR**: {str(e)}\n")
        
        raise

if __name__ == "__main__":
    main()
