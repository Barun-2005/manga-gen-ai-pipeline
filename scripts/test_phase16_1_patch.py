#!/usr/bin/env python3
"""
Phase 16.1 Patch Test Script: Dialogue Bubble Layout & Shape Variety Upgrade

This script comprehensively tests:
1. Robust bubble layout engine with zero overlap tolerance
2. Multiple bubble shapes (rounded, jagged, thought, dashed, narrative)
3. Automatic tone detection and shape selection
4. Enhanced debug overlays with overlap visualization
5. Comprehensive validation with overlap analysis
6. Production-ready manga dialogue presentation

Quality Criteria:
- Zero bubble overlaps (non-negotiable)
- 100% visible text with no cutoffs
- Correct tone-to-shape mapping
- Visually pleasing layout
- Comprehensive validation reports
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.dialogue_placer import DialoguePlacementEngine
from validators.bubble_validator import BubbleValidator
from scripts.run_full_pipeline import MangaGenPipeline
import cv2


def test_bubble_shapes_and_tones():
    """Test all bubble shapes with appropriate tone detection."""
    
    print("🎨 Test 1: Bubble Shapes & Tone Detection")
    print("=" * 60)
    
    # Test cases for each bubble shape/tone
    test_cases = [
        {
            "dialogue": "Hello there, how are you?",
            "expected_tone": "normal",
            "expected_shape": "rounded",
            "description": "Normal speech - rounded bubble"
        },
        {
            "dialogue": "What an amazing discovery!",
            "expected_tone": "excited", 
            "expected_shape": "jagged",
            "description": "Excited speech - jagged bubble"
        },
        {
            "dialogue": "I'm so angry about this!!",
            "expected_tone": "angry",
            "expected_shape": "jagged", 
            "description": "Angry speech - jagged bubble"
        },
        {
            "dialogue": "Shh... we should be quiet...",
            "expected_tone": "whisper",
            "expected_shape": "dashed",
            "description": "Whisper/uncertainty - dashed bubble"
        },
        {
            "dialogue": "I think this might be important",
            "expected_tone": "thought",
            "expected_shape": "thought",
            "description": "Internal thought - thought bubble"
        },
        {
            "dialogue": "Meanwhile, in the ancient temple chamber...",
            "expected_tone": "narration",
            "expected_shape": "narrative",
            "description": "Narration - narrative box"
        }
    ]
    
    engine = DialoguePlacementEngine("black_and_white")
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n   Test {i}: {test_case['description']}")
        
        # Test tone detection
        detected_tone = engine.detect_dialogue_tone(test_case["dialogue"])
        detected_shape = engine.select_bubble_shape(detected_tone)
        
        tone_correct = detected_tone == test_case["expected_tone"]
        shape_correct = detected_shape == test_case["expected_shape"]
        
        print(f"     Text: '{test_case['dialogue']}'")
        print(f"     Expected: {test_case['expected_tone']} → {test_case['expected_shape']}")
        print(f"     Detected: {detected_tone} → {detected_shape}")
        print(f"     Result: {'✅ PASS' if (tone_correct and shape_correct) else '❌ FAIL'}")
        
        results.append({
            "test_case": test_case["description"],
            "tone_correct": tone_correct,
            "shape_correct": shape_correct,
            "passed": tone_correct and shape_correct
        })
    
    passed_tests = sum(1 for r in results if r["passed"])
    print(f"\n   📊 Shape/Tone Detection: {passed_tests}/{len(results)} tests passed")
    
    return passed_tests == len(results)


def test_multi_bubble_layout():
    """Test multi-bubble layout with overlap prevention."""
    
    print("\n🔧 Test 2: Multi-Bubble Layout Engine")
    print("=" * 60)
    
    # Test cases with multiple bubbles
    test_scenarios = [
        {
            "name": "diverse_tones",
            "prompt": "ninja in mystical chamber",
            "dialogue": [
                "What is this place?",
                "Amazing! Ancient magic still flows here!",
                "We should be very quiet...",
                "I think there's something behind that wall",
                "Meanwhile, the temple guardians awakened..."
            ],
            "description": "5 bubbles with diverse tones and shapes"
        },
        {
            "name": "excitement_heavy",
            "prompt": "ninja discovers treasure",
            "dialogue": [
                "Incredible treasure!",
                "This is absolutely fantastic!",
                "We're rich beyond our wildest dreams!",
                "I can't believe what I'm seeing!"
            ],
            "description": "4 bubbles with excitement (jagged shapes)"
        },
        {
            "name": "thought_heavy",
            "prompt": "ninja contemplates choice",
            "dialogue": [
                "I wonder if I should take this path",
                "Maybe there's another way around",
                "I think the left passage looks safer",
                "Perhaps I should wait for backup"
            ],
            "description": "4 bubbles with thoughts (thought bubbles)"
        }
    ]
    
    # Create output directories
    output_dir = Path("outputs/runs/phase16_1_patch")
    debug_dir = Path("outputs/debug/phase16_1_patch")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for scenario in test_scenarios:
        print(f"\n   🧪 Scenario: {scenario['description']}")
        
        success = test_single_scenario(scenario, output_dir, debug_dir)
        results.append({
            "scenario": scenario["name"],
            "description": scenario["description"],
            "success": success
        })
    
    passed_scenarios = sum(1 for r in results if r["success"])
    print(f"\n   📊 Layout Scenarios: {passed_scenarios}/{len(results)} passed")
    
    return passed_scenarios == len(results)


def test_single_scenario(scenario: dict, output_dir: Path, debug_dir: Path) -> bool:
    """Test a single multi-bubble scenario."""
    
    try:
        # Generate base panel first
        pipeline = MangaGenPipeline()
        panel_success = pipeline.run_complete_pipeline(
            inline_prompt=scenario["prompt"],
            color_mode="black_and_white",
            enable_dialogue=False,
            run_name=f"phase16_1_{scenario['name']}"
        )
        
        if not panel_success:
            print(f"     ❌ Panel generation failed")
            return False
        
        # Find generated panel
        panel_dir = Path(f"outputs/runs/phase16_1_{scenario['name']}/panels/base")
        panel_files = list(panel_dir.glob("*.png"))
        
        if not panel_files:
            print(f"     ❌ No panel found")
            return False
        
        panel_path = panel_files[0]
        
        # Test dialogue placement with layout engine
        engine = DialoguePlacementEngine("black_and_white")
        engine.enable_debug_mode()
        
        # Load image
        image = cv2.imread(str(panel_path))
        if image is None:
            print(f"     ❌ Could not load panel")
            return False
        
        # Place dialogue with multiple bubbles
        result_image, bubbles, metadata = engine.place_dialogue(
            str(panel_path),
            scenario["dialogue"]
        )
        
        # Save results
        dialogue_output = output_dir / f"{scenario['name']}_dialogue.png"
        cv2.imwrite(str(dialogue_output), result_image)
        
        # Create and save debug overlay
        debug_overlay = engine.create_debug_overlay(result_image, bubbles)
        debug_output = debug_dir / f"{scenario['name']}_debug.png"
        cv2.imwrite(str(debug_output), debug_overlay)
        
        # Validate with comprehensive overlap checking
        validator = BubbleValidator()
        validation_results = validator.validate_bubble_placement(
            str(dialogue_output), bubbles, "black_and_white"
        )
        
        # Save validation results
        import json
        validation_output = output_dir / f"{scenario['name']}_validation.json"
        with open(validation_output, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
        
        # Check critical metrics
        overlap_analysis = validation_results.get("overlap_analysis", {})
        overlap_count = overlap_analysis.get("overlap_count", 0)
        zero_overlap = validation_results.get("zero_overlap_achieved", False)
        validation_passed = validation_results.get("validation_passed", False)
        
        # Check shape variety
        shape_usage = metadata.get("shape_usage", {})
        shapes_used = len(shape_usage)
        
        print(f"     📊 Bubbles placed: {len(bubbles)}")
        print(f"     📊 Shapes used: {shapes_used} ({list(shape_usage.keys())})")
        print(f"     📊 Overlaps: {overlap_count}")
        print(f"     📊 Zero overlap: {'✅' if zero_overlap else '❌'}")
        print(f"     📊 Validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")
        
        # Success criteria: zero overlaps + validation pass
        success = zero_overlap and validation_passed
        print(f"     🎯 Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
        
        return success
        
    except Exception as e:
        print(f"     ❌ Error: {e}")
        return False


def generate_comprehensive_report(output_dir: Path):
    """Generate comprehensive test report."""
    
    print("\n📋 Generating Comprehensive Report")
    print("=" * 60)
    
    # Find all validation files
    validation_files = list(output_dir.glob("*_validation.json"))
    
    if not validation_files:
        print("   ⚠️ No validation files found")
        return
    
    import json
    
    total_bubbles = 0
    total_overlaps = 0
    zero_overlap_scenarios = 0
    shape_usage_total = {}
    
    report_content = f"""# Phase 16.1 Patch Test Report
