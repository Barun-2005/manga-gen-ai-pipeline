#!/usr/bin/env python3
"""
Local Visual Flow Checker
Phase 13: Enhanced Prompt Testing + Local Visual Flow Validator

This module provides local OpenCV-based visual flow analysis to reduce
dependency on VLM models for basic coherence checks.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# Optional imports with fallbacks
try:
    import imagehash
    from PIL import Image
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    print("Warning: imagehash not available. Perceptual hash similarity will be disabled.")

try:
    from skimage.metrics import structural_similarity as ssim
    SSIM_AVAILABLE = True
except ImportError:
    SSIM_AVAILABLE = False
    print("Warning: scikit-image not available. SSIM calculation will use fallback method.")


class LocalFlowChecker:
    """Local OpenCV-based visual flow analysis for manga panels."""
    
    def __init__(self):
        """Initialize the local flow checker."""
        self.confidence_threshold = 0.6
        self.similarity_threshold = 0.7
        
        # Initialize feature detectors
        self.sift = cv2.SIFT_create()
        self.orb = cv2.ORB_create()
        
        # Initialize face detector
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        
    def load_image(self, image_path: str) -> Optional[np.ndarray]:
        """Load and preprocess image for analysis."""
        try:
            image = cv2.imread(image_path)
            if image is None:
                print(f"   ⚠️  Could not load image: {image_path}")
                return None
            return image
        except Exception as e:
            print(f"   ❌ Error loading image {image_path}: {e}")
            return None
    
    def calculate_structural_similarity(self, img1: np.ndarray, img2: np.ndarray) -> float:
        """Calculate SSIM between two images."""
        try:
            # Convert to grayscale
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # Resize to same dimensions
            h, w = min(gray1.shape[0], gray2.shape[0]), min(gray1.shape[1], gray2.shape[1])
            gray1 = cv2.resize(gray1, (w, h))
            gray2 = cv2.resize(gray2, (w, h))

            # Calculate SSIM if available
            if SSIM_AVAILABLE:
                from skimage.metrics import structural_similarity as ssim
                similarity = ssim(gray1, gray2)
                return float(similarity)
            else:
                # Fallback to normalized cross-correlation
                correlation = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]
                return float(correlation)

        except Exception as e:
            print(f"   ⚠️  SSIM calculation failed: {e}")
            # Final fallback to simple correlation
            try:
                gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
                gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
                h, w = min(gray1.shape[0], gray2.shape[0]), min(gray1.shape[1], gray2.shape[1])
                gray1 = cv2.resize(gray1, (w, h))
                gray2 = cv2.resize(gray2, (w, h))
                correlation = cv2.matchTemplate(gray1, gray2, cv2.TM_CCOEFF_NORMED)[0][0]
                return float(correlation)
            except:
                return 0.5  # Default neutral similarity
    
    def calculate_perceptual_hash_similarity(self, img1_path: str, img2_path: str) -> float:
        """Calculate perceptual hash similarity between images."""
        if not IMAGEHASH_AVAILABLE:
            return 0.5  # Default similarity when imagehash not available

        try:
            # Load images with PIL for imagehash
            pil_img1 = Image.open(img1_path)
            pil_img2 = Image.open(img2_path)

            # Calculate perceptual hashes
            hash1 = imagehash.phash(pil_img1)
            hash2 = imagehash.phash(pil_img2)

            # Calculate similarity (lower hash difference = higher similarity)
            hash_diff = hash1 - hash2
            max_diff = len(hash1.hash) ** 2  # Maximum possible difference
            similarity = 1.0 - (hash_diff / max_diff)

            return float(similarity)

        except Exception as e:
            print(f"   ⚠️  Perceptual hash calculation failed: {e}")
            return 0.5
    
    def detect_scene_change(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Detect abrupt scene/background changes between panels."""
        
        # Calculate structural similarity
        ssim_score = self.calculate_structural_similarity(img1, img2)
        
        # Analyze color histograms
        hist1 = cv2.calcHist([img1], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([img2], [0, 1, 2], None, [50, 50, 50], [0, 256, 0, 256, 0, 256])
        hist_correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Determine if scene change is abrupt
        is_abrupt_change = ssim_score < 0.3 and hist_correlation < 0.5

        return {
            "ssim_score": float(ssim_score),
            "histogram_correlation": float(hist_correlation),
            "is_abrupt_change": bool(is_abrupt_change),
            "confidence": float(0.8 if ssim_score > 0.1 else 0.6)  # Lower confidence for very different images
        }
    
    def detect_character_presence(self, img: np.ndarray) -> Dict[str, Any]:
        """Detect character presence and basic pose information."""
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Face detection
        faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
        
        # Basic character region detection using contours
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by size (potential character regions)
        min_area = img.shape[0] * img.shape[1] * 0.01  # At least 1% of image
        character_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        return {
            "faces_detected": int(len(faces)),
            "face_regions": faces.tolist() if len(faces) > 0 else [],
            "character_regions": int(len(character_contours)),
            "has_character": bool(len(faces) > 0 or len(character_contours) > 0),
            "confidence": float(0.9 if len(faces) > 0 else 0.6)
        }
    
    def analyze_lighting_consistency(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Any]:
        """Analyze lighting consistency between panels."""
        
        # Convert to LAB color space for better lighting analysis
        lab1 = cv2.cvtColor(img1, cv2.COLOR_BGR2LAB)
        lab2 = cv2.cvtColor(img2, cv2.COLOR_BGR2LAB)
        
        # Extract L (lightness) channel
        l1 = lab1[:, :, 0]
        l2 = lab2[:, :, 0]
        
        # Calculate mean brightness
        mean_brightness1 = np.mean(l1)
        mean_brightness2 = np.mean(l2)
        brightness_diff = abs(mean_brightness1 - mean_brightness2)
        
        # Calculate brightness distribution similarity
        hist1 = cv2.calcHist([l1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([l2], [0], None, [256], [0, 256])
        lighting_correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        
        # Determine consistency
        is_consistent = brightness_diff < 30 and lighting_correlation > 0.7

        return {
            "brightness_difference": float(brightness_diff),
            "lighting_correlation": float(lighting_correlation),
            "is_consistent": bool(is_consistent),
            "confidence": float(0.8)
        }
    
    def analyze_panel_pair(self, img1_path: str, img2_path: str) -> Dict[str, Any]:
        """Analyze visual flow between two consecutive panels."""
        
        # Load images
        img1 = self.load_image(img1_path)
        img2 = self.load_image(img2_path)
        
        if img1 is None or img2 is None:
            return {
                "error": "Could not load images",
                "confidence": 0.0,
                "analysis_method": "local_opencv",
                "success": False
            }
        
        # Perform various analyses
        scene_analysis = self.detect_scene_change(img1, img2)
        char1_analysis = self.detect_character_presence(img1)
        char2_analysis = self.detect_character_presence(img2)
        lighting_analysis = self.analyze_lighting_consistency(img1, img2)
        
        # Calculate perceptual similarity
        perceptual_similarity = self.calculate_perceptual_hash_similarity(img1_path, img2_path)
        
        # Determine overall flow quality
        flow_issues = []
        if scene_analysis["is_abrupt_change"]:
            flow_issues.append("abrupt_scene_change")
        
        if char1_analysis["has_character"] != char2_analysis["has_character"]:
            flow_issues.append("character_presence_change")
        
        if not lighting_analysis["is_consistent"]:
            flow_issues.append("lighting_inconsistency")
        
        # Calculate overall confidence
        confidences = [
            scene_analysis["confidence"],
            char1_analysis["confidence"],
            char2_analysis["confidence"],
            lighting_analysis["confidence"]
        ]
        overall_confidence = np.mean(confidences)
        
        return {
            "analysis_method": "local_opencv",
            "success": True,
            "confidence": float(overall_confidence),
            "scene_analysis": scene_analysis,
            "character_analysis": {
                "panel1": char1_analysis,
                "panel2": char2_analysis,
                "presence_consistent": char1_analysis["has_character"] == char2_analysis["has_character"]
            },
            "lighting_analysis": lighting_analysis,
            "perceptual_similarity": float(perceptual_similarity),
            "flow_issues": flow_issues,
            "flow_quality": "good" if len(flow_issues) == 0 else "poor" if len(flow_issues) > 2 else "fair",
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_sequence(self, panel_paths: List[str]) -> Dict[str, Any]:
        """Analyze visual flow across a complete panel sequence."""
        
        print(f"🔍 Analyzing visual flow for {len(panel_paths)} panels using local OpenCV...")
        
        if len(panel_paths) < 2:
            return {
                "error": "Need at least 2 panels for flow analysis",
                "success": False
            }
        
        sequence_analysis = {
            "analysis_method": "local_opencv",
            "success": True,
            "total_panels": len(panel_paths),
            "panel_pairs": [],
            "overall_flow_quality": "unknown",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        # Analyze each consecutive pair
        confidences = []
        flow_qualities = []
        
        for i in range(len(panel_paths) - 1):
            print(f"   📊 Analyzing panels {i+1} → {i+2}")
            
            pair_analysis = self.analyze_panel_pair(panel_paths[i], panel_paths[i+1])
            sequence_analysis["panel_pairs"].append({
                "panel1_index": i,
                "panel2_index": i + 1,
                "panel1_path": panel_paths[i],
                "panel2_path": panel_paths[i+1],
                "analysis": pair_analysis
            })
            
            if pair_analysis.get("success", False):
                confidences.append(pair_analysis["confidence"])
                flow_qualities.append(pair_analysis["flow_quality"])
        
        # Calculate overall metrics
        if confidences:
            sequence_analysis["confidence"] = float(np.mean(confidences))
            
            # Determine overall flow quality
            quality_scores = {"good": 3, "fair": 2, "poor": 1}
            avg_quality_score = np.mean([quality_scores.get(q, 1) for q in flow_qualities])
            
            if avg_quality_score >= 2.5:
                sequence_analysis["overall_flow_quality"] = "good"
            elif avg_quality_score >= 1.5:
                sequence_analysis["overall_flow_quality"] = "fair"
            else:
                sequence_analysis["overall_flow_quality"] = "poor"
        
        print(f"   ✅ Local flow analysis complete")
        print(f"   📊 Overall quality: {sequence_analysis['overall_flow_quality']}")
        print(f"   🎯 Confidence: {sequence_analysis['confidence']:.3f}")
        
        return sequence_analysis


def main():
    """Test the local flow checker."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Local Visual Flow Checker")
    parser.add_argument("--test-dir", type=str, help="Directory containing test panels")
    parser.add_argument("--output", type=str, help="Output file for analysis results")
    
    args = parser.parse_args()
    
    if not args.test_dir:
        print("Local Visual Flow Checker")
        print("Usage: python scripts/local_flow_checker.py --test-dir <panel_directory>")
        return
    
    checker = LocalFlowChecker()
    
    # Find panel images
    test_dir = Path(args.test_dir)
    panel_paths = sorted([str(p) for p in test_dir.glob("*.png")])
    
    if not panel_paths:
        print(f"❌ No PNG files found in {test_dir}")
        return
    
    print(f"🔍 Testing local flow checker with {len(panel_paths)} panels")
    
    # Analyze sequence
    results = checker.analyze_sequence(panel_paths)
    
    # Save results
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"💾 Results saved to {args.output}")
    else:
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
