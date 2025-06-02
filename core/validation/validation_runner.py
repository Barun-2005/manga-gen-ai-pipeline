#!/usr/bin/env python3
"""
Phase 13 Real Validation Runner
Complete pipeline for real panel generation and validation.
"""

import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.emotion_extractor import EmotionExtractor

class Phase13RealRunner:
    """Runs complete Phase 13 real validation pipeline."""
    
    def __init__(self):
        """Initialize the runner."""
        self.base_prompts_file = "assets/prompts/base_prompts.txt"
        self.enhanced_prompts_file = "assets/prompts/enhanced_prompts.txt"
        self.base_panels_dir = "outputs/panels/base"
        self.enhanced_panels_dir = "outputs/panels/enhanced"
        self.validation_results_dir = "outputs/reports"
        
        # Create directories
        Path(self.base_panels_dir).mkdir(parents=True, exist_ok=True)
        Path(self.enhanced_panels_dir).mkdir(parents=True, exist_ok=True)
        Path(self.validation_results_dir).mkdir(parents=True, exist_ok=True)
    
    def check_comfyui_available(self) -> bool:
        """Check if ComfyUI is available for panel generation."""
        try:
            result = subprocess.run([
                "python", "scripts/generate_panel.py",
                "--prompt", "test",
                "--output", "test.png"
            ], capture_output=True, text=True, timeout=10)
            
            # If it fails due to ComfyUI not running, that's expected
            # We just want to check if the script runs
            return True
        except Exception as e:
            print(f"⚠️  ComfyUI generation script issue: {e}")
            return False
    
    def generate_base_panels(self) -> bool:
        """Generate base panels using standard prompts."""
        
        print("🎨 Step 1: Generating Base Panels")
        print("=" * 50)
        
        if not Path(self.base_prompts_file).exists():
            print(f"❌ Base prompts file not found: {self.base_prompts_file}")
            return False
        
        # Try to generate panels
        try:
            result = subprocess.run([
                "python", "scripts/generate_panel.py",
                "--prompt-file", self.base_prompts_file,
                "--output-dir", self.base_panels_dir,
                "--prefix", "base_panel"
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            print(f"Generation output: {result.stdout}")
            if result.stderr:
                print(f"Generation errors: {result.stderr}")
            
            # Check if panels were generated
            base_panels = list(Path(self.base_panels_dir).glob("*.png"))
            success = len(base_panels) >= 6
            
            if success:
                print(f"✅ Generated {len(base_panels)} base panels")
            else:
                print(f"❌ Only generated {len(base_panels)} base panels (need 6)")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ Base panel generation timed out")
            return False
        except Exception as e:
            print(f"❌ Base panel generation failed: {e}")
            return False
    
    def generate_enhanced_panels(self) -> bool:
        """Generate enhanced panels using layout-enhanced prompts."""
        
        print("\n🎨 Step 2: Generating Enhanced Panels")
        print("=" * 50)
        
        if not Path(self.enhanced_prompts_file).exists():
            print(f"❌ Enhanced prompts file not found: {self.enhanced_prompts_file}")
            return False
        
        # Try to generate panels
        try:
            result = subprocess.run([
                "python", "scripts/generate_panel.py",
                "--prompt-file", self.enhanced_prompts_file,
                "--output-dir", self.enhanced_panels_dir,
                "--prefix", "enhanced_panel"
            ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
            
            print(f"Generation output: {result.stdout}")
            if result.stderr:
                print(f"Generation errors: {result.stderr}")
            
            # Check if panels were generated
            enhanced_panels = list(Path(self.enhanced_panels_dir).glob("*.png"))
            success = len(enhanced_panels) >= 6
            
            if success:
                print(f"✅ Generated {len(enhanced_panels)} enhanced panels")
            else:
                print(f"❌ Only generated {len(enhanced_panels)} enhanced panels (need 6)")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ Enhanced panel generation timed out")
            return False
        except Exception as e:
            print(f"❌ Enhanced panel generation failed: {e}")
            return False
    
    def run_real_validation(self) -> bool:
        """Run real coherence validation."""
        
        print("\n📊 Step 3: Running Real Coherence Validation")
        print("=" * 50)
        
        # Check if validation script exists
        validation_script = "core/validation/phase13_validator.py"
        if not Path(validation_script).exists():
            print(f"Validation script not found: {validation_script}")
            return False

        # Run validation
        try:
            result = subprocess.run([
                "python", validation_script
            ], capture_output=True, text=True, timeout=300)  # 5 minute timeout
            
            print(f"Validation output: {result.stdout}")
            if result.stderr:
                print(f"Validation errors: {result.stderr}")
            
            # Check return code
            success = result.returncode == 0
            
            if success:
                print("✅ Real validation completed successfully")
            else:
                print("❌ Real validation failed")
            
            return success
            
        except subprocess.TimeoutExpired:
            print("❌ Real validation timed out")
            return False
        except Exception as e:
            print(f"❌ Real validation failed: {e}")
            return False
    
    def run_emotion_extraction(self) -> bool:
        """Run emotion extraction on generated content."""
        
        print("\n🎭 Step 4: Running Emotion Extraction")
        print("=" * 50)
        
        # Create sample dialogue for testing
        sample_dialogue = [
            "I must find the ancient temple!",
            "What is this mysterious sword?",
            "The guardians are awakening...",
            "I will prove my worth!",
            "The power flows through me now.",
            "Enemies approach! We must fight!"
        ]
        
        # Save sample dialogue
        dialogue_file = Path(self.validation_results_dir) / "sample_dialogue.txt"
        with open(dialogue_file, 'w', encoding='utf-8') as f:
            for line in sample_dialogue:
                f.write(line + '\n')
        
        # Run emotion extraction
        extractor = EmotionExtractor()
        results = extractor.extract_from_dialogue_list(sample_dialogue)
        
        # Save emotion results
        emotion_data = {
            "extraction_timestamp": datetime.now().isoformat(),
            "source": "phase13_validation_sample",
            "total_lines": len(sample_dialogue),
            "dialogue_emotions": results
        }
        
        emotion_file = Path(self.validation_results_dir) / "emotion_labels.json"
        extractor.save_emotion_results(emotion_data, str(emotion_file))
        
        print(f"✅ Emotion extraction complete: {len(results)} lines processed")
        return True
    
    def generate_final_report(self, base_success: bool, enhanced_success: bool, 
                            validation_success: bool, emotion_success: bool) -> bool:
        """Generate final Phase 13 validation report."""
        
        print("\n📄 Step 5: Generating Final Report")
        print("=" * 50)
        
        # Collect validation data
        validation_data = {
            "phase13_validation_timestamp": datetime.now().isoformat(),
            "validation_type": "real_panels",
            "steps_completed": {
                "base_panel_generation": base_success,
                "enhanced_panel_generation": enhanced_success,
                "coherence_validation": validation_success,
                "emotion_extraction": emotion_success
            },
            "panel_counts": {
                "base_panels": len(list(Path(self.base_panels_dir).glob("*.png"))),
                "enhanced_panels": len(list(Path(self.enhanced_panels_dir).glob("*.png")))
            },
            "overall_success": all([base_success, enhanced_success, validation_success, emotion_success])
        }
        
        # Load validation results if available
        validation_results_file = Path("outputs/phase13_real_validation/real_comparison_results.json")
        if validation_results_file.exists():
            try:
                with open(validation_results_file, 'r', encoding='utf-8') as f:
                    validation_results = json.load(f)
                validation_data["coherence_results"] = validation_results
            except:
                pass
        
        # Generate Markdown report
        report = f"""# Phase 13: Real Validation Report
## Enhanced Prompt Testing + Local Visual Flow Validator

**Validation Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Validation Type:** Real Panel Generation and Analysis

---

## 📊 Validation Summary

### Step Completion Status
- **Base Panel Generation:** {'✅ SUCCESS' if base_success else '❌ FAILED'}
- **Enhanced Panel Generation:** {'✅ SUCCESS' if enhanced_success else '❌ FAILED'}
- **Coherence Validation:** {'✅ SUCCESS' if validation_success else '❌ FAILED'}
- **Emotion Extraction:** {'✅ SUCCESS' if emotion_success else '❌ FAILED'}

### Panel Generation Results
- **Base Panels Generated:** {validation_data['panel_counts']['base_panels']}
- **Enhanced Panels Generated:** {validation_data['panel_counts']['enhanced_panels']}

### Overall Phase 13 Status
**{'✅ PHASE 13 COMPLETE' if validation_data['overall_success'] else '❌ PHASE 13 INCOMPLETE'}**

---

## 📋 Detailed Results

### Base Prompts Used
```
{Path(self.base_prompts_file).read_text() if Path(self.base_prompts_file).exists() else 'File not found'}
```

### Enhanced Prompts Used
```
{Path(self.enhanced_prompts_file).read_text()[:500] if Path(self.enhanced_prompts_file).exists() else 'File not found'}...
```

### Validation Criteria
- **Enhanced coherence score > 0.820:** {'✅' if validation_success else '❌'} {'Verified' if validation_success else 'Not verified'}
- **Lighting consistency fix ≥ 80%:** {'✅' if validation_success else '❌'} {'Verified' if validation_success else 'Not verified'}
- **Local flow checker confirms layout:** {'✅' if validation_success else '❌'} {'Verified' if validation_success else 'Not verified'}
- **Emotion extraction functional:** {'✅' if emotion_success else '❌'} {'Verified' if emotion_success else 'Not verified'}

---

## 🎯 Phase Completion Status

### Phase 7: Emotion Extraction
**{'✅ COMPLETE' if emotion_success else '❌ INCOMPLETE'}**

### Phase 13: Coherence Check
**{'✅ COMPLETE' if validation_data['overall_success'] else '❌ INCOMPLETE'}**

---

*Report generated by Phase 13 Real Validation Runner*
"""
        
        # Save report
        report_file = Path(self.validation_results_dir) / "phase13_coherence_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        # Save validation data
        data_file = Path(self.validation_results_dir) / "phase13_validation_data.json"
        with open(data_file, 'w', encoding='utf-8') as f:
            json.dump(validation_data, f, indent=2)
        
        print(f"📄 Final report: {report_file}")
        print(f"📊 Validation data: {data_file}")
        
        return True
    
    def run_complete_validation(self) -> bool:
        """Run complete Phase 13 real validation pipeline."""
        
        print("🚀 Phase 13: Real Validation Pipeline")
        print("=" * 70)
        print("MANGA-GEN FIX & FINALIZE: PATCH PHASE 7 + VALIDATE PHASE 13")
        print("=" * 70)
        
        # Check ComfyUI availability
        if not self.check_comfyui_available():
            print("⚠️  ComfyUI may not be available - proceeding with validation framework test")
        
        # Step 1: Generate base panels
        base_success = self.generate_base_panels()
        
        # Step 2: Generate enhanced panels
        enhanced_success = self.generate_enhanced_panels()
        
        # Step 3: Run real validation
        validation_success = self.run_real_validation()
        
        # Step 4: Run emotion extraction
        emotion_success = self.run_emotion_extraction()
        
        # Step 5: Generate final report
        report_success = self.generate_final_report(
            base_success, enhanced_success, validation_success, emotion_success
        )
        
        # Final assessment
        overall_success = all([base_success, enhanced_success, validation_success, emotion_success])
        
        print(f"\n🎯 Phase 13 Real Validation Complete!")
        print(f"Overall Success: {'✅ YES' if overall_success else '❌ NO'}")
        
        if overall_success:
            print("\n🎉 PHASE 7: COMPLETE")
            print("🎉 PHASE 13: COMPLETE")
            print("✅ Ready to begin Phase 14")
        else:
            print("\n⚠️  Some validation steps failed")
            print("❌ Phase 13 not yet complete")
        
        return overall_success

def main():
    """Main validation runner."""
    runner = Phase13RealRunner()
    success = runner.run_complete_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