## Dialogue Bubble Layout & Shape Variety Upgrade

**Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}
**Quality Standard**: Zero bubble overlaps + 100% text visibility

## Test Results Summary

"""
    
    for validation_file in validation_files:
        scenario_name = validation_file.stem.replace("_validation", "")
        
        with open(validation_file, 'r', encoding='utf-8') as f:
            validation_data = json.load(f)
        
        bubble_count = validation_data.get("bubble_count", 0)
        overlap_analysis = validation_data.get("overlap_analysis", {})
        overlap_count = overlap_analysis.get("overlap_count", 0)
        zero_overlap = validation_data.get("zero_overlap_achieved", False)
        validation_passed = validation_data.get("validation_passed", False)
        
        total_bubbles += bubble_count
        total_overlaps += overlap_count
        if zero_overlap:
            zero_overlap_scenarios += 1
        
        # Collect shape usage
        for result in validation_data.get("individual_results", []):
            shape = result.get("shape", "unknown")
            shape_usage_total[shape] = shape_usage_total.get(shape, 0) + 1
        
        status = "✅ PASS" if (zero_overlap and validation_passed) else "❌ FAIL"
        
        report_content += f"""### {scenario_name.replace('_', ' ').title()}
- **Bubbles**: {bubble_count}
- **Overlaps**: {overlap_count}
- **Zero Overlap**: {'✅' if zero_overlap else '❌'}
- **Validation**: {'✅ PASS' if validation_passed else '❌ FAIL'}
- **Overall**: {status}

