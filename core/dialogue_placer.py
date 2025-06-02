#!/usr/bin/env python3
"""
Smart Dialogue Placement Engine for Manga Panels

This module provides intelligent dialogue bubble placement that:
- Detects important visual regions (faces, hands, characters)
- Places bubbles in empty areas while avoiding key features
- Dynamically sizes and positions bubbles based on text and panel structure
- Supports both color and black_and_white modes
"""

import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path
import json
from dataclasses import dataclass
import math
import time
from PIL import Image, ImageDraw, ImageFont


@dataclass
class DialogueBubble:
    """Represents a dialogue bubble with position and styling."""
    text: str
    x: int
    y: int
    width: int
    height: int
    speaker: str = "unknown"
    alignment: str = "left"  # left, right, center
    bubble_type: str = "speech"  # speech, thought, shout
    confidence: float = 1.0
    shape: str = "rounded"  # rounded, jagged, thought, dashed, narrative
    tone: str = "normal"  # normal, excited, angry, whisper, thought, narration
    priority: int = 1  # Layout priority (1=highest, 5=lowest)

    def get_bounds(self) -> tuple:
        """Get bubble boundaries as (left, top, right, bottom)."""
        return (self.x, self.y, self.x + self.width, self.y + self.height)

    def overlaps_with(self, other: 'DialogueBubble', margin: int = 5) -> bool:
        """Check if this bubble overlaps with another bubble."""
        left1, top1, right1, bottom1 = self.get_bounds()
        left2, top2, right2, bottom2 = other.get_bounds()

        # Add margin for separation
        left1 -= margin
        top1 -= margin
        right1 += margin
        bottom1 += margin

        return not (right1 <= left2 or left1 >= right2 or bottom1 <= top2 or top1 >= bottom2)

    def distance_to(self, other: 'DialogueBubble') -> float:
        """Calculate distance between bubble centers."""
        center1_x = self.x + self.width // 2
        center1_y = self.y + self.height // 2
        center2_x = other.x + other.width // 2
        center2_y = other.y + other.height // 2

        return ((center1_x - center2_x) ** 2 + (center1_y - center2_y) ** 2) ** 0.5


@dataclass
class VisualRegion:
    """Represents an important visual region to avoid."""
    x: int
    y: int
    width: int
    height: int
    importance: float  # 0.0 to 1.0
    region_type: str  # face, hand, character, object


