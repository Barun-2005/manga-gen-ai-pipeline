#!/usr/bin/env python3
"""
Face Detection for Smart Dialogue Placement

Uses OpenCV to detect faces in manga panels and creates exclusion zones
so dialogue bubbles don't cover character faces.

V3 Implementation - Phase 2
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import os

class FaceDetector:
    """
    Detects faces in manga/anime images to create safe zones for bubble placement.
    
    Uses Haar Cascade for frontal faces and lbpcascade for anime-style faces.
    """
    
    def __init__(self):
        # Load cascade classifiers
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.anime_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'
        )
        
        # Try to load anime-specific cascade if available
        # This is a custom cascade trained on anime faces
        custom_cascade_path = Path(__file__).parent / "lbpcascade_animeface.xml"
        if custom_cascade_path.exists():
            self.anime_cascade = cv2.CascadeClassifier(str(custom_cascade_path))
        else:
            self.anime_cascade = None
    
    def detect_faces(self, image_path: str, expansion_factor: float = 0.2) -> List[Dict]:
        """
        Detect faces in an image and return exclusion zones.
        
        Args:
            image_path: Path to the image file
            expansion_factor: How much to expand face bounding box (0.2 = 20%)
            
        Returns:
            List of exclusion zones as dicts with x, y, width, height (as percentages)
        """
        # Load image
        img = cv2.imread(image_path)
        if img is None:
            print(f"⚠️ Could not load image: {image_path}")
            return []
        
        # Get image dimensions for percentage conversion
        img_height, img_width = img.shape[:2]
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Detect faces using multiple methods for better coverage
        faces = []
        
        # Method 1: Standard Haar cascade
        detected = self.face_cascade.detectMultiScale(
            gray, 
            scaleFactor=1.1, 
            minNeighbors=3,
            minSize=(int(img_width * 0.05), int(img_height * 0.05))
        )
        faces.extend(detected)
        
        # Method 2: Anime face cascade (if available)
        if self.anime_cascade is not None:
            anime_detected = self.anime_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=3,
                minSize=(int(img_width * 0.05), int(img_height * 0.05))
            )
            faces.extend(anime_detected)
        
        # Deduplicate overlapping detections
        faces = self._merge_overlapping_boxes(faces)
        
        # Create exclusion zones with expansion
        exclusion_zones = []
        for (x, y, w, h) in faces:
            # Expand the box
            expand_x = w * expansion_factor
            expand_y = h * expansion_factor
            
            new_x = max(0, x - expand_x / 2)
            new_y = max(0, y - expand_y / 2)
            new_w = min(w + expand_x, img_width - new_x)
            new_h = min(h + expand_y, img_height - new_y)
            
            # Convert to percentages for frontend
            exclusion_zones.append({
                "x": (new_x / img_width) * 100,
                "y": (new_y / img_height) * 100,
                "width": (new_w / img_width) * 100,
                "height": (new_h / img_height) * 100,
                "type": "face"
            })
        
        print(f"🔍 Detected {len(exclusion_zones)} face(s) in {Path(image_path).name}")
        return exclusion_zones
    
    def _merge_overlapping_boxes(self, boxes, overlap_threshold: float = 0.5) -> List:
        """Merge overlapping bounding boxes to avoid duplicates."""
        if len(boxes) == 0:
            return []
        
        # Convert to list of tuples for processing
        boxes = list(boxes)
        
        merged = []
        used = set()
        
        for i, box1 in enumerate(boxes):
            if i in used:
                continue
            
            x1, y1, w1, h1 = box1
            combined_boxes = [(x1, y1, w1, h1)]
            used.add(i)
            
            for j, box2 in enumerate(boxes):
                if j in used:
                    continue
                
                x2, y2, w2, h2 = box2
                
                # Check overlap
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                overlap_area = overlap_x * overlap_y
                
                area1 = w1 * h1
                area2 = w2 * h2
                
                if overlap_area > min(area1, area2) * overlap_threshold:
                    combined_boxes.append((x2, y2, w2, h2))
                    used.add(j)
            
            # Combine all overlapping boxes into one
            if combined_boxes:
                min_x = min(b[0] for b in combined_boxes)
                min_y = min(b[1] for b in combined_boxes)
                max_x = max(b[0] + b[2] for b in combined_boxes)
                max_y = max(b[1] + b[3] for b in combined_boxes)
                merged.append((min_x, min_y, max_x - min_x, max_y - min_y))
        
        return merged
    
    def find_safe_bubble_positions(
        self, 
        image_path: str, 
        exclusion_zones: Optional[List[Dict]] = None,
        num_positions: int = 4
    ) -> List[Dict]:
        """
        Find safe positions for dialogue bubbles that don't overlap with faces.
        
        Args:
            image_path: Path to the image
            exclusion_zones: Pre-computed exclusion zones (if None, will detect faces)
            num_positions: Number of positions to return
            
        Returns:
            List of safe positions as dicts with x, y (percentages from top-left of panel)
        """
        # Get exclusion zones if not provided
        if exclusion_zones is None:
            exclusion_zones = self.detect_faces(image_path)
        
        # Define candidate positions - BORDER SNAPPING PRIORITY
        # Positions are in percentages
        # V4.9: Prioritize TOP and BOTTOM edges for cleaner look
        candidate_positions = [
            # TOP EDGE (highest priority - clean space above characters)
            {"x": 40, "y": 5, "anchor": "top-center"},
            {"x": 10, "y": 8, "anchor": "top-left"},
            {"x": 70, "y": 8, "anchor": "top-right"},
            
            # BOTTOM EDGE (second priority - narration zone)
            {"x": 40, "y": 82, "anchor": "bottom-center"},
            {"x": 10, "y": 75, "anchor": "bottom-left"},
            {"x": 70, "y": 75, "anchor": "bottom-right"},
            
            # CORNERS (fallback if top/bottom edges blocked)
            {"x": 10, "y": 35, "anchor": "mid-left"},
            {"x": 75, "y": 35, "anchor": "mid-right"},
            
            # SIDE EDGES (last resort)
            {"x": 5, "y": 40, "anchor": "left-center"},
            {"x": 80, "y": 40, "anchor": "right-center"},
        ]
        
        safe_positions = []
        
        for pos in candidate_positions:
            is_safe = True
            
            # Check if this position overlaps with any exclusion zone
            for zone in exclusion_zones:
                # Simple overlap check (bubble is roughly 20x15% of panel)
                bubble_w, bubble_h = 25, 20
                
                pos_right = pos["x"] + bubble_w
                pos_bottom = pos["y"] + bubble_h
                zone_right = zone["x"] + zone["width"]
                zone_bottom = zone["y"] + zone["height"]
                
                # Check if rectangles overlap
                if not (pos_right < zone["x"] or 
                        pos["x"] > zone_right or 
                        pos_bottom < zone["y"] or 
                        pos["y"] > zone_bottom):
                    is_safe = False
                    break
            
            if is_safe:
                safe_positions.append(pos)
                if len(safe_positions) >= num_positions:
                    break
        
        # If not enough safe positions, add corners anyway (they're less likely to cover faces)
        if len(safe_positions) < num_positions:
            corners = [p for p in candidate_positions if "corner" in p.get("anchor", "")]
            for corner in corners:
                if corner not in safe_positions:
                    safe_positions.append(corner)
                    if len(safe_positions) >= num_positions:
                        break
        
        return safe_positions[:num_positions]


def match_speaker_to_face(
    faces: List[Dict],
    speaker_position: str,
    panel_width: int = 100
) -> Optional[Dict]:
    """
    V4.8 Speaker Matching: Match speaker_position (from LLM) to a detected face.
    
    Args:
        faces: List of detected faces with x, y, width, height (as percentages)
        speaker_position: "left", "right", or "center" (from LLM dialogue output)
        panel_width: Width of panel (default 100 for percentage-based)
        
    Returns:
        The face dict that matches the speaker position, or None if no match.
        Use this to calculate bubble tail direction.
    """
    if not faces:
        return None
    
    if not isinstance(speaker_position, str):
        speaker_position = "center"
    
    speaker_position = speaker_position.lower().strip()
    
    if speaker_position == "left":
        # Target leftmost face (smallest x)
        return min(faces, key=lambda f: f.get('x', 50))
    elif speaker_position == "right":
        # Target rightmost face (largest x)
        return max(faces, key=lambda f: f.get('x', 50))
    else:
        # Center - target face closest to horizontal center
        center = panel_width / 2
        return min(faces, key=lambda f: abs(f.get('x', 50) + f.get('width', 0) / 2 - center))


def get_tail_direction(
    bubble_x: float,
    bubble_y: float,
    target_face: Optional[Dict],
    panel_width: int = 100,
    panel_height: int = 100
) -> str:
    """
    V4.3 Bubble Tail: Calculate which direction the tail should point.
    
    Args:
        bubble_x, bubble_y: Bubble position (percentages)
        target_face: The face to point toward (from match_speaker_to_face)
        panel_width, panel_height: Panel dimensions (default 100 for percentages)
        
    Returns:
        Direction string: "left", "right", "up", "down", or "none"
    """
    if not target_face:
        return "none"
    
    # Get face center
    face_center_x = target_face.get('x', 50) + target_face.get('width', 0) / 2
    face_center_y = target_face.get('y', 50) + target_face.get('height', 0) / 2
    
    # Calculate direction from bubble to face
    dx = face_center_x - bubble_x
    dy = face_center_y - bubble_y
    
    # Determine primary direction based on larger delta
    if abs(dx) > abs(dy):
        return "left" if dx < 0 else "right"
    else:
        return "up" if dy < 0 else "down"


def detect_faces_in_panel(image_path: str) -> Dict:
    """
    Convenience function to detect faces and get safe positions for a panel.
    
    Returns:
        Dict with exclusion_zones and safe_positions
    """
    detector = FaceDetector()
    exclusion_zones = detector.detect_faces(image_path)
    safe_positions = detector.find_safe_bubble_positions(image_path, exclusion_zones)
    
    return {
        "exclusion_zones": exclusion_zones,
        "safe_positions": safe_positions,
        "face_count": len(exclusion_zones)
    }


# Main entry point for testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        result = detect_faces_in_panel(image_path)
        print(f"\n📊 Results for {image_path}:")
        print(f"   Faces detected: {result['face_count']}")
        print(f"   Exclusion zones: {result['exclusion_zones']}")
        print(f"   Safe positions: {result['safe_positions']}")
    else:
        print("Usage: python face_detector.py <image_path>")
