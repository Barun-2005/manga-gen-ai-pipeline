"""
V4.1 Layout Templates Library

Defines manga page layouts based on narrative archetypes.
Each template specifies panel positions as percentages of page dimensions.

Archetypes:
- EXPOSITION: World building, establishing shots
- DIALOGUE: Character conversations
- ACTION: Fights, chases, intense moments
- REVEAL: Plot twists, dramatic moments
- CLIFFHANGER: Chapter ending hooks
"""

from typing import Dict, List, Any

# =============================================================================
# LAYOUT TEMPLATES
# =============================================================================

LAYOUT_TEMPLATES: Dict[str, Dict[str, Any]] = {
    
    # =========================================================================
    # DEFAULT/FALLBACK - Classic 2x2 grid
    # =========================================================================
    "2x2_grid": {
        "name": "Classic Grid",
        "archetype": "DEFAULT",
        "panel_count": 4,
        "description": "Standard 2x2 manga layout, equal sized panels",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 50, "h": 50},
            {"id": 1, "x": 50, "y": 0, "w": 50, "h": 50},
            {"id": 2, "x": 0, "y": 50, "w": 50, "h": 50},
            {"id": 3, "x": 50, "y": 50, "w": 50, "h": 50},
        ]
    },
    
    # =========================================================================
    # EXPOSITION LAYOUTS (3) - World building, settings
    # =========================================================================
    "expo_1splash": {
        "name": "Full Splash",
        "archetype": "EXPOSITION",
        "panel_count": 1,
        "description": "Single full-page establishing shot for major locations",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 100},
        ]
    },
    
    "expo_1big_3small": {
        "name": "Big Top",
        "archetype": "EXPOSITION",
        "panel_count": 4,
        "description": "Large establishing panel at top (60%), 3 small details below",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 60},     # Big establishing shot
            {"id": 1, "x": 0, "y": 60, "w": 33, "h": 40},    # Detail 1
            {"id": 2, "x": 33, "y": 60, "w": 34, "h": 40},   # Detail 2
            {"id": 3, "x": 67, "y": 60, "w": 33, "h": 40},   # Detail 3
        ]
    },
    
    "expo_2wide_2small": {
        "name": "Wide Doubles",
        "archetype": "EXPOSITION",
        "panel_count": 4,
        "description": "2 wide panoramic panels + 2 small details",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 35},    # Wide panorama 1
            {"id": 1, "x": 0, "y": 35, "w": 100, "h": 35},   # Wide panorama 2
            {"id": 2, "x": 0, "y": 70, "w": 50, "h": 30},    # Small detail 1
            {"id": 3, "x": 50, "y": 70, "w": 50, "h": 30},   # Small detail 2
        ]
    },
    
    # =========================================================================
    # DIALOGUE LAYOUTS (4) - Character conversations
    # =========================================================================
    "talk_5panel": {
        "name": "Conversation Flow",
        "archetype": "DIALOGUE",
        "panel_count": 5,
        "description": "5 panels for back-and-forth dialogue",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 50, "h": 40},     # Speaker 1
            {"id": 1, "x": 50, "y": 0, "w": 50, "h": 40},    # Speaker 2
            {"id": 2, "x": 0, "y": 40, "w": 100, "h": 20},   # Wide reaction
            {"id": 3, "x": 0, "y": 60, "w": 50, "h": 40},    # Speaker 1
            {"id": 4, "x": 50, "y": 60, "w": 50, "h": 40},   # Speaker 2
        ]
    },
    
    "talk_6panel_grid": {
        "name": "Dialogue Grid",
        "archetype": "DIALOGUE",
        "panel_count": 6,
        "description": "3x2 grid for extended conversation",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 50, "h": 33},
            {"id": 1, "x": 50, "y": 0, "w": 50, "h": 33},
            {"id": 2, "x": 0, "y": 33, "w": 50, "h": 34},
            {"id": 3, "x": 50, "y": 33, "w": 50, "h": 34},
            {"id": 4, "x": 0, "y": 67, "w": 50, "h": 33},
            {"id": 5, "x": 50, "y": 67, "w": 50, "h": 33},
        ]
    },
    
    "talk_4panel_focus": {
        "name": "Focus Dialogue",
        "archetype": "DIALOGUE",
        "panel_count": 4,
        "description": "4 panels with center focus for emotional moments",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 55, "h": 50},     # Speaker close-up
            {"id": 1, "x": 55, "y": 0, "w": 45, "h": 50},    # Reaction
            {"id": 2, "x": 0, "y": 50, "w": 45, "h": 50},    # Environment
            {"id": 3, "x": 45, "y": 50, "w": 55, "h": 50},   # Key response
        ]
    },
    
    "talk_reaction_strip": {
        "name": "Reaction Strip",
        "archetype": "DIALOGUE",
        "panel_count": 5,
        "description": "2 big speakers + 3 small reaction strip at bottom",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 50, "h": 55},     # Main speaker 1
            {"id": 1, "x": 50, "y": 0, "w": 50, "h": 55},    # Main speaker 2
            {"id": 2, "x": 0, "y": 55, "w": 33, "h": 45},    # Reaction 1
            {"id": 3, "x": 33, "y": 55, "w": 34, "h": 45},   # Reaction 2
            {"id": 4, "x": 67, "y": 55, "w": 33, "h": 45},   # Reaction 3
        ]
    },
    
    # =========================================================================
    # ACTION LAYOUTS (4) - Fights, chases, intense moments
    # =========================================================================
    "action_2slant": {
        "name": "Dynamic Split",
        "archetype": "ACTION",
        "panel_count": 2,
        "description": "2 diagonal panels for dynamic action sequence",
        "slanted": True,
        "angle": 10,
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 50, "slant": "down"},
            {"id": 1, "x": 0, "y": 50, "w": 100, "h": 50, "slant": "up"},
        ]
    },
    
    "action_3dynamic": {
        "name": "Triple Impact",
        "archetype": "ACTION",
        "panel_count": 3,
        "description": "3 panels with varied sizes for action sequence",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 60, "h": 55},     # Main action
            {"id": 1, "x": 60, "y": 0, "w": 40, "h": 55},    # Reaction/follow-up
            {"id": 2, "x": 0, "y": 55, "w": 100, "h": 45},   # Wide impact
        ]
    },
    
    "action_panorama": {
        "name": "Action Panorama",
        "archetype": "ACTION",
        "panel_count": 3,
        "description": "Wide panoramic action + 2 quick cuts",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 55},    # Wide action panorama
            {"id": 1, "x": 0, "y": 55, "w": 50, "h": 45},    # Quick cut 1
            {"id": 2, "x": 50, "y": 55, "w": 50, "h": 45},   # Quick cut 2
        ]
    },
    
    "action_impact": {
        "name": "Impact Focus",
        "archetype": "ACTION",
        "panel_count": 4,
        "description": "Large impact panel + 3 quick reaction cuts",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 65},    # Big impact moment
            {"id": 1, "x": 0, "y": 65, "w": 33, "h": 35},    # Quick cut 1
            {"id": 2, "x": 33, "y": 65, "w": 34, "h": 35},   # Quick cut 2
            {"id": 3, "x": 67, "y": 65, "w": 33, "h": 35},   # Quick cut 3
        ]
    },
    
    # =========================================================================
    # REVEAL LAYOUTS (2) - Plot twists, dramatic moments
    # =========================================================================
    "reveal_fullpage": {
        "name": "Full Reveal",
        "archetype": "REVEAL",
        "panel_count": 1,
        "description": "Single full-page reveal for maximum impact",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 100},
        ]
    },
    
    "reveal_buildup": {
        "name": "Buildup Reveal",
        "archetype": "REVEAL",
        "panel_count": 4,
        "description": "3 small buildup panels leading to big reveal",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 33, "h": 35},     # Buildup 1
            {"id": 1, "x": 33, "y": 0, "w": 34, "h": 35},    # Buildup 2
            {"id": 2, "x": 67, "y": 0, "w": 33, "h": 35},    # Buildup 3
            {"id": 3, "x": 0, "y": 35, "w": 100, "h": 65},   # BIG REVEAL
        ]
    },
    
    # =========================================================================
    # CLIFFHANGER LAYOUTS (2) - Chapter ending hooks
    # =========================================================================
    "cliff_fade": {
        "name": "Fade Out",
        "archetype": "CLIFFHANGER",
        "panel_count": 3,
        "description": "2 panels + partial 3rd that gets 'cut off' for suspense",
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 100, "h": 40},    # Setup
            {"id": 1, "x": 0, "y": 40, "w": 100, "h": 40},   # Tension
            {"id": 2, "x": 0, "y": 80, "w": 100, "h": 20},   # Cut-off reveal (partial)
        ]
    },
    
    "cliff_split": {
        "name": "Split Moment",
        "archetype": "CLIFFHANGER",
        "panel_count": 3,
        "description": "Dramatic diagonal split with cliffhanger moment",
        "slanted": True,
        "angle": 8,
        "layout": [
            {"id": 0, "x": 0, "y": 0, "w": 50, "h": 50},     # Protagonist
            {"id": 1, "x": 50, "y": 0, "w": 50, "h": 50},    # Antagonist
            {"id": 2, "x": 0, "y": 50, "w": 100, "h": 50},   # Cliffhanger moment
        ]
    },
}


