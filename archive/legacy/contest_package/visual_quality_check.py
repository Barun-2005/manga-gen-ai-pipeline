import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List

def analyze_image_content(image_path: str) -> Dict[str, Any]:
    """Analyze image content for basic quality metrics."""
    
    if not os.path.exists(image_path):
        return {"error": "Image not found"}
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return {"error": "Could not load image"}
    
    height, width = image.shape[:2]
    
    # Basic image properties
    analysis = {
        "file_size": os.path.getsize(image_path),
        "dimensions": f"{width}x{height}",
        "aspect_ratio": round(width/height, 2)
    }
    
    # Convert to grayscale for analysis
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Check for face-like regions using Haar cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    analysis["face_regions"] = len(faces)
    
    # Check image contrast and detail
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    analysis["detail_score"] = round(laplacian_var, 2)
    analysis["detail_quality"] = "High" if laplacian_var > 500 else "Medium" if laplacian_var > 100 else "Low"
    
    # Check for edge content (indicates line art)
    edges = cv2.Canny(gray, 50, 150)
    edge_pixels = np.sum(edges > 0)
    edge_percentage = (edge_pixels / (width * height)) * 100
    analysis["edge_content"] = round(edge_percentage, 2)
    analysis["lineart_quality"] = "High" if edge_percentage > 5 else "Medium" if edge_percentage > 2 else "Low"
    
    # Check brightness distribution
    mean_brightness = np.mean(gray)
    analysis["brightness"] = round(mean_brightness, 2)
    analysis["brightness_balance"] = "Good" if 50 < mean_brightness < 200 else "Poor"
    
    return analysis

def main():
    """Analyze generated manga panels for visual quality."""
    
    print("🔍 VISUAL QUALITY ASSESSMENT - PHASE 1 GENERATED PANELS")
    print("=" * 70)
    
    # Find generated panels
    output_dir = Path("contest_package/output/phase1_quality")
    panel_files = [f for f in output_dir.glob("*.png") if not f.name.endswith(".temp_0.png") and not f.name.endswith(".temp_1.png") and not f.name.endswith(".temp_2.png")]
    
    if not panel_files:
        print("❌ No generated panels found!")
        return
    
    print(f"📊 Found {len(panel_files)} generated panels")
    
    # Analyze each panel
    results = []
    for panel_path in sorted(panel_files):
        print(f"\n📋 Analyzing: {panel_path.name}")
        
        analysis = analyze_image_content(str(panel_path))
        
        if "error" in analysis:
            print(f"   ❌ Error: {analysis['error']}")
            continue
        
        # Print analysis results
        print(f"   📏 Dimensions: {analysis['dimensions']}")
        print(f"   📁 File Size: {analysis['file_size']:,} bytes ({analysis['file_size']/1024/1024:.1f} MB)")
        print(f"   👤 Face Regions: {analysis['face_regions']}")
        print(f"   🎨 Detail Quality: {analysis['detail_quality']} (score: {analysis['detail_score']})")
        print(f"   ✏️  Lineart Quality: {analysis['lineart_quality']} ({analysis['edge_content']}% edges)")
        print(f"   💡 Brightness: {analysis['brightness_balance']} (value: {analysis['brightness']})")
        
        # Determine overall quality assessment
        quality_score = 0
        if analysis['face_regions'] > 0:
            quality_score += 2
            print(f"   ✅ Has face-like regions")
        else:
            print(f"   ❌ No clear face regions detected")
        
        if analysis['detail_score'] > 100:
            quality_score += 2
            print(f"   ✅ Good image detail")
        else:
            print(f"   ⚠️  Low image detail")
        
        if analysis['edge_content'] > 2:
            quality_score += 2
            print(f"   ✅ Good lineart content")
        else:
            print(f"   ⚠️  Limited lineart")
        
        if analysis['brightness_balance'] == "Good":
            quality_score += 1
            print(f"   ✅ Good brightness balance")
        else:
            print(f"   ⚠️  Poor brightness balance")
        
        # Overall assessment
        if quality_score >= 6:
            overall = "✅ GOOD QUALITY"
        elif quality_score >= 4:
            overall = "⚠️  ACCEPTABLE QUALITY"
        else:
            overall = "❌ POOR QUALITY"
        
        print(f"   🎯 Overall: {overall} (score: {quality_score}/7)")
        
        results.append({
            "file": panel_path.name,
            "analysis": analysis,
            "quality_score": quality_score,
            "overall": overall
        })
    
    # Summary
    print(f"\n🎯 VISUAL QUALITY SUMMARY")
    print("=" * 50)
    
    good_quality = len([r for r in results if r['quality_score'] >= 6])
    acceptable_quality = len([r for r in results if 4 <= r['quality_score'] < 6])
    poor_quality = len([r for r in results if r['quality_score'] < 4])
    
    print(f"📊 Total Panels: {len(results)}")
    print(f"✅ Good Quality: {good_quality}")
    print(f"⚠️  Acceptable Quality: {acceptable_quality}")
    print(f"❌ Poor Quality: {poor_quality}")
    
    success_rate = (good_quality + acceptable_quality) / len(results) if results else 0
    print(f"📈 Success Rate: {success_rate:.1%}")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS")
    print("-" * 30)
    
    avg_faces = sum(r['analysis']['face_regions'] for r in results) / len(results) if results else 0
    if avg_faces < 0.5:
        print("🔧 Improve prompts to generate clearer character faces")
    
    avg_detail = sum(r['analysis']['detail_score'] for r in results) / len(results) if results else 0
    if avg_detail < 200:
        print("🔧 Enhance prompts for more detailed artwork")
    
    avg_edges = sum(r['analysis']['edge_content'] for r in results) / len(results) if results else 0
    if avg_edges < 3:
        print("🔧 Add lineart-specific terms to prompts")
    
    if success_rate >= 0.67:
        print("🎉 Visual quality meets minimum standards for Phase 1!")
        print("📋 Ready to proceed with dialogue integration improvements")
    else:
        print("⚠️  Visual quality needs improvement before proceeding")
        print("🎯 Focus on prompt engineering and model optimization")
    
    return success_rate >= 0.67

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ PHASE 1 VISUAL QUALITY: PASSED' if success else '❌ PHASE 1 VISUAL QUALITY: NEEDS WORK'}")
