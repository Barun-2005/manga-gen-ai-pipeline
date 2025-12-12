import os
import sys
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Tuple

def analyze_all_recent_images():
    """Analyze all recent images to identify quality patterns."""
    print("🔍 ANALYZING ALL RECENT IMAGES FOR QUALITY PATTERNS")
    print("=" * 70)
    
    # Get all recent images from ComfyUI output
    output_dir = Path("ComfyUI-master/output")
    if not output_dir.exists():
        print("❌ ComfyUI output directory not found")
        return
    
    # Get images from last 24 hours
    import time
    recent_images = []
    current_time = time.time()
    
    for img_file in output_dir.glob("*.png"):
        file_time = img_file.stat().st_mtime
        if current_time - file_time < 86400:  # 24 hours
            recent_images.append(img_file)
    
    # Sort by modification time (newest first)
    recent_images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    print(f"📊 Found {len(recent_images)} recent images")
    
    # Analyze each image
    quality_results = []
    
    for i, img_path in enumerate(recent_images[:15]):  # Analyze last 15 images
        print(f"\n📋 Image {i+1}: {img_path.name}")
        
        result = analyze_image_content_detailed(str(img_path))
        result["filename"] = img_path.name
        result["file_time"] = img_path.stat().st_mtime
        quality_results.append(result)
        
        # Print summary
        if result.get("error"):
            print(f"   ❌ Error: {result['error']}")
        else:
            print(f"   📁 Size: {result['file_size']:,} bytes")
            print(f"   👤 Faces: {result['faces_detected']}")
            print(f"   🎨 Content Type: {result['content_type']}")
            print(f"   📊 Quality Score: {result['quality_score']:.2f}")
    
    # Identify patterns
    print(f"\n🔍 QUALITY PATTERN ANALYSIS")
    print("=" * 50)
    
    high_quality = [r for r in quality_results if not r.get("error") and r["quality_score"] >= 0.7]
    medium_quality = [r for r in quality_results if not r.get("error") and 0.4 <= r["quality_score"] < 0.7]
    poor_quality = [r for r in quality_results if not r.get("error") and r["quality_score"] < 0.4]
    
    print(f"📊 Quality Distribution:")
    print(f"   ✅ High Quality (≥0.7): {len(high_quality)} images")
    print(f"   ⚠️  Medium Quality (0.4-0.7): {len(medium_quality)} images")
    print(f"   ❌ Poor Quality (<0.4): {len(poor_quality)} images")
    
    # Analyze poor quality images in detail
    if poor_quality:
        print(f"\n🔍 POOR QUALITY IMAGE ANALYSIS:")
        for result in poor_quality:
            print(f"   📋 {result['filename']}:")
            print(f"      Content Type: {result['content_type']}")
            print(f"      Issues: {', '.join(result['issues'])}")
            
            # Copy for manual inspection
            source_path = output_dir / result['filename']
            dest_path = f"contest_package/output/poor_quality_{result['filename']}"
            import shutil
            shutil.copy2(source_path, dest_path)
            print(f"      📁 Copied to: {dest_path}")
    
    # Identify the source of quality discrepancy
    print(f"\n🎯 ROOT CAUSE ANALYSIS:")
    
    if len(poor_quality) > 0:
        print(f"✅ CONFIRMED: Found {len(poor_quality)} poor quality images")
        
        # Analyze common characteristics of poor quality images
        poor_content_types = [r['content_type'] for r in poor_quality]
        poor_issues = []
        for r in poor_quality:
            poor_issues.extend(r['issues'])
        
        from collections import Counter
        content_counter = Counter(poor_content_types)
        issue_counter = Counter(poor_issues)
        
        print(f"   📊 Poor Quality Content Types:")
        for content_type, count in content_counter.most_common():
            print(f"      - {content_type}: {count} images")
        
        print(f"   📊 Most Common Issues:")
        for issue, count in issue_counter.most_common(5):
            print(f"      - {issue}: {count} occurrences")
        
        # Recommendations
        print(f"\n🔧 RECOMMENDATIONS:")
        if "abstract_content" in [r['content_type'] for r in poor_quality]:
            print(f"   - Issue: Abstract/non-character content being generated")
            print(f"   - Fix: Check prompt content and workflow parameters")
        
        if "no_faces" in poor_issues:
            print(f"   - Issue: Images without recognizable characters")
            print(f"   - Fix: Improve character-focused prompts")
        
        if "low_detail" in poor_issues:
            print(f"   - Issue: Low detail/blurry images")
            print(f"   - Fix: Increase sampling steps and CFG scale")
    
    else:
        print(f"⚠️  NO POOR QUALITY IMAGES FOUND in recent generation")
        print(f"   - All recent images appear to be good quality")
        print(f"   - The quality discrepancy may be from older generation")
        print(f"   - Or the issue may be in specific workflow paths not tested")
    
    return quality_results

