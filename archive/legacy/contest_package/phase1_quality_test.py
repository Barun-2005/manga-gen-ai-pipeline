import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add pipeline_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))

from enhanced_panel_generator import EnhancedPanelGenerator

def main():
    """
    Phase 1 Quality Test: Enhanced panel generation with validation and dialogue.
    
    Tests:
    1. Quality validation with emotion/pose detection
    2. Visual dialogue bubble placement
    3. Publication-ready output verification
    """
    print("🚀 PHASE 1: QUALITY VALIDATION & DIALOGUE INTEGRATION TEST")
    print("=" * 70)
    
    # Create output directory
    output_dir = Path("contest_package/output/phase1_quality")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test scenarios with specific requirements
    test_scenarios = [
        {
            "name": "happy_standing_bw",
            "style": "bw",
            "emotion": "happy",
            "pose": "standing",
            "dialogue": ["This is amazing!", "I can't believe it worked!"],
            "scene_description": "character in outdoor setting with clear background"
        },
        {
            "name": "angry_arms_crossed_color",
            "style": "color",
            "emotion": "angry",
            "pose": "arms_crossed",
            "dialogue": ["I won't forgive this!", "How dare you!"],
            "scene_description": "character in confrontational scene with dramatic lighting"
        },
        {
            "name": "surprised_jumping_bw",
            "style": "bw",
            "emotion": "surprised",
            "pose": "jumping",
            "dialogue": ["What?! No way!", "This is impossible!"],
            "scene_description": "character in dynamic action scene with motion effects"
        }
    ]
    
    # Initialize results tracking
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 1 - Quality Validation & Dialogue Integration",
        "scenarios": [],
        "summary": {
            "total_tests": len(test_scenarios),
            "successful_generations": 0,
            "quality_validations_passed": 0,
            "dialogue_integrations_successful": 0,
            "publication_ready": 0
        }
    }
    
    # Run tests for each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"   Style: {scenario['style']}")
        print(f"   Emotion: {scenario['emotion']}")
        print(f"   Pose: {scenario['pose']}")
        print(f"   Dialogue: {len(scenario['dialogue'])} lines")
        
        # Initialize generator for this style
        generator = EnhancedPanelGenerator(scenario['style'])
        
        # Generate panel
        output_path = output_dir / f"{scenario['name']}.png"
        
        result = generator.generate_quality_panel(
            output_image=str(output_path),
            style=scenario['style'],
            emotion=scenario['emotion'],
            pose=scenario['pose'],
            dialogue_lines=scenario['dialogue'],
            scene_description=scenario['scene_description']
        )
        
        # Process results
        scenario_result = {
            "scenario": scenario['name'],
            "config": scenario,
            "result": result,
            "output_path": str(output_path),
            "file_exists": os.path.exists(output_path),
            "file_size": os.path.getsize(output_path) if os.path.exists(output_path) else 0
        }
        
        # Update summary statistics
        if result.get("success"):
            test_results["summary"]["successful_generations"] += 1
            
            # Check quality validation
            validation = result.get("validation", {})
            if validation.get("quality_passed"):
                test_results["summary"]["quality_validations_passed"] += 1
            
            # Check dialogue integration
            dialogue = result.get("dialogue", {})
            if dialogue.get("dialogue_added") and dialogue.get("quality_passed"):
                test_results["summary"]["dialogue_integrations_successful"] += 1
            
            # Check publication readiness (all criteria met)
            if (validation.get("quality_passed") and 
                dialogue.get("dialogue_added") and 
                dialogue.get("quality_passed")):
                test_results["summary"]["publication_ready"] += 1
        
        test_results["scenarios"].append(scenario_result)
        
        # Print immediate results
        if result.get("success"):
            print(f"   ✅ Generation: SUCCESS ({result.get('attempts', 1)} attempts)")
            
            validation = result.get("validation", {})
            emotion_conf = validation.get("emotion_result", {}).get("confidence", 0)
            pose_conf = validation.get("pose_result", {}).get("confidence", 0)
            print(f"   🔍 Validation: Emotion {emotion_conf:.2f}, Pose {pose_conf:.2f}")
            
            dialogue = result.get("dialogue", {})
            if dialogue.get("dialogue_added"):
                bubble_quality = dialogue.get("bubble_quality", {})
                face_overlap = bubble_quality.get("face_overlap_score", 1.0)
                print(f"   💬 Dialogue: {dialogue.get('bubble_count', 0)} bubbles, {face_overlap:.2f} face overlap")
            
            # File verification
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                print(f"   📁 Output: {output_path.name} ({file_size:,} bytes)")
            
        else:
            print(f"   ❌ Generation: FAILED - {result.get('error', 'Unknown error')}")
    
    # Save detailed results
    results_path = output_dir / "phase1_test_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    
    # Generate summary report
    summary_path = output_dir / "PHASE1_SUMMARY.md"
    generate_summary_report(test_results, summary_path)
    
    # Print final summary
    print(f"\n🎯 PHASE 1 TEST RESULTS SUMMARY")
    print("=" * 50)
    summary = test_results["summary"]
    print(f"📊 Total Tests: {summary['total_tests']}")
    print(f"✅ Successful Generations: {summary['successful_generations']}/{summary['total_tests']}")
    print(f"🔍 Quality Validations Passed: {summary['quality_validations_passed']}/{summary['total_tests']}")
    print(f"💬 Dialogue Integrations Successful: {summary['dialogue_integrations_successful']}/{summary['total_tests']}")
    print(f"📚 Publication Ready: {summary['publication_ready']}/{summary['total_tests']}")
    
    # Success criteria check
    success_rate = summary['publication_ready'] / summary['total_tests']
    if success_rate >= 0.67:  # At least 2/3 must be publication ready
        print(f"\n🎉 PHASE 1: SUCCESS ({success_rate:.1%} publication ready)")
        print(f"📁 Results saved to: {output_dir}")
        print(f"📋 Summary report: {summary_path}")
        return True
    else:
        print(f"\n❌ PHASE 1: NEEDS IMPROVEMENT ({success_rate:.1%} publication ready)")
        print(f"🎯 Target: ≥67% publication ready")
        return False

