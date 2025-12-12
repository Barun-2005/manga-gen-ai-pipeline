import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add pipeline_v2 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))

from multi_panel_generator import MultiPanelGenerator
from pdf_compiler import MangaPDFCompiler

def main():
    """
    Phase 2 Test: Complete multi-panel manga generation with PDF compilation.
    
    Tests:
    1. Story structure generation from user prompts
    2. Multi-panel generation with character consistency
    3. Enhanced prompt engineering for better quality
    4. PDF compilation for publication-ready output
    """
    print("🚀 PHASE 2: MULTI-PANEL GENERATION & STORY STRUCTURE TEST")
    print("=" * 70)
    
    # Test scenarios with different story types and complexities
    test_scenarios = [
        {
            "name": "adventure_story_bw",
            "prompt": "A young ninja discovers a magical scroll that grants incredible powers but attracts dangerous enemies",
            "style": "bw",
            "panels": 4,
            "expected_themes": ["discovery", "power", "conflict"]
        },
        {
            "name": "slice_of_life_color",
            "prompt": "A high school student tries to confess their feelings but keeps getting interrupted by funny situations",
            "style": "color", 
            "panels": 4,
            "expected_themes": ["romance", "comedy", "school"]
        },
        {
            "name": "action_story_bw",
            "prompt": "A warrior must defeat three monsters to save their village from an ancient curse",
            "style": "bw",
            "panels": 5,
            "expected_themes": ["battle", "heroism", "sacrifice"]
        }
    ]
    
    # Initialize results tracking
    test_results = {
        "timestamp": datetime.now().isoformat(),
        "phase": "Phase 2 - Multi-Panel Generation & Story Structure",
        "scenarios": [],
        "summary": {
            "total_tests": len(test_scenarios),
            "successful_manga": 0,
            "quality_manga": 0,
            "pdf_compiled": 0,
            "character_consistency_avg": 0.0,
            "prompt_quality_assessment": "pending"
        }
    }
    
    # Initialize generators
    multi_generator = MultiPanelGenerator()
    pdf_compiler = MangaPDFCompiler()
    
    # Run tests for each scenario
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"   📝 Prompt: '{scenario['prompt']}'")
        print(f"   🎨 Style: {scenario['style']}")
        print(f"   📊 Panels: {scenario['panels']}")
        
        # Generate complete manga
        manga_result = multi_generator.generate_complete_manga(
            user_prompt=scenario['prompt'],
            style=scenario['style'],
            panels=scenario['panels']
        )
        
        # Compile PDF if manga generation was successful
        pdf_path = None
        pdf_success = False
        
        if manga_result.get("success"):
            try:
                print(f"\n   📚 Compiling PDF...")
                pdf_path = pdf_compiler.compile_manga_pdf(
                    manga_dir=manga_result["output_directory"],
                    story_data=manga_result["story_data"]
                )
                pdf_success = True
                print(f"   ✅ PDF compiled: {Path(pdf_path).name}")
            except Exception as e:
                print(f"   ❌ PDF compilation failed: {e}")
        
        # Analyze prompt quality effectiveness
        prompt_analysis = analyze_prompt_effectiveness(manga_result, scenario)
        
        # Process results
        scenario_result = {
            "scenario": scenario,
            "manga_result": manga_result,
            "pdf_path": pdf_path,
            "pdf_success": pdf_success,
            "prompt_analysis": prompt_analysis,
            "output_directory": manga_result.get("output_directory"),
            "success": manga_result.get("success", False)
        }
        
        test_results["scenarios"].append(scenario_result)
        
        # Update summary statistics
        if manga_result.get("success"):
            test_results["summary"]["successful_manga"] += 1
            
            # Check quality criteria
            metrics = manga_result.get("quality_metrics", {})
            quality_rate = metrics.get("quality_passed", 0) / scenario["panels"]
            consistency_score = metrics.get("character_consistency_score", 0.0)
            
            if quality_rate >= 0.5 and consistency_score >= 0.6:
                test_results["summary"]["quality_manga"] += 1
        
        if pdf_success:
            test_results["summary"]["pdf_compiled"] += 1
        
        # Print immediate results
        if manga_result.get("success"):
            metrics = manga_result["quality_metrics"]
            print(f"   ✅ Manga Generation: SUCCESS")
            print(f"      📊 Successful Panels: {metrics['successful_panels']}/{scenario['panels']}")
            print(f"      🔍 Quality Passed: {metrics['quality_passed']}/{scenario['panels']}")
            print(f"      💬 Dialogue Integrated: {metrics['dialogue_integrated']}/{scenario['panels']}")
            print(f"      🎭 Character Consistency: {metrics['character_consistency_score']:.2f}")
            print(f"      📚 PDF: {'✅' if pdf_success else '❌'}")
        else:
            print(f"   ❌ Manga Generation: FAILED")
            error = manga_result.get("error", "Unknown error")
            print(f"      Error: {error}")
    
    # Calculate overall metrics
    consistency_scores = []
    for scenario in test_results["scenarios"]:
        if scenario["manga_result"].get("success"):
            score = scenario["manga_result"]["quality_metrics"]["character_consistency_score"]
            consistency_scores.append(score)
    
    if consistency_scores:
        test_results["summary"]["character_consistency_avg"] = sum(consistency_scores) / len(consistency_scores)
    
    # Assess prompt quality effectiveness
    test_results["summary"]["prompt_quality_assessment"] = assess_overall_prompt_quality(test_results)
    
    # Save detailed results
    results_dir = Path("contest_package/output/phase2_results")
    results_dir.mkdir(parents=True, exist_ok=True)
    
    results_path = results_dir / "phase2_test_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(test_results, f, indent=2)
    
    # Generate summary report
    summary_path = results_dir / "PHASE2_SUMMARY.md"
    generate_phase2_summary(test_results, summary_path)
    
    # Print final summary
    print(f"\n🎯 PHASE 2 TEST RESULTS SUMMARY")
    print("=" * 50)
    summary = test_results["summary"]
    print(f"📊 Total Tests: {summary['total_tests']}")
    print(f"✅ Successful Manga: {summary['successful_manga']}/{summary['total_tests']}")
    print(f"🔍 Quality Manga: {summary['quality_manga']}/{summary['total_tests']}")
    print(f"📚 PDF Compiled: {summary['pdf_compiled']}/{summary['total_tests']}")
    print(f"🎭 Avg Character Consistency: {summary['character_consistency_avg']:.2f}")
    print(f"📝 Prompt Quality: {summary['prompt_quality_assessment']}")
    
    # Success criteria check
    success_rate = summary['quality_manga'] / summary['total_tests']
    pdf_rate = summary['pdf_compiled'] / summary['total_tests']
    
    phase2_success = (
        success_rate >= 0.67 and  # At least 2/3 quality manga
        pdf_rate >= 0.67 and     # At least 2/3 PDF compiled
        summary['character_consistency_avg'] >= 0.6  # Good consistency
    )
    
    if phase2_success:
        print(f"\n🎉 PHASE 2: SUCCESS")
        print(f"📋 Ready for Phase 3: Production Optimization")
    else:
        print(f"\n⚠️ PHASE 2: NEEDS IMPROVEMENT")
        print(f"🎯 Focus areas:")
        if success_rate < 0.67:
            print(f"   - Improve manga quality (current: {success_rate:.1%})")
        if pdf_rate < 0.67:
            print(f"   - Fix PDF compilation (current: {pdf_rate:.1%})")
        if summary['character_consistency_avg'] < 0.6:
            print(f"   - Enhance character consistency (current: {summary['character_consistency_avg']:.2f})")
    
    print(f"\n📁 Results saved to: {results_dir}")
    return phase2_success

