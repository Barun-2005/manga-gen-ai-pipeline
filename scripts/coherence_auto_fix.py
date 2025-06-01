#!/usr/bin/env python3
"""
Coherence Auto-Fix System

Automatically fixes narrative coherence issues identified by the coherence analyzer.
Regenerates problematic panels with improved prompts and consistency checks.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.eval_coherence import CoherenceEvaluator
# Import will be done dynamically to avoid circular imports


class CoherenceAutoFix:
    """Automatically fixes coherence issues in manga sequences."""
    
    def __init__(self):
        self.evaluator = CoherenceEvaluator()
        # Generator will be imported when needed
        
    def analyze_issues(self, coherence_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze coherence results to identify specific fixable issues."""
        
        issues_summary = {
            "visual_continuity": [],
            "character_consistency": [],
            "narrative_flow": [],
            "low_scoring_sequences": []
        }
        
        sequences = coherence_results.get("sequence_results", [])
        
        for seq in sequences:
            seq_id = seq.get("sequence_id", 0)
            score = seq.get("coherence_score", 0.0)
            issues = seq.get("issues_detected", [])
            
            # Flag low-scoring sequences
            if score < 0.6:
                issues_summary["low_scoring_sequences"].append({
                    "sequence_id": seq_id,
                    "score": score,
                    "panel_range": seq.get("panel_range", "unknown"),
                    "issues": issues
                })
            
            # Categorize issues
            for issue in issues:
                issue_lower = issue.lower()
                
                if any(word in issue_lower for word in ["background", "lighting", "art style", "visual"]):
                    issues_summary["visual_continuity"].append({
                        "sequence_id": seq_id,
                        "issue": issue
                    })
                
                if any(word in issue_lower for word in ["character", "appearance", "outfit", "samurai"]):
                    issues_summary["character_consistency"].append({
                        "sequence_id": seq_id,
                        "issue": issue
                    })
                
                if any(word in issue_lower for word in ["narrative", "transition", "connection", "flow"]):
                    issues_summary["narrative_flow"].append({
                        "sequence_id": seq_id,
                        "issue": issue
                    })
        
        return issues_summary
    
    def generate_improved_prompts(self, manga_results: Dict[str, Any], issues_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improved prompts based on identified issues."""
        
        improved_scenes = []
        
        for chapter in manga_results.get("chapters", []):
            for scene in chapter.get("scenes", []):
                scene_num = scene.get("scene_number", 0)
                original_prompt = scene.get("image_prompt", "")
                
                # Check if this scene needs improvement
                needs_improvement = False
                relevant_issues = []
                
                for issue_cat in issues_summary.values():
                    if isinstance(issue_cat, list):
                        for issue_item in issue_cat:
                            if isinstance(issue_item, dict) and "sequence_id" in issue_item:
                                # Check if this scene is in a problematic sequence
                                seq_id = issue_item["sequence_id"]
                                # Rough mapping: sequence 1 covers scenes 1-3, sequence 2 covers 2-4, etc.
                                if seq_id <= scene_num <= seq_id + 2:
                                    needs_improvement = True
                                    relevant_issues.append(issue_item.get("issue", ""))
                
                if needs_improvement:
                    improved_prompt = self.improve_scene_prompt(
                        original_prompt, 
                        scene_num, 
                        relevant_issues,
                        manga_results
                    )
                    
                    improved_scenes.append({
                        "scene_number": scene_num,
                        "chapter_number": chapter.get("chapter_number", 1),
                        "original_prompt": original_prompt,
                        "improved_prompt": improved_prompt,
                        "issues_addressed": relevant_issues,
                        "description": scene.get("description", ""),
                        "dialogue": scene.get("dialogue", ""),
                        "emotion": scene.get("emotion", "neutral")
                    })
        
        return {"improved_scenes": improved_scenes}
    
    def improve_scene_prompt(self, original_prompt: str, scene_num: int, issues: List[str], manga_results: Dict[str, Any]) -> str:
        """Improve a single scene prompt based on identified issues."""
        
        # Get context from surrounding scenes for consistency
        prev_scene = self.get_scene_by_number(manga_results, scene_num - 1)
        next_scene = self.get_scene_by_number(manga_results, scene_num + 1)
        
        # Base improvements
        improvements = []
        
        # Character consistency fixes
        if any("character" in issue.lower() or "samurai" in issue.lower() for issue in issues):
            improvements.append("CONSISTENT CHARACTER: The same samurai warrior throughout - same armor, katana, facial features, and build")
        
        # Background continuity fixes
        if any("background" in issue.lower() for issue in issues):
            if prev_scene:
                prev_setting = self.extract_setting(prev_scene.get("description", ""))
                improvements.append(f"BACKGROUND CONTINUITY: Smooth transition from {prev_setting}")
        
        # Lighting consistency fixes
        if any("lighting" in issue.lower() for issue in issues):
            improvements.append("CONSISTENT LIGHTING: Maintain atmospheric lighting that matches the scene's mood and time of day")
        
        # Art style consistency
        if any("art style" in issue.lower() for issue in issues):
            improvements.append("CONSISTENT ART STYLE: Traditional manga style with clean lines, detailed backgrounds, and consistent character proportions")
        
        # Narrative flow fixes
        if any("narrative" in issue.lower() or "transition" in issue.lower() for issue in issues):
            improvements.append("CLEAR NARRATIVE FLOW: Visual elements that clearly connect to the story progression")
        
        # Build improved prompt
        improved_prompt = original_prompt
        
        if improvements:
            consistency_notes = " | ".join(improvements)
            improved_prompt = f"{original_prompt} | COHERENCE FIXES: {consistency_notes}"
        
        return improved_prompt
    
    def get_scene_by_number(self, manga_results: Dict[str, Any], scene_num: int) -> Dict[str, Any]:
        """Get scene data by scene number."""
        for chapter in manga_results.get("chapters", []):
            for scene in chapter.get("scenes", []):
                if scene.get("scene_number") == scene_num:
                    return scene
        return {}
    
    def extract_setting(self, description: str) -> str:
        """Extract setting/location from scene description."""
        description_lower = description.lower()
        
        if "village" in description_lower:
            return "village setting"
        elif "mountain" in description_lower:
            return "mountain environment"
        elif "temple" in description_lower:
            return "temple interior"
        elif "battlefield" in description_lower:
            return "battle scene"
        else:
            return "similar environment"
    
    def regenerate_problematic_panels(self, manga_dir: str, improved_scenes: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improved prompts and save them for manual regeneration."""

        print(f"🔧 Preparing improved prompts for {len(improved_scenes['improved_scenes'])} problematic panels...")

        regeneration_results = {
            "improved_prompts": [],
            "scenes_to_regenerate": [],
            "success_count": 0
        }

        # Create improved prompts file
        improved_prompts_file = Path(manga_dir) / "improved_prompts.json"

        for scene_data in improved_scenes["improved_scenes"]:
            scene_num = scene_data["scene_number"]
            chapter_num = scene_data["chapter_number"]
            improved_prompt = scene_data["improved_prompt"]

            print(f"   ✨ Improved prompt for Scene {scene_num} (Chapter {chapter_num})")

            regeneration_results["improved_prompts"].append({
                "scene_number": scene_num,
                "chapter_number": chapter_num,
                "original_prompt": scene_data["original_prompt"],
                "improved_prompt": improved_prompt,
                "description": scene_data["description"],
                "dialogue": scene_data["dialogue"],
                "emotion": scene_data["emotion"],
                "issues_addressed": scene_data["issues_addressed"]
            })

            regeneration_results["scenes_to_regenerate"].append(f"Scene {scene_num}")
            regeneration_results["success_count"] += 1

        # Save improved prompts
        with open(improved_prompts_file, 'w', encoding='utf-8') as f:
            json.dump(regeneration_results["improved_prompts"], f, indent=2)

        print(f"   📁 Improved prompts saved: {improved_prompts_file}")

        return regeneration_results
    
    def auto_fix_coherence_issues(self, manga_dir: str) -> Dict[str, Any]:
        """Main auto-fix function that analyzes and fixes coherence issues."""
        
        print(f"🔧 Starting auto-fix for coherence issues in: {manga_dir}")
        
        # Load existing coherence results
        coherence_file = Path(manga_dir) / "coherence_results.json"
        if not coherence_file.exists():
            print("❌ No coherence results found. Run coherence analysis first.")
            return {"error": "No coherence results found"}
        
        with open(coherence_file, 'r', encoding='utf-8') as f:
            coherence_results = json.load(f)
        
        # Load manga results
        manga_file = Path(manga_dir) / "manga_results.json"
        if not manga_file.exists():
            print("❌ No manga results found.")
            return {"error": "No manga results found"}
        
        with open(manga_file, 'r', encoding='utf-8') as f:
            manga_results = json.load(f)
        
        # Analyze issues
        print("🔍 Analyzing coherence issues...")
        issues_summary = self.analyze_issues(coherence_results)
        
        print(f"   📊 Found {len(issues_summary['low_scoring_sequences'])} low-scoring sequences")
        print(f"   🎨 Visual continuity issues: {len(issues_summary['visual_continuity'])}")
        print(f"   👤 Character consistency issues: {len(issues_summary['character_consistency'])}")
        print(f"   📖 Narrative flow issues: {len(issues_summary['narrative_flow'])}")
        
        # Generate improved prompts
        print("✨ Generating improved prompts...")
        improved_scenes = self.generate_improved_prompts(manga_results, issues_summary)
        
        if not improved_scenes["improved_scenes"]:
            print("✅ No scenes need improvement based on current analysis.")
            return {
                "status": "no_fixes_needed",
                "issues_summary": issues_summary
            }
        
        # Regenerate problematic panels
        regeneration_results = self.regenerate_problematic_panels(manga_dir, improved_scenes)
        
        # Save auto-fix results
        autofix_results = {
            "timestamp": datetime.now().isoformat(),
            "manga_directory": manga_dir,
            "issues_summary": issues_summary,
            "improved_scenes": improved_scenes,
            "regeneration_results": regeneration_results,
            "original_coherence_score": coherence_results.get("overall_coherence_score", 0.0)
        }
        
        autofix_file = Path(manga_dir) / "autofix_results.json"
        with open(autofix_file, 'w', encoding='utf-8') as f:
            json.dump(autofix_results, f, indent=2)
        
        print(f"\n🎉 Auto-fix analysis complete!")
        print(f"   ✨ Generated improved prompts for: {regeneration_results['success_count']} panels")
        print(f"   📋 Scenes to regenerate: {', '.join(regeneration_results['scenes_to_regenerate'])}")
        print(f"   📁 Results saved: {autofix_file}")
        print(f"   📝 Improved prompts: {Path(manga_dir) / 'improved_prompts.json'}")
        print(f"\n💡 Next steps:")
        print(f"   1. Review improved prompts in improved_prompts.json")
        print(f"   2. Regenerate manga with: python scripts/generate_quality_manga.py --fix-coherence")
        print(f"   3. Re-run coherence analysis to verify improvements")
        
        return autofix_results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Auto-fix narrative coherence issues in manga",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/coherence_auto_fix.py outputs/quality_manga_20250601_202543
        """
    )
    
    parser.add_argument(
        "manga_dir",
        help="Path to manga output directory"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize auto-fix system
        autofix = CoherenceAutoFix()
        
        # Run auto-fix
        results = autofix.auto_fix_coherence_issues(args.manga_dir)
        
        if "error" in results:
            print(f"❌ Auto-fix failed: {results['error']}")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Auto-fix system failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