def analyze_image_content_detailed(image_path: str) -> Dict[str, Any]:
    """Detailed analysis of image content to identify quality issues."""
    
    result = {
        "file_size": 0,
        "faces_detected": 0,
        "content_type": "unknown",
        "quality_score": 0.0,
        "issues": []
    }
    
    if not os.path.exists(image_path):
        result["error"] = "File not found"
        return result
    
    # Basic file info
    result["file_size"] = os.path.getsize(image_path)
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        result["error"] = "Could not load image"
        return result
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    
    # Face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    result["faces_detected"] = len(faces)
    
    # Content type analysis
    result["content_type"] = classify_image_content(gray, faces)
    
    # Quality metrics
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    brightness = gray.mean()
    
    # Edge detection for structure
    edges = cv2.Canny(gray, 50, 150)
    edge_pixels = np.sum(edges > 0)
    edge_ratio = edge_pixels / (width * height)
    
    # Quality scoring
    quality_score = 0.0
    
    # Face presence (0-0.3)
    if len(faces) > 0:
        quality_score += 0.3
    else:
        result["issues"].append("no_faces")
    
    # Sharpness (0-0.3)
    if sharpness > 500:
        quality_score += 0.3
    elif sharpness > 100:
        quality_score += 0.2
    elif sharpness > 50:
        quality_score += 0.1
    else:
        result["issues"].append("low_detail")
    
    # Contrast (0-0.2)
    if contrast > 40:
        quality_score += 0.2
    elif contrast > 20:
        quality_score += 0.1
    else:
        result["issues"].append("low_contrast")
    
    # Structure/edges (0-0.2)
    if edge_ratio > 0.05:
        quality_score += 0.2
    elif edge_ratio > 0.02:
        quality_score += 0.1
    else:
        result["issues"].append("no_structure")
    
    result["quality_score"] = quality_score
    result["sharpness"] = sharpness
    result["contrast"] = contrast
    result["edge_ratio"] = edge_ratio
    
    return result

def classify_image_content(gray_image: np.ndarray, faces: np.ndarray) -> str:
    """Classify the type of content in the image."""
    
    height, width = gray_image.shape
    
    # Check for character content
    if len(faces) > 0:
        return "character_with_face"
    
    # Check for structured content vs abstract
    edges = cv2.Canny(gray_image, 30, 100)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    significant_contours = [c for c in contours if cv2.contourArea(c) > 100]
    
    if len(significant_contours) > 10:
        return "structured_content"
    elif len(significant_contours) > 3:
        return "simple_content"
    else:
        # Check if it's abstract/cloudy content
        blur_score = cv2.Laplacian(gray_image, cv2.CV_64F).var()
        if blur_score < 50:
            return "abstract_content"
        else:
            return "minimal_content"

def test_specific_workflow_paths():
    """Test specific workflow paths that might be causing poor quality."""
    print(f"\n🧪 TESTING SPECIFIC WORKFLOW PATHS")
    print("=" * 50)
    
    # Test the enhanced panel generator path (what's used in Phase 2)
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))
        from enhanced_panel_generator import EnhancedPanelGenerator
        
        print(f"📋 Testing Enhanced Panel Generator...")
        
        generator = EnhancedPanelGenerator("bw")
        
        result = generator.generate_quality_panel(
            output_image="contest_package/output/enhanced_generator_test.png",
            style="bw",
            emotion="happy",
            pose="standing",
            dialogue_lines=["Hello!", "Nice day!"],
            scene_description="simple anime character test"
        )
        
        if result.get("success"):
            print(f"   ✅ Enhanced generator succeeded")
            
            # Analyze the result
            if os.path.exists("contest_package/output/enhanced_generator_test.png"):
                analysis = analyze_image_content_detailed("contest_package/output/enhanced_generator_test.png")
                print(f"   📊 Quality Score: {analysis['quality_score']:.2f}")
                print(f"   🎨 Content Type: {analysis['content_type']}")
                
                if analysis['quality_score'] < 0.4:
                    print(f"   ❌ FOUND POOR QUALITY SOURCE: Enhanced Panel Generator")
                    print(f"   🔧 Issues: {', '.join(analysis['issues'])}")
                else:
                    print(f"   ✅ Enhanced generator produces good quality")
        else:
            print(f"   ❌ Enhanced generator failed: {result.get('error', 'Unknown error')}")
    
    except Exception as e:
        print(f"   ❌ Enhanced generator test failed: {e}")

def main():
    """Main investigation function."""
    print("🔍 IDENTIFYING SOURCE OF POOR QUALITY IMAGES")
    print("=" * 70)
    
    # Analyze all recent images
    quality_results = analyze_all_recent_images()
    
    # Test specific workflow paths
    test_specific_workflow_paths()
    
    # Final summary
    poor_quality_count = len([r for r in quality_results if not r.get("error") and r["quality_score"] < 0.4])
    
    print(f"\n🎯 INVESTIGATION CONCLUSION")
    print("=" * 50)
    
    if poor_quality_count > 0:
        print(f"✅ QUALITY DISCREPANCY CONFIRMED")
        print(f"   Found {poor_quality_count} poor quality images")
        print(f"   Check copied files in contest_package/output/ for manual inspection")
    else:
        print(f"⚠️  NO QUALITY DISCREPANCY FOUND")
        print(f"   All recent images appear to be good quality")
        print(f"   The issue may be in specific conditions not yet tested")

if __name__ == "__main__":
    main()
