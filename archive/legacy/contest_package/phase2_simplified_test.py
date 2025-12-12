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
    Phase 2 Simplified Test: Focus on single complete manga generation.
    
    Tests core Phase 2 functionality:
    1. Story structure generation
    2. Multi-panel generation (3 panels)
    3. Character consistency
    4. PDF compilation
    """
    print("🚀 PHASE 2: SIMPLIFIED MULTI-PANEL MANGA TEST")
    print("=" * 60)
    
    # Single focused test scenario
    test_scenario = {
        "name": "simple_adventure",
        "prompt": "A brave warrior finds a magical sword and must face a dragon",
        "style": "bw",
        "panels": 3
    }
    
    print(f"📝 Test Scenario: {test_scenario['name']}")
    print(f"   Prompt: '{test_scenario['prompt']}'")
    print(f"   Style: {test_scenario['style']}")
    print(f"   Panels: {test_scenario['panels']}")
    
    # Initialize generators
    print(f"\n🔧 Initializing generators...")
    multi_generator = MultiPanelGenerator()
    pdf_compiler = MangaPDFCompiler()
    
    # Generate complete manga
    print(f"\n🎨 Generating complete manga...")
    manga_result = multi_generator.generate_complete_manga(
        user_prompt=test_scenario['prompt'],
        style=test_scenario['style'],
        panels=test_scenario['panels']
    )
    
    # Analyze results
    print(f"\n📊 ANALYZING RESULTS...")
    
    if manga_result.get("success"):
        metrics = manga_result["quality_metrics"]
        
        print(f"✅ Manga Generation: SUCCESS")
        print(f"   📊 Successful Panels: {metrics['successful_panels']}/{test_scenario['panels']}")
        print(f"   🔍 Quality Passed: {metrics['quality_passed']}/{test_scenario['panels']}")
        print(f"   💬 Dialogue Integrated: {metrics['dialogue_integrated']}/{test_scenario['panels']}")
        print(f"   🎭 Character Consistency: {metrics['character_consistency_score']:.2f}")
        
        # Test PDF compilation
        print(f"\n📚 Compiling PDF...")
        try:
            pdf_path = pdf_compiler.compile_manga_pdf(
                manga_dir=manga_result["output_directory"],
                story_data=manga_result["story_data"]
            )
            print(f"✅ PDF compiled successfully: {Path(pdf_path).name}")
            pdf_success = True
        except Exception as e:
            print(f"❌ PDF compilation failed: {e}")
            pdf_success = False
        
        # Check generated files
        output_dir = Path(manga_result["output_directory"])
        panel_files = list(output_dir.glob("panel_*.png"))
        
        print(f"\n📁 Generated Files:")
        print(f"   📂 Output Directory: {output_dir}")
        print(f"   🖼️  Panel Images: {len(panel_files)}")
        
        for panel_file in sorted(panel_files):
            if panel_file.exists():
                size_mb = panel_file.stat().st_size / 1024 / 1024
                print(f"      - {panel_file.name}: {size_mb:.1f}MB")
        
        if output_dir.joinpath("story_structure.json").exists():
            print(f"   📖 Story Structure: ✅")
        
        if pdf_success and Path(pdf_path).exists():
            pdf_size_mb = Path(pdf_path).stat().st_size / 1024 / 1024
            print(f"   📚 PDF File: {Path(pdf_path).name} ({pdf_size_mb:.1f}MB)")
        
        # Assess prompt quality
        print(f"\n📝 PROMPT QUALITY ASSESSMENT:")
        
        story_data = manga_result.get("story_data", {})
        if story_data:
            character = story_data.get("character", {})
            panels = story_data.get("panels", [])
            
            print(f"   📖 Story Generated: ✅")
            print(f"   🎭 Character: {character.get('name', 'Unknown')}")
            print(f"   📝 Character Description: {len(character.get('appearance', ''))} chars")
            print(f"   📊 Panel Details: {len(panels)} panels with detailed prompts")
            
            # Check prompt specificity
            if panels:
                avg_prompt_length = sum(len(p.get('visual_prompt', '')) for p in panels) / len(panels)
                print(f"   📏 Avg Prompt Length: {avg_prompt_length:.0f} characters")
                
                if avg_prompt_length > 100:
                    print(f"   ✅ Prompt Quality: High (detailed descriptions)")
                elif avg_prompt_length > 50:
                    print(f"   ⚠️  Prompt Quality: Medium (moderate detail)")
                else:
                    print(f"   ❌ Prompt Quality: Low (insufficient detail)")
        
        # Overall assessment
        success_rate = metrics['successful_panels'] / test_scenario['panels']
        quality_rate = metrics['quality_passed'] / test_scenario['panels']
        consistency_score = metrics['character_consistency_score']
        
        print(f"\n🎯 PHASE 2 ASSESSMENT:")
        print(f"   📊 Panel Success Rate: {success_rate:.1%}")
        print(f"   🔍 Quality Pass Rate: {quality_rate:.1%}")
        print(f"   🎭 Character Consistency: {consistency_score:.2f}")
        print(f"   📚 PDF Compilation: {'✅' if pdf_success else '❌'}")
        
        # Success criteria
        phase2_success = (
            success_rate >= 0.67 and      # At least 2/3 panels successful
            quality_rate >= 0.33 and      # At least 1/3 quality passed (relaxed)
            consistency_score >= 0.5 and  # Reasonable consistency
            pdf_success                    # PDF compilation works
        )
        
        if phase2_success:
            print(f"\n🎉 PHASE 2: SUCCESS")
            print(f"   ✅ Multi-panel generation working")
            print(f"   ✅ Story structure system functional")
            print(f"   ✅ Character consistency maintained")
            print(f"   ✅ PDF compilation operational")
            print(f"   📋 Ready for Phase 3: Production Optimization")
        else:
            print(f"\n⚠️ PHASE 2: PARTIAL SUCCESS")
            print(f"   🔧 Areas needing improvement:")
            if success_rate < 0.67:
                print(f"      - Panel generation reliability")
            if quality_rate < 0.33:
                print(f"      - Image quality validation")
            if consistency_score < 0.5:
                print(f"      - Character consistency")
            if not pdf_success:
                print(f"      - PDF compilation")
        
        # Save results summary
        results_dir = Path("contest_package/output/phase2_simplified")
        results_dir.mkdir(parents=True, exist_ok=True)
        
        summary = {
            "timestamp": datetime.now().isoformat(),
            "test_scenario": test_scenario,
            "manga_result": manga_result,
            "pdf_success": pdf_success,
            "pdf_path": pdf_path if pdf_success else None,
            "assessment": {
                "success_rate": success_rate,
                "quality_rate": quality_rate,
                "consistency_score": consistency_score,
                "pdf_compiled": pdf_success,
                "phase2_success": phase2_success
            }
        }
        
        with open(results_dir / "phase2_simplified_results.json", 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n📁 Results saved to: {results_dir}")
        
        return phase2_success
        
    else:
        print(f"❌ Manga Generation: FAILED")
        error = manga_result.get("error", "Unknown error")
        print(f"   Error: {error}")
        
        print(f"\n🔧 DIAGNOSIS:")
        print(f"   - Check ComfyUI server status")
        print(f"   - Verify model availability")
        print(f"   - Review prompt generation")
        
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ PHASE 2 SIMPLIFIED TEST: PASSED' if success else '❌ PHASE 2 SIMPLIFIED TEST: NEEDS WORK'}")
    sys.exit(0 if success else 1)
