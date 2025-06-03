"""
Core Module

Core manga generation components including emotion extraction,
visual flow checking, and coherence analysis.
"""

from .emotion_extractor import EmotionExtractor
from .emotion_matcher import EmotionMatcher
from .pose_matcher import PoseMatcher
from .local_flow_checker import LocalFlowChecker
from .coherence_analyzer import CoherenceAnalyzer
from .output_manager import OutputManager
from .panel_generator import EnhancedPanelGenerator

__all__ = [
    "EmotionExtractor",
    "EmotionMatcher",
    "PoseMatcher",
    "LocalFlowChecker",
    "CoherenceAnalyzer",
    "OutputManager",
    "EnhancedPanelGenerator"
]
