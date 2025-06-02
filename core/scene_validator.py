"""
Scene Validation System with Image Embedding Checks

Comprehensive validation for scene coherence including character consistency,
location continuity, and visual flow analysis using both local OpenCV and
advanced image embedding techniques.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

from core.local_flow_checker import LocalFlowChecker
from core.coherence_analyzer import CoherenceAnalyzer

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False


class SceneValidator:
    """Advanced scene validation with image embedding and coherence analysis."""
    
    def __init__(self):
        """Initialize scene validator."""
        self.local_flow_checker = LocalFlowChecker()
        self.coherence_analyzer = CoherenceAnalyzer(use_local_flow_checker=True)
        
    def validate_scene_coherence(
        self,
        panel_paths: List[str],
        scene_metadata: Dict[str, Any],
        color_mode: str = "color"
    ) -> Dict[str, Any]:
        """
        Comprehensive scene coherence validation.
        
        Args:
            panel_paths: List of panel image file paths
            scene_metadata: Scene metadata including character and setting info
            
        Returns:
            Detailed validation results
        """
        print(f"🔍 Validating scene coherence for {len(panel_paths)} panels...")
        print(f"   🎨 Color mode: {color_mode}")

        if len(panel_paths) < 2:
            return {
                "error": "Need at least 2 panels for coherence validation",
                "coherence_score": 0.0,
                "validation_timestamp": datetime.now().isoformat(),
                "color_mode": color_mode
            }
        
        # Character consistency analysis
        character_analysis = self._analyze_character_consistency(panel_paths, scene_metadata)
        
        # Location/background continuity
        location_analysis = self._analyze_location_continuity(panel_paths, scene_metadata)
        
        # Visual flow analysis
        flow_analysis = self._analyze_visual_flow(panel_paths)
        
        # Image embedding similarity
        embedding_analysis = self._analyze_image_embeddings(panel_paths)
        
        # Lighting consistency
        lighting_analysis = self._analyze_lighting_consistency(panel_paths)
        
        # Combine all analyses
        overall_analysis = self._combine_scene_analyses(
            character_analysis, location_analysis, flow_analysis,
            embedding_analysis, lighting_analysis, scene_metadata, color_mode
        )
        
        return overall_analysis
    
    def _analyze_character_consistency(
        self, 
        panel_paths: List[str], 
        scene_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze character appearance consistency across panels."""
        
        print("   👤 Analyzing character consistency...")
        
        character_scores = []
        character_issues = []
        
        # Get character descriptors from metadata
        characters = scene_metadata.get("characters", [])
        
        for i in range(len(panel_paths) - 1):
            current_panel = panel_paths[i]
            next_panel = panel_paths[i + 1]
            
            # Use local flow checker for character analysis
            flow_result = self.local_flow_checker.analyze_panel_pair(
                current_panel, next_panel
            )
            
            char_analysis = flow_result.get("character_analysis", {})
            char_consistency = char_analysis.get("presence_consistent", True)
            
            if char_consistency:
                character_scores.append(0.9)
            else:
                character_scores.append(0.4)
                character_issues.append(f"Character inconsistency between panels {i+1} and {i+2}")
        
        avg_character_score = np.mean(character_scores) if character_scores else 0.5
        
        return {
            "character_consistency_score": float(avg_character_score),
            "character_issues": character_issues,
            "characters_tracked": len(characters),
            "panel_transitions_analyzed": len(character_scores)
        }
    
    def _analyze_location_continuity(
        self, 
        panel_paths: List[str], 
        scene_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze location/background continuity."""
        
        print("   🏛️ Analyzing location continuity...")
        
        location_scores = []
        location_issues = []
        
        settings = scene_metadata.get("settings", {})
        expected_location = settings.get("location", "unknown")
        
        for i in range(len(panel_paths) - 1):
            current_panel = panel_paths[i]
            next_panel = panel_paths[i + 1]
            
            # Use local flow checker for scene change detection
            flow_result = self.local_flow_checker.analyze_panel_pair(
                current_panel, next_panel
            )
            
            scene_analysis = flow_result.get("scene_analysis", {})
            is_abrupt_change = scene_analysis.get("is_abrupt_change", False)
            
            if not is_abrupt_change:
                location_scores.append(0.9)
            else:
                location_scores.append(0.3)
                location_issues.append(f"Abrupt scene change between panels {i+1} and {i+2}")
        
        avg_location_score = np.mean(location_scores) if location_scores else 0.5
        
        return {
            "location_continuity_score": float(avg_location_score),
            "location_issues": location_issues,
            "expected_location": expected_location,
            "abrupt_changes_detected": len([s for s in location_scores if s < 0.5])
        }
    
    def _analyze_visual_flow(self, panel_paths: List[str]) -> Dict[str, Any]:
        """Analyze overall visual flow between panels."""
        
        print("   🌊 Analyzing visual flow...")
        
        flow_scores = []
        flow_issues = []
        
        for i in range(len(panel_paths) - 1):
            current_panel = panel_paths[i]
            next_panel = panel_paths[i + 1]
            
            # Use local flow checker
            flow_result = self.local_flow_checker.analyze_panel_pair(
                current_panel, next_panel
            )
            
            flow_quality = flow_result.get("flow_quality", "poor")
            flow_issues_list = flow_result.get("flow_issues", [])
            
            if flow_quality == "good":
                flow_scores.append(0.9)
            elif flow_quality == "fair":
                flow_scores.append(0.7)
            else:
                flow_scores.append(0.4)
                flow_issues.extend([f"Panel {i+1}-{i+2}: {issue}" for issue in flow_issues_list])
        
        avg_flow_score = np.mean(flow_scores) if flow_scores else 0.5
        
        return {
            "visual_flow_score": float(avg_flow_score),
            "flow_issues": flow_issues,
            "smooth_transitions": len([s for s in flow_scores if s > 0.8]),
            "problematic_transitions": len([s for s in flow_scores if s < 0.5])
        }
    
    def _analyze_image_embeddings(self, panel_paths: List[str]) -> Dict[str, Any]:
        """Analyze image similarity using perceptual hashing and structural similarity."""
        
        print("   🔗 Analyzing image embeddings...")
        
        if not PIL_AVAILABLE or not IMAGEHASH_AVAILABLE:
            return {
                "embedding_analysis": "Limited - PIL/imagehash not available",
                "perceptual_similarity_avg": 0.5,
                "structural_similarity_avg": 0.5
            }
        
        perceptual_similarities = []
        structural_similarities = []
        
        for i in range(len(panel_paths) - 1):
            current_panel = panel_paths[i]
            next_panel = panel_paths[i + 1]
            
            # Perceptual hash similarity
            perceptual_sim = self.local_flow_checker.calculate_perceptual_hash_similarity(
                current_panel, next_panel
            )
            perceptual_similarities.append(perceptual_sim)
            
            # Structural similarity
            try:
                img1 = cv2.imread(current_panel)
                img2 = cv2.imread(next_panel)
                if img1 is not None and img2 is not None:
                    structural_sim = self.local_flow_checker.calculate_structural_similarity(img1, img2)
                    structural_similarities.append(structural_sim)
            except Exception as e:
                print(f"   ⚠️ Structural similarity failed: {e}")
                structural_similarities.append(0.5)
        
        return {
            "perceptual_similarity_avg": float(np.mean(perceptual_similarities)) if perceptual_similarities else 0.5,
            "structural_similarity_avg": float(np.mean(structural_similarities)) if structural_similarities else 0.5,
            "embedding_transitions_analyzed": len(perceptual_similarities),
            "high_similarity_transitions": len([s for s in perceptual_similarities if s > 0.7])
        }
    
    def _analyze_lighting_consistency(self, panel_paths: List[str]) -> Dict[str, Any]:
        """Analyze lighting consistency across panels."""
        
        print("   💡 Analyzing lighting consistency...")
        
        lighting_scores = []
        lighting_issues = []
        
        for i in range(len(panel_paths) - 1):
            current_panel = panel_paths[i]
            next_panel = panel_paths[i + 1]
            
            # Use local flow checker for lighting analysis
            flow_result = self.local_flow_checker.analyze_panel_pair(
                current_panel, next_panel
            )
            
            lighting_analysis = flow_result.get("lighting_analysis", {})
            is_consistent = lighting_analysis.get("is_consistent", True)
            
            if is_consistent:
                lighting_scores.append(0.9)
            else:
                lighting_scores.append(0.4)
                lighting_issues.append(f"Lighting inconsistency between panels {i+1} and {i+2}")
        
        avg_lighting_score = np.mean(lighting_scores) if lighting_scores else 0.5
        
        return {
            "lighting_consistency_score": float(avg_lighting_score),
            "lighting_issues": lighting_issues,
            "consistent_transitions": len([s for s in lighting_scores if s > 0.8])
        }
    
    def _combine_scene_analyses(
        self,
        character_analysis: Dict[str, Any],
        location_analysis: Dict[str, Any],
        flow_analysis: Dict[str, Any],
        embedding_analysis: Dict[str, Any],
        lighting_analysis: Dict[str, Any],
        scene_metadata: Dict[str, Any],
        color_mode: str = "color"
    ) -> Dict[str, Any]:
        """Combine all analyses into final scene validation result."""
        
        # Calculate weighted overall score
        weights = {
            "character": 0.25,
            "location": 0.25,
            "flow": 0.25,
            "lighting": 0.15,
            "embedding": 0.10
        }
        
        overall_score = (
            character_analysis["character_consistency_score"] * weights["character"] +
            location_analysis["location_continuity_score"] * weights["location"] +
            flow_analysis["visual_flow_score"] * weights["flow"] +
            lighting_analysis["lighting_consistency_score"] * weights["lighting"] +
            embedding_analysis["perceptual_similarity_avg"] * weights["embedding"]
        )
        
        # Collect all issues
        all_issues = (
            character_analysis["character_issues"] +
            location_analysis["location_issues"] +
            flow_analysis["flow_issues"] +
            lighting_analysis["lighting_issues"]
        )
        
        # Determine overall assessment
        if overall_score >= 0.85:
            assessment = "Excellent scene coherence"
            recommendation = "Scene flows naturally with strong visual consistency"
        elif overall_score >= 0.70:
            assessment = "Good scene coherence"
            recommendation = "Scene has acceptable visual flow with minor inconsistencies"
        elif overall_score >= 0.50:
            assessment = "Fair scene coherence"
            recommendation = "Scene has noticeable inconsistencies that may affect flow"
        else:
            assessment = "Poor scene coherence"
            recommendation = "Scene has significant visual inconsistencies requiring attention"
        
        return {
            "validation_timestamp": datetime.now().isoformat(),
            "color_mode": color_mode,
            "scene_info": {
                "scene_name": scene_metadata.get("scene_name", "Unknown"),
                "panel_count": len(scene_metadata.get("panels", [])),
                "characters": scene_metadata.get("characters", []),
                "settings": scene_metadata.get("settings", {}),
                "color_mode": color_mode
            },
            "overall_coherence_score": round(overall_score, 3),
            "component_scores": {
                "character_consistency": character_analysis["character_consistency_score"],
                "location_continuity": location_analysis["location_continuity_score"],
                "visual_flow": flow_analysis["visual_flow_score"],
                "lighting_consistency": lighting_analysis["lighting_consistency_score"],
                "image_similarity": embedding_analysis["perceptual_similarity_avg"]
            },
            "visual_consistency": {
                "character_consistent": character_analysis["character_consistency_score"] > 0.7,
                "background_consistent": location_analysis["location_continuity_score"] > 0.7,
                "lighting_consistent": lighting_analysis["lighting_consistency_score"] > 0.7,
                "style_consistent": flow_analysis["visual_flow_score"] > 0.7
            },
            "detailed_analysis": {
                "character_analysis": character_analysis,
                "location_analysis": location_analysis,
                "flow_analysis": flow_analysis,
                "embedding_analysis": embedding_analysis,
                "lighting_analysis": lighting_analysis
            },
            "issues_detected": all_issues,
            "overall_assessment": assessment,
            "recommendation": recommendation,
            "success": overall_score > 0.6,
            "analysis_method": "comprehensive_scene_validation"
        }
