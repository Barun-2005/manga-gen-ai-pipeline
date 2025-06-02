#!/usr/bin/env python3
"""
Phase 13 Real Validation Framework
NO SIMULATION - Real panel generation and analysis only.

This script provides the framework for real Phase 13 validation once
actual panel generation is available.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.local_flow_checker import LocalFlowChecker
from core.coherence_analyzer import CoherenceAnalyzer

class Phase13RealValidator:
    """Real validation framework for Phase 13 - no simulation allowed."""
    
    def __init__(self):
        """Initialize the real validator."""
        self.validation_dir = Path("outputs/reports")
        self.validation_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize analyzers
        self.local_checker = LocalFlowChecker()
        self.coherence_analyzer = CoherenceAnalyzer(use_local_flow_checker=True)
        
        print("Phase 13 Real Validator initialized")
        print("NO SIMULATION - Real panels required")
    
    def load_real_prompts(self):
        """Load the extracted real prompts."""
        
        enhanced_file = self.validation_dir / "enhanced_prompts.json"
        base_file = self.validation_dir / "base_prompts.json"
        
        if not enhanced_file.exists() or not base_file.exists():
            print("❌ Real prompts not found! Run extract_real_prompts.py first.")
            return None, None
        
        with open(enhanced_file, 'r', encoding='utf-8') as f:
            enhanced_prompts = json.load(f)
        
        with open(base_file, 'r', encoding='utf-8') as f:
            base_prompts = json.load(f)
        
        print(f"Loaded {len(enhanced_prompts)} enhanced prompts")
        print(f"Loaded {len(base_prompts)} base prompts")
        
        return enhanced_prompts, base_prompts
    
    def check_panel_availability(self):
        """Check if real generated panels are available."""
        
        # Check for base panels (generated with base prompts)
        base_panel_dirs = [
            "outputs/panels/base",
            "outputs/base_panels",
            "outputs/original_panels",
            "outputs/standard_panels"
        ]

        # Check for enhanced panels (generated with enhanced prompts)
        enhanced_panel_dirs = [
            "outputs/panels/enhanced",
            "outputs/enhanced_panels",
            "outputs/layout_enhanced_panels",
            "outputs/improved_panels"
        ]
        
        base_panels = []
        enhanced_panels = []
        
        # Find base panels
        for panel_dir in base_panel_dirs:
            panel_path = Path(panel_dir)
            if panel_path.exists():
                panels = sorted([str(p) for p in panel_path.glob("*.png")])
                if len(panels) >= 6:
                    base_panels = panels[:6]
                    print(f"Found {len(base_panels)} base panels in {panel_dir}")
                    break

        # Find enhanced panels
        for panel_dir in enhanced_panel_dirs:
            panel_path = Path(panel_dir)
            if panel_path.exists():
                panels = sorted([str(p) for p in panel_path.glob("*.png")])
                if len(panels) >= 6:
                    enhanced_panels = panels[:6]
                    print(f"Found {len(enhanced_panels)} enhanced panels in {panel_dir}")
                    break
        
        return base_panels, enhanced_panels
    
    def analyze_real_panels(self, panel_paths, set_name):
        """Analyze real panels using local flow checker."""
        
        print(f"Analyzing {set_name} panel set ({len(panel_paths)} panels)...")

        if len(panel_paths) < 6:
            print(f"Insufficient panels: need 6, found {len(panel_paths)}")
            return None
        
        # Create scene data for the panels
        scene_data = []
        for i, panel_path in enumerate(panel_paths):
            scene = {
                "description": f"{set_name} manga panel {i+1}",
                "dialogue": "",
                "emotion": "neutral",
                "panel_index": i,
                "panel_path": panel_path
            }
            scene_data.append(scene)
        
        # Run real coherence analysis
        try:
            analysis_result = self.coherence_analyzer.analyze_sequence_coherence(panel_paths, scene_data)
            
            # Add metadata
            analysis_result.update({
                "set_name": set_name,
                "panel_count": len(panel_paths),
                "analysis_timestamp": datetime.now().isoformat(),
                "validation_type": "real_panels",
                "local_flow_checker_used": True
            })
            
            # Extract key metrics
            coherence_score = analysis_result.get("coherence_score", 0.0)
            overall_assessment = analysis_result.get("overall_assessment", "unknown")
            visual_consistency = analysis_result.get("visual_consistency", {})
            issues_detected = analysis_result.get("issues_detected", [])
            
            print(f"   Coherence score: {coherence_score:.3f}")
            print(f"   Assessment: {overall_assessment}")
            print(f"   Issues detected: {len(issues_detected)}")
            print(f"   Lighting consistent: {visual_consistency.get('lighting_consistency', False)}")
            
            return analysis_result
            
        except Exception as e:
            print(f"   Analysis failed: {e}")
            return None

    def compare_real_results(self, base_result, enhanced_result, base_prompts, enhanced_prompts):
        """Compare real analysis results."""

        print("Comparing real analysis results...")
        
        # Extract scores
        base_score = base_result.get("coherence_score", 0.0)
        enhanced_score = enhanced_result.get("coherence_score", 0.0)
        
        # Calculate improvement
        score_delta = enhanced_score - base_score
        percent_improvement = (score_delta / base_score * 100) if base_score > 0 else 0
        
        # Extract visual consistency
        base_visual = base_result.get("visual_consistency", {})
        enhanced_visual = enhanced_result.get("visual_consistency", {})
        
        # Count issues
        base_issues = len(base_result.get("issues_detected", []))
        enhanced_issues = len(enhanced_result.get("issues_detected", []))
        issues_resolved = max(0, base_issues - enhanced_issues)
        
        # Check lighting improvement
        lighting_improved = (
            not base_visual.get("lighting_consistency", True) and
            enhanced_visual.get("lighting_consistency", False)
        )
        
        comparison = {
            "validation_type": "real_panels",
            "comparison_timestamp": datetime.now().isoformat(),
            "scores": {
                "base": base_score,
                "enhanced": enhanced_score,
                "delta": score_delta,
                "percent_improvement": percent_improvement
            },
            "visual_consistency": {
                "base": base_visual,
                "enhanced": enhanced_visual,
                "lighting_improved": lighting_improved
            },
            "issues": {
                "base_count": base_issues,
                "enhanced_count": enhanced_issues,
                "resolved_count": issues_resolved,
                "resolution_rate": (issues_resolved / base_issues * 100) if base_issues > 0 else 0
            },
            "prompts_used": {
                "base_prompts": [p["base_prompt"] for p in base_prompts[:3]],  # First 3 for reference
                "enhanced_prompts": [p["enhanced_prompt"] for p in enhanced_prompts[:3]]
            },
            "success_criteria": {
                "coherence_improved": score_delta > 0,
                "exceeds_820_threshold": enhanced_score > 0.820,
                "lighting_consistency_fixed": lighting_improved,
                "local_flow_coverage": True,  # Always true for this validator
                "issues_reduced": issues_resolved > 0
            }
        }
        
        print(f"   Score change: {base_score:.3f} -> {enhanced_score:.3f} (Delta{score_delta:+.3f})")
        print(f"   Improvement: {percent_improvement:+.1f}%")
        print(f"   Issues resolved: {issues_resolved}/{base_issues}")
        print(f"   Lighting improved: {lighting_improved}")
        
        return comparison
    
    def save_real_results(self, base_result, enhanced_result, comparison):
        """Save real validation results."""
        
        print("Saving real validation results...")

        # Save individual results
        base_file = self.validation_dir / "real_base_analysis.json"
        enhanced_file = self.validation_dir / "real_enhanced_analysis.json"
        comparison_file = self.validation_dir / "real_comparison_results.json"

        with open(base_file, 'w', encoding='utf-8') as f:
            json.dump(base_result, f, indent=2)

        with open(enhanced_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_result, f, indent=2)

        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2)

        print(f"   Base analysis: {base_file}")
        print(f"   Enhanced analysis: {enhanced_file}")
        print(f"   Comparison: {comparison_file}")
        
        return {
            "base_analysis": str(base_file),
            "enhanced_analysis": str(enhanced_file),
            "comparison_results": str(comparison_file)
        }
    
    def run_real_validation(self):
        """Run complete real validation."""
        
        print("Phase 13: Real Validation (NO SIMULATION)")
        print("=" * 70)
        
        # Load real prompts
        enhanced_prompts, base_prompts = self.load_real_prompts()
        if not enhanced_prompts or not base_prompts:
            return {"error": "Real prompts not available", "success": False}
        
        # Check for real panels
        base_panels, enhanced_panels = self.check_panel_availability()
        
        if not base_panels:
            print("❌ No base panels found!")
            print("   📝 Required: Generate 6 panels using base prompts")
            print("   📁 Save to: outputs/base_panels/")
            return {"error": "Base panels not generated", "success": False}
        
        if not enhanced_panels:
            print("❌ No enhanced panels found!")
            print("   📝 Required: Generate 6 panels using enhanced prompts")
            print("   📁 Save to: outputs/enhanced_panels/")
            return {"error": "Enhanced panels not generated", "success": False}
        
        # Analyze both sets
        base_result = self.analyze_real_panels(base_panels, "base")
        enhanced_result = self.analyze_real_panels(enhanced_panels, "enhanced")
        
        if not base_result or not enhanced_result:
            return {"error": "Analysis failed", "success": False}
        
        # Compare results
        comparison = self.compare_real_results(base_result, enhanced_result, base_prompts, enhanced_prompts)
        
        # Save results
        file_paths = self.save_real_results(base_result, enhanced_result, comparison)
        
        # Final assessment
        success_criteria = comparison.get("success_criteria", {})
        enhanced_score = comparison.get("scores", {}).get("enhanced", 0.0)
        
        print(f"\nPhase 13 Real Validation Results:")
        print(f"   Coherence improved: {success_criteria.get('coherence_improved', False)}")
        print(f"   Exceeds 0.820 threshold: {success_criteria.get('exceeds_820_threshold', False)}")
        print(f"   Lighting fixed: {success_criteria.get('lighting_consistency_fixed', False)}")
        print(f"   Local flow coverage: {success_criteria.get('local_flow_coverage', False)}")

        # Determine success
        phase_success = (
            success_criteria.get('coherence_improved', False) and
            success_criteria.get('exceeds_820_threshold', False) and
            success_criteria.get('local_flow_coverage', False)
        )

        if phase_success:
            print(f"\nPHASE 13 SUCCESS: Enhanced prompts show real improvement!")
            print(f"   Enhanced score: {enhanced_score:.3f}")
        else:
            print(f"\nPHASE 13 FAILED: Enhanced prompts did not improve coherence")
            print(f"   Enhanced score: {enhanced_score:.3f} (required > 0.820)")
        
        return {
            "success": phase_success,
            "enhanced_score": enhanced_score,
            "comparison": comparison,
            "file_paths": file_paths
        }

def main():
    """Main validation function."""
    
    print("Phase 13: Real Validation Framework")
    print("NO SIMULATION ALLOWED - Real panels required")
    print("=" * 70)
    
    validator = Phase13RealValidator()
    results = validator.run_real_validation()
    
    if results.get("success", False):
        print("\n✅ Phase 13 validation passed with real panels!")
        return 0
    else:
        error = results.get("error", "Validation failed")
        print(f"\n❌ Phase 13 validation failed: {error}")
        return 1

if __name__ == "__main__":
    exit(main())
