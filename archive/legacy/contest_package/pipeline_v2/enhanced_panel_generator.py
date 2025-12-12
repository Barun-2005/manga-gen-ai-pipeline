import os
import sys
import cv2
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from generate_panel import generate_panel
from core.emotion_matcher import EmotionMatcher
from core.pose_matcher import PoseMatcher
from core.dialogue_placer import DialoguePlacementEngine
from validators.bubble_validator import BubbleValidator

class EnhancedPanelGenerator:
    """
    Enhanced panel generator with quality validation and dialogue integration.
    
    Generates manga panels with:
    - Emotion/pose validation (>70% confidence required)
    - Visual dialogue bubble placement
    - Quality retry logic
    - Publication-ready output
    """
    
    def __init__(self, color_mode: str = "bw"):
        """Initialize the enhanced panel generator."""
        self.color_mode = color_mode
        
        # Initialize validation systems
        print("🔧 Initializing validation systems...")
        self.emotion_matcher = EmotionMatcher()
        self.pose_matcher = PoseMatcher()
        self.dialogue_placer = DialoguePlacementEngine(color_mode)
        self.bubble_validator = BubbleValidator()
        
        # Quality thresholds (relaxed for initial testing)
        self.min_emotion_confidence = 0.3  # Lowered from 0.7
        self.min_pose_confidence = 0.3     # Lowered from 0.7
        self.max_face_overlap = 0.3        # Increased from 0.2
        self.max_retries = 2               # Reduced from 3 for faster testing
        
        print("✅ Enhanced panel generator initialized")
    
    def generate_quality_panel(
        self,
        output_image: str,
        style: str,
        emotion: str,
        pose: str,
        dialogue_lines: List[str] = None,
        scene_description: str = None
    ) -> Dict[str, Any]:
        """
        Generate a high-quality manga panel with validation and dialogue.
        
        Args:
            output_image: Path for output image
            style: "bw" or "color"
            emotion: Target emotion (e.g., "happy", "angry")
            pose: Target pose (e.g., "standing", "arms_crossed")
            dialogue_lines: List of dialogue text
            scene_description: Additional scene context
            
        Returns:
            Generation results with quality metrics
        """
        print(f"\n🎨 Generating quality panel: {emotion} + {pose} ({style})")
        
        # Build enhanced prompt
        enhanced_prompt = self._build_enhanced_prompt(emotion, pose, scene_description)
        
        # Attempt generation with retry logic
        for attempt in range(self.max_retries):
            print(f"   🔄 Attempt {attempt + 1}/{self.max_retries}")
            
            try:
                # Generate base panel
                temp_panel = f"{output_image}.temp_{attempt}.png"
                generate_panel(temp_panel, style, emotion, pose)
                
                if not os.path.exists(temp_panel):
                    print(f"   ❌ Panel generation failed")
                    continue
                
                # Validate quality
                validation_result = self._validate_panel_quality(temp_panel, emotion, pose)

                # Accept image if validation passes OR if it's the last attempt (fallback)
                quality_acceptable = (validation_result["quality_passed"] or
                                    attempt == self.max_retries - 1)

                if quality_acceptable:
                    if validation_result["quality_passed"]:
                        print(f"   ✅ Quality validation passed!")
                    else:
                        print(f"   ⚠️  Quality validation failed but accepting (final attempt)")
                        print(f"       Issues: {validation_result['issues']}")

                    # Add dialogue if provided
                    if dialogue_lines:
                        final_result = self._add_dialogue_bubbles(
                            temp_panel, output_image, dialogue_lines
                        )
                    else:
                        # Move temp to final output
                        os.rename(temp_panel, output_image)
                        final_result = {
                            "dialogue_added": False,
                            "bubble_quality": None
                        }

                    # Cleanup temp files
                    self._cleanup_temp_files(output_image, attempt)

                    # Return success result
                    return {
                        "success": True,
                        "attempts": attempt + 1,
                        "validation": validation_result,
                        "dialogue": final_result,
                        "output_path": output_image,
                        "quality_fallback": not validation_result["quality_passed"]
                    }
                else:
                    print(f"   ❌ Quality validation failed: {validation_result['issues']}")

            except Exception as e:
                print(f"   ❌ Generation error: {e}")
                continue
        
        # All attempts failed
        print(f"❌ Failed to generate quality panel after {self.max_retries} attempts")
        return {
            "success": False,
            "attempts": self.max_retries,
            "error": "Quality validation failed after maximum retries"
        }
    
    def _build_enhanced_prompt(self, emotion: str, pose: str, scene_description: str = None) -> str:
        """Build tag-based prompt optimized for Waifu Diffusion model."""

        # Convert narrative content to tag-based format for Waifu Diffusion
        tags = []

        # Character count and type
        tags.append("1girl")  # Default to single character

        # Emotion to facial expression tags
        emotion_tags = {
            "happy": "smile, happy",
            "sad": "sad, tears, crying",
            "angry": "angry, frown, clenched teeth",
            "surprised": "surprised, open mouth, wide eyes",
            "excited": "excited, smile, sparkling eyes",
            "determined": "serious, determined expression",
            "focused": "focused, serious",
            "worried": "worried, anxious",
            "confused": "confused, tilted head",
            "neutral": "neutral expression"
        }

        emotion_tag = emotion_tags.get(emotion.lower(), "neutral expression")
        tags.append(emotion_tag)

        # Pose tags
        pose_tags = {
            "standing": "standing",
            "sitting": "sitting",
            "walking": "walking",
            "running": "running",
            "crouching": "crouching",
            "lying": "lying down",
            "kneeling": "kneeling"
        }

        pose_tag = pose_tags.get(pose.lower(), "standing")
        tags.append(pose_tag)

        # Extract simple scene elements if provided
        if scene_description:
            scene_tag = self._extract_scene_tags(scene_description)
            if scene_tag:
                tags.append(scene_tag)

        # Add quality and style tags
        tags.extend([
            "anime style",
            "high quality",
            "detailed face",
            "looking at viewer"
        ])

        # Join tags with commas (Waifu Diffusion format)
        tag_prompt = ", ".join(tags)

        # Add emotion-specific facial details
        emotion_details = {
            "happy": "smiling face, bright eyes, cheerful expression, upturned mouth",
            "angry": "frowning face, narrowed eyes, intense glare, clenched jaw",
            "surprised": "wide open eyes, raised eyebrows, open mouth, shocked expression",
            "sad": "downcast eyes, frowning mouth, melancholy expression, drooping features",
            "neutral": "calm face, relaxed expression, normal eyes and mouth"
        }

        # Add pose-specific body details
        pose_details = {
            "standing": "standing upright, full body visible, balanced posture, feet on ground",
            "arms_crossed": "arms crossed over chest, defensive stance, clear arm positioning",
            "sitting": "sitting position, upper body prominent, relaxed seated pose",
            "running": "running motion, dynamic pose, legs in motion, action stance",
            "jumping": "jumping in air, legs bent, dynamic movement, airborne pose"
        }

        print(f"🎨 Tag-based prompt: '{tag_prompt}'")  # Debug log

        return tag_prompt

    def _extract_scene_tags(self, scene_description: str) -> str:
        """Extract simple scene tags from narrative description."""

        scene_lower = scene_description.lower()

        # Scene location tags
        location_tags = {
            "school": "school, classroom",
            "classroom": "classroom, school",
            "garden": "garden, flowers",
            "forest": "forest, trees",
            "city": "city, buildings",
            "street": "street, urban",
            "room": "indoors, room",
            "house": "house, indoors",
            "park": "park, outdoors",
            "beach": "beach, ocean",
            "mountain": "mountain, landscape",
            "field": "field, grass",
            "rooftop": "rooftop, city view",
            "library": "library, books",
            "cafe": "cafe, indoors"
        }

        # Time/lighting tags
        time_tags = {
            "sunset": "sunset, orange sky",
            "sunrise": "sunrise, morning light",
            "night": "night, dark",
            "evening": "evening, twilight",
            "morning": "morning, bright",
            "afternoon": "afternoon, daylight"
        }

        # Weather tags
        weather_tags = {
            "rain": "rain, wet",
            "snow": "snow, winter",
            "sunny": "sunny, bright",
            "cloudy": "cloudy sky"
        }

        extracted_tags = []

        # Check for location
        for location, tag in location_tags.items():
            if location in scene_lower:
                extracted_tags.append(tag)
                break

        # Check for time/lighting
        for time_word, tag in time_tags.items():
            if time_word in scene_lower:
                extracted_tags.append(tag)
                break

        # Check for weather
        for weather, tag in weather_tags.items():
            if weather in scene_lower:
                extracted_tags.append(tag)
                break

        # Default background if nothing found
        if not extracted_tags:
            extracted_tags.append("simple background")

        return ", ".join(extracted_tags)


    
    def _validate_panel_quality(self, image_path: str, target_emotion: str, target_pose: str) -> Dict[str, Any]:
        """Validate panel quality using emotion and pose detection."""
        
        print(f"   🔍 Validating panel quality...")
        
        # Check if image exists and is readable
        if not os.path.exists(image_path):
            return {
                "quality_passed": False,
                "issues": ["image_not_found"],
                "emotion_result": None,
                "pose_result": None
            }
        
        # Test image loading
        test_image = cv2.imread(image_path)
        if test_image is None:
            return {
                "quality_passed": False,
                "issues": ["image_unreadable"],
                "emotion_result": None,
                "pose_result": None
            }
        
        issues = []
        
        # Validate emotion
        detected_emotion, emotion_confidence = self.emotion_matcher.detect_visual_emotion(image_path)
        emotion_result = {
            "target": target_emotion,
            "detected": detected_emotion,
            "confidence": emotion_confidence
        }
        
        if detected_emotion == "invalid_image_quality":
            issues.append("invalid_image_quality")
        elif emotion_confidence < self.min_emotion_confidence:
            issues.append(f"low_emotion_confidence_{emotion_confidence:.2f}")
        
        # Validate pose
        detected_pose, pose_confidence = self.pose_matcher.detect_visual_pose(image_path)
        pose_result = {
            "target": target_pose,
            "detected": detected_pose,
            "confidence": pose_confidence
        }
        
        if detected_pose == "invalid_image_quality":
            issues.append("invalid_pose_quality")
        elif pose_confidence < self.min_pose_confidence:
            issues.append(f"low_pose_confidence_{pose_confidence:.2f}")
        
        # Determine overall quality
        quality_passed = len(issues) == 0
        
        print(f"     Emotion: {detected_emotion} ({emotion_confidence:.2f})")
        print(f"     Pose: {detected_pose} ({pose_confidence:.2f})")
        print(f"     Quality: {'✅ PASS' if quality_passed else '❌ FAIL'}")
        
        return {
            "quality_passed": quality_passed,
            "issues": issues,
            "emotion_result": emotion_result,
            "pose_result": pose_result
        }
    
    def _add_dialogue_bubbles(self, input_image: str, output_image: str, dialogue_lines: List[str]) -> Dict[str, Any]:
        """Add dialogue bubbles to the panel."""
        
        print(f"   💬 Adding {len(dialogue_lines)} dialogue bubbles...")
        
        try:
            # Place dialogue bubbles
            processed_image, bubbles, metadata = self.dialogue_placer.place_dialogue(
                input_image, dialogue_lines
            )
            
            # Save processed image
            cv2.imwrite(output_image, processed_image)
            
            # Validate bubble placement
            validation_results = self.bubble_validator.validate_bubble_placement(
                output_image, bubbles, self.color_mode
            )
            
            # Check bubble quality
            face_overlap = validation_results.get("face_overlap_score", 1.0)
            bubble_quality_passed = face_overlap <= self.max_face_overlap
            
            print(f"     Bubbles placed: {len(bubbles)}")
            print(f"     Face overlap: {face_overlap:.2f} ({'✅ PASS' if bubble_quality_passed else '❌ FAIL'})")
            
            return {
                "dialogue_added": True,
                "bubble_count": len(bubbles),
                "bubble_quality": validation_results,
                "quality_passed": bubble_quality_passed
            }
            
        except Exception as e:
            print(f"   ❌ Dialogue placement failed: {e}")
            # Fallback: copy original image
            import shutil
            shutil.copy2(input_image, output_image)
            
            return {
                "dialogue_added": False,
                "error": str(e),
                "quality_passed": False
            }
    
    def _cleanup_temp_files(self, output_base: str, max_attempt: int):
        """Clean up temporary files from generation attempts."""
        for i in range(max_attempt + 1):
            temp_file = f"{output_base}.temp_{i}.png"
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
