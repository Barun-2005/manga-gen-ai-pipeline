#!/usr/bin/env python3
"""
Emotion Matcher Module

Validates that generated manga panels match the intended emotional state
by comparing intended emotions with detected emotions from images.
"""

import cv2
import json
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.emotion_extractor import EmotionExtractor


class EmotionMatcher:
    """Matches intended emotions with detected emotions from generated images."""
    
    def __init__(self):
        """Initialize the emotion matcher."""
        self.emotion_extractor = EmotionExtractor()
        
        # Emotion mapping for visual detection
        self.emotion_mappings = {
            "happy": ["happy", "joy", "excited", "cheerful"],
            "sad": ["sad", "melancholy", "depressed", "sorrowful"],
            "angry": ["angry", "furious", "mad", "irritated"],
            "scared": ["scared", "afraid", "terrified", "anxious"],
            "surprised": ["surprised", "shocked", "amazed", "astonished"],
            "neutral": ["neutral", "calm", "composed", "stoic"],
            "disgusted": ["disgusted", "revolted", "repulsed"],
            "contempt": ["contempt", "disdain", "scornful"]
        }
        
        # Load face cascade for emotion detection
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            print(f"Warning: Could not load face cascade: {e}")
            self.face_cascade = None
    
    def extract_intended_emotion(self, scene_metadata: Dict[str, Any]) -> str:
        """
        Extract intended emotion from scene metadata or dialogue.
        
        Args:
            scene_metadata: Scene metadata containing dialogue and emotion info
            
        Returns:
            Intended emotion label
        """
        # Check if emotion is explicitly provided
        if "emotion" in scene_metadata:
            return scene_metadata["emotion"].lower()
        
        # Extract from dialogue if available
        if "dialogue" in scene_metadata:
            dialogue = scene_metadata["dialogue"]
            emotion_result = self.emotion_extractor.extract_dialogue_emotion(dialogue)
            return emotion_result.get("emotion", "neutral")
        
        # Extract from scene description
        if "description" in scene_metadata:
            description = scene_metadata["description"]
            emotion_result = self.emotion_extractor.extract_dialogue_emotion(description)
            return emotion_result.get("emotion", "neutral")
        
        return "neutral"
    
    def detect_visual_emotion(self, image_path: str) -> Tuple[str, float]:
        """
        Detect emotion from image using basic facial analysis.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Tuple of (detected_emotion, confidence_score)
        """
        try:
            # Load image
            image = cv2.imread(image_path)
            if image is None:
                return "neutral", 0.0
            
            # Convert to grayscale for face detection
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Detect faces
            if self.face_cascade is None:
                return "neutral", 0.5
            
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            if len(faces) == 0:
                return "neutral", 0.3
            
            # For now, use basic heuristics based on image properties
            # In a production system, you'd use a trained emotion classifier
            emotion, confidence = self._analyze_image_emotion(image, faces)
            
            return emotion, confidence
            
        except Exception as e:
            print(f"Error detecting emotion in {image_path}: {e}")
            return "neutral", 0.0
    
    def _analyze_image_emotion(self, image: np.ndarray, faces: np.ndarray) -> Tuple[str, float]:
        """
        Analyze image for emotional content using basic heuristics.
        
        Args:
            image: OpenCV image array
            faces: Detected face regions
            
        Returns:
            Tuple of (emotion, confidence)
        """
        # Basic heuristic analysis
        # In production, replace with trained emotion classifier
        
        # Analyze color distribution
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Calculate brightness and saturation
        brightness = np.mean(hsv[:, :, 2])
        saturation = np.mean(hsv[:, :, 1])
        
        # Simple heuristics (replace with ML model in production)
        if brightness < 80:
            return "sad", 0.6
        elif brightness > 180 and saturation > 100:
            return "happy", 0.7
        elif saturation < 50:
            return "neutral", 0.8
        else:
            return "neutral", 0.5
    
    def match_emotion(self, intended_emotion: str, detected_emotion: str) -> Tuple[bool, float]:
        """
        Check if detected emotion matches intended emotion.
        
        Args:
            intended_emotion: The emotion that was intended
            detected_emotion: The emotion detected from the image
            
        Returns:
            Tuple of (is_match, confidence_score)
        """
        intended_lower = intended_emotion.lower()
        detected_lower = detected_emotion.lower()
        
        # Direct match
        if intended_lower == detected_lower:
            return True, 1.0
        
        # Check emotion mappings for similar emotions
        for base_emotion, variants in self.emotion_mappings.items():
            if intended_lower in variants and detected_lower in variants:
                return True, 0.8
        
        # Partial matches for related emotions
        related_matches = {
            ("happy", "excited"): 0.7,
            ("sad", "melancholy"): 0.7,
            ("angry", "frustrated"): 0.7,
            ("scared", "anxious"): 0.7,
            ("surprised", "shocked"): 0.8
        }
        
        for (e1, e2), confidence in related_matches.items():
            if (intended_lower == e1 and detected_lower == e2) or \
               (intended_lower == e2 and detected_lower == e1):
                return True, confidence
        
        return False, 0.0
    
    def validate_panel_emotion(self, image_path: str, scene_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that a panel's emotion matches the intended emotion.
        
        Args:
            image_path: Path to the generated panel image
            scene_metadata: Scene metadata containing emotion information
            
        Returns:
            Validation result dictionary
        """
        # Extract intended emotion
        intended_emotion = self.extract_intended_emotion(scene_metadata)
        
        # Detect visual emotion
        detected_emotion, detection_confidence = self.detect_visual_emotion(image_path)
        
        # Check match
        is_match, match_confidence = self.match_emotion(intended_emotion, detected_emotion)
        
        # Determine overall status
        overall_confidence = (detection_confidence + match_confidence) / 2
        status = "✔️" if is_match and overall_confidence >= 0.7 else "❌"
        
        return {
            "intended_emotion": intended_emotion,
            "detected_emotion": detected_emotion,
            "emotion_confidence": detection_confidence,
            "match_confidence": match_confidence,
            "overall_confidence": overall_confidence,
            "is_match": is_match,
            "status": status
        }


if __name__ == "__main__":
    # Test the emotion matcher
    matcher = EmotionMatcher()
    
    # Test with sample metadata
    test_metadata = {
        "dialogue": "I'm so happy to see you!",
        "description": "Character smiling brightly"
    }
    
    intended = matcher.extract_intended_emotion(test_metadata)
    print(f"Intended emotion: {intended}")
    
    # Test emotion matching
    match_result = matcher.match_emotion("happy", "joy")
    print(f"Match result: {match_result}")
