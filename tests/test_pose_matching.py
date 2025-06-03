#!/usr/bin/env python3
"""
Unit Tests for Pose Matching

Tests the pose matcher functionality for Phase 17.
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

from core.pose_matcher import PoseMatcher


class TestPoseMatcher(unittest.TestCase):
    """Test cases for PoseMatcher class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = PoseMatcher()
        
    def test_extract_intended_pose_from_explicit(self):
        """Test extracting pose from explicit metadata."""
        metadata = {"pose": "standing"}
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "standing")
        
    def test_extract_intended_pose_from_description(self):
        """Test extracting pose from description."""
        metadata = {"description": "The character is kneeling on the ground"}
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "kneeling")
        
    def test_extract_intended_pose_from_action(self):
        """Test extracting pose from action field."""
        metadata = {"action": "running through the forest"}
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "running")
        
    def test_extract_intended_pose_from_dialogue(self):
        """Test extracting pose from dialogue."""
        metadata = {"dialogue": "I'm sitting here waiting for you"}
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "sitting")
        
    def test_extract_intended_pose_default(self):
        """Test default pose when no clear pose found."""
        metadata = {"description": "A character in a room"}
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "standing")
        
    def test_match_pose_direct(self):
        """Test direct pose matching."""
        is_match, confidence = self.matcher.match_pose("standing", "standing")
        self.assertTrue(is_match)
        self.assertEqual(confidence, 1.0)
        
    def test_match_pose_similar(self):
        """Test similar pose matching."""
        is_match, confidence = self.matcher.match_pose("standing", "upright")
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.7)
        
    def test_match_pose_related(self):
        """Test related pose matching."""
        is_match, confidence = self.matcher.match_pose("standing", "walking")
        self.assertTrue(is_match)
        self.assertGreater(confidence, 0.5)
        
    def test_match_pose_no_match(self):
        """Test non-matching poses."""
        is_match, confidence = self.matcher.match_pose("standing", "lying")
        self.assertFalse(is_match)
        self.assertEqual(confidence, 0.0)
        
    def test_detect_visual_pose_no_image(self):
        """Test pose detection with non-existent image."""
        result = self.matcher.detect_visual_pose("nonexistent.jpg")
        pose, confidence = result
        self.assertEqual(pose, "standing")
        self.assertEqual(confidence, 0.0)
        
    def test_detect_visual_pose_with_dummy_image(self):
        """Test pose detection with a dummy image."""
        # Create a temporary dummy image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a simple test image
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128  # Gray image
            cv2.imwrite(tmp_file.name, test_image)
            
            # Test pose detection
            pose, confidence = self.matcher.detect_visual_pose(tmp_file.name)
            
            # Should return some pose and confidence
            self.assertIsInstance(pose, str)
            self.assertIsInstance(confidence, float)
            self.assertGreaterEqual(confidence, 0.0)
            self.assertLessEqual(confidence, 1.0)
            
            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_analyze_image_pose_tall_figure(self):
        """Test pose analysis on tall figure (likely standing)."""
        # Create tall, narrow image (standing pose)
        tall_image = np.ones((200, 50, 3), dtype=np.uint8) * 128
        keypoint_count = 10
        
        pose, confidence = self.matcher._analyze_image_pose(tall_image, keypoint_count)
        
        # Should detect standing or walking
        self.assertIn(pose, ["standing", "walking"])
        self.assertGreater(confidence, 0.0)
    
    def test_analyze_image_pose_wide_figure(self):
        """Test pose analysis on wide figure (likely lying)."""
        # Create wide, short image (lying pose)
        wide_image = np.ones((50, 200, 3), dtype=np.uint8) * 128
        keypoint_count = 5

        pose, confidence = self.matcher._analyze_image_pose(wide_image, keypoint_count)

        # Should detect some pose with reasonable confidence
        self.assertIsInstance(pose, str)
        self.assertGreater(confidence, 0.0)
    
    def test_validate_panel_pose_complete(self):
        """Test complete panel pose validation."""
        # Create a temporary dummy image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Create a tall test image (standing pose)
            test_image = np.ones((200, 80, 3), dtype=np.uint8) * 128
            cv2.imwrite(tmp_file.name, test_image)
            
            # Test metadata
            metadata = {
                "description": "Character standing upright",
                "action": "standing confidently"
            }
            
            # Validate
            result = self.matcher.validate_panel_pose(tmp_file.name, metadata)
            
            # Check result structure
            self.assertIn("intended_pose", result)
            self.assertIn("detected_pose", result)
            self.assertIn("pose_confidence", result)
            self.assertIn("match_confidence", result)
            self.assertIn("overall_confidence", result)
            self.assertIn("is_match", result)
            self.assertIn("status", result)
            
            # Check types
            self.assertIsInstance(result["intended_pose"], str)
            self.assertIsInstance(result["detected_pose"], str)
            self.assertIsInstance(result["pose_confidence"], float)
            self.assertIsInstance(result["match_confidence"], float)
            self.assertIsInstance(result["overall_confidence"], float)
            self.assertIsInstance(result["is_match"], bool)
            self.assertIn(result["status"], ["✔️", "❌"])
            
            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_pose_keywords_coverage(self):
        """Test that pose keywords cover expected poses."""
        expected_poses = ["standing", "sitting", "kneeling", "lying", "walking", "running", "jumping"]
        
        for pose in expected_poses:
            self.assertIn(pose, self.matcher.pose_keywords)
            self.assertIsInstance(self.matcher.pose_keywords[pose], list)
            self.assertGreater(len(self.matcher.pose_keywords[pose]), 0)
    
    def test_pose_similarities_coverage(self):
        """Test that pose similarities are properly defined."""
        for pose, similar_list in self.matcher.pose_similarities.items():
            self.assertIsInstance(similar_list, list)
            self.assertGreater(len(similar_list), 0)
            
            # Each similar pose should be a string
            for similar_pose in similar_list:
                self.assertIsInstance(similar_pose, str)


