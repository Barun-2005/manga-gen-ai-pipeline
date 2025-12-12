import os
import sys
import time
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from enhanced_panel_generator import EnhancedPanelGenerator
from core.emotion_matcher import EmotionMatcher
from core.pose_matcher import PoseMatcher

def test_fixed_generation():
    """Test manga generation with optimized parameters."""
    print("🎯 FINAL QUALITY VERIFICATION TEST")
    print("=" * 60)
    print("Testing both critical issues:")
    print("1. ComfyUI prompt processing (should not terminate)")
    print("2. Generated image quality (should achieve >0.3 confidence)")
    print()
    
    # Create output directory
    output_dir = Path("contest_package/output/final_verification")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test scenarios designed to verify quality
    test_scenarios = [
        {
            "name": "simple_character_bw",
            "style": "bw",
            "emotion": "happy",
            "pose": "standing",
            "dialogue": ["Hello!", "Nice to meet you!"],
            "description": "Simple test with basic character"
        },
        {
            "name": "detailed_character_color",
            "style": "color",
            "emotion": "surprised",
            "pose": "arms_crossed",
            "dialogue": ["What?!", "I can't believe it!"],
            "description": "Detailed test with complex character"
        }
    ]
    
    # Initialize validation systems
    emotion_matcher = EmotionMatcher()
    pose_matcher = PoseMatcher()
    
    results = {
        "comfyui_stability": True,
        "generation_success": 0,
        "quality_success": 0,
        "scenarios": []
    }
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"   Description: {scenario['description']}")
        print(f"   Style: {scenario['style']}")
        print(f"   Target: {scenario['emotion']} emotion, {scenario['pose']} pose")
        
        # Generate panel with optimized system
        try:
            generator = EnhancedPanelGenerator(scenario['style'])
            
            output_path = output_dir / f"{scenario['name']}.png"
            
            print(f"   🎨 Generating panel...")
            
            result = generator.generate_quality_panel(
                output_image=str(output_path),
                style=scenario['style'],
                emotion=scenario['emotion'],
                pose=scenario['pose'],
                dialogue_lines=scenario['dialogue'],
                scene_description=f"high quality anime character with clear face and {scenario['emotion']} expression"
            )
            
            scenario_result = {
                "scenario": scenario,
                "generation_success": False,
                "file_exists": False,
                "file_size": 0,
                "emotion_detection": {"detected": "none", "confidence": 0.0},
                "pose_detection": {"detected": "none", "confidence": 0.0},
                "quality_passed": False
            }
            
            # Check if generation succeeded
            if result.get("success"):
                print(f"   ✅ Generation completed")
                results["generation_success"] += 1
                scenario_result["generation_success"] = True
                
                # Check if file exists
                if os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    scenario_result["file_exists"] = True
                    scenario_result["file_size"] = file_size
                    
                    print(f"   📁 File created: {file_size:,} bytes ({file_size/1024/1024:.1f}MB)")
                    
                    # Test emotion detection
                    print(f"   🎭 Testing emotion detection...")
                    try:
                        detected_emotion, emotion_confidence = emotion_matcher.detect_visual_emotion(str(output_path))
                        scenario_result["emotion_detection"] = {
                            "detected": detected_emotion,
                            "confidence": emotion_confidence
                        }
                        
                        print(f"      Detected: {detected_emotion} (confidence: {emotion_confidence:.3f})")
                        
                        if emotion_confidence > 0.3:
                            print(f"      ✅ Emotion confidence > 0.3 threshold")
                        else:
                            print(f"      ❌ Emotion confidence below 0.3 threshold")
                            
                    except Exception as e:
                        print(f"      ❌ Emotion detection failed: {e}")
                    
                    # Test pose detection
                    print(f"   🤸 Testing pose detection...")
                    try:
                        detected_pose, pose_confidence = pose_matcher.detect_visual_pose(str(output_path))
                        scenario_result["pose_detection"] = {
                            "detected": detected_pose,
                            "confidence": pose_confidence
                        }
                        
                        print(f"      Detected: {detected_pose} (confidence: {pose_confidence:.3f})")
                        
                        if pose_confidence > 0.3:
                            print(f"      ✅ Pose confidence > 0.3 threshold")
                        else:
                            print(f"      ❌ Pose confidence below 0.3 threshold")
                            
                    except Exception as e:
                        print(f"      ❌ Pose detection failed: {e}")
                    
                    # Overall quality assessment
                    emotion_ok = scenario_result["emotion_detection"]["confidence"] > 0.3
                    pose_ok = scenario_result["pose_detection"]["confidence"] > 0.3
                    
                    if emotion_ok and pose_ok:
                        print(f"   🎉 QUALITY SUCCESS: Both emotion and pose > 0.3")
                        scenario_result["quality_passed"] = True
                        results["quality_success"] += 1
                    elif emotion_ok or pose_ok:
                        print(f"   ⚠️  PARTIAL SUCCESS: One detection system working")
                    else:
                        print(f"   ❌ QUALITY FAILURE: Both detections below threshold")
                        
                        # Additional debugging for quality failures
                        print(f"   🔍 Quality debugging:")
                        import cv2
                        img = cv2.imread(str(output_path))
                        if img is not None:
                            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                            
                            # Face detection
                            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
                            print(f"      OpenCV faces detected: {len(faces)}")
                            
                            # Image quality metrics
                            sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
                            contrast = gray.std()
                            print(f"      Image sharpness: {sharpness:.2f}")
                            print(f"      Image contrast: {contrast:.2f}")
                else:
                    print(f"   ❌ File not created")
            else:
                print(f"   ❌ Generation failed: {result.get('error', 'Unknown error')}")
                results["comfyui_stability"] = False
            
            results["scenarios"].append(scenario_result)
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
            results["comfyui_stability"] = False
    
    # Final assessment
    print(f"\n🎯 FINAL VERIFICATION RESULTS")
    print("=" * 50)
    
    print(f"📊 Generation Success: {results['generation_success']}/{len(test_scenarios)}")
    print(f"🔍 Quality Success: {results['quality_success']}/{len(test_scenarios)}")
    print(f"⚡ ComfyUI Stability: {'✅' if results['comfyui_stability'] else '❌'}")
    
    # Issue resolution status
    print(f"\n🔧 ISSUE RESOLUTION STATUS:")
    
    # Issue 1: ComfyUI Prompt Processing
    if results["comfyui_stability"] and results["generation_success"] > 0:
        print(f"✅ Issue 1 RESOLVED: ComfyUI processes prompts without terminating")
    else:
        print(f"❌ Issue 1 UNRESOLVED: ComfyUI still has processing issues")
    
    # Issue 2: Image Quality
    if results["quality_success"] > 0:
        print(f"✅ Issue 2 RESOLVED: Generated images achieve >0.3 confidence scores")
        print(f"   Quality success rate: {results['quality_success']}/{len(test_scenarios)}")
    else:
        print(f"❌ Issue 2 UNRESOLVED: Image quality still below standards")
    
    # Overall success
    overall_success = (
        results["comfyui_stability"] and
        results["generation_success"] >= len(test_scenarios) * 0.5 and
        results["quality_success"] >= len(test_scenarios) * 0.5
    )
    
    if overall_success:
        print(f"\n🎉 CRITICAL ISSUES RESOLVED!")
        print(f"✅ ComfyUI integration is stable")
        print(f"✅ Image quality meets publication standards")
        print(f"📋 Ready to proceed with Phase 2/3 implementation")
    else:
        print(f"\n⚠️  ISSUES PARTIALLY RESOLVED")
        print(f"🔧 Some problems remain - continue debugging")
    
    # Save results
    import json
    results_path = output_dir / "verification_results.json"
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Results saved to: {results_path}")
    
    return overall_success

if __name__ == "__main__":
    print("🔍 FINAL VERIFICATION OF CRITICAL ISSUE FIXES")
    print("=" * 70)
    print("This test verifies that both critical issues have been resolved:")
    print("1. ComfyUI prompt processing failure")
    print("2. Generated image quality problems")
    print()
    
    success = test_fixed_generation()
    
    if success:
        print(f"\n✅ VERIFICATION PASSED: Critical issues resolved")
        print(f"🚀 System ready for production manga generation")
    else:
        print(f"\n❌ VERIFICATION FAILED: Issues require further debugging")
    
    sys.exit(0 if success else 1)
