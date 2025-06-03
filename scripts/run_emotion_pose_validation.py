#!/usr/bin/env python3
"""
Emotion & Pose Validation Script

Runs end-to-end emotion and pose validation for manga panels.
Generates panels, validates them, and produces detailed reports.
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.panel_generator import EnhancedPanelGenerator
from core.output_manager import OutputManager
from image_gen.prompt_builder import PromptBuilder


class EmotionPoseValidator:
    """Validates emotion and pose matching in generated manga panels."""
    
    def __init__(self, output_dir: str = "outputs/runs"):
        """Initialize the validator."""
        self.output_manager = OutputManager(output_dir)
        self.panel_generator = EnhancedPanelGenerator()
        self.prompt_builder = PromptBuilder()
        
    def run_validation(self, test_scenes: List[Dict[str, Any]], run_id: str = None) -> Dict[str, Any]:
        """
        Run emotion and pose validation on test scenes.
        
        Args:
            test_scenes: List of test scene metadata
            run_id: Optional run identifier
            
        Returns:
            Validation results summary
        """
        if not run_id:
            run_id = f"emotion_pose_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        print(f"🎭 Starting emotion & pose validation: {run_id}")
        
        # Create run directory
        run_dir = self.output_manager.create_new_run(run_id)
        panels_dir = run_dir / "panels"
        validation_dir = run_dir / "validation"
        panels_dir.mkdir(exist_ok=True)
        validation_dir.mkdir(exist_ok=True)
        
        # Validation results
        validation_results = {}
        summary_stats = {
            "total_panels": len(test_scenes),
            "passed_panels": 0,
            "failed_panels": 0,
            "emotion_matches": 0,
            "pose_matches": 0,
            "overall_pass_rate": 0.0
        }
        
        # Process each test scene
        for i, scene in enumerate(test_scenes):
            panel_name = f"panel_{i+1:03d}.png"
            panel_path = panels_dir / panel_name
            
            print(f"\n📸 Generating panel {i+1}/{len(test_scenes)}: {panel_name}")
            
            # Generate panel
            success = self._generate_test_panel(scene, str(panel_path))
            
            if not success:
                print(f"❌ Failed to generate panel {panel_name}")
                validation_results[panel_name] = {
                    "generation_success": False,
                    "error": "Panel generation failed"
                }
                summary_stats["failed_panels"] += 1
                continue
            
            # Validate emotion and pose
            print(f"🔍 Validating emotion and pose for {panel_name}")
            validation_result = self.panel_generator.validate_panel_emotion_pose(
                str(panel_path), scene
            )
            
            # Update results
            validation_results[panel_name] = {
                "generation_success": True,
                "scene_metadata": scene,
                **validation_result
            }
            
            # Update statistics
            if validation_result["overall_status"] == "✔️":
                summary_stats["passed_panels"] += 1
            else:
                summary_stats["failed_panels"] += 1
            
            if validation_result["emotion_validation"]["status"] == "✔️":
                summary_stats["emotion_matches"] += 1
            
            if validation_result["pose_validation"]["status"] == "✔️":
                summary_stats["pose_matches"] += 1
        
        # Calculate pass rates
        if summary_stats["total_panels"] > 0:
            summary_stats["overall_pass_rate"] = summary_stats["passed_panels"] / summary_stats["total_panels"]
            summary_stats["emotion_pass_rate"] = summary_stats["emotion_matches"] / summary_stats["total_panels"]
            summary_stats["pose_pass_rate"] = summary_stats["pose_matches"] / summary_stats["total_panels"]
        
        # Save results
        results_data = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "summary": summary_stats,
            "panel_results": validation_results
        }
        
        # Save JSON report
        json_report_path = validation_dir / "emotion_pose_report.json"
        with open(json_report_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)
        
        # Save markdown report
        md_report_path = validation_dir / "emotion_pose_report.md"
        self._save_markdown_report(results_data, md_report_path)
        
        print(f"\n📊 Validation complete!")
        print(f"Overall pass rate: {summary_stats['overall_pass_rate']:.1%}")
        print(f"Emotion match rate: {summary_stats['emotion_pass_rate']:.1%}")
        print(f"Pose match rate: {summary_stats['pose_pass_rate']:.1%}")
        print(f"Reports saved to: {validation_dir}")
        
        return results_data
    
    def _generate_test_panel(self, scene_metadata: Dict[str, Any], output_path: str) -> bool:
        """Generate a test panel from scene metadata."""
        try:
            # Build prompt from scene metadata
            description = scene_metadata.get("description", "character in scene")
            
            # Use prompt builder to create enhanced prompt
            story_data = {"scenes": [description]}
            positive_prompt, negative_prompt = self.prompt_builder.build_manga_panel_prompt(
                story_data, 0, panel_index=0
            )
            
            # Generate panel
            success = self.panel_generator.generate_panel(
                prompt=positive_prompt,
                output_path=output_path,
                generation_method="txt2img"
            )
            
            return success
            
        except Exception as e:
            print(f"Error generating test panel: {e}")
            return False
    
    def _save_markdown_report(self, results_data: Dict[str, Any], output_path: Path):
        """Save validation results as markdown report."""
        
        summary = results_data["summary"]
        panel_results = results_data["panel_results"]
        
        md_content = f"""# Emotion & Pose Validation Report

