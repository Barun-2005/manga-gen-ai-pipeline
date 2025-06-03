#!/usr/bin/env python3
"""
Pose Matcher Module - Phase 17B Production Version

Validates that generated manga panels match the intended character pose
using MediaPipe for production-quality pose detection.
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import sys
import re
import warnings
warnings.filterwarnings("ignore")

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("Warning: MediaPipe not available, falling back to basic detection")

try:
    from pipeline.utils import detect_pose_keypoints
except ImportError:
    detect_pose_keypoints = None


class PoseMatcher:
    """Matches intended poses with detected poses from generated images using MediaPipe."""

    def __init__(self):
        """Initialize the pose matcher."""

        # Pose categories and their keywords
        self.pose_keywords = {
            "standing": ["standing", "upright", "vertical", "erect"],
            "sitting": ["sitting", "seated", "chair", "bench"],
            "kneeling": ["kneeling", "kneel", "on knees", "genuflect"],
            "lying": ["lying", "laying", "horizontal", "prone", "supine"],
            "walking": ["walking", "stepping", "striding", "moving"],
            "running": ["running", "sprinting", "dashing", "racing"],
            "jumping": ["jumping", "leaping", "hopping", "bouncing"],
            "crouching": ["crouching", "crouch", "squatting", "hunched"],
            "reaching": ["reaching", "extending", "stretching", "grasping"],
            "pointing": ["pointing", "indicating", "gesturing", "directing"],
            "fighting": ["fighting", "combat", "attacking", "defensive"],
            "dancing": ["dancing", "twirling", "spinning", "graceful"],
            "falling": ["falling", "tumbling", "collapsing", "dropping"],
            "climbing": ["climbing", "ascending", "scaling", "mounting"]
        }

        # Initialize MediaPipe pose detection
        self.pose_detector = None
        if MEDIAPIPE_AVAILABLE:
            try:
                self.mp_pose = mp.solutions.pose
                self.pose_detector = self.mp_pose.Pose(
                    static_image_mode=True,
                    model_complexity=1,
                    enable_segmentation=False,
                    min_detection_confidence=0.5
                )
                print("✅ MediaPipe pose detection initialized")
            except Exception as e:
                print(f"Warning: Could not initialize MediaPipe: {e}")
                self.pose_detector = None

        if self.pose_detector is None:
            print("⚠️ Using fallback pose detection")
        
        # Pose similarity mappings
        self.pose_similarities = {
            "standing": ["upright", "vertical"],
            "sitting": ["seated", "resting"],
            "kneeling": ["genuflecting", "bowing"],
            "lying": ["reclining", "horizontal"],
            "walking": ["stepping", "strolling"],
            "running": ["sprinting", "jogging"],
            "jumping": ["leaping", "hopping"],
            "crouching": ["squatting", "hunching"],
            "reaching": ["extending", "grasping"],
            "pointing": ["gesturing", "indicating"],
            "fighting": ["combat", "attacking"],
            "dancing": ["twirling", "graceful"],
            "falling": ["tumbling", "collapsing"],
            "climbing": ["ascending", "scaling"]
        }
    
    def extract_intended_pose(self, scene_metadata: Dict[str, Any]) -> str:
        """
        Extract intended pose from scene metadata or description.
        
        Args:
            scene_metadata: Scene metadata containing pose information
            
        Returns:
            Intended pose label
        """
        # Check if pose is explicitly provided
        if "pose" in scene_metadata:
            return scene_metadata["pose"].lower()
        
        # Extract from description
        text_to_analyze = ""
        if "description" in scene_metadata:
            text_to_analyze += scene_metadata["description"] + " "
        if "dialogue" in scene_metadata:
            text_to_analyze += scene_metadata["dialogue"] + " "
        if "action" in scene_metadata:
            text_to_analyze += scene_metadata["action"] + " "
        
        if not text_to_analyze.strip():
            return "standing"  # Default pose
        
        # Analyze text for pose keywords
        text_lower = text_to_analyze.lower()
        
        # Count pose keyword matches
        pose_scores = {}
        for pose, keywords in self.pose_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                pose_scores[pose] = score
        
        # Return highest scoring pose or default
        if pose_scores:
            return max(pose_scores.items(), key=lambda x: x[1])[0]
        else:
            return "standing"
    
    def detect_visual_pose(self, image_path: str) -> Tuple[str, float]:
        """
        Detect pose from image using MediaPipe or fallback methods.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (detected_pose, confidence_score)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return "standing", 0.0

            # Try MediaPipe first
            if self.pose_detector is not None:
                return self._detect_pose_mediapipe(image)

            # Fallback to basic detection
            return self._detect_pose_fallback(image)

        except Exception as e:
            print(f"Error detecting pose in {image_path}: {e}")
            return "standing", 0.0

    def _detect_pose_mediapipe(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Detect pose using MediaPipe.

        Args:
            image: OpenCV image array (BGR format)

        Returns:
            Tuple of (pose, confidence)
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Process image with MediaPipe
            results = self.pose_detector.process(rgb_image)

            if not results.pose_landmarks:
                return "standing", 0.3

            # Extract pose from landmarks
            pose, confidence = self._classify_pose_from_landmarks(results.pose_landmarks)

            return pose, confidence

        except Exception as e:
            print(f"Error in MediaPipe pose detection: {e}")
            return "standing", 0.0

    def _classify_pose_from_landmarks(self, landmarks) -> Tuple[str, float]:
        """
        Classify pose from MediaPipe landmarks.

        Args:
            landmarks: MediaPipe pose landmarks

        Returns:
            Tuple of (pose, confidence)
        """
        try:
            # Extract key landmark positions
            landmarks_array = np.array([[lm.x, lm.y, lm.z] for lm in landmarks.landmark])

            # Key landmark indices (MediaPipe pose model)
            nose = landmarks_array[0]
            left_shoulder = landmarks_array[11]
            right_shoulder = landmarks_array[12]
            left_hip = landmarks_array[23]
            right_hip = landmarks_array[24]
            left_knee = landmarks_array[25]
            right_knee = landmarks_array[26]
            left_ankle = landmarks_array[27]
            right_ankle = landmarks_array[28]

            # Calculate pose characteristics
            shoulder_center = (left_shoulder + right_shoulder) / 2
            hip_center = (left_hip + right_hip) / 2

            # Vertical alignment (standing vs lying)
            torso_vertical = abs(shoulder_center[1] - hip_center[1])
            torso_horizontal = abs(shoulder_center[0] - hip_center[0])

            # Knee positions relative to hips
            left_knee_below_hip = left_knee[1] > left_hip[1]
            right_knee_below_hip = right_knee[1] > right_hip[1]

            # Ankle positions relative to knees
            left_ankle_below_knee = left_ankle[1] > left_knee[1]
            right_ankle_below_knee = right_ankle[1] > right_knee[1]

            # Classify pose based on landmark relationships
            if torso_vertical < 0.1:  # Very horizontal torso
                return "lying", 0.8
            elif not (left_knee_below_hip and right_knee_below_hip):  # Knees above hips
                return "jumping", 0.7
            elif not (left_ankle_below_knee and right_ankle_below_knee):  # Ankles above knees
                return "sitting", 0.7
            elif torso_vertical > 0.3:  # Very vertical torso
                # Check for movement indicators
                shoulder_width = abs(left_shoulder[0] - right_shoulder[0])
                hip_width = abs(left_hip[0] - right_hip[0])
                if abs(shoulder_width - hip_width) > 0.1:
                    return "walking", 0.6
                else:
                    return "standing", 0.8
            else:
                return "crouching", 0.6

        except Exception as e:
            print(f"Error classifying pose from landmarks: {e}")
            return "standing", 0.3

    def _detect_pose_fallback(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Fallback pose detection using basic methods.

        Args:
            image: OpenCV image array

        Returns:
            Tuple of (pose, confidence)
        """
        try:
            # Use existing pose keypoint detection if available
            if detect_pose_keypoints is not None:
                keypoint_count = detect_pose_keypoints(image)
            else:
                keypoint_count = 0

            # Analyze image dimensions and contours for pose estimation
            pose, confidence = self._analyze_image_pose_basic(image, keypoint_count)

            return pose, confidence

        except Exception as e:
            print(f"Error in fallback pose detection: {e}")
            return "standing", 0.0
    
    def _analyze_image_pose_basic(self, image: np.ndarray, keypoint_count: int) -> Tuple[str, float]:
        """
        Analyze image for pose using basic heuristics.
        
        Args:
            image: OpenCV image array
            keypoint_count: Number of detected keypoints
            
        Returns:
            Tuple of (pose, confidence)
        """
        height, width = image.shape[:2]
        aspect_ratio = height / width
        
        # Convert to grayscale for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Find contours to analyze body shape
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return "standing", 0.3
        
        # Find largest contour (likely the main figure)
        largest_contour = max(contours, key=cv2.contourArea)
        
        # Get bounding rectangle
        x, y, w, h = cv2.boundingRect(largest_contour)
        contour_aspect = h / w if w > 0 else 1.0
        
        # Basic pose heuristics based on shape analysis
        if contour_aspect > 2.0:
            # Tall and narrow - likely standing or walking
            if keypoint_count > 15:
                return "walking", 0.7
            else:
                return "standing", 0.8
        elif contour_aspect < 0.8:
            # Wide and short - likely lying or crouching
            return "lying", 0.7
        elif 1.0 <= contour_aspect <= 1.5:
            # Square-ish - could be sitting or kneeling
            if y + h > height * 0.6:  # Lower in image
                return "sitting", 0.6
            else:
                return "kneeling", 0.6
        else:
            # Default case
            return "standing", 0.5
    
    def match_pose(self, intended_pose: str, detected_pose: str) -> Tuple[bool, float]:
        """
        Check if detected pose matches intended pose.
        
        Args:
            intended_pose: The pose that was intended
            detected_pose: The pose detected from the image
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        intended_lower = intended_pose.lower()
        detected_lower = detected_pose.lower()
        
        # Direct match
        if intended_lower == detected_lower:
            return True, 1.0
        
        # Check similarity mappings
        if intended_lower in self.pose_similarities:
            similar_poses = self.pose_similarities[intended_lower]
            if detected_lower in similar_poses:
                return True, 0.8
        
        # Check reverse mapping
        for base_pose, similar_list in self.pose_similarities.items():
            if intended_lower in similar_list and detected_lower == base_pose:
                return True, 0.8
        
        # Partial matches for related poses
        related_matches = {
            ("standing", "walking"): 0.6,
            ("sitting", "kneeling"): 0.5,
            ("running", "jumping"): 0.7,
            ("crouching", "kneeling"): 0.6,
            ("lying", "falling"): 0.5,
            ("reaching", "pointing"): 0.7
        }
        
        for (p1, p2), confidence in related_matches.items():
            if (intended_lower == p1 and detected_lower == p2) or \
               (intended_lower == p2 and detected_lower == p1):
                return True, confidence
        
        return False, 0.0
    
    def validate_panel_pose(self, image_path: str, scene_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a panel's pose matches the intended pose.
        
        Args:
            image_path: Path to the generated panel image
            scene_metadata: Scene metadata containing pose information
            
        Returns:
            Validation result dictionary
        """
        # Extract intended pose
        intended_pose = self.extract_intended_pose(scene_metadata)
        
        # Detect visual pose
        detected_pose, detection_confidence = self.detect_visual_pose(image_path)
        
        # Check match
        is_match, match_confidence = self.match_pose(intended_pose, detected_pose)
        
        # Determine overall status
        overall_confidence = (detection_confidence + match_confidence) / 2
        status = "✔️" if is_match and overall_confidence >= 0.7 else "❌"
        
        return {
            "intended_pose": intended_pose,
            "detected_pose": detected_pose,
            "pose_confidence": detection_confidence,
            "match_confidence": match_confidence,
            "overall_confidence": overall_confidence,
            "is_match": is_match,
            "status": status
        }


if __name__ == "__main__":
    # Test the pose matcher
    matcher = PoseMatcher()
    
    # Test with sample metadata
    test_metadata = {
        "description": "Character is kneeling on the ground",
        "action": "kneeling in prayer"
    }
    
    intended = matcher.extract_intended_pose(test_metadata)
    print(f"Intended pose: {intended}")
    
    # Test pose matching
    match_result = matcher.match_pose("kneeling", "sitting")
    print(f"Match result: {match_result}")
