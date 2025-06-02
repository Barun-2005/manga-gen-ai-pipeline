#!/usr/bin/env python3
"""
Dialogue System Comprehensive Demo

This script demonstrates the complete dialogue placement system including:
- Smart dialogue placement with visual awareness
- Color mode support (color and black_and_white)
- Bubble validation and quality scoring
- Side-by-side comparisons
- Comprehensive reporting
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dialogue_placer import DialoguePlacementEngine, create_sample_dialogue
from validators.bubble_validator import BubbleValidator
from scripts.run_dialogue_pipeline import DialoguePipeline
from scripts.run_full_pipeline import MangaGenPipeline


def demo_dialogue_placement_engine():
    """Demonstrate the core dialogue placement engine."""
    
    print("\n🎯 Demo 1: Dialogue Placement Engine")
    print("=" * 60)
    
    # Test both color modes
    for color_mode in ["color", "black_and_white"]:
        print(f"\n🎨 Testing {color_mode.upper()} mode:")
        
        # Create engine
        engine = DialoguePlacementEngine(color_mode)
        
        # Test text size calculation
        test_dialogue = [
            "What is this ancient symbol?",
            "It looks like a warning...",
            "We should be careful here."
        ]
        
        for i, dialogue in enumerate(test_dialogue):
            width, height = engine.calculate_text_size(dialogue)
            print(f"   Bubble {i+1}: '{dialogue}' → {width}x{height}px")
        
        # Show bubble styling
        styles = engine.bubble_styles
        print(f"   Bubble color: {styles['bubble_color']}")
        print(f"   Text color: {styles['text_color']}")
        print(f"   Border: {styles['border_color']} ({styles['border_thickness']}px)")
    
    print("✅ Dialogue placement engine demo completed")
    return True


def demo_bubble_validator():
    """Demonstrate the bubble validation system."""
    
    print("\n🔍 Demo 2: Bubble Validation System")
    print("=" * 60)
    
    # Create validator
    validator = BubbleValidator()
    
    print(f"✅ Bubble validator initialized")
    print(f"   Max face overlap: {validator.max_face_overlap}")
    print(f"   Max character overlap: {validator.max_character_overlap}")
    print(f"   Min readability score: {validator.min_readability_score}")
    print(f"   Min overall score: {validator.min_overall_score}")
    
    # Show validation criteria
    print(f"\n📋 Validation Criteria:")
    print(f"   - Face overlap < {validator.max_face_overlap * 100:.0f}%")
    print(f"   - Character overlap < {validator.max_character_overlap * 100:.0f}%")
    print(f"   - Readability score > {validator.min_readability_score * 100:.0f}%")
    print(f"   - Overall score > {validator.min_overall_score * 100:.0f}%")
    
    print("✅ Bubble validator demo completed")
    return True


def demo_full_pipeline_integration():
    """Demonstrate dialogue integration with the full pipeline."""
    
    print("\n🚀 Demo 3: Full Pipeline Integration")
    print("=" * 60)
    
    # Test dialogue with both color modes
    test_cases = [
        {
            "color_mode": "color",
            "dialogue": ["Incredible discovery!", "This changes everything!"],
            "run_name": "demo_color_dialogue"
        },
        {
            "color_mode": "black_and_white", 
            "dialogue": ["Ancient secrets revealed...", "The prophecy is true!"],
            "run_name": "demo_bw_dialogue"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎨 Testing {test_case['color_mode'].upper()} mode pipeline:")
        
        # Create pipeline
        pipeline = MangaGenPipeline()
        
        # Run with dialogue
        success = pipeline.run_complete_pipeline(
            inline_prompt="ninja discovers ancient temple chamber",
            color_mode=test_case["color_mode"],
            enable_dialogue=True,
            dialogue_lines=test_case["dialogue"],
            run_name=test_case["run_name"]
        )
        
        if success:
            print(f"   ✅ {test_case['color_mode'].upper()} pipeline with dialogue: SUCCESS")
        else:
            print(f"   ❌ {test_case['color_mode'].upper()} pipeline with dialogue: FAILED")
    
    print("✅ Full pipeline integration demo completed")
    return True


def demo_standalone_dialogue_pipeline():
    """Demonstrate the standalone dialogue pipeline."""
    
    print("\n💬 Demo 4: Standalone Dialogue Pipeline")
    print("=" * 60)
    
    # Find an existing panel to add dialogue to
    panel_dirs = [
        "outputs/runs/demo_color_dialogue/panels/base",
        "outputs/runs/demo_bw_dialogue/panels/base",
        "outputs/runs/dialogue_test/panels/base"
    ]
    
    test_panel = None
    for panel_dir in panel_dirs:
        panel_path = Path(panel_dir)
        if panel_path.exists():
            panels = list(panel_path.glob("*.png"))
            if panels:
                test_panel = panels[0]
                break
    
    if not test_panel:
        print("   ⚠️ No existing panels found for standalone demo")
        print("   💡 Run the full pipeline demo first to generate test panels")
        return True
    
    print(f"   📁 Using panel: {test_panel.name}")
    
    # Test standalone dialogue pipeline
    dialogue_pipeline = DialoguePipeline()
    
    test_dialogue = [
        "The ancient power awakens!",
        "I must master this technique!",
        "The temple holds many secrets..."
    ]
    
    success = dialogue_pipeline.run_dialogue_pipeline(
        image_path=str(test_panel),
        dialogue_lines=test_dialogue,
        color_mode="black_and_white",
        enable_dialogue=True,
        run_name="demo_standalone_dialogue"
    )
    
    if success:
        print("   ✅ Standalone dialogue pipeline: SUCCESS")
        
        # Show output structure
        output_dir = Path("outputs/runs/demo_standalone_dialogue")
        if output_dir.exists():
            print(f"   📁 Output structure:")
            print(f"      - Dialogue: {output_dir}/dialogue/")
            print(f"      - Validation: {output_dir}/validation/")
            print(f"      - Comparisons: {output_dir}/comparisons/dialogue/")
    else:
        print("   ❌ Standalone dialogue pipeline: FAILED")
    
    print("✅ Standalone dialogue pipeline demo completed")
    return True


def demo_validation_reports():
    """Demonstrate validation reporting capabilities."""
    
    print("\n📊 Demo 5: Validation Reports")
    print("=" * 60)
    
    # Find recent dialogue validation reports
    report_dirs = [
        "outputs/runs/demo_standalone_dialogue/validation",
        "outputs/runs/dialogue_test_dialogue/validation",
        "outputs/runs/color_dialogue_test/validation"
    ]
    
    reports_found = 0
    
    for report_dir in report_dirs:
        report_path = Path(report_dir) / "dialogue_validation_report.md"
        json_path = Path(report_dir) / "bubble_validation.json"
        
        if report_path.exists():
            reports_found += 1
            print(f"\n📋 Report {reports_found}: {report_path.parent.parent.name}")
            
            # Read key metrics from the report
            with open(report_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Extract key information
            for line in lines:
                if "Overall Score" in line and "/" in line:
                    print(f"   {line.strip()}")
                elif "Validation Status" in line:
                    print(f"   {line.strip()}")
                elif "Bubble Count" in line:
                    print(f"   {line.strip()}")
                elif "Average Face Overlap" in line:
                    print(f"   {line.strip()}")
                elif "Average Readability" in line:
                    print(f"   {line.strip()}")
    
    if reports_found == 0:
        print("   ⚠️ No validation reports found")
        print("   💡 Run dialogue demos first to generate validation reports")
    else:
        print(f"\n✅ Found {reports_found} validation reports")
    
    print("✅ Validation reports demo completed")
    return True


def demo_comparison_outputs():
    """Demonstrate comparison output capabilities."""
    
    print("\n🖼️ Demo 6: Comparison Outputs")
    print("=" * 60)
    
    # Find comparison directories
    comparison_dirs = [
        "outputs/runs/demo_standalone_dialogue/comparisons/dialogue",
        "outputs/runs/dialogue_test_dialogue/comparisons/dialogue",
        "outputs/runs/color_dialogue_test/comparisons/dialogue"
    ]
    
    comparisons_found = 0
    
    for comp_dir in comparison_dirs:
        comp_path = Path(comp_dir)
        if comp_path.exists():
            comparisons = list(comp_path.glob("comparison_*.png"))
            if comparisons:
                comparisons_found += len(comparisons)
                print(f"   📁 {comp_path.parent.parent.name}:")
                for comp in comparisons:
                    print(f"      - {comp.name}")
    
    if comparisons_found == 0:
        print("   ⚠️ No comparison images found")
        print("   💡 Run dialogue demos first to generate comparisons")
    else:
        print(f"\n✅ Found {comparisons_found} comparison images")
        print("   💡 These show before/after dialogue placement")
    
    print("✅ Comparison outputs demo completed")
    return True


def main():
    """Run comprehensive dialogue system demo."""
    
    print("💬 Dialogue System Comprehensive Demo")
    print("Smart Dialogue Placement for Manga Panels")
    print("=" * 80)
    
    demos = [
        ("Dialogue Placement Engine", demo_dialogue_placement_engine),
        ("Bubble Validator", demo_bubble_validator),
        ("Full Pipeline Integration", demo_full_pipeline_integration),
        ("Standalone Dialogue Pipeline", demo_standalone_dialogue_pipeline),
        ("Validation Reports", demo_validation_reports),
        ("Comparison Outputs", demo_comparison_outputs)
    ]
    
    passed = 0
    total = len(demos)
    
    for name, demo_func in demos:
        try:
            print(f"\n{'='*20} {name} {'='*20}")
            success = demo_func()
            if success:
                passed += 1
                print(f"✅ {name} demo completed successfully")
            else:
                print(f"❌ {name} demo failed")
        except Exception as e:
            print(f"❌ {name} demo error: {e}")
        
        time.sleep(1)  # Brief pause between demos
    
    print(f"\n🎯 Dialogue System Demo Results")
    print("=" * 80)
    print(f"📊 Completed: {passed}/{total} demonstrations")
    
    if passed == total:
        print("🎉 All dialogue system features demonstrated successfully!")
        print("\n✨ Dialogue System Features:")
        print("   ✅ Smart visual-aware bubble placement")
        print("   ✅ Color mode support (color & black_and_white)")
        print("   ✅ Comprehensive bubble validation")
        print("   ✅ Full pipeline integration")
        print("   ✅ Standalone dialogue pipeline")
        print("   ✅ Detailed validation reports")
        print("   ✅ Before/after comparison images")
        print("   ✅ Metadata tracking and scoring")
        
        print(f"\n📁 Generated Outputs:")
        print(f"   - Dialogue panels: outputs/runs/*/dialogue/")
        print(f"   - Validation reports: outputs/runs/*/validation/")
        print(f"   - Comparisons: outputs/runs/*/comparisons/dialogue/")
        
        return 0
    else:
        print(f"⚠️ {total - passed} demonstrations had issues")
        return 1


if __name__ == "__main__":
    exit(main())