class TestPoseMatcherIntegration(unittest.TestCase):
    """Integration tests for pose matcher."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.matcher = PoseMatcher()
    
    def test_full_workflow_standing_pose(self):
        """Test full workflow with standing pose."""
        # Create test image and metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Tall, narrow image (standing)
            test_image = np.ones((200, 80, 3), dtype=np.uint8) * 128
            cv2.imwrite(tmp_file.name, test_image)
            
            metadata = {
                "pose": "standing",
                "description": "Character standing upright",
                "action": "standing confidently"
            }
            
            result = self.matcher.validate_panel_pose(tmp_file.name, metadata)
            
            # Should extract standing pose
            self.assertEqual(result["intended_pose"], "standing")
            
            # Should have reasonable confidence
            self.assertGreater(result["overall_confidence"], 0.1)

            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_full_workflow_sitting_pose(self):
        """Test full workflow with sitting pose."""
        # Create test image and metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Square-ish image (sitting)
            test_image = np.ones((120, 100, 3), dtype=np.uint8) * 128
            cv2.imwrite(tmp_file.name, test_image)
            
            metadata = {
                "pose": "sitting",
                "description": "Character sitting on a chair",
                "dialogue": "I'm sitting here waiting"
            }
            
            result = self.matcher.validate_panel_pose(tmp_file.name, metadata)
            
            # Should extract sitting pose
            self.assertEqual(result["intended_pose"], "sitting")
            
            # Should have reasonable confidence
            self.assertGreater(result["overall_confidence"], 0.1)

            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_full_workflow_lying_pose(self):
        """Test full workflow with lying pose."""
        # Create test image and metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            # Wide, short image (lying)
            test_image = np.ones((60, 180, 3), dtype=np.uint8) * 128
            cv2.imwrite(tmp_file.name, test_image)
            
            metadata = {
                "pose": "lying",
                "description": "Character lying down on the ground",
                "action": "resting horizontally"
            }
            
            result = self.matcher.validate_panel_pose(tmp_file.name, metadata)
            
            # Should extract lying pose
            self.assertEqual(result["intended_pose"], "lying")
            
            # Should have reasonable confidence
            self.assertGreater(result["overall_confidence"], 0.1)

            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV
    
    def test_keyword_extraction_multiple_sources(self):
        """Test pose extraction from multiple metadata sources."""
        metadata = {
            "description": "Character walking through the forest",
            "action": "moving forward",
            "dialogue": "I'm walking to the temple"
        }
        
        result = self.matcher.extract_intended_pose(metadata)
        self.assertEqual(result, "walking")


if __name__ == "__main__":
    unittest.main()