def analyze_prompt_effectiveness(manga_result: dict, scenario: dict) -> dict:
    """Analyze how well the enhanced prompts performed."""
    
    analysis = {
        "story_generation": "success" if manga_result.get("story_data") else "failed",
        "character_consistency": manga_result.get("quality_metrics", {}).get("character_consistency_score", 0.0),
        "panel_success_rate": 0.0,
        "dialogue_integration_rate": 0.0,
        "prompt_specificity": "high" if len(scenario["prompt"]) > 50 else "medium" if len(scenario["prompt"]) > 20 else "low"
    }
    
    if manga_result.get("success"):
        metrics = manga_result["quality_metrics"]
        total_panels = scenario["panels"]
        
        analysis["panel_success_rate"] = metrics["successful_panels"] / total_panels
        analysis["dialogue_integration_rate"] = metrics["dialogue_integrated"] / total_panels
    
    return analysis

def assess_overall_prompt_quality(test_results: dict) -> str:
    """Assess overall prompt quality effectiveness."""
    
    scenarios = test_results["scenarios"]
    if not scenarios:
        return "insufficient_data"
    
    # Analyze success patterns
    high_success = sum(1 for s in scenarios if s["manga_result"].get("success") and 
                      s["prompt_analysis"]["panel_success_rate"] >= 0.75)
    
    total_scenarios = len(scenarios)
    success_rate = high_success / total_scenarios
    
    avg_consistency = test_results["summary"]["character_consistency_avg"]
    
    if success_rate >= 0.67 and avg_consistency >= 0.7:
        return "excellent - prompts generating high quality results"
    elif success_rate >= 0.5 and avg_consistency >= 0.6:
        return "good - prompts working well with minor improvements needed"
    elif success_rate >= 0.33:
        return "moderate - prompts need significant enhancement"
    else:
        return "poor - fundamental prompt engineering issues detected"

