import os
import sys
import time
from pathlib import Path

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))

from enhanced_panel_generator import EnhancedPanelGenerator
from story_generator import StoryGenerator

def test_character_focused_fix():
    """Test the character-focused prompt fix to ensure consistent quality."""
    print("🎯 TESTING CHARACTER-FOCUSED PROMPT FIX")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path("contest_package/output/character_focused_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Test scenarios that previously might have generated poor quality
    test_scenarios = [
        {
            "name": "story_based_test",
            "type": "story_generation",
            "input": "A character discovers a magical garden",
            "expected": "Should generate character with face, not just garden"
        },
        {
            "name": "scene_heavy_test", 
            "type": "story_generation",
            "input": "Beautiful sunset scene with character watching",
            "expected": "Should focus on character, not sunset"
        },
        {
            "name": "direct_enhanced_test",
            "type": "enhanced_generator",
            "emotion": "surprised",
            "pose": "standing",
            "scene": "magical forest background",
            "expected": "Should generate character with face, forest as background"
        }
    ]
    
    results = []
    
    for i, scenario in enumerate(test_scenarios, 1):
        print(f"\n📋 Test {i}/{len(test_scenarios)}: {scenario['name']}")
        print(f"   Type: {scenario['type']}")
        print(f"   Expected: {scenario['expected']}")
        
        if scenario['type'] == 'story_generation':
            result = test_story_generation_fix(scenario, output_dir)
        else:
            result = test_enhanced_generator_fix(scenario, output_dir)
        
        results.append(result)
        
        # Print immediate results
        if result['success']:
            print(f"   ✅ Generation: SUCCESS")
            print(f"   👤 Faces Detected: {result['faces_detected']}")
            print(f"   🎨 Content Type: {result['content_type']}")
            print(f"   📊 Quality Score: {result['quality_score']:.2f}")
            
            if result['faces_detected'] > 0:
                print(f"   🎉 CHARACTER-FOCUSED: SUCCESS")
            else:
                print(f"   ❌ CHARACTER-FOCUSED: FAILED (no faces)")
        else:
            print(f"   ❌ Generation: FAILED")
    
    # Analyze results
    print(f"\n📊 CHARACTER-FOCUSED FIX RESULTS")
    print("=" * 50)
    
    successful_generations = len([r for r in results if r['success']])
    character_focused = len([r for r in results if r['success'] and r['faces_detected'] > 0])
    high_quality = len([r for r in results if r['success'] and r['quality_score'] >= 0.7])
    
    print(f"✅ Successful Generations: {successful_generations}/{len(test_scenarios)}")
    print(f"👤 Character-Focused (with faces): {character_focused}/{len(test_scenarios)}")
    print(f"🎨 High Quality (≥0.7): {high_quality}/{len(test_scenarios)}")
    
    # Success criteria
    fix_success = (
        successful_generations >= len(test_scenarios) * 0.8 and  # 80% generation success
        character_focused >= len(test_scenarios) * 0.8           # 80% character-focused
    )
    
    if fix_success:
        print(f"\n🎉 CHARACTER-FOCUSED FIX: SUCCESS")
        print(f"✅ Fix ensures consistent character generation")
        print(f"✅ Quality discrepancy resolved")
    else:
        print(f"\n⚠️ CHARACTER-FOCUSED FIX: NEEDS IMPROVEMENT")
        print(f"🔧 Some scenarios still not generating character-focused content")
    
    return fix_success

def test_story_generation_fix(scenario: dict, output_dir: Path) -> dict:
    """Test story generation with character-focused fix."""
    
    try:
        story_generator = StoryGenerator()
        
        print(f"   📝 Input: '{scenario['input']}'")
        
        # Generate story
        story_data = story_generator.generate_manga_story(scenario['input'], panels=1)
        
        if not story_data or not story_data.get("panels"):
            return {"success": False, "error": "Story generation failed"}
        
        panel_data = story_data["panels"][0]
        visual_prompt = panel_data['visual_prompt']
        
        print(f"   📋 Generated Prompt ({len(visual_prompt)} chars):")
        print(f"      {visual_prompt[:100]}...")
        
        # Check if prompt is character-focused
        character_keywords = ["character", "face", "facial", "eyes", "portrait", "anime"]
        character_focus = any(keyword in visual_prompt.lower() for keyword in character_keywords)
        
        if character_focus:
            print(f"   ✅ Prompt is character-focused")
        else:
            print(f"   ⚠️ Prompt may not be character-focused")
        
        # Generate image using enhanced generator
        generator = EnhancedPanelGenerator("bw")
        
        output_path = output_dir / f"{scenario['name']}.png"
        
        result = generator.generate_quality_panel(
            output_image=str(output_path),
            style="bw",
            emotion=panel_data['character_emotion'],
            pose=panel_data['character_pose'],
            dialogue_lines=panel_data['dialogue'][:2],  # Limit dialogue
            scene_description=visual_prompt
        )
        
        if result.get("success") and os.path.exists(output_path):
            # Analyze generated image
            analysis = analyze_generated_image(str(output_path))
            
            return {
                "success": True,
                "scenario": scenario['name'],
                "prompt": visual_prompt,
                "character_focus": character_focus,
                **analysis
            }
        else:
            return {"success": False, "error": "Image generation failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def test_enhanced_generator_fix(scenario: dict, output_dir: Path) -> dict:
    """Test enhanced generator with character-focused fix."""
    
    try:
        generator = EnhancedPanelGenerator("bw")
        
        output_path = output_dir / f"{scenario['name']}.png"
        
        print(f"   🎭 Emotion: {scenario['emotion']}")
        print(f"   🤸 Pose: {scenario['pose']}")
        print(f"   🖼️ Scene: {scenario['scene']}")
        
        result = generator.generate_quality_panel(
            output_image=str(output_path),
            style="bw",
            emotion=scenario['emotion'],
            pose=scenario['pose'],
            dialogue_lines=["Test dialogue"],
            scene_description=scenario['scene']
        )
        
        if result.get("success") and os.path.exists(output_path):
            # Analyze generated image
            analysis = analyze_generated_image(str(output_path))
            
            return {
                "success": True,
                "scenario": scenario['name'],
                "character_focus": True,  # Enhanced generator is always character-focused
                **analysis
            }
        else:
            return {"success": False, "error": "Image generation failed"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_generated_image(image_path: str) -> dict:
    """Analyze generated image for character focus and quality."""
    
    import cv2
    import numpy as np
    
    if not os.path.exists(image_path):
        return {"faces_detected": 0, "content_type": "missing", "quality_score": 0.0}
    
    # Load image
    image = cv2.imread(image_path)
    if image is None:
        return {"faces_detected": 0, "content_type": "invalid", "quality_score": 0.0}
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Face detection
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)
    faces_detected = len(faces)
    
    # Quality metrics
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    
    # Content type classification
    if faces_detected > 0:
        content_type = "character_with_face"
    else:
        # Check for structured content
        edges = cv2.Canny(gray, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        significant_contours = len([c for c in contours if cv2.contourArea(c) > 100])
        
        if significant_contours > 10:
            content_type = "structured_content"
        else:
            content_type = "abstract_content"
    
    # Quality score calculation
    quality_score = 0.0
    
    # Face presence (0-0.4)
    if faces_detected > 0:
        quality_score += 0.4
    
    # Sharpness (0-0.3)
    if sharpness > 500:
        quality_score += 0.3
    elif sharpness > 100:
        quality_score += 0.2
    
    # Contrast (0-0.3)
    if contrast > 40:
        quality_score += 0.3
    elif contrast > 20:
        quality_score += 0.2
    
    return {
        "faces_detected": faces_detected,
        "content_type": content_type,
        "quality_score": quality_score,
        "sharpness": sharpness,
        "contrast": contrast
    }

if __name__ == "__main__":
    print("🔧 TESTING CHARACTER-FOCUSED QUALITY FIX")
    print("=" * 70)
    print("This test verifies that the prompt fixes ensure consistent character generation")
    print()
    
    success = test_character_focused_fix()
    
    if success:
        print(f"\n✅ CHARACTER-FOCUSED FIX: VERIFIED")
        print(f"🎯 Quality discrepancy resolved - all images should now have characters")
    else:
        print(f"\n❌ CHARACTER-FOCUSED FIX: NEEDS MORE WORK")
        print(f"🔧 Additional prompt engineering required")
    
    sys.exit(0 if success else 1)
