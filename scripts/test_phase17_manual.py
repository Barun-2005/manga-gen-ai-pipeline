#!/usr/bin/env python3
"""
Manual Test for Phase 17

Quick manual test to verify Phase 17 functionality without ComfyUI dependency.
"""

import sys
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.emotion_matcher import EmotionMatcher
from core.pose_matcher import PoseMatcher
from core.panel_generator import EnhancedPanelGenerator


def create_test_image(image_type: str = "bright") -> str:
    """Create a test image for validation."""
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        if image_type == "bright":
            # Bright image (should be detected as happy)
            test_image = np.ones((200, 100, 3), dtype=np.uint8)
            test_image[:, :] = [255, 255, 255]  # Bright white
        elif image_type == "dark":
            # Dark image (should be detected as sad)
            test_image = np.ones((200, 100, 3), dtype=np.uint8) * 30
        elif image_type == "tall":
            # Tall image (should be detected as standing)
            test_image = np.ones((200, 80, 3), dtype=np.uint8) * 128
        elif image_type == "wide":
            # Wide image (should be detected as lying)
            test_image = np.ones((80, 200, 3), dtype=np.uint8) * 128
        else:
            # Default neutral image
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
        
        cv2.imwrite(tmp_file.name, test_image)
        return tmp_file.name


def test_emotion_matcher():
    """Test emotion matcher functionality."""
    print("🎭 Testing Emotion Matcher...")
    
    matcher = EmotionMatcher()
    
    # Test 1: Extract intended emotion
    metadata = {
        "dialogue": "I'm so happy and excited!",
        "description": "Character smiling brightly"
    }
    intended = matcher.extract_intended_emotion(metadata)
    print(f"   Intended emotion: {intended}")
    assert intended == "happy", f"Expected 'happy', got '{intended}'"
    
    # Test 2: Detect visual emotion
    bright_image = create_test_image("bright")
    detected, confidence = matcher.detect_visual_emotion(bright_image)
    print(f"   Detected emotion: {detected} (confidence: {confidence:.2f})")
    
    # Test 3: Match emotions
    is_match, match_conf = matcher.match_emotion("happy", "happy")
    print(f"   Direct match: {is_match} (confidence: {match_conf:.2f})")
    assert is_match and match_conf == 1.0
    
    # Test 4: Full validation
    result = matcher.validate_panel_emotion(bright_image, metadata)
    print(f"   Validation result: {result['status']}")
    
    # Cleanup
    Path(bright_image).unlink(missing_ok=True)
    
    print("   ✅ Emotion matcher tests passed!")


def test_pose_matcher():
    """Test pose matcher functionality."""
    print("🤸 Testing Pose Matcher...")
    
    matcher = PoseMatcher()
    
    # Test 1: Extract intended pose
    metadata = {
        "description": "Character is standing upright",
        "action": "standing confidently"
    }
    intended = matcher.extract_intended_pose(metadata)
    print(f"   Intended pose: {intended}")
    assert intended == "standing", f"Expected 'standing', got '{intended}'"
    
    # Test 2: Detect visual pose
    tall_image = create_test_image("tall")
    detected, confidence = matcher.detect_visual_pose(tall_image)
    print(f"   Detected pose: {detected} (confidence: {confidence:.2f})")
    
    # Test 3: Match poses
    is_match, match_conf = matcher.match_pose("standing", "standing")
    print(f"   Direct match: {is_match} (confidence: {match_conf:.2f})")
    assert is_match and match_conf == 1.0
    
    # Test 4: Full validation
    result = matcher.validate_panel_pose(tall_image, metadata)
    print(f"   Validation result: {result['status']}")
    
    # Cleanup
    Path(tall_image).unlink(missing_ok=True)
    
    print("   ✅ Pose matcher tests passed!")


def test_panel_generator_integration():
    """Test panel generator integration."""
    print("🎨 Testing Panel Generator Integration...")
    
    # Create generator (this will initialize emotion and pose matchers)
    generator = EnhancedPanelGenerator()
    
    # Verify matchers are initialized
    assert hasattr(generator, 'emotion_matcher')
    assert hasattr(generator, 'pose_matcher')
    assert generator.emotion_matcher is not None
    assert generator.pose_matcher is not None
    print("   ✅ Matchers initialized correctly")
    
    # Test validation method
    test_image = create_test_image("bright")
    metadata = {
        "emotion": "happy",
        "pose": "standing",
        "dialogue": "I'm so happy!",
        "description": "Character standing and smiling"
    }
    
    result = generator.validate_panel_emotion_pose(test_image, metadata)
    
    # Check result structure
    assert "emotion_validation" in result
    assert "pose_validation" in result
    assert "overall_status" in result
    
    emotion_val = result["emotion_validation"]
    pose_val = result["pose_validation"]
    
    assert "intended_emotion" in emotion_val
    assert "detected_emotion" in emotion_val
    assert "status" in emotion_val
    
    assert "intended_pose" in pose_val
    assert "detected_pose" in pose_val
    assert "status" in pose_val
    
    print(f"   Emotion: {emotion_val['intended_emotion']} → {emotion_val['detected_emotion']} ({emotion_val['status']})")
    print(f"   Pose: {pose_val['intended_pose']} → {pose_val['detected_pose']} ({pose_val['status']})")
    print(f"   Overall: {result['overall_status']}")
    
    # Cleanup
    Path(test_image).unlink(missing_ok=True)
    
    print("   ✅ Panel generator integration tests passed!")


def test_prompt_enhancement():
    """Test that prompt enhancement is working."""
    print("📝 Testing Prompt Enhancement...")
    
    from image_gen.prompt_builder import PromptBuilder
    
    builder = PromptBuilder()
    
    # Test story data
    story_data = {
        "scenes": ["happy character jumping with joy"]
    }
    
    # Build prompt
    positive_prompt, negative_prompt = builder.build_manga_panel_prompt(
        story_data, 0, panel_index=0
    )
    
    print(f"   Generated prompt: {positive_prompt[:100]}...")
    
    # Check that emotion and pose tags are injected
    assert "[emotion:" in positive_prompt, "Emotion tag not found in prompt"
    assert "[pose:" in positive_prompt, "Pose tag not found in prompt"
    
    print("   ✅ Emotion and pose tags found in prompt")
    print("   ✅ Prompt enhancement tests passed!")


def main():
    """Run all manual tests."""
    print("🚀 Starting Phase 17 Manual Tests\n")
    
    try:
        test_emotion_matcher()
        print()
        
        test_pose_matcher()
        print()
        
        test_panel_generator_integration()
        print()
        
        test_prompt_enhancement()
        print()
        
        print("🎉 All Phase 17 manual tests passed!")
        print("\n✅ Phase 17 is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
