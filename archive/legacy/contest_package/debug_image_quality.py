import os
import sys
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'core'))

from core.emotion_matcher import EmotionMatcher
from core.pose_matcher import PoseMatcher

def analyze_image_quality(image_path):
    """Comprehensive analysis of generated image quality."""
    print(f"🔍 ANALYZING IMAGE QUALITY: {Path(image_path).name}")
    print("=" * 60)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Basic image properties
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Could not load image")
        return
    
    height, width = image.shape[:2]
    file_size = os.path.getsize(image_path)
    
    print(f"📊 Basic Properties:")
    print(f"   Dimensions: {width}x{height}")
    print(f"   File Size: {file_size:,} bytes ({file_size/1024/1024:.1f}MB)")
    print(f"   Aspect Ratio: {width/height:.2f}")
    
    # Image quality metrics
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Sharpness (Laplacian variance)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    print(f"   Sharpness Score: {laplacian_var:.2f} ({'High' if laplacian_var > 500 else 'Medium' if laplacian_var > 100 else 'Low'})")
    
    # Contrast
    contrast = gray.std()
    print(f"   Contrast Score: {contrast:.2f} ({'High' if contrast > 50 else 'Medium' if contrast > 30 else 'Low'})")
    
    # Brightness
    brightness = gray.mean()
    print(f"   Brightness: {brightness:.2f} ({'Good' if 50 < brightness < 200 else 'Poor'})")
    
    # Face detection analysis
    print(f"\n👤 Face Detection Analysis:")
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    
    print(f"   Faces Detected: {len(faces)}")
    
    if len(faces) > 0:
        for i, (x, y, w, h) in enumerate(faces):
            print(f"   Face {i+1}: Position ({x}, {y}), Size {w}x{h}")
            
            # Extract face region for detailed analysis
            face_region = gray[y:y+h, x:x+w]
            face_sharpness = cv2.Laplacian(face_region, cv2.CV_64F).var()
            face_contrast = face_region.std()
            
            print(f"      Face Sharpness: {face_sharpness:.2f}")
            print(f"      Face Contrast: {face_contrast:.2f}")
            
            # Check for distortion indicators
            if face_sharpness < 50:
                print(f"      ⚠️  Face appears blurry")
            if face_contrast < 20:
                print(f"      ⚠️  Face has low contrast")
            if w < 50 or h < 50:
                print(f"      ⚠️  Face is very small")
            if w/h > 1.5 or h/w > 1.5:
                print(f"      ⚠️  Face aspect ratio is distorted")
    else:
        print(f"   ❌ No faces detected - this explains 0.0 emotion scores")
    
    # Edge detection for pose analysis
    print(f"\n🤸 Pose Detection Analysis:")
    edges = cv2.Canny(gray, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
    print(f"   Significant Contours: {len(significant_contours)}")
    
    if len(significant_contours) < 5:
        print(f"   ⚠️  Very few body contours detected - explains 0.0 pose scores")
    
    # Test with actual validation systems
    print(f"\n🧪 Validation System Test:")
    try:
        emotion_matcher = EmotionMatcher()
        detected_emotion, emotion_confidence = emotion_matcher.detect_visual_emotion(image_path)
        print(f"   Emotion Detection: {detected_emotion} (confidence: {emotion_confidence:.3f})")
        
        if emotion_confidence == 0.0:
            print(f"   ❌ Zero emotion confidence confirms quality issues")
        
    except Exception as e:
        print(f"   ❌ Emotion detection failed: {e}")
    
    try:
        pose_matcher = PoseMatcher()
        detected_pose, pose_confidence = pose_matcher.detect_visual_pose(image_path)
        print(f"   Pose Detection: {detected_pose} (confidence: {pose_confidence:.3f})")
        
        if pose_confidence == 0.0:
            print(f"   ❌ Zero pose confidence confirms quality issues")
        
    except Exception as e:
        print(f"   ❌ Pose detection failed: {e}")
    
    # Overall quality assessment
    print(f"\n🎯 Quality Assessment:")
    
    quality_issues = []
    
    if len(faces) == 0:
        quality_issues.append("No detectable faces")
    if laplacian_var < 100:
        quality_issues.append("Low image sharpness")
    if contrast < 30:
        quality_issues.append("Low contrast")
    if len(significant_contours) < 5:
        quality_issues.append("Insufficient body structure")
    
    if quality_issues:
        print(f"   ❌ Quality Issues Found:")
        for issue in quality_issues:
            print(f"      - {issue}")
    else:
        print(f"   ✅ Image quality appears acceptable")
    
    return quality_issues

def test_optimized_generation():
    """Test generation with optimized parameters for better quality."""
    print(f"\n🔧 TESTING OPTIMIZED GENERATION PARAMETERS")
    print("=" * 60)
    
    # Import ComfyUI client
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'image_gen'))
    from image_gen.comfy_client import load_workflow_template
    
    # Create optimized workflow with better parameters
    try:
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        
        # Optimize generation parameters
        if "3" in workflow:  # KSampler node
            workflow["3"]["inputs"]["steps"] = 30  # Increase steps
            workflow["3"]["inputs"]["cfg"] = 8.0   # Increase CFG for better prompt adherence
            workflow["3"]["inputs"]["sampler_name"] = "dpmpp_2m_sde"  # Better sampler
            workflow["3"]["inputs"]["scheduler"] = "karras"
        
        # Optimize image dimensions for better quality
        if "5" in workflow:  # EmptyLatentImage node
            workflow["5"]["inputs"]["width"] = 768   # Higher resolution
            workflow["5"]["inputs"]["height"] = 1024
        
        # Use a more specific, quality-focused prompt
        optimized_prompt = "high quality anime character portrait, detailed face, clear eyes, natural expression, professional artwork, clean lineart"
        
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", optimized_prompt
        )
        
        print(f"📝 Optimized Prompt: {optimized_prompt}")
        print(f"🔧 Optimized Parameters:")
        print(f"   Steps: 30 (increased from 25)")
        print(f"   CFG Scale: 8.0 (increased from 7.5)")
        print(f"   Sampler: dpmpp_2m_sde (improved)")
        print(f"   Resolution: 768x1024 (increased)")
        
        # Send to ComfyUI
        import requests
        import uuid
        
        prompt_id = str(uuid.uuid4())
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }
        
        print(f"\n📤 Sending optimized workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Optimized workflow queued")
            print(f"⏳ Waiting 45 seconds for high-quality generation...")
            
            import time
            time.sleep(45)
            
            # Check for new images
            output_dir = Path("ComfyUI-master/output")
            if output_dir.exists():
                recent_files = []
                for img_file in output_dir.glob("*.png"):
                    if time.time() - img_file.stat().st_mtime < 60:
                        recent_files.append(img_file)
                
                if recent_files:
                    latest_file = max(recent_files, key=lambda x: x.stat().st_mtime)
                    size = latest_file.stat().st_size
                    print(f"✅ New optimized image generated: {latest_file.name} ({size:,} bytes)")
                    
                    # Copy to test directory
                    test_path = "contest_package/output/optimized_quality_test.png"
                    import shutil
                    shutil.copy2(latest_file, test_path)
                    
                    # Analyze the optimized image
                    print(f"\n📊 OPTIMIZED IMAGE ANALYSIS:")
                    quality_issues = analyze_image_quality(test_path)
                    
                    if len(quality_issues) < 2:
                        print(f"\n🎉 SUCCESS: Optimized parameters improved image quality!")
                        return True
                    else:
                        print(f"\n⚠️  PARTIAL IMPROVEMENT: Some issues remain")
                        return False
                else:
                    print(f"❌ No new images generated")
                    return False
        else:
            print(f"❌ Failed to queue optimized workflow: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Optimized generation test failed: {e}")
        return False

