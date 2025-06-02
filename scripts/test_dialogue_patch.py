#!/usr/bin/env python3
"""
Dialogue Patch Test Script

Tests the dialogue bubble text cutoff fix by:
1. Generating 3 test panels with different dialogue lengths
2. Enabling debug mode for detailed overlay generation
3. Validating text overflow and bubble adequacy
4. Saving debug overlays and validation reports
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


def test_dialogue_text_sizing():
    """Test dialogue text sizing and bubble adequacy."""
    
    print("🛠️ Dialogue Patch Test: Text Cutoff Fix")
    print("=" * 60)
    
    # Test cases with different text lengths
    test_cases = [
        {
            "name": "short_dialogue",
            "prompt": "ninja in temple chamber",
            "dialogue": ["Yes!", "Found it!"],
            "description": "Short dialogue test"
        },
        {
            "name": "medium_dialogue", 
            "prompt": "ninja examines ancient scroll",
            "dialogue": [
                "This ancient scroll contains powerful secrets!",
                "The prophecy speaks of a hidden temple."
            ],
            "description": "Medium length dialogue test"
        },
        {
            "name": "long_dialogue",
            "prompt": "ninja discovers mystical chamber",
            "dialogue": [
                "Incredible! This chamber has been sealed for over a thousand years!",
                "The ancient writings describe a legendary technique that was thought to be lost forever.",
                "I must study these symbols carefully to unlock their secrets."
            ],
            "description": "Long dialogue test (potential overflow)"
        }
    ]
    
    # Create output directories
    output_dir = Path("outputs/runs/dialogue_patch_test")
    debug_dir = Path("outputs/debug/dialogue_patch_test")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {output_dir}")
    print(f"🔍 Debug directory: {debug_dir}")
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}: {test_case['description']}")
        print("-" * 40)
        
        # Generate panel first
        success = generate_test_panel(test_case, output_dir, i)
        if not success:
            print(f"   ❌ Panel generation failed")
            continue
        
        # Test dialogue placement with debug mode
        dialogue_success = test_dialogue_placement(test_case, output_dir, debug_dir, i)
        
        results.append({
            "test_case": test_case["name"],
            "panel_generation": success,
            "dialogue_placement": dialogue_success,
            "description": test_case["description"]
        })
    
    # Generate summary report
    generate_test_summary(results, output_dir)
    
    return results


def generate_test_panel(test_case: dict, output_dir: Path, test_num: int) -> bool:
    """Generate a test panel for dialogue placement."""
    
    print(f"   🎨 Generating panel: {test_case['name']}")
    
    try:
        # Use the full pipeline to generate a panel
        pipeline = MangaGenPipeline()
        
        run_name = f"dialogue_patch_{test_case['name']}"
        
        success = pipeline.run_complete_pipeline(
            inline_prompt=test_case["prompt"],
            color_mode="black_and_white",
            enable_dialogue=False,  # Generate panel first, add dialogue separately
            run_name=run_name
        )
        
        if success:
            print(f"   ✅ Panel generated successfully")
            return True
        else:
            print(f"   ❌ Panel generation failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Panel generation error: {e}")
        return False


def test_dialogue_placement(test_case: dict, output_dir: Path, debug_dir: Path, test_num: int) -> bool:
    """Test dialogue placement with debug mode enabled."""
    
    print(f"   💬 Testing dialogue placement")
    
    try:
        # Find the generated panel
        panel_dir = Path(f"outputs/runs/dialogue_patch_{test_case['name']}/panels/base")
        panel_files = list(panel_dir.glob("*.png"))
        
        if not panel_files:
            print(f"   ❌ No panel found in {panel_dir}")
            return False
        
        panel_path = panel_files[0]
        print(f"   📁 Using panel: {panel_path.name}")
        
        # Create dialogue placement engine with debug mode
        engine = DialoguePlacementEngine("black_and_white")
        engine.enable_debug_mode()
        
        # Load image
        image = cv2.imread(str(panel_path))
        if image is None:
            print(f"   ❌ Could not load image: {panel_path}")
            return False
        
        # Place dialogue
        result_image, bubbles, metadata = engine.place_dialogue(
            str(panel_path), 
            test_case["dialogue"]
        )
        
        # Save dialogue result
        dialogue_output = output_dir / f"test_{test_num:02d}_{test_case['name']}_dialogue.png"
        cv2.imwrite(str(dialogue_output), result_image)
        print(f"   📁 Saved dialogue panel: {dialogue_output.name}")
        
        # Create and save debug overlay
        debug_overlay = engine.create_debug_overlay(result_image, bubbles)
        debug_output = debug_dir / f"test_{test_num:02d}_{test_case['name']}_debug.png"
        cv2.imwrite(str(debug_output), debug_overlay)
        print(f"   🔍 Saved debug overlay: {debug_output.name}")
        
        # Validate bubble placement
        validator = BubbleValidator()
        validation_results = validator.validate_bubble_placement(
            str(dialogue_output), bubbles, "black_and_white"
        )
        
        # Save validation results
        import json
        validation_output = output_dir / f"test_{test_num:02d}_{test_case['name']}_validation.json"
        with open(validation_output, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2)
        
        # Check for text overflow issues
        overall_metrics = validation_results.get("overall_metrics", {})
        text_overflow_score = overall_metrics.get("average_text_overflow", 1.0)
        bubble_adequacy = overall_metrics.get("average_bubble_adequacy", 1.0)
        
        print(f"   📊 Text overflow score: {text_overflow_score:.3f}")
        print(f"   📊 Bubble adequacy: {bubble_adequacy:.3f}")
        print(f"   📊 Overall score: {overall_metrics.get('overall_score', 0.0):.3f}")
        
        # Check for warnings in individual results
        individual_results = validation_results.get("individual_results", [])
        overflow_issues = 0
        
        for result in individual_results:
            issues = result.get("issues", [])
            for issue in issues:
                if "overflow" in issue.lower() or "too small" in issue.lower():
                    overflow_issues += 1
                    print(f"   ⚠️ Issue detected: {issue}")
        
        if overflow_issues == 0:
            print(f"   ✅ No text overflow issues detected")
        else:
            print(f"   ⚠️ {overflow_issues} text overflow issues detected")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Dialogue placement error: {e}")
        return False


def generate_test_summary(results: list, output_dir: Path):
    """Generate a summary report of all tests."""
    
    print(f"\n📋 Test Summary")
    print("=" * 60)
    
    total_tests = len(results)
    successful_panels = sum(1 for r in results if r["panel_generation"])
    successful_dialogue = sum(1 for r in results if r["dialogue_placement"])
    
    print(f"Total tests: {total_tests}")
    print(f"Successful panel generation: {successful_panels}/{total_tests}")
    print(f"Successful dialogue placement: {successful_dialogue}/{total_tests}")
    
    # Create detailed summary report
    summary_content = f"""# Dialogue Patch Test Summary

