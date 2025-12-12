#!/usr/bin/env python3
"""
MangaGen - Dialogue Bubble Placer

Places dialogue bubbles on manga panels using the salvaged DialoguePlacementEngine.

Usage:
    python scripts/place_bubbles.py --panels outputs/ --scene scene_plan.json
    python scripts/place_bubbles.py --panels outputs/ --scene scene_plan.json --output bubbles.json

Features:
    - Face detection to avoid covering characters
    - Tone-based bubble shape selection (speech, thought, shout, whisper)
    - Force-directed layout optimization
    - Reading order arrangement
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Run: pip install opencv-python Pillow numpy")
    sys.exit(1)

from src.schemas import MangaScenePlan, BubblePlacement

# Import the salvaged DialoguePlacementEngine
SALVAGED_DIR = Path(__file__).parent.parent / "archive" / "salvaged"
sys.path.insert(0, str(SALVAGED_DIR))

try:
    from dialogue_placer import DialoguePlacementEngine, DialogueBubble
    DIALOGUE_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ DialoguePlacementEngine not available: {e}")
    print("   Using fallback simple bubble placement")
    DIALOGUE_ENGINE_AVAILABLE = False


# ============================================
# Simple Fallback Bubble Placer
# ============================================

class SimpleBubblePlacer:
    """
    Simple fallback bubble placer when DialoguePlacementEngine is not available.
    Places bubbles in corners/edges of the panel.
    """
    
    def __init__(self, style: str = "bw_manga"):
        self.style = style
        print("📍 Using simple bubble placement (fallback)")
    
    def calculate_bubble_positions(
        self,
        image_path: Path,
        dialogues: List[Dict[str, Any]]
    ) -> List[BubblePlacement]:
        """Calculate bubble positions for a panel."""
        img = Image.open(image_path)
        width, height = img.size
        
        # Define placement zones (top-left, top-right, bottom-left, bottom-right)
        zones = [
            {"x": 20, "y": 20},                           # Top-left
            {"x": width - 220, "y": 20},                  # Top-right
            {"x": 20, "y": height - 120},                 # Bottom-left
            {"x": width - 220, "y": height - 120},        # Bottom-right
        ]
        
        bubbles = []
        for i, dialogue in enumerate(dialogues):
            zone = zones[i % len(zones)]
            
            # Estimate bubble size based on text length
            text = dialogue.get("text", "")
            char_width = 8
            bubble_width = min(200, max(80, len(text) * char_width))
            bubble_height = max(50, (len(text) // 25 + 1) * 25 + 20)
            
            bubble = BubblePlacement(
                panel_number=dialogue.get("panel_number", 1),
                x=zone["x"],
                y=zone["y"] + (i // 4) * 100,
                width=bubble_width,
                height=bubble_height,
                text=text,
                speaker=dialogue.get("speaker", ""),
                bubble_type=dialogue.get("bubble_type", "speech")
            )
            bubbles.append(bubble)
        
        return bubbles


# ============================================
# Smart Bubble Placer (uses salvaged engine)
# ============================================

class SmartBubblePlacer:
    """
    Smart bubble placer using the salvaged DialoguePlacementEngine.
    Features face detection, tone analysis, and force-directed optimization.
    """
    
    def __init__(self, style: str = "bw_manga"):
        color_mode = "bw" if style == "bw_manga" else "color"
        self.engine = DialoguePlacementEngine(color_mode=color_mode)
        print("🎯 Using smart bubble placement (face detection, tone analysis)")
    
    def calculate_bubble_positions(
        self,
        image_path: Path,
        dialogues: List[Dict[str, Any]]
    ) -> List[BubblePlacement]:
        """Calculate optimal bubble positions for a panel."""
        # Load image
        image = cv2.imread(str(image_path))
        if image is None:
            print(f"⚠️ Could not load image: {image_path}")
            return []
        
        # Detect visual regions to avoid
        visual_regions = self.engine.detect_visual_regions(image)
        print(f"   Detected {len(visual_regions)} visual regions to avoid")
        
        # Create dialogue bubbles
        engine_bubbles = []
        for i, dialogue in enumerate(dialogues):
            text = dialogue.get("text", "")
            if not text:
                continue
            
            # Calculate text size
            width, height = self.engine.calculate_text_size(text)
            
            # Detect dialogue tone
            tone = self.engine.detect_dialogue_tone(text)
            bubble_shape = self.engine.select_bubble_shape(tone)
            
            # Find optimal position (returns x, y, score)
            x, y, _score = self.engine.find_grid_position(
                image=image,
                bubble_width=width,
                bubble_height=height,
                visual_regions=visual_regions,
                existing_bubbles=engine_bubbles,
                bubble_index=i
            )
            
            bubble = DialogueBubble(
                text=text,
                x=x,
                y=y,
                width=width,
                height=height,
                speaker=dialogue.get("speaker", "unknown"),
                bubble_type=dialogue.get("bubble_type", "speech"),
                priority=i + 1  # Use priority for ordering
            )
            engine_bubbles.append(bubble)
        
        # Optimize layout
        if len(engine_bubbles) > 1:
            engine_bubbles = self.engine.optimize_bubble_layout(
                bubbles=engine_bubbles,
                image_shape=image.shape
            )
        
        # Arrange by reading order
        engine_bubbles = self.engine.arrange_bubbles_by_reading_order(engine_bubbles)
        
        # Convert to BubblePlacement schema
        result = []
        for bubble in engine_bubbles:
            result.append(BubblePlacement(
                panel_number=dialogues[0].get("panel_number", 1) if dialogues else 1,
                x=bubble.x,
                y=bubble.y,
                width=bubble.width,
                height=bubble.height,
                text=bubble.text,
                speaker=bubble.speaker,
                bubble_type=bubble.bubble_type
            ))
        
        return result


# ============================================
# Main Pipeline
# ============================================

def place_bubbles(
    scene_plan: MangaScenePlan,
    panels_dir: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Calculate bubble positions for all panels.
    
    Args:
        scene_plan: The scene plan with dialogue data
        panels_dir: Directory containing panel images
        output_path: Optional path to save bubbles.json
        
    Returns:
        Dictionary with bubble placement data per panel
    """
    panels_dir = Path(panels_dir)
    
    # Initialize bubble placer
    if DIALOGUE_ENGINE_AVAILABLE:
        placer = SmartBubblePlacer(style=scene_plan.style)
    else:
        placer = SimpleBubblePlacer(style=scene_plan.style)
    
    # Process each panel
    all_bubbles = {}
    
    for panel in scene_plan.panels:
        panel_path = panels_dir / f"panel_{panel.panel_number:02d}.png"
        
        if not panel_path.exists():
            print(f"⚠️ Panel image not found: {panel_path}")
            continue
        
        # Prepare dialogue data
        dialogues = []
        for d in panel.dialogue:
            dialogues.append({
                "panel_number": panel.panel_number,
                "speaker": d.speaker,
                "text": d.text,
                "emotion": d.emotion,
                "bubble_type": d.bubble_type
            })
        
        if not dialogues:
            print(f"   Panel {panel.panel_number}: No dialogue")
            all_bubbles[f"panel_{panel.panel_number:02d}"] = []
            continue
        
        print(f"   Panel {panel.panel_number}: {len(dialogues)} dialogue line(s)")
        
        # Calculate positions
        bubbles = placer.calculate_bubble_positions(panel_path, dialogues)
        
        all_bubbles[f"panel_{panel.panel_number:02d}"] = [
            b.model_dump() for b in bubbles
        ]
    
    # Save results
    if output_path:
        output_path = Path(output_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_bubbles, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved bubble data to: {output_path}")
    
    return all_bubbles


def main():
    parser = argparse.ArgumentParser(
        description="Calculate dialogue bubble positions for manga panels",
        epilog="Example: python place_bubbles.py --panels outputs/ --scene scene_plan.json"
    )
    parser.add_argument(
        "--panels",
        type=str,
        required=True,
        help="Directory containing panel images"
    )
    parser.add_argument(
        "--scene",
        type=str,
        required=True,
        help="Path to scene_plan.json"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="bubbles.json",
        help="Output JSON file path (default: bubbles.json)"
    )
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("💬 MangaGen - Bubble Placer")
    print("=" * 50)
    
    # Load scene plan
    scene_path = Path(args.scene)
    if not scene_path.exists():
        print(f"❌ Scene plan not found: {scene_path}")
        sys.exit(1)
    
    print(f"📄 Loading scene plan: {scene_path}")
    with open(scene_path, "r", encoding="utf-8") as f:
        scene_data = json.load(f)
    
    scene_plan = MangaScenePlan(**scene_data)
    print(f"   Title: {scene_plan.title}")
    print(f"   Panels: {len(scene_plan.panels)}")
    
    # Check panels directory
    panels_dir = Path(args.panels)
    if not panels_dir.exists():
        print(f"❌ Panels directory not found: {panels_dir}")
        sys.exit(1)
    
    # Count dialogue
    total_dialogue = sum(len(p.dialogue) for p in scene_plan.panels)
    print(f"   Total dialogue lines: {total_dialogue}")
    print()
    
    # Place bubbles
    print("📍 Calculating bubble positions...")
    all_bubbles = place_bubbles(
        scene_plan=scene_plan,
        panels_dir=panels_dir,
        output_path=Path(args.output)
    )
    
    # Summary
    print()
    print("=" * 50)
    print("📋 Bubble Placement Summary")
    print("=" * 50)
    
    total_bubbles = 0
    for panel_key, bubbles in all_bubbles.items():
        print(f"  {panel_key}: {len(bubbles)} bubble(s)")
        total_bubbles += len(bubbles)
    
    print(f"\nTotal bubbles placed: {total_bubbles}")
    print()
    print("✅ Bubble placement complete!")
    print(f"📄 Output: {args.output}")


if __name__ == "__main__":
    main()