def generate_phase2_summary(results: dict, output_path: Path):
    """Generate a comprehensive Phase 2 summary report."""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Phase 2: Multi-Panel Generation & Story Structure Results\n\n")
        f.write(f"**Test Date**: {results['timestamp']}\n\n")
        
        # Executive Summary
        summary = results['summary']
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Tests**: {summary['total_tests']}\n")
        f.write(f"- **Successful Manga**: {summary['successful_manga']}/{summary['total_tests']} ({summary['successful_manga']/summary['total_tests']:.1%})\n")
        f.write(f"- **Quality Manga**: {summary['quality_manga']}/{summary['total_tests']} ({summary['quality_manga']/summary['total_tests']:.1%})\n")
        f.write(f"- **PDF Compilation**: {summary['pdf_compiled']}/{summary['total_tests']} ({summary['pdf_compiled']/summary['total_tests']:.1%})\n")
        f.write(f"- **Character Consistency**: {summary['character_consistency_avg']:.2f}/1.0\n")
        f.write(f"- **Prompt Quality Assessment**: {summary['prompt_quality_assessment']}\n\n")
        
        # Individual Results
        f.write("## Individual Test Results\n\n")
        for scenario in results['scenarios']:
            name = scenario['scenario']['name']
            manga_result = scenario['manga_result']
            
            f.write(f"### {name}\n")
            f.write(f"- **Prompt**: {scenario['scenario']['prompt']}\n")
            f.write(f"- **Style**: {scenario['scenario']['style']}\n")
            f.write(f"- **Panels**: {scenario['scenario']['panels']}\n")
            f.write(f"- **Success**: {'✅' if manga_result.get('success') else '❌'}\n")
            
            if manga_result.get('success'):
                metrics = manga_result['quality_metrics']
                f.write(f"- **Successful Panels**: {metrics['successful_panels']}/{scenario['scenario']['panels']}\n")
                f.write(f"- **Quality Passed**: {metrics['quality_passed']}/{scenario['scenario']['panels']}\n")
                f.write(f"- **Dialogue Integrated**: {metrics['dialogue_integrated']}/{scenario['scenario']['panels']}\n")
                f.write(f"- **Character Consistency**: {metrics['character_consistency_score']:.2f}\n")
                f.write(f"- **PDF Compiled**: {'✅' if scenario['pdf_success'] else '❌'}\n")
                f.write(f"- **Output Directory**: {scenario['output_directory']}\n")
            
            f.write("\n")
        
        # Success Criteria
        success_rate = summary['quality_manga'] / summary['total_tests']
        pdf_rate = summary['pdf_compiled'] / summary['total_tests']
        
        f.write("## Success Criteria Analysis\n\n")
        f.write("### Targets:\n")
        f.write("- Quality Manga: ≥67%\n")
        f.write("- PDF Compilation: ≥67%\n")
        f.write("- Character Consistency: ≥0.6\n\n")
        
        f.write("### Achieved:\n")
        f.write(f"- Quality Manga: {success_rate:.1%}\n")
        f.write(f"- PDF Compilation: {pdf_rate:.1%}\n")
        f.write(f"- Character Consistency: {summary['character_consistency_avg']:.2f}\n\n")
        
        phase2_success = (success_rate >= 0.67 and pdf_rate >= 0.67 and summary['character_consistency_avg'] >= 0.6)
        f.write(f"**Overall Status**: {'✅ PASSED' if phase2_success else '❌ NEEDS IMPROVEMENT'}\n\n")
        
        # Next Steps
        f.write("## Next Steps\n\n")
        if phase2_success:
            f.write("✅ Phase 2 completed successfully. Ready for Phase 3: Production Optimization.\n\n")
            f.write("**Phase 3 Focus Areas:**\n")
            f.write("- Style-specific model optimization\n")
            f.write("- Quality threshold refinement\n")
            f.write("- Character reference system\n")
            f.write("- Production workflow optimization\n")
        else:
            f.write("❌ Phase 2 needs improvement before proceeding.\n\n")
            f.write("**Improvement Areas:**\n")
            if success_rate < 0.67:
                f.write("- Enhance prompt engineering for better image quality\n")
            if pdf_rate < 0.67:
                f.write("- Fix PDF compilation issues\n")
            if summary['character_consistency_avg'] < 0.6:
                f.write("- Improve character consistency across panels\n")

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