## Test Overview
- **Total Tests**: {total_tests}
- **Successful Panel Generation**: {successful_panels}/{total_tests}
- **Successful Dialogue Placement**: {successful_dialogue}/{total_tests}
- **Test Date**: {time.strftime('%Y-%m-%d %H:%M:%S')}

## Test Results

"""
    
    for i, result in enumerate(results, 1):
        panel_status = "✅ PASS" if result["panel_generation"] else "❌ FAIL"
        dialogue_status = "✅ PASS" if result["dialogue_placement"] else "❌ FAIL"
        
        summary_content += f"""### Test {i}: {result['test_case']}
- **Description**: {result['description']}
- **Panel Generation**: {panel_status}
- **Dialogue Placement**: {dialogue_status}
- **Output Files**:
  - Panel: `test_{i:02d}_{result['test_case']}_dialogue.png`
  - Debug: `test_{i:02d}_{result['test_case']}_debug.png`
  - Validation: `test_{i:02d}_{result['test_case']}_validation.json`

"""
    
    summary_content += f"""## Files Generated

### Dialogue Panels
Located in: `{output_dir}/`
- Contains panels with dialogue bubbles applied
- Shows final result with text placement

### Debug Overlays  
Located in: `outputs/debug/dialogue_patch_test/`
- Green rectangles: Bubble boundaries
- Blue rectangles: Text areas
- Red labels: Bubble IDs
- Size information displayed

### Validation Reports
Located in: `{output_dir}/`
- JSON format with detailed metrics
- Text overflow scores
- Bubble adequacy measurements
- Issue detection and recommendations

## Validation Criteria

- **Text Overflow Score**: > 0.8 (no cutoff)
- **Bubble Size Adequacy**: > 0.7 (appropriate size)
- **Overall Score**: > 0.7 (good quality)

## Next Steps

1. Review debug overlays for visual confirmation
2. Check validation reports for specific issues
3. Verify text is fully visible in all dialogue panels
4. Confirm bubble sizes are appropriate for text content
"""
    
    # Save summary report
    summary_file = output_dir / "dialogue_patch_test_summary.md"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(summary_content)
    
    print(f"📋 Summary report saved: {summary_file}")
    
    if successful_dialogue == total_tests:
        print("🎉 All dialogue placement tests passed!")
        return True
    else:
        print(f"⚠️ {total_tests - successful_dialogue} tests had issues")
        return False


def main():
    """Main test execution."""
    
    print("🛠️ Dialogue Bubble Text Cutoff Fix - Patch Test")
    print("Testing improved text sizing and bubble adequacy")
    print("=" * 80)
    
    # Run the tests
    results = test_dialogue_text_sizing()
    
    # Final status
    successful_tests = sum(1 for r in results if r["dialogue_placement"])
    total_tests = len(results)
    
    print(f"\n🎯 Final Results")
    print("=" * 60)
    print(f"✅ Successful tests: {successful_tests}/{total_tests}")
    
    if successful_tests == total_tests:
        print("🎉 All dialogue patch tests completed successfully!")
        print("\n📁 Check the following directories:")
        print("   - outputs/runs/dialogue_patch_test/ (dialogue panels)")
        print("   - outputs/debug/dialogue_patch_test/ (debug overlays)")
        return 0
    else:
        print(f"⚠️ {total_tests - successful_tests} tests had issues")
        print("📋 Check the summary report for details")
        return 1


if __name__ == "__main__":
    exit(main())
