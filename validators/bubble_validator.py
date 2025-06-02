#!/usr/bin/env python3
"""
Bubble Validator for Dialogue Placement Quality

This module validates dialogue bubble placement quality by checking:
- Speech bubble overlap with faces, hands, and key body parts
- Bubble-to-text overflow and readability
- Left/right alignment based on assumed speaker
- Overall dialogue placement quality scores
"""

import cv2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import json
from dataclasses import dataclass
from core.dialogue_placer import DialogueBubble, VisualRegion, DialoguePlacementEngine


@dataclass
class BubbleValidationResult:
    """Results from bubble placement validation."""
    bubble_id: int
    overlap_with_faces: float
    overlap_with_hands: float
    overlap_with_characters: float
    text_readability_score: float
    alignment_score: float
    text_overflow_score: float  # New: Check for text cutoff
    bubble_size_adequacy: float  # New: Check if bubble is large enough
    overall_score: float
    issues: List[str]


class BubbleValidator:
    """Validator for dialogue bubble placement quality."""
    
    def __init__(self):
        """Initialize the bubble validator."""
        self.face_cascade = None
        self.hand_cascade = None
        self._load_detection_models()
        
        # Validation thresholds
        self.max_face_overlap = 0.2
        self.max_hand_overlap = 0.3
        self.max_character_overlap = 0.4
        self.min_readability_score = 0.6
        self.min_overall_score = 0.7
        self.max_bubble_overlap = 0.0  # Zero tolerance for bubble overlaps
        self.bubble_separation_threshold = 15  # Minimum separation between bubbles
    
    def _load_detection_models(self):
        """Load OpenCV detection models."""
        try:
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            print(f"✅ Loaded face detection for bubble validation")
        except Exception as e:
            print(f"⚠️ Could not load face detection: {e}")
    
    def validate_bubble_placement(self, image_path: str, bubbles: List[DialogueBubble],
                                 color_mode: str = "color") -> Dict[str, Any]:
        """
        Validate dialogue bubble placement quality.
        
        Args:
            image_path: Path to the image with bubbles
            bubbles: List of placed dialogue bubbles
            color_mode: Color mode (color or black_and_white)
            
        Returns:
            Validation results dictionary
        """
        print(f"   🔍 Validating {len(bubbles)} dialogue bubbles")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            return self._create_error_result(f"Could not load image: {image_path}")
        
        # Detect visual features
        faces = self._detect_faces(image)
        characters = self._detect_characters(image)
        
        # Validate each bubble
        bubble_results = []
        for i, bubble in enumerate(bubbles):
            result = self._validate_single_bubble(image, bubble, faces, characters, i)
            bubble_results.append(result)
        
        # Calculate overall scores
        overall_metrics = self._calculate_overall_metrics(bubble_results, bubbles)
        
        # Check for bubble overlaps
        overlap_analysis = self._analyze_bubble_overlaps(bubbles)

        # Update overall validation status
        has_overlaps = overlap_analysis["overlap_count"] > 0
        validation_passed = (overall_metrics["overall_score"] >= self.min_overall_score and
                           not has_overlaps)

        # Generate validation report
        validation_report = {
            "validation_type": "dialogue_bubble_placement",
            "image_path": image_path,
            "color_mode": color_mode,
            "bubble_count": len(bubbles),
            "faces_detected": len(faces),
            "characters_detected": len(characters),
            "overall_metrics": overall_metrics,
            "overlap_analysis": overlap_analysis,
            "individual_results": [self._bubble_result_to_dict(r) for r in bubble_results],
            "validation_passed": validation_passed,
            "zero_overlap_achieved": not has_overlaps,
            "recommendations": self._generate_recommendations(bubble_results, overall_metrics, overlap_analysis)
        }
        
        return validation_report
    
    def _detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces in the image."""
        faces = []
        
        if self.face_cascade is not None:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            detected_faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            faces = [(int(x), int(y), int(w), int(h)) for x, y, w, h in detected_faces]
        
        return faces
    
    def _detect_characters(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect character/body regions in the image."""
        # For now, use edge detection to find potential character regions
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        characters = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            
            # Filter for character-sized regions
            if 2000 < area < 50000 and h > w * 0.8:  # Roughly human proportions
                characters.append((x, y, w, h))
        
        return characters
    
    def _validate_single_bubble(self, image: np.ndarray, bubble: DialogueBubble,
                               faces: List[Tuple[int, int, int, int]],
                               characters: List[Tuple[int, int, int, int]],
                               bubble_id: int) -> BubbleValidationResult:
        """Validate a single dialogue bubble."""
        issues = []
        
        # Check overlap with faces
        face_overlap = self._calculate_max_overlap_with_regions(bubble, faces)
        if face_overlap > self.max_face_overlap:
            issues.append(f"Overlaps with face ({face_overlap:.2f})")
        
        # Check overlap with characters
        character_overlap = self._calculate_max_overlap_with_regions(bubble, characters)
        if character_overlap > self.max_character_overlap:
            issues.append(f"Overlaps with character ({character_overlap:.2f})")
        
        # Check text readability
        readability_score = self._calculate_text_readability(image, bubble)
        if readability_score < self.min_readability_score:
            issues.append(f"Poor text readability ({readability_score:.2f})")
        
        # Check alignment (simplified - could be enhanced with speaker detection)
        alignment_score = self._calculate_alignment_score(bubble, image.shape[1])

        # Check text overflow and bubble size adequacy
        text_overflow_score, bubble_size_adequacy = self._check_text_overflow(bubble)
        if text_overflow_score < 0.8:
            issues.append(f"Text overflow detected ({text_overflow_score:.2f})")
        if bubble_size_adequacy < 0.7:
            issues.append(f"Bubble too small for text ({bubble_size_adequacy:.2f})")

        # Calculate overall score
        overall_score = self._calculate_bubble_overall_score(
            face_overlap, character_overlap, readability_score, alignment_score,
            text_overflow_score, bubble_size_adequacy
        )
        
        return BubbleValidationResult(
            bubble_id=bubble_id,
            overlap_with_faces=face_overlap,
            overlap_with_hands=0.0,  # Placeholder - hand detection not implemented
            overlap_with_characters=character_overlap,
            text_readability_score=readability_score,
            alignment_score=alignment_score,
            text_overflow_score=text_overflow_score,
            bubble_size_adequacy=bubble_size_adequacy,
            overall_score=overall_score,
            issues=issues
        )
    
    def _calculate_max_overlap_with_regions(self, bubble: DialogueBubble,
                                          regions: List[Tuple[int, int, int, int]]) -> float:
        """Calculate maximum overlap between bubble and any region."""
        max_overlap = 0.0
        
        for x, y, w, h in regions:
            overlap = self._calculate_overlap(
                bubble.x, bubble.y, bubble.width, bubble.height,
                x, y, w, h
            )
            max_overlap = max(max_overlap, overlap)
        
        return max_overlap
    
    def _calculate_overlap(self, x1: int, y1: int, w1: int, h1: int,
                          x2: int, y2: int, w2: int, h2: int) -> float:
        """Calculate overlap ratio between two rectangles."""
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left >= right or top >= bottom:
            return 0.0
        
        intersection_area = (right - left) * (bottom - top)
        bubble_area = w1 * h1
        
        return intersection_area / bubble_area if bubble_area > 0 else 0.0
    
    def _calculate_text_readability(self, image: np.ndarray, bubble: DialogueBubble) -> float:
        """Calculate text readability score based on contrast and size."""
        # Extract bubble region
        x, y, w, h = bubble.x, bubble.y, bubble.width, bubble.height
        
        # Ensure coordinates are within image bounds
        x = max(0, min(x, image.shape[1] - 1))
        y = max(0, min(y, image.shape[0] - 1))
        w = min(w, image.shape[1] - x)
        h = min(h, image.shape[0] - y)
        
        if w <= 0 or h <= 0:
            return 0.0
        
        bubble_region = image[y:y+h, x:x+w]
        
        if bubble_region.size == 0:
            return 0.0
        
        # Convert to grayscale
        gray_region = cv2.cvtColor(bubble_region, cv2.COLOR_BGR2GRAY)
        
        # Calculate contrast (standard deviation of pixel values)
        contrast = np.std(gray_region)
        
        # Normalize contrast score (higher is better)
        contrast_score = min(1.0, contrast / 50.0)
        
        # Factor in bubble size (larger bubbles are more readable)
        size_score = min(1.0, (w * h) / 10000.0)
        
        # Combine scores
        readability_score = (contrast_score * 0.7) + (size_score * 0.3)
        
        return readability_score
    
    def _calculate_alignment_score(self, bubble: DialogueBubble, image_width: int) -> float:
        """Calculate alignment score based on bubble position."""
        # Simple heuristic: bubbles in left half should be left-aligned, etc.
        bubble_center_x = bubble.x + bubble.width // 2
        
        if bubble_center_x < image_width // 2:
            # Left side - prefer left alignment
            alignment_score = 1.0 - (bubble.x / (image_width // 2))
        else:
            # Right side - prefer right alignment
            right_edge = bubble.x + bubble.width
            alignment_score = (right_edge - image_width // 2) / (image_width // 2)
        
        return max(0.0, min(1.0, alignment_score))

    def _check_text_overflow(self, bubble: DialogueBubble) -> Tuple[float, float]:
        """Check for text overflow and bubble size adequacy."""
        # Estimate text requirements
        text_length = len(bubble.text)
        estimated_lines = max(1, text_length // 25)  # Rough estimate

        # Calculate required dimensions
        min_text_width = min(200, text_length * 8)  # Rough character width estimate
        min_text_height = estimated_lines * 20  # Rough line height estimate

        # Add padding requirements
        required_width = min_text_width + 40  # 20px padding each side
        required_height = min_text_height + 30  # 15px padding top/bottom

        # Calculate adequacy scores
        width_adequacy = min(1.0, bubble.width / required_width) if required_width > 0 else 1.0
        height_adequacy = min(1.0, bubble.height / required_height) if required_height > 0 else 1.0

        # Text overflow score (1.0 = no overflow, 0.0 = severe overflow)
        text_overflow_score = min(width_adequacy, height_adequacy)

        # Bubble size adequacy (how well the bubble size matches text needs)
        bubble_size_adequacy = (width_adequacy + height_adequacy) / 2

        return text_overflow_score, bubble_size_adequacy

    def _analyze_bubble_overlaps(self, bubbles: List[DialogueBubble]) -> Dict[str, Any]:
        """Analyze bubble overlaps and separation."""
        if len(bubbles) <= 1:
            return {
                "overlap_count": 0,
                "overlap_pairs": [],
                "min_separation": float('inf'),
                "average_separation": float('inf'),
                "separation_violations": 0
            }

        overlap_pairs = []
        separations = []
        separation_violations = 0

        for i, bubble1 in enumerate(bubbles):
            for j, bubble2 in enumerate(bubbles[i+1:], i+1):
                # Check for overlap using the same method as layout engine
                if bubble1.overlaps_with(bubble2, margin=self.bubble_separation_threshold):
                    overlap_pairs.append((i, j))

                # Calculate separation distance
                distance = bubble1.distance_to(bubble2)
                separations.append(distance)

                if distance < self.bubble_separation_threshold:
                    separation_violations += 1

        min_separation = min(separations) if separations else float('inf')
        avg_separation = sum(separations) / len(separations) if separations else float('inf')

        return {
            "overlap_count": len(overlap_pairs),
            "overlap_pairs": overlap_pairs,
            "min_separation": round(min_separation, 2),
            "average_separation": round(avg_separation, 2),
            "separation_violations": separation_violations,
            "separation_threshold": self.bubble_separation_threshold
        }

    def _calculate_bubble_overall_score(self, face_overlap: float, character_overlap: float,
                                      readability_score: float, alignment_score: float,
                                      text_overflow_score: float, bubble_size_adequacy: float) -> float:
        """Calculate overall score for a single bubble."""
        # Penalties for overlaps
        face_penalty = min(1.0, face_overlap / self.max_face_overlap)
        character_penalty = min(1.0, character_overlap / self.max_character_overlap)
        
        # Combine scores
        overlap_score = 1.0 - (face_penalty * 0.5 + character_penalty * 0.3)

        overall_score = (
            overlap_score * 0.3 +
            readability_score * 0.25 +
            alignment_score * 0.15 +
            text_overflow_score * 0.2 +
            bubble_size_adequacy * 0.1
        )
        
        return max(0.0, min(1.0, overall_score))
    
    def _calculate_overall_metrics(self, bubble_results: List[BubbleValidationResult],
                                 bubbles: List[DialogueBubble]) -> Dict[str, Any]:
        """Calculate overall validation metrics."""
        if not bubble_results:
            return {
                "overall_score": 0.0,
                "average_face_overlap": 0.0,
                "average_character_overlap": 0.0,
                "average_readability": 0.0,
                "average_alignment": 0.0,
                "bubbles_with_issues": 0,
                "total_issues": 0
            }
        
        # Calculate averages
        avg_overall = sum(r.overall_score for r in bubble_results) / len(bubble_results)
        avg_face_overlap = sum(r.overlap_with_faces for r in bubble_results) / len(bubble_results)
        avg_character_overlap = sum(r.overlap_with_characters for r in bubble_results) / len(bubble_results)
        avg_readability = sum(r.text_readability_score for r in bubble_results) / len(bubble_results)
        avg_alignment = sum(r.alignment_score for r in bubble_results) / len(bubble_results)
        avg_text_overflow = sum(r.text_overflow_score for r in bubble_results) / len(bubble_results)
        avg_bubble_adequacy = sum(r.bubble_size_adequacy for r in bubble_results) / len(bubble_results)
        
        # Count issues
        bubbles_with_issues = sum(1 for r in bubble_results if r.issues)
        total_issues = sum(len(r.issues) for r in bubble_results)
        
        return {
            "overall_score": round(avg_overall, 3),
            "average_face_overlap": round(avg_face_overlap, 3),
            "average_character_overlap": round(avg_character_overlap, 3),
            "average_readability": round(avg_readability, 3),
            "average_alignment": round(avg_alignment, 3),
            "average_text_overflow": round(avg_text_overflow, 3),
            "average_bubble_adequacy": round(avg_bubble_adequacy, 3),
            "bubbles_with_issues": bubbles_with_issues,
            "total_issues": total_issues
        }
    
    def _generate_recommendations(self, bubble_results: List[BubbleValidationResult],
                                overall_metrics: Dict[str, Any],
                                overlap_analysis: Dict[str, Any] = None) -> List[str]:
        """Generate recommendations for improving bubble placement."""
        recommendations = []

        # Check overlap issues first (highest priority)
        if overlap_analysis and overlap_analysis["overlap_count"] > 0:
            recommendations.append(f"CRITICAL: {overlap_analysis['overlap_count']} bubble overlaps detected - must be resolved")
            recommendations.append("Use force-directed layout optimization to separate overlapping bubbles")

        if overlap_analysis and overlap_analysis["separation_violations"] > 0:
            recommendations.append(f"Improve bubble separation - {overlap_analysis['separation_violations']} bubbles too close")

        # Standard quality recommendations
        if overall_metrics["average_face_overlap"] > self.max_face_overlap:
            recommendations.append("Reduce bubble overlap with character faces")

        if overall_metrics["average_character_overlap"] > self.max_character_overlap:
            recommendations.append("Improve bubble positioning to avoid character bodies")

        if overall_metrics["average_readability"] < self.min_readability_score:
            recommendations.append("Increase bubble size or improve text contrast")

        if overall_metrics["average_text_overflow"] < 0.8:
            recommendations.append("Increase bubble sizes to prevent text cutoff")

        if overall_metrics["average_bubble_adequacy"] < 0.7:
            recommendations.append("Use larger bubbles to better accommodate text")

        if overall_metrics["bubbles_with_issues"] > len(bubble_results) * 0.5:
            recommendations.append("Consider using larger empty areas for bubble placement")

        # Success message
        if not recommendations:
            if overlap_analysis and overlap_analysis["overlap_count"] == 0:
                recommendations.append("Excellent! Zero bubble overlaps achieved with good placement quality")
            else:
                recommendations.append("Dialogue placement quality is good")
        
        return recommendations
    
    def _bubble_result_to_dict(self, result: BubbleValidationResult) -> Dict[str, Any]:
        """Convert bubble validation result to dictionary."""
        return {
            "bubble_id": result.bubble_id,
            "overlap_with_faces": result.overlap_with_faces,
            "overlap_with_hands": result.overlap_with_hands,
            "overlap_with_characters": result.overlap_with_characters,
            "text_readability_score": result.text_readability_score,
            "alignment_score": result.alignment_score,
            "text_overflow_score": result.text_overflow_score,
            "bubble_size_adequacy": result.bubble_size_adequacy,
            "overall_score": result.overall_score,
            "issues": result.issues
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """Create error result for validation."""
        return {
            "validation_type": "dialogue_bubble_placement",
            "error": error_message,
            "validation_passed": False,
            "overall_metrics": {"overall_score": 0.0},
            "recommendations": ["Fix image loading issues"]
        }