def generate_summary_report(results: dict, output_path: Path):
    """Generate a markdown summary report."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Phase 1: Quality Validation & Dialogue Integration Results\n\n")
        f.write(f"**Test Date**: {results['timestamp']}\n\n")
        
        # Summary statistics
        summary = results['summary']
        f.write("## Summary Statistics\n\n")
        f.write("| Metric | Count | Percentage |\n")
        f.write("|--------|-------|------------|\n")
        f.write(f"| Total Tests | {summary['total_tests']} | 100% |\n")
        f.write(f"| Successful Generations | {summary['successful_generations']} | {summary['successful_generations']/summary['total_tests']:.1%} |\n")
        f.write(f"| Quality Validations Passed | {summary['quality_validations_passed']} | {summary['quality_validations_passed']/summary['total_tests']:.1%} |\n")
        f.write(f"| Dialogue Integrations Successful | {summary['dialogue_integrations_successful']} | {summary['dialogue_integrations_successful']/summary['total_tests']:.1%} |\n")
        f.write(f"| Publication Ready | {summary['publication_ready']} | {summary['publication_ready']/summary['total_tests']:.1%} |\n\n")
        
        # Individual test results
        f.write("## Individual Test Results\n\n")
        for scenario in results['scenarios']:
            name = scenario['scenario']
            config = scenario['config']
            result = scenario['result']
            
            f.write(f"### {name}\n")
            f.write(f"- **Style**: {config['style']}\n")
            f.write(f"- **Emotion**: {config['emotion']}\n")
            f.write(f"- **Pose**: {config['pose']}\n")
            f.write(f"- **Dialogue Lines**: {len(config['dialogue'])}\n")
            f.write(f"- **Success**: {'✅' if result.get('success') else '❌'}\n")
            
            if result.get('success'):
                validation = result.get('validation', {})
                dialogue = result.get('dialogue', {})
                
                f.write(f"- **Attempts**: {result.get('attempts', 1)}\n")
                f.write(f"- **Emotion Confidence**: {validation.get('emotion_result', {}).get('confidence', 0):.2f}\n")
                f.write(f"- **Pose Confidence**: {validation.get('pose_result', {}).get('confidence', 0):.2f}\n")
                f.write(f"- **Dialogue Added**: {'✅' if dialogue.get('dialogue_added') else '❌'}\n")
                f.write(f"- **Bubble Count**: {dialogue.get('bubble_count', 0)}\n")
                
                if dialogue.get('bubble_quality'):
                    face_overlap = dialogue['bubble_quality'].get('face_overlap_score', 1.0)
                    f.write(f"- **Face Overlap**: {face_overlap:.2f} ({'✅' if face_overlap <= 0.2 else '❌'})\n")
            else:
                f.write(f"- **Error**: {result.get('error', 'Unknown')}\n")
            
            f.write(f"- **Output File**: {scenario['output_path']}\n")
            f.write(f"- **File Size**: {scenario['file_size']:,} bytes\n\n")
        
        # Success criteria
        success_rate = summary['publication_ready'] / summary['total_tests']
        f.write("## Success Criteria\n\n")
        f.write("- **Target**: ≥67% publication ready\n")
        f.write(f"- **Achieved**: {success_rate:.1%}\n")
        f.write(f"- **Status**: {'✅ PASSED' if success_rate >= 0.67 else '❌ NEEDS IMPROVEMENT'}\n\n")
        
        f.write("## Next Steps\n\n")
        if success_rate >= 0.67:
            f.write("✅ Phase 1 completed successfully. Ready for Phase 2: Multi-Panel Generation.\n")
        else:
            f.write("❌ Phase 1 needs improvement. Focus on:\n")
            f.write("- Improving emotion/pose detection accuracy\n")
            f.write("- Optimizing dialogue bubble placement\n")
            f.write("- Enhancing prompt quality for better image generation\n")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