def main():
    """Main quality debug function."""
    print("🔍 IMAGE QUALITY DEBUG ANALYSIS")
    print("=" * 70)
    
    # Analyze the latest generated image
    latest_image = "contest_package/output/quality_test_latest.png"
    if os.path.exists(latest_image):
        quality_issues = analyze_image_quality(latest_image)
        
        if quality_issues:
            print(f"\n🔧 ATTEMPTING QUALITY OPTIMIZATION...")
            optimization_success = test_optimized_generation()
            
            if optimization_success:
                print(f"\n✅ SOLUTION FOUND: Optimized parameters improve image quality")
                print(f"🎯 Recommended fixes:")
                print(f"   - Increase sampling steps to 30+")
                print(f"   - Increase CFG scale to 8.0+")
                print(f"   - Use better sampler (dpmpp_2m_sde)")
                print(f"   - Increase resolution to 768x1024+")
                print(f"   - Use more specific, quality-focused prompts")
            else:
                print(f"\n⚠️  PARTIAL SUCCESS: Parameter optimization helps but more work needed")
        else:
            print(f"\n✅ Current image quality is acceptable")
    else:
        print(f"❌ No test image found at {latest_image}")
        print(f"🔧 Running optimized generation test anyway...")
        test_optimized_generation()

if __name__ == "__main__":
    main()