# =============================================================================
# FALLBACK TEMPLATES (by panel count)
# =============================================================================

FALLBACK_TEMPLATES: Dict[int, str] = {
    1: "reveal_fullpage",      # 1 panel = splash
    2: "action_2slant",        # 2 panels = dynamic action
    3: "cliff_fade",           # 3 panels = suspense
    4: "2x2_grid",             # 4 panels = classic (default)
    5: "talk_5panel",          # 5 panels = dialogue
    6: "talk_6panel_grid",     # 6 panels = extended dialogue
}


# =============================================================================
# ARCHETYPE TO RECOMMENDED TEMPLATES
# =============================================================================

ARCHETYPE_TEMPLATES: Dict[str, List[str]] = {
    "EXPOSITION": ["expo_1splash", "expo_1big_3small", "expo_2wide_2small"],
    "DIALOGUE": ["talk_5panel", "talk_6panel_grid", "talk_4panel_focus", "talk_reaction_strip"],
    "ACTION": ["action_2slant", "action_3dynamic", "action_panorama", "action_impact"],
    "REVEAL": ["reveal_fullpage", "reveal_buildup"],
    "CLIFFHANGER": ["cliff_fade", "cliff_split"],
    "DEFAULT": ["2x2_grid"],
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_template(name: str) -> Dict[str, Any]:
    """Get a layout template by name, with fallback to 2x2_grid."""
    return LAYOUT_TEMPLATES.get(name, LAYOUT_TEMPLATES["2x2_grid"])


def get_template_for_panel_count(count: int) -> str:
    """Get the appropriate fallback template name for a given panel count."""
    return FALLBACK_TEMPLATES.get(count, "2x2_grid")


def get_templates_for_archetype(archetype: str) -> List[str]:
    """Get list of recommended template names for an archetype."""
    return ARCHETYPE_TEMPLATES.get(archetype.upper(), ARCHETYPE_TEMPLATES["DEFAULT"])


def validate_template(template_name: str, panel_count: int) -> str:
    """
    V4.6 Safety Valve: Validate template matches panel count.
    If mismatch, return a compatible fallback template.
    """
    template = LAYOUT_TEMPLATES.get(template_name)
    
    if not template:
        print(f"⚠️ Unknown template '{template_name}', falling back to 2x2_grid")
        return "2x2_grid"
    
    expected_count = template["panel_count"]
    
    if panel_count != expected_count:
        print(f"⚠️ Panel count mismatch! Template '{template_name}' expects {expected_count}, got {panel_count}")
        fallback = get_template_for_panel_count(panel_count)
        print(f"   → Auto-switched to: {fallback}")
        return fallback
    
    return template_name