**Run ID**: {results_data["run_id"]}  
**Timestamp**: {results_data["timestamp"]}

## Summary Statistics

- **Total Panels**: {summary["total_panels"]}
- **Passed Panels**: {summary["passed_panels"]} ({summary["overall_pass_rate"]:.1%})
- **Failed Panels**: {summary["failed_panels"]}
- **Emotion Match Rate**: {summary["emotion_pass_rate"]:.1%}
- **Pose Match Rate**: {summary["pose_pass_rate"]:.1%}

## Panel Results

"""
        
        for panel_name, result in panel_results.items():
            if not result.get("generation_success", False):
                md_content += f"**{panel_name}**: GENERATION FAILED\n"
                md_content += f"- Error: {result.get('error', 'Unknown error')}\n\n"
                continue
            
            status = result["overall_status"]
            emotion_val = result["emotion_validation"]
            pose_val = result["pose_validation"]
            
            md_content += f"**{panel_name}**: {status}\n"
            md_content += f"- **Intended Emotion**: {emotion_val['intended_emotion']}\n"
            md_content += f"- **Detected Emotion**: {emotion_val['detected_emotion']} (confidence: {emotion_val['emotion_confidence']:.2f})\n"
            md_content += f"- **Emotion Status**: {emotion_val['status']}\n"
            md_content += f"- **Intended Pose**: {pose_val['intended_pose']}\n"
            md_content += f"- **Detected Pose**: {pose_val['detected_pose']} (confidence: {pose_val['pose_confidence']:.2f})\n"
            md_content += f"- **Pose Status**: {pose_val['status']}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)


def create_test_scenes() -> List[Dict[str, Any]]:
    """Create test scenes for validation."""
    
    test_scenes = [
        {
            "description": "happy character jumping with joy",
            "emotion": "happy",
            "pose": "jumping",
            "dialogue": "I'm so excited!"
        },
        {
            "description": "angry character standing with fists clenched",
            "emotion": "angry", 
            "pose": "standing",
            "dialogue": "This is unacceptable!"
        },
        {
            "description": "sad character sitting alone",
            "emotion": "sad",
            "pose": "sitting",
            "dialogue": "I feel so lonely..."
        },
        {
            "description": "scared character crouching in fear",
            "emotion": "scared",
            "pose": "crouching",
            "dialogue": "What was that noise?"
        },
        {
            "description": "surprised character pointing at something",
            "emotion": "surprised",
            "pose": "pointing",
            "dialogue": "Look over there!"
        }
    ]
    
    return test_scenes


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Run emotion and pose validation")
    parser.add_argument("--run-id", help="Custom run identifier")
    parser.add_argument("--output-dir", default="outputs/runs", help="Output directory")
    
    args = parser.parse_args()
    
    # Create validator
    validator = EmotionPoseValidator(args.output_dir)
    
    # Create test scenes
    test_scenes = create_test_scenes()
    
    # Run validation
    results = validator.run_validation(test_scenes, args.run_id)
    
    # Print summary
    summary = results["summary"]
    print(f"\n🎯 Final Results:")
    print(f"   Overall Success: {summary['passed_panels']}/{summary['total_panels']} panels")
    print(f"   Pass Rate: {summary['overall_pass_rate']:.1%}")
    
    # Return success if at least 75% pass
    success_threshold = 0.75
    if summary["overall_pass_rate"] >= success_threshold:
        print(f"✅ Validation PASSED (≥{success_threshold:.0%} threshold)")
        return 0
    else:
        print(f"❌ Validation FAILED (<{success_threshold:.0%} threshold)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
