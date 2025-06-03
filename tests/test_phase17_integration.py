#!/usr/bin/env python3
"""
Phase 17 Integration Tests

Tests the complete emotion and pose validation pipeline.
"""

import unittest
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.run_emotion_pose_validation import EmotionPoseValidator, create_test_scenes
from core.panel_generator import EnhancedPanelGenerator
from core.emotion_matcher import EmotionMatcher
from core.pose_matcher import PoseMatcher


class TestPhase17Integration(unittest.TestCase):
    """Integration tests for Phase 17 emotion and pose validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.validator = EmotionPoseValidator(str(self.temp_dir))
        
    def tearDown(self):
        """Clean up test fixtures."""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
    
    def test_create_test_scenes(self):
        """Test that test scenes are properly created."""
        scenes = create_test_scenes()
        
        # Should have multiple test scenes
        self.assertGreater(len(scenes), 0)
        
        # Each scene should have required fields
        for scene in scenes:
            self.assertIn("description", scene)
            self.assertIn("emotion", scene)
            self.assertIn("pose", scene)
            self.assertIn("dialogue", scene)
            
            # Fields should be non-empty strings
            self.assertIsInstance(scene["description"], str)
            self.assertIsInstance(scene["emotion"], str)
            self.assertIsInstance(scene["pose"], str)
            self.assertIsInstance(scene["dialogue"], str)
            
            self.assertGreater(len(scene["description"]), 0)
            self.assertGreater(len(scene["emotion"]), 0)
            self.assertGreater(len(scene["pose"]), 0)
            self.assertGreater(len(scene["dialogue"]), 0)
    
    @patch('core.panel_generator.EnhancedPanelGenerator.generate_panel')
    def test_emotion_pose_validator_with_mock_generation(self, mock_generate):
        """Test emotion pose validator with mocked panel generation."""
        # Mock successful panel generation
        mock_generate.return_value = True
        
        # Create a simple test scene
        test_scenes = [{
            "description": "happy character jumping",
            "emotion": "happy",
            "pose": "jumping",
            "dialogue": "I'm so excited!"
        }]
        
        # Mock the validation methods to return predictable results
        with patch.object(self.validator.panel_generator, 'validate_panel_emotion_pose') as mock_validate:
            mock_validate.return_value = {
                "emotion_validation": {
                    "intended_emotion": "happy",
                    "detected_emotion": "happy",
                    "emotion_confidence": 0.8,
                    "match_confidence": 1.0,
                    "overall_confidence": 0.9,
                    "is_match": True,
                    "status": "✔️"
                },
                "pose_validation": {
                    "intended_pose": "jumping",
                    "detected_pose": "jumping",
                    "pose_confidence": 0.7,
                    "match_confidence": 1.0,
                    "overall_confidence": 0.85,
                    "is_match": True,
                    "status": "✔️"
                },
                "overall_status": "✔️"
            }
            
            # Run validation
            results = self.validator.run_validation(test_scenes, "test_run")
            
            # Check results structure
            self.assertIn("run_id", results)
            self.assertIn("summary", results)
            self.assertIn("panel_results", results)
            
            # Check summary statistics
            summary = results["summary"]
            self.assertEqual(summary["total_panels"], 1)
            self.assertEqual(summary["passed_panels"], 1)
            self.assertEqual(summary["failed_panels"], 0)
            self.assertEqual(summary["overall_pass_rate"], 1.0)
            
            # Check that files were created
            run_dir = self.temp_dir / "test_run"
            self.assertTrue(run_dir.exists())
            self.assertTrue((run_dir / "validation").exists())
            self.assertTrue((run_dir / "validation" / "emotion_pose_report.json").exists())
            self.assertTrue((run_dir / "validation" / "emotion_pose_report.md").exists())
    
    def test_enhanced_panel_generator_validation_method(self):
        """Test that enhanced panel generator has validation method."""
        generator = EnhancedPanelGenerator()
        
        # Should have the validation method
        self.assertTrue(hasattr(generator, 'validate_panel_emotion_pose'))
        self.assertTrue(callable(getattr(generator, 'validate_panel_emotion_pose')))
        
        # Should have emotion and pose matchers
        self.assertTrue(hasattr(generator, 'emotion_matcher'))
        self.assertTrue(hasattr(generator, 'pose_matcher'))
        self.assertIsInstance(generator.emotion_matcher, EmotionMatcher)
        self.assertIsInstance(generator.pose_matcher, PoseMatcher)
    
    def test_emotion_matcher_initialization(self):
        """Test emotion matcher initialization."""
        matcher = EmotionMatcher()
        
        # Should have required attributes
        self.assertTrue(hasattr(matcher, 'emotion_mappings'))
        self.assertTrue(hasattr(matcher, 'emotion_extractor'))
        
        # Should have required methods
        self.assertTrue(hasattr(matcher, 'extract_intended_emotion'))
        self.assertTrue(hasattr(matcher, 'detect_visual_emotion'))
        self.assertTrue(hasattr(matcher, 'match_emotion'))
        self.assertTrue(hasattr(matcher, 'validate_panel_emotion'))
    
    def test_pose_matcher_initialization(self):
        """Test pose matcher initialization."""
        matcher = PoseMatcher()
        
        # Should have required attributes
        self.assertTrue(hasattr(matcher, 'pose_keywords'))
        self.assertTrue(hasattr(matcher, 'pose_similarities'))
        
        # Should have required methods
        self.assertTrue(hasattr(matcher, 'extract_intended_pose'))
        self.assertTrue(hasattr(matcher, 'detect_visual_pose'))
        self.assertTrue(hasattr(matcher, 'match_pose'))
        self.assertTrue(hasattr(matcher, 'validate_panel_pose'))
    
    @patch('core.panel_generator.EnhancedPanelGenerator.generate_panel')
    def test_validation_with_multiple_scenes(self, mock_generate):
        """Test validation with multiple test scenes."""
        # Mock successful panel generation
        mock_generate.return_value = True
        
        # Use the standard test scenes
        test_scenes = create_test_scenes()
        
        # Mock validation to return mixed results
        def mock_validation_side_effect(image_path, _scene_metadata):
            # Return pass for first 3 scenes, fail for others
            scene_index = int(Path(image_path).stem.split('_')[1]) - 1
            if scene_index < 3:
                return {
                    "emotion_validation": {
                        "intended_emotion": "happy",
                        "detected_emotion": "happy",
                        "emotion_confidence": 0.8,
                        "status": "✔️"
                    },
                    "pose_validation": {
                        "intended_pose": "standing",
                        "detected_pose": "standing",
                        "pose_confidence": 0.7,
                        "status": "✔️"
                    },
                    "overall_status": "✔️"
                }
            else:
                return {
                    "emotion_validation": {
                        "intended_emotion": "sad",
                        "detected_emotion": "happy",
                        "emotion_confidence": 0.6,
                        "status": "❌"
                    },
                    "pose_validation": {
                        "intended_pose": "sitting",
                        "detected_pose": "sitting",
                        "pose_confidence": 0.8,
                        "status": "✔️"
                    },
                    "overall_status": "❌"
                }
        
        with patch.object(self.validator.panel_generator, 'validate_panel_emotion_pose', 
                         side_effect=mock_validation_side_effect):
            
            # Run validation
            results = self.validator.run_validation(test_scenes, "multi_test")
            
            # Check that we processed all scenes
            summary = results["summary"]
            self.assertEqual(summary["total_panels"], len(test_scenes))
            self.assertEqual(summary["passed_panels"], 3)
            self.assertEqual(summary["failed_panels"], len(test_scenes) - 3)
            
            # Check pass rate calculation
            expected_pass_rate = 3 / len(test_scenes)
            self.assertAlmostEqual(summary["overall_pass_rate"], expected_pass_rate, places=2)
    
    def test_validation_report_generation(self):
        """Test that validation reports are properly generated."""
        # Create mock results data
        results_data = {
            "run_id": "test_report",
            "timestamp": "2024-01-01T12:00:00",
            "summary": {
                "total_panels": 2,
                "passed_panels": 1,
                "failed_panels": 1,
                "overall_pass_rate": 0.5,
                "emotion_pass_rate": 0.5,
                "pose_pass_rate": 1.0
            },
            "panel_results": {
                "panel_001.png": {
                    "generation_success": True,
                    "emotion_validation": {
                        "intended_emotion": "happy",
                        "detected_emotion": "happy",
                        "emotion_confidence": 0.8,
                        "status": "✔️"
                    },
                    "pose_validation": {
                        "intended_pose": "jumping",
                        "detected_pose": "jumping",
                        "pose_confidence": 0.7,
                        "status": "✔️"
                    },
                    "overall_status": "✔️"
                },
                "panel_002.png": {
                    "generation_success": True,
                    "emotion_validation": {
                        "intended_emotion": "sad",
                        "detected_emotion": "happy",
                        "emotion_confidence": 0.6,
                        "status": "❌"
                    },
                    "pose_validation": {
                        "intended_pose": "sitting",
                        "detected_pose": "sitting",
                        "pose_confidence": 0.8,
                        "status": "✔️"
                    },
                    "overall_status": "❌"
                }
            }
        }
        
        # Create validation directory
        validation_dir = self.temp_dir / "validation"
        validation_dir.mkdir(parents=True)
        
        # Generate markdown report
        md_path = validation_dir / "test_report.md"
        self.validator._save_markdown_report(results_data, md_path)
        
        # Check that report was created
        self.assertTrue(md_path.exists())
        
        # Check report content
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Should contain key information
        self.assertIn("Emotion & Pose Validation Report", content)
        self.assertIn("test_report", content)
        self.assertIn("**Total Panels**: 2", content)
        self.assertIn("panel_001.png", content)
        self.assertIn("panel_002.png", content)
        self.assertIn("✔️", content)
        self.assertIn("❌", content)


class TestPhase17Components(unittest.TestCase):
    """Test individual Phase 17 components."""
    
    def test_emotion_pose_validation_integration(self):
        """Test integration between emotion and pose validation."""
        generator = EnhancedPanelGenerator()
        
        # Create test metadata
        metadata = {
            "description": "happy character jumping with joy",
            "emotion": "happy",
            "pose": "jumping",
            "dialogue": "I'm so excited!"
        }
        
        # Create a dummy image file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
            import cv2
            import numpy as np
            
            # Create a simple test image
            test_image = np.ones((100, 100, 3), dtype=np.uint8) * 128
            cv2.imwrite(tmp_file.name, test_image)
            
            # Test validation
            result = generator.validate_panel_emotion_pose(tmp_file.name, metadata)
            
            # Check result structure
            self.assertIn("emotion_validation", result)
            self.assertIn("pose_validation", result)
            self.assertIn("overall_status", result)
            
            # Check that both validations ran
            emotion_val = result["emotion_validation"]
            pose_val = result["pose_validation"]
            
            self.assertIn("intended_emotion", emotion_val)
            self.assertIn("detected_emotion", emotion_val)
            self.assertIn("status", emotion_val)
            
            self.assertIn("intended_pose", pose_val)
            self.assertIn("detected_pose", pose_val)
            self.assertIn("status", pose_val)
            
            # Overall status should be based on both validations
            expected_status = "✔️" if (emotion_val["status"] == "✔️" and pose_val["status"] == "✔️") else "❌"
            self.assertEqual(result["overall_status"], expected_status)
            
            # Clean up
            try:
                Path(tmp_file.name).unlink()
            except PermissionError:
                pass  # File may still be in use by OpenCV


if __name__ == "__main__":
    unittest.main()
