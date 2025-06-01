#!/usr/bin/env python3
"""
Fix Manga Coherence

Regenerates manga panels with improved coherence based on analysis results.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from image_gen.image_generator import generate_image
from scripts.place_dialogue import place_dialogue
from scripts.compile_pdf import compile_manga_pdf


def create_coherent_prompts():
    """Create coherent image prompts that address continuity issues."""
    
    # Character reference for consistency
    character_ref = "A young samurai warrior with traditional dark blue armor, silver katana, determined facial expression, black hair in topknot, athletic build"
    
    # Art style consistency
    art_style = "Traditional manga style with clean lines, detailed backgrounds, consistent character proportions, black and white"
    
    coherent_prompts = [
        # Scene 1: Cursed village beginning
        f"{art_style}, {character_ref}, standing at edge of cursed village with withered trees, abandoned houses, dark storm clouds overhead, ominous atmosphere, dramatic composition",
        
        # Scene 2: Meeting sage (same village setting)
        f"{art_style}, {character_ref}, encountering mysterious old sage with glowing eyes and tattered robes, ancient stone monument with mystical symbols, same cursed village background, magical energy swirling",
        
        # Scene 3: Kneeling before sage (consistent village)
        f"{art_style}, {character_ref}, kneeling respectfully before sage, same cursed village setting with dead trees and dark sky, showing humility and determination",
        
        # Scene 4: Mountain transition (clear path from village)
        f"{art_style}, {character_ref}, beginning to climb mountain path that leads away from village, rocky terrain, mist-covered peaks, maintaining character consistency",
        
        # Scene 5: Mountain peak temple (consistent mountain setting)
        f"{art_style}, {character_ref}, facing massive stone guardian with glowing red eyes at mountain peak temple entrance, lightning in stormy sky, dramatic confrontation",
        
        # Scene 6: Battle scene (same temple entrance)
        f"{art_style}, {character_ref}, epic battle with stone guardian at temple entrance, dynamic sword action, magical energy effects, debris flying, mountain temple setting",
        
        # Scene 7: Temple interior (clear transition inside)
        f"{art_style}, {character_ref}, inside sacred temple approaching pedestal with floating Crystal Sword in beam of light, ancient pillars, mystical symbols, divine atmosphere",
        
        # Scene 8: Claiming sword (same temple interior)
        f"{art_style}, {character_ref}, grasping Crystal Sword with brilliant magical energy radiating, same temple interior, mystical light filling the space",
        
        # Scene 9: Village restored (return to original village)
        f"{art_style}, {character_ref}, returning to village now healed and restored, green grass where decay was, happy villagers emerging, same village layout but renewed"
    ]
    
    return coherent_prompts


def regenerate_manga_with_coherence(manga_dir: str):
    """Regenerate manga panels with improved coherence."""
    
    print(f"🔧 Regenerating manga with improved coherence: {manga_dir}")
    
    # Load existing manga results
    manga_file = Path(manga_dir) / "manga_results.json"
    if not manga_file.exists():
        print("❌ No manga results found")
        return False
    
    with open(manga_file, 'r', encoding='utf-8') as f:
        manga_results = json.load(f)
    
    # Get coherent prompts
    coherent_prompts = create_coherent_prompts()
    
    print(f"🎨 Regenerating {len(coherent_prompts)} panels with coherence fixes...")
    
    # Create backup of original
    backup_dir = Path(manga_dir) / "original_backup"
    backup_dir.mkdir(exist_ok=True)
    
    regeneration_success = 0
    total_scenes = 0
    
    # Regenerate each scene
    for chapter in manga_results["chapters"]:
        chapter_num = chapter["chapter_number"]
        chapter_dir = Path(manga_dir) / f"chapter_{chapter_num:02d}"
        
        for scene in chapter["scenes"]:
            scene_num = scene["scene_number"]
            total_scenes += 1
            
            if scene_num > len(coherent_prompts):
                print(f"   ⚠️  No coherent prompt for scene {scene_num}")
                continue
            
            print(f"   🎨 Regenerating Scene {scene_num} (Chapter {chapter_num})...")
            
            # Backup original if exists
            original_panel = Path(scene["panel_path"])
            if original_panel.exists():
                backup_path = backup_dir / f"scene_{scene_num:02d}_original.png"
                import shutil
                shutil.copy2(original_panel, backup_path)
            
            # Generate new panel with coherent prompt
            coherent_prompt = coherent_prompts[scene_num - 1]
            
            try:
                generated_path = generate_image(
                    prompt=coherent_prompt,
                    index=scene_num,
                    output_dir=str(chapter_dir)
                )
                
                if generated_path and Path(generated_path).exists():
                    # Ensure correct filename
                    target_path = chapter_dir / f"scene_{scene_num:02d}.png"
                    if str(generated_path) != str(target_path):
                        Path(generated_path).rename(target_path)
                    
                    print(f"      ✅ Scene {scene_num} regenerated successfully")
                    
                    # Regenerate dialogue bubble
                    dialogue_lines = scene.get("dialogue_lines", [])
                    if dialogue_lines:
                        bubble_path = chapter_dir / f"scene_{scene_num:02d}_bubble.png"
                        
                        bubble_success = place_dialogue(
                            str(target_path),
                            dialogue_lines,
                            str(bubble_path)
                        )
                        
                        if bubble_success:
                            print(f"      💬 Dialogue added successfully")
                        else:
                            print(f"      ⚠️  Dialogue placement failed")
                    
                    regeneration_success += 1
                    
                else:
                    print(f"      ❌ Scene {scene_num} regeneration failed")
                    
            except Exception as e:
                print(f"      ❌ Scene {scene_num} error: {e}")
    
    # Update manga results with coherence info
    manga_results["coherence_fixed"] = True
    manga_results["coherence_fix_timestamp"] = datetime.now().isoformat()
    manga_results["regenerated_scenes"] = regeneration_success
    
    # Save updated results
    with open(manga_file, 'w', encoding='utf-8') as f:
        json.dump(manga_results, f, indent=2)
    
    # Regenerate PDF
    print(f"\n📄 Regenerating manga PDF...")
    try:
        pdf_path = compile_manga_pdf(manga_dir)
        print(f"✅ Updated PDF created: {pdf_path}")
    except Exception as e:
        print(f"❌ PDF regeneration failed: {e}")
    
    print(f"\n🎉 Coherence fix complete!")
    print(f"   ✅ Successfully regenerated: {regeneration_success}/{total_scenes} scenes")
    print(f"   📁 Original panels backed up to: {backup_dir}")
    
    return regeneration_success > 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix manga coherence issues by regenerating panels",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/fix_manga_coherence.py outputs/quality_manga_20250601_202543
        """
    )
    
    parser.add_argument(
        "manga_dir",
        help="Path to manga output directory"
    )
    
    args = parser.parse_args()
    
    try:
        success = regenerate_manga_with_coherence(args.manga_dir)
        
        if success:
            print(f"\n💡 Next steps:")
            print(f"   1. Run coherence analysis: python scripts/eval_coherence.py {args.manga_dir}")
            print(f"   2. Generate updated reports: python scripts/generate_coherence_report.py --input {args.manga_dir}")
            print(f"   3. Compare before/after coherence scores")
            return 0
        else:
            print(f"❌ Coherence fix failed")
            return 1
        
    except Exception as e:
        print(f"❌ Coherence fix error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