"""
    
    # Overall statistics
    zero_overlap_rate = (zero_overlap_scenarios / len(validation_files)) * 100
    
    report_content += f"""## Overall Statistics

- **Total Scenarios**: {len(validation_files)}
- **Total Bubbles**: {total_bubbles}
- **Total Overlaps**: {total_overlaps}
- **Zero Overlap Rate**: {zero_overlap_rate:.1f}%
- **Zero Overlap Scenarios**: {zero_overlap_scenarios}/{len(validation_files)}

## Shape Usage Statistics

"""
    
    for shape, count in shape_usage_total.items():
        percentage = (count / total_bubbles) * 100 if total_bubbles > 0 else 0
        report_content += f"- **{shape.title()}**: {count} bubbles ({percentage:.1f}%)\n"
    
    report_content += f"""
## Quality Assessment

**CRITICAL REQUIREMENT**: Zero bubble overlaps
- **Status**: {'✅ ACHIEVED' if total_overlaps == 0 else '❌ FAILED'}
- **Overlap Count**: {total_overlaps}

**Shape Variety**: {len(shape_usage_total)} different shapes used
**Layout Quality**: {'✅ EXCELLENT' if zero_overlap_rate >= 100 else '⚠️ NEEDS IMPROVEMENT'}

## Files Generated

### Dialogue Panels
"""
    
    dialogue_files = list(output_dir.glob("*_dialogue.png"))
    for dialogue_file in dialogue_files:
        report_content += f"- `{dialogue_file.name}`\n"
    
    report_content += f"""
### Debug Overlays
"""
    
    debug_files = list(Path("outputs/debug/phase16_1_patch").glob("*_debug.png"))
    for debug_file in debug_files:
        report_content += f"- `{debug_file.name}`\n"
    
    report_content += f"""
### Validation Reports
"""
    
    for validation_file in validation_files:
        report_content += f"- `{validation_file.name}`\n"
    
    # Save report
    report_file = output_dir / "phase16_1_patch_report.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"   📋 Report saved: {report_file}")
    print(f"   📊 Zero overlap rate: {zero_overlap_rate:.1f}%")
    print(f"   📊 Total overlaps: {total_overlaps}")
    
    return total_overlaps == 0


def main():
    """Run comprehensive Phase 16.1 patch tests."""
    
    print("🚀 Phase 16.1 Patch Test: Dialogue Bubble Layout & Shape Variety")
    print("Testing zero-overlap layout engine with multiple bubble shapes")
    print("=" * 80)
    
    # Run all tests
    test_results = []
    
    # Test 1: Shape and tone detection
    shapes_test = test_bubble_shapes_and_tones()
    test_results.append(("Shape/Tone Detection", shapes_test))
    
    # Test 2: Multi-bubble layout
    layout_test = test_multi_bubble_layout()
    test_results.append(("Multi-Bubble Layout", layout_test))
    
    # Generate comprehensive report
    output_dir = Path("outputs/runs/phase16_1_patch")
    report_success = generate_comprehensive_report(output_dir)
    test_results.append(("Zero Overlap Achievement", report_success))
    
    # Final results
    passed_tests = sum(1 for _, result in test_results if result)
    total_tests = len(test_results)
    
    print(f"\n🎯 Phase 16.1 Patch Test Results")
    print("=" * 80)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n📊 Overall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 Phase 16.1 Patch: ALL TESTS PASSED!")
        print("✅ Zero bubble overlaps achieved")
        print("✅ Multiple bubble shapes working")
        print("✅ Layout engine optimized")
        print("✅ Comprehensive validation complete")
        print("\n📁 Review outputs in:")
        print("   - outputs/runs/phase16_1_patch/ (dialogue panels)")
        print("   - outputs/debug/phase16_1_patch/ (debug overlays)")
        return 0
    else:
        print("❌ Phase 16.1 Patch: TESTS FAILED")
        print("⚠️ Review outputs and fix issues before approval")
        return 1


if __name__ == "__main__":
    exit(main())
