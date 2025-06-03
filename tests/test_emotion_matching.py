#!/usr/bin/env python3
"""
Unit Tests for Emotion Matching

Tests the emotion matcher functionality for Phase 17.
"""

import unittest
import sys
import tempfile
import cv2
import numpy as np
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.emotion_matcher import EmotionMatcher


class TestEmotionMatcher(unittest.TestCase):
    """Test cases for EmotionMatcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = EmotionMatcher()
        
    def test_extract_intended_emotion_from_explicit(self):
        """Test extracting emotion from explicit metadata."""
        metadata = {"emotion": "happy"}
        result = self.matcher.extract_intended_emotion(metadata)
        self.assertEqual(result, "happy")
        
    def test_extract_intended_emotion_from_dialogue(self):
        """Test extracting emotion from dialogue."""
        metadata = {"dialogue": "I'm so excited and happy!"}
        result = self.matcher.extract_intended_emotion(metadata)
        self.assertEqual(result, "happy")
        
    def test_extract_intended_emotion_from_description(self):
        """Test extracting emotion from description."""
        metadata = {"description": "The character looks very sad and depressed"}
        result = self.matcher.extract_intended_emotion(metadata)
        self.assertEqual(result, "sad")
        
    def test_extract_intended_emotion_default(self):
        """Test default emotion when no clear emotion found."""
        metadata = {"description": "A character in a room"}
        result = self.matcher.extract_intended_emotion(metadata)
        self.assertEqual(result, "neutral")
        
    def test_match_emotion_direct(self):
        """Test direct emotion matching."""
        is_match, confidence = self.matcher.match_emotion("happy", "happy")
        self.assertTrue(is_match)
        self.assertEqual(confidence, 1.0)
        
    def test_match_emotion_similar(self):
        """Test similar emotion matching."""
        is_match, confidence = self.matcher.match_emotion("happy", "joy")
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.7)
        
    def test_match_emotion_related(self):
        """Test related emotion matching."""
        is_match, confidence = self.matcher.match_emotion("happy", "excited")
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.6)
        
    def test_match_emotion_no_match(self):
        """Test non-matching emotions."""
        is_match, confidence = self.matcher.match_emotion("happy", "angry")
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        
    def test_detect_visual_emotion_no_image(self):
        """Test emotion detection with non-existent image."""
        result = self.matcher.detect_visual_emotion("nonexistent.jpg")
        emotion, confidence = result
        self.assertEqual(emotion, "neutral")
        self.assertEqual(confidence, 0.0)
        
    def test_detect_visual_emotion_with_dummy_image(self):
        """Test emotion detection with a dummy image."""
        # Create a temporary dummy image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a simple test image
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Gray image
            cv2.imwrite(tmp_file.name, test_image)
            
            # Test emotion detection
            emotion, confidence = self.matcher.detect_visual_emotion(tmp_file.name)
            
            # Should return some emotion and confidence
            self.assertIsInstance(emotion, str)
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_validate_panel_emotion_complete(self):
        """Test complete panel emotion validation."""
        # Create a temporary dummy image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a bright, colorful test image (should be detected as happy)
            test_image = np.ones((100, 100, 3), dtype=np.uint8)
            test_image[:, :, 0] = 255  # Blue channel
            test_image[:, :, 1] = 255  # Green channel  
            test_image[:, :, 2] = 255  # Red channel (bright white)
            cv2.imwrite(tmp_file.name, test_image)
            
            # Test metadata
            metadata = {
                "dialogue": "I'm so happy!",
                "description": "Character smiling brightly"
            }
            
            # Validate
            result = self.matcher.validate_panel_emotion(tmp_file.name, metadata)
            
            # Check result structure
            self.assertIn("intended_emotion", result)
            self.assertIn("detected_emotion", result)
            self.assertIn("emotion_confidence", result)
            self.assertIn("match_confidence", result)
            self.assertIn("overall_confidence", result)
            self.assertIn("is_match", result)
            self.assertIn("status", result)
            
            # Check types
            self.assertIsInstance(result["intended_emotion"], str)
            self.assertIsInstance(result["detected_emotion"], str)
            self.assertIsInstance(result["emotion_confidence"], float)
            self.assertIsInstance(result["match_confidence"], float)
            self.assertIsInstance(result["overall_confidence"], float)
            self.assertIsInstance(result["is_match"], bool)
            self.assertIn(result["status"], ["✔️", "❌"])
            
            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_emotion_mappings_coverage(self):
        """Test that emotion mappings cover expected emotions."""
        expected_emotions = ["happy", "sad", "angry", "scared", "surprised", "neutral"]
        
        for emotion in expected_emotions:
            self.assertIn(emotion, self.matcher.emotion_mappings)
            self.assertIsInstance(self.matcher.emotion_mappings[emotion], list)
            self.assertGreater(len(self.matcher.emotion_mappings[emotion]), 0)
    
    def test_analyze_image_emotion_bright_image(self):
        """Test emotion analysis on bright image."""
        # Create bright image
        bright_image = np.ones((100, 100, 3), dtype=np.uint8) * 200
        faces = np.array([[10, 10, 50, 50]])  # Dummy face detection
        
        emotion, confidence = self.matcher._analyze_image_emotion(bright_image, faces)
        
        # Should detect positive emotion for bright image
        self.assertIn(emotion, ["happy", "neutral"])
        self.assertGreater(confidence, 0.0)
    
    def test_analyze_image_emotion_dark_image(self):
        """Test emotion analysis on dark image."""
        # Create dark image
        dark_image = np.ones((100, 100, 3), dtype=np.uint8) * 50
        faces = np.array([[10, 10, 50, 50]])  # Dummy face detection
        
        emotion, confidence = self.matcher._analyze_image_emotion(dark_image, faces)
        
        # Should detect negative emotion for dark image
        self.assertIn(emotion, ["sad", "neutral"])
        self.assertGreater(confidence, 0.0)


class TestEmotionMatcherIntegration(unittest.TestCase):
    """Integration tests for emotion matcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = EmotionMatcher()
    
    def test_full_workflow_happy_scene(self):
        """Test full workflow with happy scene."""
        # Create test image and metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Bright, saturated image
            test_image = np.ones((100, 100, 3), dtype=np.uint8)
            test_image[:, :] = [255, 255, 255]  # Bright white
            cv2.imwrite(tmp_file.name, test_image)
            
            metadata = {
                "emotion": "happy",
                "dialogue": "This is wonderful!",
                "description": "Character jumping with joy"
            }
            
            result = self.matcher.validate_panel_emotion(tmp_file.name, metadata)
            
            # Should extract happy emotion
            self.assertEqual(result["intended_emotion"], "happy")
            
            # Should have reasonable confidence
            self.assertGreater(result["overall_confidence"], 0.1)

            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_full_workflow_sad_scene(self):
        """Test full workflow with sad scene."""
        # Create test image and metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Dark image
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 30
            cv2.imwrite(tmp_file.name, test_image)
            
            metadata = {
                "emotion": "sad",
                "dialogue": "I feel terrible...",
                "description": "Character crying alone"
            }
            
            result = self.matcher.validate_panel_emotion(tmp_file.name, metadata)
            
            # Should extract sad emotion
            self.assertEqual(result["intended_emotion"], "sad")
            
            # Should have reasonable confidence
            self.assertGreater(result["overall_confidence"], 0.1)

            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV


if __name__ == "__main__":
    unittest.main()