class DialoguePlacementEngine:
    """Main engine for intelligent dialogue bubble placement."""
    
    def __init__(self, color_mode: str = "color"):
        """Initialize the dialogue placement engine."""
        self.color_mode = color_mode
        self.face_cascade = None
        self.body_cascade = None
        
        # Load OpenCV cascades for detection
        self._load_detection_models()
        
        # Bubble styling based on color mode
        self.bubble_styles = self._get_bubble_styles()
        
        # Placement parameters
        self.min_bubble_size = (80, 40)
        self.max_bubble_size = (400, 200)  # Increased for better text fit
        self.margin = 10
        self.overlap_threshold = 0.3

        # Text sizing parameters
        self.font_size = 16  # Base font size for PIL calculations
        self.text_padding_x = 25  # Increased horizontal padding inside bubble
        self.text_padding_y = 20  # Increased vertical padding inside bubble
        self.line_spacing = 1.3   # Increased line spacing multiplier
        self.max_chars_per_line = 22  # Reduced characters per line for better fit
        self.size_safety_margin = 1.15  # 15% safety margin for bubble sizing

        # Layout engine parameters
        self.bubble_separation = 30  # Increased minimum distance between bubbles
        self.max_layout_iterations = 150  # More iterations for better optimization
        self.layout_force_strength = 2.0  # Much stronger force for bubble repulsion
        self.preferred_reading_order = "top_to_bottom"  # Reading flow preference
        self.grid_spacing = 60  # Larger grid spacing for initial placement

        # Bubble shape parameters
        self.shape_styles = self._initialize_shape_styles()

        # Tone detection keywords
        self.tone_keywords = {
            "excited": ["!", "wow", "amazing", "incredible", "awesome", "fantastic"],
            "angry": ["!!", "damn", "hell", "angry", "furious", "rage"],
            "whisper": ["...", "shh", "quiet", "whisper", "softly"],
            "thought": ["think", "wonder", "maybe", "perhaps", "hmm"],
            "narration": ["meanwhile", "later", "suddenly", "then", "now"]
        }

        # Debug settings
        self.debug_mode = False
        self.debug_overlays = []
        self.layout_debug_info = []
        
    def _load_detection_models(self):
        """Load OpenCV detection models."""
        try:
            # Try to load face detection cascade
            face_cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(face_cascade_path)
            
            # Try to load body detection cascade
            body_cascade_path = cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            self.body_cascade = cv2.CascadeClassifier(body_cascade_path)
            
            print(f"✅ Loaded OpenCV detection models")
            
        except Exception as e:
            print(f"⚠️ Could not load detection models: {e}")
            self.face_cascade = None
            self.body_cascade = None
    
    def _get_bubble_styles(self) -> Dict[str, Any]:
        """Get bubble styling based on color mode."""
        if self.color_mode == "black_and_white":
            return {
                "bubble_color": (255, 255, 255),  # White bubble
                "border_color": (0, 0, 0),        # Black border
                "text_color": (0, 0, 0),          # Black text
                "border_thickness": 2,
                "font_scale": 0.6,
                "font_thickness": 1
            }
        else:  # color mode
            return {
                "bubble_color": (255, 255, 255),  # White bubble
                "border_color": (0, 0, 0),        # Black border
                "text_color": (0, 0, 0),          # Black text
                "border_thickness": 2,
                "font_scale": 0.6,
                "font_thickness": 1
            }

    def _initialize_shape_styles(self) -> Dict[str, Dict[str, Any]]:
        """Initialize bubble shape styling parameters."""
        return {
            "rounded": {
                "border_radius": 15,
                "border_thickness": 2,
                "padding_multiplier": 1.0,
                "text_alignment": "center"
            },
            "jagged": {
                "border_radius": 0,
                "border_thickness": 3,
                "padding_multiplier": 1.2,
                "text_alignment": "center",
                "jagged_intensity": 8
            },
            "thought": {
                "border_radius": 20,
                "border_thickness": 1,
                "padding_multiplier": 1.3,
                "text_alignment": "center",
                "cloud_bubbles": True
            },
            "dashed": {
                "border_radius": 10,
                "border_thickness": 1,
                "padding_multiplier": 1.1,
                "text_alignment": "center",
                "dash_pattern": [5, 3]
            },
            "narrative": {
                "border_radius": 3,
                "border_thickness": 2,
                "padding_multiplier": 1.1,
                "text_alignment": "left",
                "rectangular": True
            }
        }

    def detect_dialogue_tone(self, text: str) -> str:
        """Detect the tone of dialogue text for appropriate bubble shape selection."""
        text_lower = text.lower()

        # Check for narration indicators first (highest priority)
        for keyword in self.tone_keywords["narration"]:
            if keyword in text_lower:
                return "narration"

        # Count exclamation marks for excitement/anger
        exclamation_count = text.count('!')
        if exclamation_count >= 2:
            return "angry"
        elif exclamation_count >= 1:
            return "excited"

        # Check for thought indicators
        for keyword in self.tone_keywords["thought"]:
            if keyword in text_lower:
                return "thought"

        # Check for ellipsis or whisper indicators (after thought check)
        if "..." in text or text.endswith(".."):
            return "whisper"

        # Check for specific tone keywords
        for tone, keywords in self.tone_keywords.items():
            if tone in ["excited", "angry", "whisper", "thought", "narration"]:  # Already handled above
                continue
            for keyword in keywords:
                if keyword in text_lower:
                    return tone

        return "normal"

    def select_bubble_shape(self, tone: str) -> str:
        """Select appropriate bubble shape based on detected tone."""
        shape_mapping = {
            "normal": "rounded",
            "excited": "jagged",
            "angry": "jagged",
            "whisper": "dashed",
            "thought": "thought",
            "narration": "narrative"
        }
        return shape_mapping.get(tone, "rounded")

    def detect_visual_regions(self, image: np.ndarray) -> List[VisualRegion]:
        """Detect important visual regions to avoid when placing bubbles."""
        regions = []
        
        # Convert to grayscale for detection
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
        
        # Detect faces
        if self.face_cascade is not None:
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
            
            for (x, y, w, h) in faces:
                regions.append(VisualRegion(
                    x=int(x), y=int(y), width=int(w), height=int(h),
                    importance=0.9, region_type="face"
                ))
        
        # Detect bodies/characters
        if self.body_cascade is not None:
            bodies = self.body_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=3, minSize=(50, 100)
            )
            
            for (x, y, w, h) in bodies:
                regions.append(VisualRegion(
                    x=int(x), y=int(y), width=int(w), height=int(h),
                    importance=0.7, region_type="character"
                ))
        
        # Detect high-contrast regions (potential important objects)
        regions.extend(self._detect_high_contrast_regions(gray))
        
        print(f"   🔍 Detected {len(regions)} visual regions to avoid")
        return regions
    
    def _detect_high_contrast_regions(self, gray_image: np.ndarray) -> List[VisualRegion]:
        """Detect high-contrast regions that might be important."""
        regions = []
        
        try:
            # Apply edge detection
            edges = cv2.Canny(gray_image, 50, 150)
            
            # Find contours
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filter contours by size and add as regions
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                
                # Only consider medium-sized regions
                if 1000 < area < 10000:
                    regions.append(VisualRegion(
                        x=x, y=y, width=w, height=h,
                        importance=0.5, region_type="object"
                    ))
            
        except Exception as e:
            print(f"   ⚠️ Error detecting high-contrast regions: {e}")
        
        return regions
    
    def calculate_text_size(self, text: str) -> Tuple[int, int]:
        """Calculate required bubble size for given text using PIL for accuracy."""
        try:
            # Create a temporary PIL image for text measurement
            temp_img = Image.new('RGB', (1000, 1000), color='white')
            draw = ImageDraw.Draw(temp_img)

            # Try to load a font, fallback to default if not available
            try:
                font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                try:
                    font = ImageFont.load_default()
                except:
                    # Fallback to OpenCV method if PIL fails
                    return self._calculate_text_size_opencv(text)

            # Wrap text to fit within reasonable width
            wrapped_lines = self._wrap_text(text, font, draw)

            # Calculate text block dimensions
            max_width = 0
            total_height = 0

            for line in wrapped_lines:
                if line.strip():  # Skip empty lines
                    bbox = draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    line_height = bbox[3] - bbox[1]

                    max_width = max(max_width, line_width)
                    total_height += int(line_height * self.line_spacing)

            # Add padding
            bubble_width = max_width + self.text_padding_x * 2
            bubble_height = total_height + self.text_padding_y * 2

            # Apply safety margin to prevent text cutoff
            bubble_width = int(bubble_width * self.size_safety_margin)
            bubble_height = int(bubble_height * self.size_safety_margin)

            # Ensure minimum size
            bubble_width = max(self.min_bubble_size[0], bubble_width)
            bubble_height = max(self.min_bubble_size[1], bubble_height)

            # Clamp to maximum size
            bubble_width = min(self.max_bubble_size[0], bubble_width)
            bubble_height = min(self.max_bubble_size[1], bubble_height)

            # Log sizing information
            print(f"     Text: '{text[:30]}...' → {bubble_width}x{bubble_height}px ({len(wrapped_lines)} lines)")

            return bubble_width, bubble_height

        except Exception as e:
            print(f"     ⚠️ PIL text sizing failed: {e}, using OpenCV fallback")
            return self._calculate_text_size_opencv(text)

    def _wrap_text(self, text: str, font, draw) -> List[str]:
        """Wrap text to fit within bubble width using PIL font metrics."""
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word

            # Check if line fits within max width
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]

            # Use character limit as backup if width calculation fails
            if line_width <= (self.max_bubble_size[0] - self.text_padding_x * 2) and len(test_line) <= self.max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines if lines else [text]  # Ensure at least one line

    def _calculate_text_size_opencv(self, text: str) -> Tuple[int, int]:
        """Fallback text sizing using OpenCV (less accurate but more reliable)."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.bubble_styles["font_scale"]
        thickness = self.bubble_styles["font_thickness"]

        # Simple word wrapping
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + " " + word if current_line else word
            if len(test_line) <= self.max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        # Calculate dimensions
        max_width = 0
        line_height = 25

        for line in lines:
            (text_width, _), _ = cv2.getTextSize(line, font, font_scale, thickness)
            max_width = max(max_width, text_width)

        total_height = len(lines) * line_height

        # Add padding
        bubble_width = max_width + self.text_padding_x * 2
        bubble_height = total_height + self.text_padding_y * 2

        # Apply safety margin to prevent text cutoff
        bubble_width = int(bubble_width * self.size_safety_margin)
        bubble_height = int(bubble_height * self.size_safety_margin)

        # Clamp to min/max sizes
        bubble_width = max(self.min_bubble_size[0], min(self.max_bubble_size[0], bubble_width))
        bubble_height = max(self.min_bubble_size[1], min(self.max_bubble_size[1], bubble_height))

        return bubble_width, bubble_height
    
    def find_optimal_position(self, image: np.ndarray, bubble_width: int, bubble_height: int,
                            visual_regions: List[VisualRegion], existing_bubbles: List[DialogueBubble]) -> Tuple[int, int, float]:
        """Find optimal position for a dialogue bubble."""
        height, width = image.shape[:2]
        best_position = (0, 0)
        best_score = -1
        
        # Grid search for optimal position
        step_size = 20
        
        for y in range(0, height - bubble_height, step_size):
            for x in range(0, width - bubble_width, step_size):
                score = self._evaluate_position(
                    x, y, bubble_width, bubble_height,
                    visual_regions, existing_bubbles, width, height
                )
                
                if score > best_score:
                    best_score = score
                    best_position = (x, y)
        
        return best_position[0], best_position[1], best_score

    def find_grid_position(self, image: np.ndarray, bubble_width: int, bubble_height: int,
                          visual_regions: List[VisualRegion], existing_bubbles: List[DialogueBubble],
                          bubble_index: int) -> Tuple[int, int, float]:
        """Find position using grid-based placement to minimize initial overlaps."""
        height, width = image.shape[:2]

        # Create a grid of potential positions
        grid_positions = []

        # Calculate grid dimensions
        cols = max(2, width // self.grid_spacing)
        rows = max(2, height // self.grid_spacing)

        for row in range(rows):
            for col in range(cols):
                x = col * self.grid_spacing
                y = row * self.grid_spacing

                # Ensure bubble fits within image
                if x + bubble_width <= width and y + bubble_height <= height:
                    score = self._evaluate_position(
                        x, y, bubble_width, bubble_height,
                        visual_regions, existing_bubbles, width, height
                    )
                    grid_positions.append((x, y, score))

        # Sort by score and return best position
        if grid_positions:
            grid_positions.sort(key=lambda pos: pos[2], reverse=True)
            best_x, best_y, best_score = grid_positions[0]

            # Add some randomization to avoid perfect grid alignment
            offset_x = (bubble_index * 20) % 40 - 20
            offset_y = (bubble_index * 15) % 30 - 15

            final_x = max(0, min(width - bubble_width, best_x + offset_x))
            final_y = max(0, min(height - bubble_height, best_y + offset_y))

            return final_x, final_y, best_score
        else:
            # Fallback to center if no good positions found
            return width // 4, height // 4, 0.5

    def _evaluate_position(self, x: int, y: int, width: int, height: int,
                          visual_regions: List[VisualRegion], existing_bubbles: List[DialogueBubble],
                          image_width: int, image_height: int) -> float:
        """Evaluate how good a position is for placing a bubble."""
        score = 1.0
        
        # Check overlap with visual regions
        for region in visual_regions:
            overlap = self._calculate_overlap(
                x, y, width, height,
                region.x, region.y, region.width, region.height
            )
            if overlap > 0:
                penalty = overlap * region.importance
                score -= penalty
        
        # Check overlap with existing bubbles
        for bubble in existing_bubbles:
            overlap = self._calculate_overlap(
                x, y, width, height,
                bubble.x, bubble.y, bubble.width, bubble.height
            )
            if overlap > self.overlap_threshold:
                score -= overlap * 2  # Heavy penalty for bubble overlap
        
        # Prefer positions in upper areas (traditional manga layout)
        vertical_preference = 1.0 - (y / image_height) * 0.3
        score *= vertical_preference
        
        # Prefer positions away from edges
        edge_margin = 20
        if x < edge_margin or y < edge_margin or \
           x + width > image_width - edge_margin or y + height > image_height - edge_margin:
            score *= 0.7
        
        return max(0, score)

    def optimize_bubble_layout(self, bubbles: List[DialogueBubble], image_shape: tuple) -> List[DialogueBubble]:
        """Optimize bubble layout using force-directed algorithm to prevent overlaps."""
        if len(bubbles) <= 1:
            return bubbles

        print(f"   🔧 Optimizing layout for {len(bubbles)} bubbles")

        height, width = image_shape[:2]
        optimized_bubbles = [bubble for bubble in bubbles]  # Create copies

        # Force-directed layout iterations with improved algorithm
        for iteration in range(self.max_layout_iterations):
            moved = False
            overlap_count = 0
            total_force = 0

            # Calculate forces for all bubbles
            forces = [(0, 0) for _ in optimized_bubbles]

            for i, bubble1 in enumerate(optimized_bubbles):
                force_x, force_y = 0, 0

                # Calculate repulsion forces from other bubbles
                for j, bubble2 in enumerate(optimized_bubbles):
                    if i == j:
                        continue

                    # Calculate center-to-center distance
                    dx = (bubble1.x + bubble1.width // 2) - (bubble2.x + bubble2.width // 2)
                    dy = (bubble1.y + bubble1.height // 2) - (bubble2.y + bubble2.height // 2)
                    distance = max(1, (dx**2 + dy**2)**0.5)

                    # Required separation distance
                    required_separation = self.bubble_separation + (bubble1.width + bubble2.width) // 4

                    # Check for overlap or too close
                    if bubble1.overlaps_with(bubble2, self.bubble_separation):
                        overlap_count += 1

                        # Calculate stronger repulsion force
                        force_magnitude = self.layout_force_strength * (required_separation / distance) * 50

                        # Normalize direction and apply force
                        if distance > 0:
                            force_x += (dx / distance) * force_magnitude
                            force_y += (dy / distance) * force_magnitude

                # Add boundary forces to keep bubbles away from edges
                margin = 20
                if bubble1.x < margin:
                    force_x += (margin - bubble1.x) * 0.5
                if bubble1.y < margin:
                    force_y += (margin - bubble1.y) * 0.5
                if bubble1.x + bubble1.width > width - margin:
                    force_x -= (bubble1.x + bubble1.width - (width - margin)) * 0.5
                if bubble1.y + bubble1.height > height - margin:
                    force_y -= (bubble1.y + bubble1.height - (height - margin)) * 0.5

                forces[i] = (force_x, force_y)
                total_force += abs(force_x) + abs(force_y)

            # Apply forces with damping
            damping = 0.8 if iteration > 20 else 0.9

            for i, (force_x, force_y) in enumerate(forces):
                if abs(force_x) > 1 or abs(force_y) > 1:  # Only move if significant force
                    new_x = int(optimized_bubbles[i].x + force_x * damping)
                    new_y = int(optimized_bubbles[i].y + force_y * damping)

                    # Keep bubbles within image bounds
                    new_x = max(0, min(width - optimized_bubbles[i].width, new_x))
                    new_y = max(0, min(height - optimized_bubbles[i].height, new_y))

                    # Update position if it changed
                    if new_x != optimized_bubbles[i].x or new_y != optimized_bubbles[i].y:
                        optimized_bubbles[i].x = new_x
                        optimized_bubbles[i].y = new_y
                        moved = True

            # Store layout debug info
            if self.debug_mode:
                self.layout_debug_info.append({
                    'iteration': iteration,
                    'overlap_count': overlap_count // 2,  # Each overlap counted twice
                    'bubbles_moved': moved
                })

            # Early termination if no overlaps
            if overlap_count == 0:
                print(f"     ✅ Layout optimized in {iteration + 1} iterations (zero overlaps)")
                break

            # Early termination if no movement
            if not moved:
                print(f"     ⚠️ Layout stabilized in {iteration + 1} iterations ({overlap_count // 2} overlaps remain)")
                break

        else:
            print(f"     ⚠️ Layout optimization completed after {self.max_layout_iterations} iterations")

        return optimized_bubbles

    def arrange_bubbles_by_reading_order(self, bubbles: List[DialogueBubble]) -> List[DialogueBubble]:
        """Arrange bubbles according to manga reading order preferences."""
        if not bubbles:
            return bubbles

        # Sort by priority first, then by position
        if self.preferred_reading_order == "top_to_bottom":
            # Sort by Y position (top to bottom), then X position (left to right)
            sorted_bubbles = sorted(bubbles, key=lambda b: (b.priority, b.y, b.x))
        else:  # left_to_right
            # Sort by X position (left to right), then Y position (top to bottom)
            sorted_bubbles = sorted(bubbles, key=lambda b: (b.priority, b.x, b.y))

        return sorted_bubbles

    def _calculate_overlap(self, x1: int, y1: int, w1: int, h1: int,
                          x2: int, y2: int, w2: int, h2: int) -> float:
        """Calculate overlap ratio between two rectangles."""
        # Calculate intersection
        left = max(x1, x2)
        top = max(y1, y2)
        right = min(x1 + w1, x2 + w2)
        bottom = min(y1 + h1, y2 + h2)
        
        if left >= right or top >= bottom:
            return 0.0
        
        intersection_area = (right - left) * (bottom - top)
        rect1_area = w1 * h1
        
        return intersection_area / rect1_area if rect1_area > 0 else 0.0

    def draw_bubble(self, image: np.ndarray, bubble: DialogueBubble) -> np.ndarray:
        """Draw a dialogue bubble on the image with shape-specific styling."""
        result_image = image.copy()

        # Get shape-specific styles
        shape_style = self.shape_styles.get(bubble.shape, self.shape_styles["rounded"])

        # Draw bubble based on shape
        if bubble.shape == "rounded":
            self._draw_rounded_bubble(result_image, bubble, shape_style)
        elif bubble.shape == "jagged":
            self._draw_jagged_bubble(result_image, bubble, shape_style)
        elif bubble.shape == "thought":
            self._draw_thought_bubble(result_image, bubble, shape_style)
        elif bubble.shape == "dashed":
            self._draw_dashed_bubble(result_image, bubble, shape_style)
        elif bubble.shape == "narrative":
            self._draw_narrative_box(result_image, bubble, shape_style)
        else:
            # Default to rounded
            self._draw_rounded_bubble(result_image, bubble, shape_style)

        # Draw text
        self._draw_text_in_bubble(result_image, bubble)

        return result_image

    def _draw_rounded_bubble(self, image: np.ndarray, bubble: DialogueBubble, style: dict):
        """Draw a rounded speech bubble."""
        center_x = bubble.x + bubble.width // 2
        center_y = bubble.y + bubble.height // 2
        axes = (bubble.width // 2 - 5, bubble.height // 2 - 5)

        # Draw filled ellipse
        cv2.ellipse(image, (center_x, center_y), axes, 0, 0, 360,
                   self.bubble_styles["bubble_color"], -1)

        # Draw border
        cv2.ellipse(image, (center_x, center_y), axes, 0, 0, 360,
                   self.bubble_styles["border_color"], style["border_thickness"])

    def _draw_jagged_bubble(self, image: np.ndarray, bubble: DialogueBubble, style: dict):
        """Draw a jagged bubble for shouting/excitement."""
        # Create jagged points around the bubble
        center_x = bubble.x + bubble.width // 2
        center_y = bubble.y + bubble.height // 2

        # Generate jagged outline points
        points = []
        num_points = 16
        jagged_intensity = style.get("jagged_intensity", 8)

        for i in range(num_points):
            angle = (2 * math.pi * i) / num_points
            base_radius_x = bubble.width // 2 - 5
            base_radius_y = bubble.height // 2 - 5

            # Add jagged variation
            variation = jagged_intensity if i % 2 == 0 else -jagged_intensity
            radius_x = base_radius_x + variation
            radius_y = base_radius_y + variation

            x = int(center_x + radius_x * math.cos(angle))
            y = int(center_y + radius_y * math.sin(angle))
            points.append([x, y])

        points = np.array(points, np.int32)

        # Draw filled polygon
        cv2.fillPoly(image, [points], self.bubble_styles["bubble_color"])

        # Draw border
        cv2.polylines(image, [points], True, self.bubble_styles["border_color"],
                     style["border_thickness"])

    def _draw_thought_bubble(self, image: np.ndarray, bubble: DialogueBubble, style: dict):
        """Draw a cloud-like thought bubble."""
        # Draw main bubble as rounded
        self._draw_rounded_bubble(image, bubble, style)

        # Add small cloud bubbles leading to the main bubble
        if style.get("cloud_bubbles", False):
            # Draw 2-3 small circles leading to the bubble
            small_radius = 8
            medium_radius = 12

            # Position small bubbles below and to the side
            small_x = bubble.x + bubble.width // 4
            small_y = bubble.y + bubble.height + 10

            medium_x = bubble.x + bubble.width // 3
            medium_y = bubble.y + bubble.height + 25

            # Draw small bubbles
            cv2.circle(image, (small_x, small_y), small_radius,
                      self.bubble_styles["bubble_color"], -1)
            cv2.circle(image, (small_x, small_y), small_radius,
                      self.bubble_styles["border_color"], 1)

            cv2.circle(image, (medium_x, medium_y), medium_radius,
                      self.bubble_styles["bubble_color"], -1)
            cv2.circle(image, (medium_x, medium_y), medium_radius,
                      self.bubble_styles["border_color"], 1)

    def _draw_dashed_bubble(self, image: np.ndarray, bubble: DialogueBubble, style: dict):
        """Draw a dashed outline bubble for whispers."""
        center_x = bubble.x + bubble.width // 2
        center_y = bubble.y + bubble.height // 2
        axes = (bubble.width // 2 - 5, bubble.height // 2 - 5)

        # Draw filled ellipse
        cv2.ellipse(image, (center_x, center_y), axes, 0, 0, 360,
                   self.bubble_styles["bubble_color"], -1)

        # Draw dashed border by drawing multiple small arcs
        dash_length = style.get("dash_pattern", [5, 3])[0]
        gap_length = style.get("dash_pattern", [5, 3])[1]

        circumference = 2 * math.pi * max(axes)
        total_pattern = dash_length + gap_length
        num_dashes = int(circumference / total_pattern)

        for i in range(num_dashes):
            start_angle = (360 * i * total_pattern) / circumference
            end_angle = start_angle + (360 * dash_length) / circumference

            cv2.ellipse(image, (center_x, center_y), axes, 0, start_angle, end_angle,
                       self.bubble_styles["border_color"], style["border_thickness"])

    def _draw_narrative_box(self, image: np.ndarray, bubble: DialogueBubble, style: dict):
        """Draw a rectangular narrative box."""
        # Draw filled rectangle
        cv2.rectangle(image,
                     (bubble.x, bubble.y),
                     (bubble.x + bubble.width, bubble.y + bubble.height),
                     self.bubble_styles["bubble_color"], -1)

        # Draw border
        cv2.rectangle(image,
                     (bubble.x, bubble.y),
                     (bubble.x + bubble.width, bubble.y + bubble.height),
                     self.bubble_styles["border_color"], style["border_thickness"])

    def _draw_text_in_bubble(self, image: np.ndarray, bubble: DialogueBubble):
        """Draw text inside a dialogue bubble with proper wrapping and sizing."""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = self.bubble_styles["font_scale"]
        thickness = self.bubble_styles["font_thickness"]
        color = self.bubble_styles["text_color"]

        # Use the same wrapping logic as text sizing
        try:
            # Try PIL-based wrapping first
            temp_img = Image.new('RGB', (1000, 1000), color='white')
            draw = ImageDraw.Draw(temp_img)

            try:
                pil_font = ImageFont.truetype("arial.ttf", self.font_size)
            except:
                pil_font = ImageFont.load_default()

            lines = self._wrap_text(bubble.text, pil_font, draw)

        except Exception as e:
            print(f"     ⚠️ PIL text wrapping failed: {e}, using simple wrapping")
            # Fallback to simple wrapping
            words = bubble.text.split()
            lines = []
            current_line = ""

            for word in words:
                test_line = current_line + " " + word if current_line else word
                if len(test_line) <= self.max_chars_per_line:
                    current_line = test_line
                else:
                    if current_line:
                        lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

        # Calculate line height and starting position
        line_height = int(self.font_size * self.line_spacing * 1.5)  # Convert to OpenCV scale
        total_text_height = len(lines) * line_height
        start_y = bubble.y + (bubble.height - total_text_height) // 2 + line_height

        # Check for text overflow and log warning
        text_area_height = len(lines) * line_height
        available_height = bubble.height - self.text_padding_y * 2

        if text_area_height > available_height:
            print(f"     ⚠️ WARNING: Text overflow detected! Text height: {text_area_height}px, Available: {available_height}px")

        # Draw each line
        for i, line in enumerate(lines):
            if not line.strip():  # Skip empty lines
                continue

            # Calculate text width for centering
            (text_width, text_height), _ = cv2.getTextSize(line, font, font_scale, thickness)
            text_x = bubble.x + (bubble.width - text_width) // 2
            text_y = start_y + i * line_height

            # Check if text fits within bubble bounds
            if text_x < bubble.x + self.text_padding_x:
                print(f"     ⚠️ WARNING: Text extends beyond left bubble boundary")
            if text_x + text_width > bubble.x + bubble.width - self.text_padding_x:
                print(f"     ⚠️ WARNING: Text extends beyond right bubble boundary")
            if text_y > bubble.y + bubble.height - self.text_padding_y:
                print(f"     ⚠️ WARNING: Text extends beyond bottom bubble boundary")

            # Draw the text
            cv2.putText(image, line, (text_x, text_y), font, font_scale, color, thickness)

        # Store debug information if debug mode is enabled
        if self.debug_mode:
            self.debug_overlays.append({
                'type': 'text_area',
                'bubble': bubble,
                'lines': lines,
                'line_height': line_height,
                'total_height': total_text_height,
                'available_height': available_height
            })

    def place_dialogue(self, image_path: str, dialogue_lines: List[str],
                      speakers: List[str] = None) -> Tuple[np.ndarray, List[DialogueBubble], Dict[str, Any]]:
        """
        Main method to place dialogue bubbles on an image.

        Args:
            image_path: Path to the input image
            dialogue_lines: List of dialogue text
            speakers: List of speaker names (optional)

        Returns:
            Tuple of (processed_image, bubble_list, placement_metadata)
        """
        print(f"   💬 Placing {len(dialogue_lines)} dialogue bubbles")

        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Detect visual regions to avoid
        visual_regions = self.detect_visual_regions(image)

        # Initialize placement tracking
        placed_bubbles = []
        placement_scores = []

        # Process each dialogue line to create initial bubbles
        initial_bubbles = []
        for i, dialogue in enumerate(dialogue_lines):
            if not dialogue.strip():
                continue

            speaker = speakers[i] if speakers and i < len(speakers) else f"speaker_{i+1}"

            # Detect tone and select appropriate shape
            tone = self.detect_dialogue_tone(dialogue)
            shape = self.select_bubble_shape(tone)

            # Calculate bubble size (with shape-specific padding)
            bubble_width, bubble_height = self.calculate_text_size(dialogue)
            shape_style = self.shape_styles.get(shape, self.shape_styles["rounded"])
            padding_mult = shape_style.get("padding_multiplier", 1.0)

            bubble_width = int(bubble_width * padding_mult)
            bubble_height = int(bubble_height * padding_mult)

            # Find initial position using grid-based placement
            x, y, score = self.find_grid_position(
                image, bubble_width, bubble_height, visual_regions, initial_bubbles, i
            )

            # Create bubble with tone and shape information
            bubble = DialogueBubble(
                text=dialogue,
                x=x, y=y,
                width=bubble_width, height=bubble_height,
                speaker=speaker,
                confidence=score,
                shape=shape,
                tone=tone,
                priority=1 if tone in ["angry", "excited"] else 2  # High priority for emphasis
            )

            initial_bubbles.append(bubble)
            placement_scores.append(score)

            print(f"     Bubble {i+1}: '{dialogue[:20]}...' tone:{tone} shape:{shape} at ({x}, {y})")

        # Optimize bubble layout to prevent overlaps
        if len(initial_bubbles) > 1:
            placed_bubbles = self.optimize_bubble_layout(initial_bubbles, image.shape)
        else:
            placed_bubbles = initial_bubbles

        # Arrange bubbles by reading order
        placed_bubbles = self.arrange_bubbles_by_reading_order(placed_bubbles)

        # Draw all bubbles on the image
        for bubble in placed_bubbles:
            image = self.draw_bubble(image, bubble)

        # Generate placement metadata
        metadata = self._generate_placement_metadata(placed_bubbles, placement_scores, visual_regions)

        return image, placed_bubbles, metadata

    def enable_debug_mode(self):
        """Enable debug mode for detailed overlay generation."""
        self.debug_mode = True
        self.debug_overlays = []

    def create_debug_overlay(self, image: np.ndarray, bubbles: List[DialogueBubble]) -> np.ndarray:
        """Create enhanced debug overlay showing bubble shapes, overlaps, and layout info."""
        debug_image = image.copy()

        # Check for overlaps and mark them
        overlap_pairs = []
        for i, bubble1 in enumerate(bubbles):
            for j, bubble2 in enumerate(bubbles[i+1:], i+1):
                if bubble1.overlaps_with(bubble2, self.bubble_separation):
                    overlap_pairs.append((i, j))

        # Draw bubbles with color coding
        for i, bubble in enumerate(bubbles):
            # Determine color based on overlap status
            has_overlap = any(i in pair for pair in overlap_pairs)
            boundary_color = (0, 0, 255) if has_overlap else (0, 255, 0)  # Red if overlap, green if not

            # Draw bubble boundary rectangle
            cv2.rectangle(debug_image,
                         (bubble.x, bubble.y),
                         (bubble.x + bubble.width, bubble.y + bubble.height),
                         boundary_color, 3 if has_overlap else 2)

            # Draw text area rectangle in blue
            text_x = bubble.x + self.text_padding_x
            text_y = bubble.y + self.text_padding_y
            text_width = bubble.width - self.text_padding_x * 2
            text_height = bubble.height - self.text_padding_y * 2

            cv2.rectangle(debug_image,
                         (text_x, text_y),
                         (text_x + text_width, text_y + text_height),
                         (255, 0, 0), 1)

            # Add bubble information labels
            label_x = bubble.x - 30
            label_y = bubble.y + 20

            # Bubble ID and shape
            cv2.putText(debug_image, f"B{i+1}:{bubble.shape[:3]}",
                       (label_x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(debug_image, f"B{i+1}:{bubble.shape[:3]}",
                       (label_x, label_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            # Size and tone information
            info_text = f"{bubble.width}x{bubble.height} {bubble.tone[:4]}"
            cv2.putText(debug_image, info_text,
                       (bubble.x, bubble.y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 2)
            cv2.putText(debug_image, info_text,
                       (bubble.x, bubble.y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # Draw overlap connections
        for i, j in overlap_pairs:
            bubble1, bubble2 = bubbles[i], bubbles[j]
            center1 = (bubble1.x + bubble1.width // 2, bubble1.y + bubble1.height // 2)
            center2 = (bubble2.x + bubble2.width // 2, bubble2.y + bubble2.height // 2)

            # Draw red line connecting overlapping bubbles
            cv2.line(debug_image, center1, center2, (0, 0, 255), 2)

            # Add overlap warning text
            mid_x = (center1[0] + center2[0]) // 2
            mid_y = (center1[1] + center2[1]) // 2
            cv2.putText(debug_image, "OVERLAP!",
                       (mid_x - 30, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            cv2.putText(debug_image, "OVERLAP!",
                       (mid_x - 30, mid_y),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

        # Enhanced legend
        legend_y = 30
        cv2.putText(debug_image, "Enhanced Debug Overlay:", (10, legend_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(debug_image, "Green: No overlap", (10, legend_y + 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(debug_image, "Red: Overlap detected", (10, legend_y + 45),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
        cv2.putText(debug_image, "Blue: Text area", (10, legend_y + 65),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)

        # Layout statistics
        stats_y = legend_y + 100
        cv2.putText(debug_image, f"Bubbles: {len(bubbles)}", (10, stats_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(debug_image, f"Overlaps: {len(overlap_pairs)}", (10, stats_y + 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # Shape usage statistics
        shape_counts = {}
        for bubble in bubbles:
            shape_counts[bubble.shape] = shape_counts.get(bubble.shape, 0) + 1

        shape_y = stats_y + 50
        cv2.putText(debug_image, "Shapes:", (10, shape_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        for i, (shape, count) in enumerate(shape_counts.items()):
            cv2.putText(debug_image, f"{shape}: {count}", (10, shape_y + 20 + i * 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

        return debug_image

    def _generate_placement_metadata(self, bubbles: List[DialogueBubble],
                                   scores: List[float], regions: List[VisualRegion]) -> Dict[str, Any]:
        """Generate metadata about the dialogue placement."""
        if not bubbles:
            return {
                "bubble_count": 0,
                "average_placement_score": 0.0,
                "bubble_overlap_score": 1.0,
                "visual_regions_detected": len(regions),
                "placement_quality": "no_dialogue"
            }

        avg_score = sum(scores) / len(scores)

        # Calculate bubble overlap score
        overlap_score = self._calculate_bubble_overlap_score(bubbles)

        # Determine placement quality
        if avg_score >= 0.8:
            quality = "excellent"
        elif avg_score >= 0.6:
            quality = "good"
        elif avg_score >= 0.4:
            quality = "fair"
        else:
            quality = "poor"

        # Calculate shape and tone usage
        shape_usage = {}
        tone_usage = {}
        for bubble in bubbles:
            shape_usage[bubble.shape] = shape_usage.get(bubble.shape, 0) + 1
            tone_usage[bubble.tone] = tone_usage.get(bubble.tone, 0) + 1

        # Analyze overlaps in detail
        overlap_pairs = []
        for i, bubble1 in enumerate(bubbles):
            for j, bubble2 in enumerate(bubbles[i+1:], i+1):
                if bubble1.overlaps_with(bubble2, self.bubble_separation):
                    overlap_pairs.append((i, j))

        return {
            "bubble_count": len(bubbles),
            "average_placement_score": round(avg_score, 3),
            "bubble_overlap_score": round(overlap_score, 3),
            "visual_regions_detected": len(regions),
            "placement_quality": quality,
            "color_mode": self.color_mode,
            "individual_scores": [round(s, 3) for s in scores],
            "shape_usage": shape_usage,
            "tone_usage": tone_usage,
            "overlap_analysis": {
                "overlap_count": len(overlap_pairs),
                "overlap_pairs": overlap_pairs,
                "zero_overlap_achieved": len(overlap_pairs) == 0
            },
            "layout_optimization": {
                "iterations_used": len(self.layout_debug_info),
                "algorithm": "force_directed",
                "reading_order": self.preferred_reading_order
            },
            "bubble_positions": [
                {
                    "bubble_id": i + 1,
                    "x": b.x, "y": b.y,
                    "width": b.width, "height": b.height,
                    "speaker": b.speaker,
                    "shape": b.shape,
                    "tone": b.tone,
                    "priority": b.priority,
                    "confidence": round(b.confidence, 3),
                    "text_preview": b.text[:30] + "..." if len(b.text) > 30 else b.text
                }
                for i, b in enumerate(bubbles)
            ]
        }

    def _calculate_bubble_overlap_score(self, bubbles: List[DialogueBubble]) -> float:
        """Calculate how well bubbles avoid overlapping each other."""
        if len(bubbles) <= 1:
            return 1.0

        total_overlap = 0.0
        comparisons = 0

        for i in range(len(bubbles)):
            for j in range(i + 1, len(bubbles)):
                overlap = self._calculate_overlap(
                    bubbles[i].x, bubbles[i].y, bubbles[i].width, bubbles[i].height,
                    bubbles[j].x, bubbles[j].y, bubbles[j].width, bubbles[j].height
                )
                total_overlap += overlap
                comparisons += 1

        avg_overlap = total_overlap / comparisons if comparisons > 0 else 0.0
        return max(0.0, 1.0 - avg_overlap)


def create_sample_dialogue() -> List[str]:
    """Create sample dialogue for testing."""
    return [
        "What is this ancient symbol?",
        "It looks like a warning...",
        "We should be careful here."
    ]


def test_dialogue_placement():
    """Test the dialogue placement system."""
    print("🧪 Testing Dialogue Placement System")

    # Create test engine
    engine = DialoguePlacementEngine("black_and_white")

    # Test text size calculation
    test_text = "This is a test dialogue bubble"
    width, height = engine.calculate_text_size(test_text)
    print(f"   Text size for '{test_text}': {width}x{height}")

    # Test bubble creation
    bubble = DialogueBubble(
        text=test_text, x=50, y=50, width=width, height=height,
        speaker="test_speaker"
    )
    print(f"   Created bubble: {bubble}")

    print("✅ Dialogue placement system test completed")


if __name__ == "__main__":
    test_dialogue_placement()
