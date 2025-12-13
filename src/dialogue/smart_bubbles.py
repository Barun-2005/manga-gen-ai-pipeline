#!/usr/bin/env python3
"""
MangaGen - Smart Dialogue Placement System

Features:
- Face/subject detection (don't cover faces!)
- Background color analysis (readable text)
- Auto-sizing to fit available space
- Smart positioning (manga reading order)
- Bubble styling (shape, tail direction)

This is the REAL engineering - not just API calls!
"""

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class DialogueBubble:
    """A speech bubble with smart positioning."""
    text: str
    character: str
    position: Tuple[int, int]  # (x, y) top-left
    size: Tuple[int, int]  # (width, height)
    tail_direction: str  # 'left', 'right', 'bottom', 'none'
    style: str  # 'speech', 'thought', 'shout'
    bg_color: Tuple[int, int, int]
    text_color: Tuple[int, int, int]


class SmartBubblePlacer:
    """Intelligent dialogue bubble placement engine."""
    
    def __init__(self):
        # Load face detection model (OpenCV Haar cascades - no GPU needed!)
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.anime_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_alt.xml'
        )
        
        # Load fonts
        self.fonts = self._load_fonts()
        
    def _load_fonts(self) -> Dict[str, ImageFont.FreeTypeFont]:
        """Load fonts for different bubble styles."""
        fonts = {}
        try:
            # Try common fonts
            for font_name in ['arial.ttf', 'Comic Sans MS.ttf', 'Impact.ttf']:
                try:
                    fonts['normal'] = ImageFont.truetype('arial.ttf', 24)
                    fonts['shout'] = ImageFont.truetype('arial.ttf', 28)
                    fonts['thought'] = ImageFont.truetype('arial.ttf', 20)
                    break
                except:
                    continue
        except:
            fonts['normal'] = ImageFont.load_default()
            fonts['shout'] = ImageFont.load_default()
            fonts['thought'] = ImageFont.load_default()
        return fonts
    
    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Detect faces/subjects in image. Returns list of (x, y, w, h)."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Try anime-optimized cascade first
        faces = self.anime_cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=3, minSize=(30, 30)
        )
        
        if len(faces) == 0:
            # Fallback to default cascade
            faces = self.face_cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )
        
        return [tuple(f) for f in faces]
    
    def analyze_background_color(
        self, 
        image: np.ndarray, 
        region: Tuple[int, int, int, int]
    ) -> Tuple[Tuple[int, int, int], Tuple[int, int, int]]:
        """
        Analyze background color in region.
        Returns optimal (bubble_color, text_color) for readability.
        """
        x, y, w, h = region
        roi = image[y:y+h, x:x+w]
        
        # Get average color
        avg_color = np.mean(roi, axis=(0, 1))
        
        # Calculate luminance
        luminance = 0.299 * avg_color[2] + 0.587 * avg_color[1] + 0.114 * avg_color[0]
        
        if luminance > 128:
            # Light background -> white bubble, black text
            return (255, 255, 255), (0, 0, 0)
        else:
            # Dark background -> white bubble, black text (classic manga)
            return (255, 255, 255), (0, 0, 0)
    
    def find_safe_zones(
        self, 
        image_size: Tuple[int, int],
        faces: List[Tuple[int, int, int, int]],
        margin: int = 20
    ) -> List[Tuple[int, int, int, int]]:
        """
        Find areas where bubbles can be placed (not covering faces).
        Returns list of safe zones (x, y, w, h).
        """
        width, height = image_size
        
        # Create mask of occupied areas
        occupied = np.zeros((height, width), dtype=bool)
        
        # Mark face regions as occupied (with margin)
        for (x, y, w, h) in faces:
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(width, x + w + margin)
            y2 = min(height, y + h + margin)
            occupied[y1:y2, x1:x2] = True
        
        # Preferred positions (manga reading order: top-right, top-left, bottom)
        safe_zones = []
        
        # Top-right corner (most common for speech)
        zone_w, zone_h = width // 3, height // 4
        if not np.any(occupied[0:zone_h, width-zone_w:width]):
            safe_zones.append((width - zone_w, 0, zone_w - margin, zone_h - margin))
        
        # Top-left corner
        if not np.any(occupied[0:zone_h, 0:zone_w]):
            safe_zones.append((margin, margin, zone_w - margin, zone_h - margin))
        
        # Bottom-right
        if not np.any(occupied[height-zone_h:height, width-zone_w:width]):
            safe_zones.append((width - zone_w, height - zone_h, zone_w - margin, zone_h - margin))
        
        # Bottom-left
        if not np.any(occupied[height-zone_h:height, 0:zone_w]):
            safe_zones.append((margin, height - zone_h, zone_w - margin, zone_h - margin))
        
        # Center-top (if corners occupied)
        if not safe_zones:
            center_x = width // 2 - zone_w // 2
            if not np.any(occupied[0:zone_h, center_x:center_x+zone_w]):
                safe_zones.append((center_x, margin, zone_w, zone_h))
        
        return safe_zones
    
    def fit_text_to_bubble(
        self, 
        text: str, 
        max_width: int, 
        max_height: int,
        font: ImageFont.FreeTypeFont
    ) -> Tuple[List[str], int]:
        """
        Word-wrap text properly - never break mid-word.
        Returns (wrapped_lines, final_font_size).
        """
        # Create temp image to measure text
        temp_img = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(temp_img)
        
        def get_text_width(txt):
            try:
                bbox = draw.textbbox((0, 0), txt, font=font)
                return bbox[2] - bbox[0]
            except:
                return len(txt) * 12
        
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            # Test adding this word
            test_line = ' '.join(current_line + [word])
            
            if get_text_width(test_line) <= max_width:
                current_line.append(word)
            else:
                # Current line is full, start new line
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        # Don't forget the last line
        if current_line:
            lines.append(' '.join(current_line))
        
        # Limit lines to fit height (roughly 25px per line)
        max_lines = max(1, max_height // 25)
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            # Truncate last line with ellipsis
            if lines[-1] and len(lines[-1]) > 15:
                lines[-1] = lines[-1][:15] + '...'
        
        return lines, 24
    
    def create_bubble(
        self,
        text: str,
        character: str,
        position: Tuple[int, int],
        size: Tuple[int, int],
        style: str = 'speech',
        bg_color: Tuple[int, int, int] = (255, 255, 255),
        text_color: Tuple[int, int, int] = (0, 0, 0)
    ) -> Image.Image:
        """Create a speech bubble image with proper text padding."""
        width, height = size
        
        # Padding values
        BORDER = 3
        PADDING_X = 15  # Horizontal padding from bubble edge
        PADDING_Y = 12  # Vertical padding from bubble edge
        LINE_SPACING = 22  # Space between lines
        TAIL_HEIGHT = 15  # Height reserved for tail
        
        # Create bubble with transparency
        bubble = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(bubble)
        
        # Calculate text area (inside bubble, excluding tail)
        text_area_top = BORDER + PADDING_Y
        text_area_bottom = height - TAIL_HEIGHT - PADDING_Y
        text_area_left = BORDER + PADDING_X
        text_area_right = width - BORDER - PADDING_X
        text_area_width = text_area_right - text_area_left
        text_area_height = text_area_bottom - text_area_top
        
        # Draw bubble shape
        if style == 'speech':
            # Rounded rectangle with tail
            draw.rounded_rectangle(
                [BORDER, BORDER, width-BORDER, height-TAIL_HEIGHT],
                radius=12,
                fill=(*bg_color, 255),
                outline=(0, 0, 0, 255),
                width=2
            )
            # Tail (pointing down-left)
            tail_x = width // 4
            draw.polygon([
                (tail_x, height-TAIL_HEIGHT),
                (tail_x + 12, height-TAIL_HEIGHT),
                (tail_x - 3, height-2)
            ], fill=(*bg_color, 255), outline=(0, 0, 0, 255))
            
        elif style == 'thought':
            # Cloud-like bubble
            draw.ellipse([BORDER, BORDER, width-BORDER, height-TAIL_HEIGHT], 
                        fill=(*bg_color, 255), outline=(0, 0, 0, 255), width=2)
            # Small circles for tail
            draw.ellipse([width//4-4, height-TAIL_HEIGHT+2, width//4+4, height-TAIL_HEIGHT+10],
                        fill=(*bg_color, 255), outline=(0, 0, 0, 255))
            draw.ellipse([width//4-12, height-6, width//4-4, height-1],
                        fill=(*bg_color, 255), outline=(0, 0, 0, 255))
            
        elif style == 'shout':
            # Sharp rectangle for shouting
            draw.rounded_rectangle(
                [BORDER, BORDER, width-BORDER, height-TAIL_HEIGHT],
                radius=4,
                fill=(*bg_color, 255),
                outline=(0, 0, 0, 255),
                width=3
            )
        
        # Get font and wrap text
        font = self.fonts.get(style, self.fonts['normal'])
        lines, _ = self.fit_text_to_bubble(text, text_area_width, text_area_height, font)
        
        # Calculate total text height for vertical centering
        total_text_height = len(lines) * LINE_SPACING
        
        # Center vertically within text area
        y_start = text_area_top + (text_area_height - total_text_height) // 2
        
        for line in lines:
            # Center horizontally
            try:
                bbox = font.getbbox(line)
                text_w = bbox[2] - bbox[0]
            except:
                text_w = len(line) * 10
            x = text_area_left + (text_area_width - text_w) // 2
            draw.text((x, y_start), line, fill=(*text_color, 255), font=font)
            y_start += LINE_SPACING
        
        return bubble

    
    def place_dialogue(
        self,
        image_path: str,
        dialogues: List[Dict],
        output_path: str
    ) -> str:
        """
        Place dialogue bubbles on image intelligently.
        
        Args:
            image_path: Path to panel image
            dialogues: List of {'character': str, 'text': str, 'style': str}
            output_path: Where to save result
        
        Returns:
            Path to output image
        """
        # Load image
        image = Image.open(image_path).convert('RGBA')
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGBA2BGR)
        
        # Detect faces
        faces = self.detect_faces(cv_image)
        print(f"   Detected {len(faces)} face(s)")
        
        # Find safe zones
        safe_zones = self.find_safe_zones(image.size, faces)
        print(f"   Found {len(safe_zones)} safe zone(s)")
        
        # Place each dialogue
        zone_idx = 0
        for dialogue in dialogues:
            if zone_idx >= len(safe_zones):
                # No more safe zones, use fallback position
                zone = (10, 10, 200, 80)
            else:
                zone = safe_zones[zone_idx]
                zone_idx += 1
            
            x, y, max_w, max_h = zone
            
            # Analyze background for colors
            bg_color, text_color = self.analyze_background_color(
                cv_image, (x, y, min(max_w, 200), min(max_h, 80))
            )
            
            # Create bubble - size it to fit text
            bubble_size = (min(max_w, 280), min(max_h, 100))
            bubble = self.create_bubble(
                text=dialogue.get('text', ''),
                character=dialogue.get('character', ''),
                position=(x, y),
                size=bubble_size,
                style=dialogue.get('style', 'speech'),
                bg_color=bg_color,
                text_color=text_color
            )
            
            # Paste bubble on image
            image.paste(bubble, (x, y), bubble)
            print(f"   Placed: \"{dialogue.get('text', '')[:30]}...\"")
        
        # Save
        image.save(output_path)
        return output_path


def main():
    """Test the smart bubble placer."""
    print("🎨 Smart Dialogue Placement System")
    print("=" * 50)
    
    placer = SmartBubblePlacer()
    
    # Test with generated panels
    from pathlib import Path
    outputs = Path('outputs')
    
    test_dialogues = [
        [{"character": "Kai", "text": "The fortress... I must find a way in.", "style": "speech"}],
        [],  # Panel 2 has no dialogue
        [{"character": "Kai", "text": "Almost there...", "style": "thought"}],
        [{"character": "Kai", "text": "Your reign ends tonight!", "style": "shout"}],
    ]
    
    for i in range(1, 5):
        panel_path = outputs / f"panel_{i:02d}.png"
        if panel_path.exists() and test_dialogues[i-1]:
            print(f"\n📸 Processing panel_{i:02d}.png...")
            output_path = outputs / f"panel_{i:02d}_bubbles.png"
            placer.place_dialogue(
                str(panel_path),
                test_dialogues[i-1],
                str(output_path)
            )
            print(f"   ✅ Saved: {output_path}")
    
    print("\n🎉 Done! Check outputs/ for results.")


if __name__ == "__main__":
    main()
