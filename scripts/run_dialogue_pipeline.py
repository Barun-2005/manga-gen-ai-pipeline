#!/usr/bin/env python3
"""
Dialogue Pipeline Runner

Standalone pipeline for adding dialogue bubbles to manga panels with:
- Smart dialogue placement using visual awareness
- Support for both color and black_and_white modes
- Comprehensive validation and quality scoring
- Side-by-side comparison outputs
"""

import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import cv2
import numpy as np

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dialogue_placer import DialoguePlacementEngine, create_sample_dialogue
from validators.bubble_validator import BubbleValidator
from core.output_manager import OutputManager


class DialoguePipeline:
    """Main pipeline for dialogue bubble placement."""
    
    def __init__(self, config_file: str = "config/output_config.json"):
        """Initialize the dialogue pipeline."""
        self.config = self._load_config(config_file)
        self.output_manager = OutputManager()
        
    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """Load configuration file."""
        config_path = Path(config_file)
        
        if not config_path.exists():
            print(f"Config file not found: {config_file}, using defaults")
            return {"color_mode": "color", "dialogue_enabled": True}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            return {"color_mode": "color", "dialogue_enabled": True}
    
    def run_dialogue_pipeline(self, image_path: str, dialogue_lines: List[str],
                            color_mode: str = None, enable_dialogue: bool = True,
                            output_dir: str = None, run_name: str = None) -> bool:
        """
        Run the complete dialogue placement pipeline.
        
        Args:
            image_path: Path to input image
            dialogue_lines: List of dialogue text
            color_mode: Color mode (color or black_and_white)
            enable_dialogue: Whether to enable dialogue placement
            output_dir: Output directory override
            run_name: Run name override
            
        Returns:
            True if successful
        """
        print("💬 Dialogue Placement Pipeline")
        print("=" * 60)
        
        # Validate inputs
        if not Path(image_path).exists():
            print(f"❌ Input image not found: {image_path}")
            return False
        
        if not enable_dialogue:
            print("⚠️ Dialogue placement disabled")
            return True
        
        # Set parameters
        active_color_mode = color_mode or self.config.get("color_mode", "color")
        
        if not run_name:
            run_name = f"dialogue_{Path(image_path).stem}"
        
        print(f"🎨 Color mode: {active_color_mode}")
        print(f"💬 Dialogue lines: {len(dialogue_lines)}")
        print(f"📁 Input: {Path(image_path).name}")
        
        # Create output structure
        if output_dir:
            base_output_dir = Path(output_dir)
        else:
            base_output_dir = Path("outputs/runs") / run_name
        
        # Create run directory
        run_dir = self.output_manager.create_new_run(run_name)
        self.output_manager.set_color_mode(active_color_mode)
        
        # Set up output directories
        dialogue_dir = run_dir / "dialogue"
        comparison_dir = run_dir / "comparisons" / "dialogue"
        validation_dir = run_dir / "validation"
        
        for dir_path in [dialogue_dir, comparison_dir, validation_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Step 1: Place dialogue bubbles
            print(f"\n💬 Step 1: Dialogue Placement")
            success = self._place_dialogue_bubbles(
                image_path, dialogue_lines, active_color_mode, dialogue_dir
            )
            
            if not success:
                print("❌ Dialogue placement failed")
                return False
            
            # Step 2: Validate bubble placement
            print(f"\n🔍 Step 2: Bubble Validation")
            validation_success = self._validate_bubble_placement(
                dialogue_dir, active_color_mode, validation_dir
            )
            
            # Step 3: Create comparisons
            print(f"\n📊 Step 3: Generate Comparisons")
            comparison_success = self._create_comparisons(
                image_path, dialogue_dir, comparison_dir
            )
            
            # Step 4: Update metadata
            print(f"\n📋 Step 4: Update Metadata")
            self._update_run_metadata(validation_dir, active_color_mode)
            
            print(f"\n🎯 Dialogue Pipeline Complete!")
            print(f"   Status: ✅ SUCCESS")
            print(f"   Output: {run_dir}")
            print(f"   Dialogue: {dialogue_dir}")
            print(f"   Comparisons: {comparison_dir}")
            
            return True
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            return False
    
    def _place_dialogue_bubbles(self, image_path: str, dialogue_lines: List[str],
                              color_mode: str, output_dir: Path) -> bool:
        """Place dialogue bubbles on the image."""
        try:
            # Initialize dialogue placement engine
            engine = DialoguePlacementEngine(color_mode)
            
            # Place dialogue
            processed_image, bubbles, metadata = engine.place_dialogue(
                image_path, dialogue_lines
            )
            
            # Save processed image
            output_path = output_dir / f"{color_mode}_with_dialogue.png"
            cv2.imwrite(str(output_path), processed_image)
            
            # Save placement metadata
            metadata_path = output_dir / "placement_metadata.json"
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            print(f"   ✅ Dialogue placed: {len(bubbles)} bubbles")
            print(f"   📁 Saved: {output_path.name}")
            print(f"   📊 Quality: {metadata['placement_quality']}")
            print(f"   🎯 Score: {metadata['average_placement_score']:.3f}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Dialogue placement error: {e}")
            return False
    
    def _validate_bubble_placement(self, dialogue_dir: Path, color_mode: str,
                                 validation_dir: Path) -> bool:
        """Validate dialogue bubble placement quality."""
        try:
            # Find dialogue image
            dialogue_image = dialogue_dir / f"{color_mode}_with_dialogue.png"
            
            if not dialogue_image.exists():
                print(f"   ⚠️ Dialogue image not found: {dialogue_image}")
                return False
            
            # Load placement metadata to get bubble information
            metadata_path = dialogue_dir / "placement_metadata.json"
            if not metadata_path.exists():
                print(f"   ⚠️ Placement metadata not found")
                return False
            
            with open(metadata_path, 'r', encoding='utf-8') as f:
                placement_metadata = json.load(f)
            
            # Create bubble objects from metadata
            from core.dialogue_placer import DialogueBubble
            bubbles = []
            for i, pos in enumerate(placement_metadata.get("bubble_positions", [])):
                bubble = DialogueBubble(
                    text=f"bubble_{i+1}",  # Text not needed for validation
                    x=pos["x"], y=pos["y"],
                    width=pos["width"], height=pos["height"],
                    speaker=pos["speaker"]
                )
                bubbles.append(bubble)
            
            # Run validation
            validator = BubbleValidator()
            validation_results = validator.validate_bubble_placement(
                str(dialogue_image), bubbles, color_mode
            )
            
            # Save validation results
            validation_path = validation_dir / "bubble_validation.json"
            with open(validation_path, 'w', encoding='utf-8') as f:
                json.dump(validation_results, f, indent=2)
            
            # Generate validation report
            self._generate_validation_report(validation_results, validation_dir)
            
            overall_score = validation_results.get("overall_metrics", {}).get("overall_score", 0.0)
            passed = validation_results.get("validation_passed", False)
            
            print(f"   ✅ Validation complete")
            print(f"   📊 Overall score: {overall_score:.3f}")
            print(f"   🎯 Status: {'PASSED' if passed else 'NEEDS IMPROVEMENT'}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Validation error: {e}")
            return False
    
    def _create_comparisons(self, original_image_path: str, dialogue_dir: Path,
                          comparison_dir: Path) -> bool:
        """Create side-by-side comparison images."""
        try:
            # Load original image
            original = cv2.imread(original_image_path)
            if original is None:
                print(f"   ⚠️ Could not load original image")
                return False
            
            # Find dialogue image
            dialogue_files = list(dialogue_dir.glob("*_with_dialogue.png"))
            if not dialogue_files:
                print(f"   ⚠️ No dialogue images found")
                return False
            
            for dialogue_file in dialogue_files:
                # Load dialogue image
                dialogue_image = cv2.imread(str(dialogue_file))
                if dialogue_image is None:
                    continue
                
                # Resize images to same height if needed
                height = min(original.shape[0], dialogue_image.shape[0])
                original_resized = cv2.resize(original, 
                    (int(original.shape[1] * height / original.shape[0]), height))
                dialogue_resized = cv2.resize(dialogue_image,
                    (int(dialogue_image.shape[1] * height / dialogue_image.shape[0]), height))
                
                # Create side-by-side comparison
                comparison = np.hstack([original_resized, dialogue_resized])
                
                # Add labels
                label_height = 30
                labeled_comparison = np.zeros((comparison.shape[0] + label_height, comparison.shape[1], 3), dtype=np.uint8)
                labeled_comparison[label_height:, :] = comparison
                
                # Add text labels
                cv2.putText(labeled_comparison, "Original", (10, 20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                cv2.putText(labeled_comparison, "With Dialogue", 
                           (original_resized.shape[1] + 10, 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                # Save comparison
                comparison_name = f"comparison_{dialogue_file.stem}.png"
                comparison_path = comparison_dir / comparison_name
                cv2.imwrite(str(comparison_path), labeled_comparison)
                
                print(f"   ✅ Comparison saved: {comparison_name}")
            
            return True
            
        except Exception as e:
            print(f"   ❌ Comparison creation error: {e}")
            return False
    
    def _update_run_metadata(self, validation_dir: Path, color_mode: str):
        """Update run metadata with dialogue information."""
        try:
            # Load validation results
            validation_path = validation_dir / "bubble_validation.json"
            if validation_path.exists():
                with open(validation_path, 'r', encoding='utf-8') as f:
                    validation_data = json.load(f)
                
                # Update run metadata
                if hasattr(self.output_manager, 'run_metadata') and self.output_manager.run_metadata:
                    overall_metrics = validation_data.get("overall_metrics", {})
                    
                    self.output_manager.run_metadata.update({
                        "dialogue_enabled": True,
                        "dialogue_bubble_score": overall_metrics.get("overall_score", 0.0),
                        "bubble_overlap_score": 1.0 - overall_metrics.get("average_face_overlap", 0.0),
                        "bubble_count": validation_data.get("bubble_count", 0),
                        "dialogue_validation_passed": validation_data.get("validation_passed", False)
                    })
                    
                    # Save updated metadata
                    self.output_manager._save_metadata()
                    
                    print(f"   ✅ Metadata updated with dialogue scores")
            
        except Exception as e:
            print(f"   ⚠️ Metadata update error: {e}")
    
    def _generate_validation_report(self, validation_results: Dict[str, Any], 
                                  validation_dir: Path):
        """Generate human-readable validation report."""
        report_path = validation_dir / "dialogue_validation_report.md"
        
        overall_metrics = validation_results.get("overall_metrics", {})
        
        report_content = f"""# Dialogue Bubble Validation Report

## Overview
- **Image**: {validation_results.get('image_path', 'Unknown')}
- **Color Mode**: {validation_results.get('color_mode', 'Unknown')}
- **Bubble Count**: {validation_results.get('bubble_count', 0)}
- **Validation Status**: {'✅ PASSED' if validation_results.get('validation_passed', False) else '❌ NEEDS IMPROVEMENT'}

## Overall Metrics
- **Overall Score**: {overall_metrics.get('overall_score', 0.0):.3f} / 1.000
- **Average Face Overlap**: {overall_metrics.get('average_face_overlap', 0.0):.3f}
- **Average Character Overlap**: {overall_metrics.get('average_character_overlap', 0.0):.3f}
- **Average Readability**: {overall_metrics.get('average_readability', 0.0):.3f}
- **Average Alignment**: {overall_metrics.get('average_alignment', 0.0):.3f}

## Issues Summary
- **Bubbles with Issues**: {overall_metrics.get('bubbles_with_issues', 0)}
- **Total Issues**: {overall_metrics.get('total_issues', 0)}

## Recommendations
"""
        
        recommendations = validation_results.get("recommendations", [])
        for rec in recommendations:
            report_content += f"- {rec}\n"
        
        report_content += f"""
## Individual Bubble Results
"""
        
        individual_results = validation_results.get("individual_results", [])
        for result in individual_results:
            bubble_id = result.get("bubble_id", 0)
            overall_score = result.get("overall_score", 0.0)
            issues = result.get("issues", [])
            
            report_content += f"""
### Bubble {bubble_id + 1}
- **Overall Score**: {overall_score:.3f}
- **Face Overlap**: {result.get('overlap_with_faces', 0.0):.3f}
- **Character Overlap**: {result.get('overlap_with_characters', 0.0):.3f}
- **Readability**: {result.get('text_readability_score', 0.0):.3f}
- **Alignment**: {result.get('alignment_score', 0.0):.3f}
- **Issues**: {', '.join(issues) if issues else 'None'}
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"   📋 Validation report: {report_path.name}")


def main():
    """Main entry point for dialogue pipeline."""
    parser = argparse.ArgumentParser(description="Manga Dialogue Placement Pipeline")
    
    # Input options
    parser.add_argument("--image", type=str, required=True, help="Input image path")
    parser.add_argument("--dialogue", nargs='+', help="Dialogue lines")
    parser.add_argument("--dialogue-file", type=str, help="File containing dialogue lines")
    
    # Pipeline options
    parser.add_argument("--color-mode", choices=["color", "black_and_white"], 
                       help="Color mode for dialogue bubbles")
    parser.add_argument("--enable-dialogue", action="store_true", default=True,
                       help="Enable dialogue placement")
    parser.add_argument("--disable-dialogue", action="store_true",
                       help="Disable dialogue placement")
    
    # Output options
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--run-name", type=str, help="Run name")
    parser.add_argument("--config", type=str, default="config/output_config.json", 
                       help="Config file")
    
    args = parser.parse_args()
    
    # Process dialogue input
    dialogue_lines = []
    
    if args.dialogue:
        dialogue_lines = args.dialogue
    elif args.dialogue_file:
        dialogue_file = Path(args.dialogue_file)
        if dialogue_file.exists():
            with open(dialogue_file, 'r', encoding='utf-8') as f:
                dialogue_lines = [line.strip() for line in f if line.strip()]
        else:
            print(f"❌ Dialogue file not found: {args.dialogue_file}")
            return 1
    else:
        # Use sample dialogue
        dialogue_lines = create_sample_dialogue()
        print("⚠️ No dialogue specified, using sample dialogue")
    
    # Determine dialogue enable state
    enable_dialogue = args.enable_dialogue and not args.disable_dialogue
    
    # Run pipeline
    pipeline = DialoguePipeline(args.config)
    
    success = pipeline.run_dialogue_pipeline(
        image_path=args.image,
        dialogue_lines=dialogue_lines,
        color_mode=args.color_mode,
        enable_dialogue=enable_dialogue,
        output_dir=args.output_dir,
        run_name=args.run_name
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit(main())
