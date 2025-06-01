#!/usr/bin/env python3
"""
Narrative Thread Tracker

NLP-only analysis using local models for dialogue threading, character tracking,
and emotional arc analysis across manga sequences.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, Counter
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class NarrativeThreadTracker:
    """Tracks narrative threads, characters, and emotional arcs using local NLP models."""
    
    def __init__(self):
        # Local NLP models for text analysis
        self.local_models = ["deepseek-r1:1.5b", "qwen3:1.7b"]
        self.fallback_nlp_model = "deepseek/deepseek-r1-0528:free"
        self.current_model_index = 0

        # OpenRouter API configuration for fallback
        self.api_keys = [
            "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",
            "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"
        ]
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
    def call_local_nlp(self, prompt: str, model: str = None) -> Optional[str]:
        """Call local Ollama model for NLP analysis with OpenRouter fallback."""
        if model is None:
            model = self.local_models[self.current_model_index]

        try:
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=45)

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                print(f"Local NLP model {model} failed: {result.stderr}")
                # Try fallback model
                if model != self.local_models[1]:
                    return self.call_local_nlp(prompt, self.local_models[1])
                else:
                    # Try OpenRouter fallback
                    return self.call_openrouter_nlp(prompt)

        except subprocess.TimeoutExpired:
            print(f"Local NLP model {model} timed out")
            return self.call_openrouter_nlp(prompt)
        except Exception as e:
            print(f"Local NLP call failed: {e}")
            return self.call_openrouter_nlp(prompt)

    def call_openrouter_nlp(self, prompt: str) -> Optional[str]:
        """Fallback to OpenRouter free NLP model."""
        try:
            import requests

            api_key = self.api_keys[0]  # Use first key

            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.fallback_nlp_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500,
                "temperature": 0.1
            }

            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                return content
            else:
                print(f"OpenRouter NLP fallback failed: {response.status_code}")
                return None

        except Exception as e:
            print(f"OpenRouter NLP fallback error: {e}")
            return None
    
    def extract_speakers(self, dialogues: List[str]) -> Dict[str, Any]:
        """
        Extract and track speaker identities across dialogue sequence.
        
        Args:
            dialogues: List of dialogue strings
            
        Returns:
            Speaker analysis results
        """
        
        print("🗣️  Analyzing speaker identities...")
        
        # Build prompt for speaker analysis
        dialogue_text = "\n".join([f"Panel {i+1}: {d}" for i, d in enumerate(dialogues) if d.strip()])
        
        if not dialogue_text.strip():
            return {
                "speakers_detected": [],
                "speaker_consistency": True,
                "dialogue_threading": "no_dialogue",
                "analysis_method": "no_content"
            }
        
        prompt = f"""Analyze this manga dialogue sequence for speaker identities and consistency:

{dialogue_text}

Identify:
1. How many distinct speakers are present
2. Are speakers consistent across panels
3. Any speaker identity confusion
4. Dialogue threading quality

Respond with speaker names/roles and consistency assessment."""
        
        # Call local NLP
        nlp_response = self.call_local_nlp(prompt)
        
        if nlp_response:
            return self._parse_speaker_response(nlp_response, dialogues)
        else:
            return self._fallback_speaker_analysis(dialogues)
    
    def _parse_speaker_response(self, response: str, dialogues: List[str]) -> Dict[str, Any]:
        """Parse NLP response for speaker analysis."""
        
        response_lower = response.lower()
        
        # Extract speaker count
        speaker_count = 1  # Default
        try:
            # Look for numbers in response
            numbers = re.findall(r'\b(\d+)\b', response)
            if numbers:
                speaker_count = int(numbers[0])
        except:
            pass
        
        # Assess consistency
        consistency_keywords = ["consistent", "same", "stable", "clear"]
        inconsistency_keywords = ["inconsistent", "confused", "unclear", "mixed"]
        
        is_consistent = any(word in response_lower for word in consistency_keywords)
        has_issues = any(word in response_lower for word in inconsistency_keywords)
        
        # Determine threading quality
        if is_consistent and not has_issues:
            threading = "natural"
        elif has_issues:
            threading = "confused"
        else:
            threading = "unclear"
        
        # Extract potential speaker names/roles
        speakers = []
        common_roles = ["narrator", "protagonist", "character", "speaker", "voice", "person"]
        for role in common_roles:
            if role in response_lower:
                speakers.append(role)
        
        if not speakers:
            speakers = [f"speaker_{i+1}" for i in range(speaker_count)]
        
        return {
            "speakers_detected": speakers[:speaker_count],
            "speaker_count": speaker_count,
            "speaker_consistency": is_consistent and not has_issues,
            "dialogue_threading": threading,
            "consistency_issues": has_issues,
            "nlp_analysis": response,
            "analysis_method": "local_nlp"
        }
    
    def _fallback_speaker_analysis(self, dialogues: List[str]) -> Dict[str, Any]:
        """Fallback speaker analysis when NLP fails."""
        
        # Simple heuristic analysis
        non_empty_dialogues = [d for d in dialogues if d.strip()]
        
        # Estimate speakers based on dialogue patterns
        speaker_count = min(len(non_empty_dialogues), 2)  # Assume max 2 speakers
        
        return {
            "speakers_detected": [f"speaker_{i+1}" for i in range(speaker_count)],
            "speaker_count": speaker_count,
            "speaker_consistency": True,  # Optimistic default
            "dialogue_threading": "unclear",
            "consistency_issues": False,
            "nlp_analysis": "Fallback analysis - NLP unavailable",
            "analysis_method": "fallback"
        }
    
    def track_character_presence(self, scene_descriptions: List[str]) -> Dict[str, Any]:
        """
        Track character appearances and disappearances across scenes.
        
        Args:
            scene_descriptions: List of scene description strings
            
        Returns:
            Character tracking analysis
        """
        
        print("👥 Tracking character presence...")
        
        # Build prompt for character tracking
        scenes_text = "\n".join([f"Scene {i+1}: {desc}" for i, desc in enumerate(scene_descriptions)])
        
        prompt = f"""Analyze these manga scene descriptions for character presence and continuity:

{scenes_text}

Track:
1. Which characters appear in each scene
2. Any characters that appear/disappear unexpectedly
3. Character consistency across scenes
4. Logical character progression

Identify character names/roles and their presence pattern."""
        
        # Call local NLP
        nlp_response = self.call_local_nlp(prompt)
        
        if nlp_response:
            return self._parse_character_response(nlp_response, scene_descriptions)
        else:
            return self._fallback_character_analysis(scene_descriptions)
    
    def _parse_character_response(self, response: str, scene_descriptions: List[str]) -> Dict[str, Any]:
        """Parse NLP response for character tracking."""
        
        response_lower = response.lower()
        
        # Extract character mentions
        common_characters = ["protagonist", "character", "person", "figure", "warrior", "samurai", 
                           "sage", "guardian", "villager", "hero", "main character"]
        
        detected_characters = []
        for char in common_characters:
            if char in response_lower:
                detected_characters.append(char)
        
        # If no specific characters found, assume main character
        if not detected_characters:
            detected_characters = ["main_character"]
        
        # Assess continuity
        continuity_keywords = ["consistent", "continuous", "stable", "logical"]
        discontinuity_keywords = ["disappear", "sudden", "unexpected", "inconsistent"]
        
        has_continuity = any(word in response_lower for word in continuity_keywords)
        has_breaks = any(word in response_lower for word in discontinuity_keywords)
        
        return {
            "characters_detected": detected_characters,
            "character_continuity": has_continuity and not has_breaks,
            "unexpected_appearances": has_breaks,
            "character_progression": "logical" if has_continuity else "unclear",
            "nlp_analysis": response,
            "analysis_method": "local_nlp"
        }
    
    def _fallback_character_analysis(self, scene_descriptions: List[str]) -> Dict[str, Any]:
        """Fallback character analysis when NLP fails."""
        
        # Simple keyword-based character detection
        character_keywords = ["samurai", "warrior", "sage", "character", "person", "figure"]
        
        detected_characters = []
        for desc in scene_descriptions:
            desc_lower = desc.lower()
            for keyword in character_keywords:
                if keyword in desc_lower and keyword not in detected_characters:
                    detected_characters.append(keyword)
        
        if not detected_characters:
            detected_characters = ["main_character"]
        
        return {
            "characters_detected": detected_characters,
            "character_continuity": True,  # Optimistic default
            "unexpected_appearances": False,
            "character_progression": "unclear",
            "nlp_analysis": "Fallback analysis - keyword detection",
            "analysis_method": "fallback"
        }
    
    def analyze_emotional_arc(self, emotions: List[str], scene_descriptions: List[str]) -> Dict[str, Any]:
        """
        Analyze emotional progression and arc consistency.
        
        Args:
            emotions: List of emotion labels
            scene_descriptions: List of scene descriptions for context
            
        Returns:
            Emotional arc analysis
        """
        
        print("💭 Analyzing emotional arc...")
        
        # Build prompt for emotional analysis
        emotion_sequence = " → ".join(emotions)
        context_text = "\n".join([f"Scene {i+1} ({emotions[i]}): {desc}" 
                                 for i, desc in enumerate(scene_descriptions)])
        
        prompt = f"""Analyze this emotional progression in a manga sequence:

Emotion Sequence: {emotion_sequence}

Scene Context:
{context_text}

Evaluate:
1. Is the emotional progression logical and natural?
2. Are there any jarring emotional transitions?
3. Does the emotional arc support the narrative?
4. Overall emotional coherence score (0.0-1.0)

Provide analysis of the emotional flow."""
        
        # Call local NLP
        nlp_response = self.call_local_nlp(prompt)
        
        if nlp_response:
            return self._parse_emotional_response(nlp_response, emotions)
        else:
            return self._fallback_emotional_analysis(emotions)
    
    def _parse_emotional_response(self, response: str, emotions: List[str]) -> Dict[str, Any]:
        """Parse NLP response for emotional analysis."""
        
        response_lower = response.lower()
        
        # Extract emotional coherence score
        score = 0.5  # Default
        try:
            score_match = re.search(r'(\d+\.?\d*)', response)
            if score_match:
                score = min(1.0, max(0.0, float(score_match.group(1))))
        except:
            pass
        
        # Assess emotional flow
        positive_keywords = ["logical", "natural", "smooth", "coherent", "good"]
        negative_keywords = ["jarring", "abrupt", "inconsistent", "confusing", "poor"]
        
        is_positive = any(word in response_lower for word in positive_keywords)
        has_issues = any(word in response_lower for word in negative_keywords)
        
        if is_positive and not has_issues:
            flow_quality = "natural"
        elif has_issues:
            flow_quality = "jarring"
        else:
            flow_quality = "unclear"
        
        # Detect emotional variety
        unique_emotions = len(set(emotions))
        emotion_variety = "high" if unique_emotions > len(emotions) * 0.7 else "moderate"
        
        return {
            "emotional_coherence_score": score,
            "emotional_flow": flow_quality,
            "emotion_variety": emotion_variety,
            "unique_emotions": unique_emotions,
            "total_scenes": len(emotions),
            "jarring_transitions": has_issues,
            "supports_narrative": is_positive,
            "nlp_analysis": response,
            "analysis_method": "local_nlp"
        }
    
    def _fallback_emotional_analysis(self, emotions: List[str]) -> Dict[str, Any]:
        """Fallback emotional analysis when NLP fails."""
        
        # Simple heuristic analysis
        unique_emotions = len(set(emotions))
        total_emotions = len(emotions)
        
        # Score based on emotional variety (not too much, not too little)
        variety_ratio = unique_emotions / total_emotions if total_emotions > 0 else 0
        
        if 0.3 <= variety_ratio <= 0.7:  # Good variety
            score = 0.7
            flow = "natural"
        elif variety_ratio > 0.7:  # Too much variety
            score = 0.4
            flow = "jarring"
        else:  # Too little variety
            score = 0.6
            flow = "monotone"
        
        return {
            "emotional_coherence_score": score,
            "emotional_flow": flow,
            "emotion_variety": "high" if variety_ratio > 0.7 else "moderate",
            "unique_emotions": unique_emotions,
            "total_scenes": total_emotions,
            "jarring_transitions": variety_ratio > 0.8,
            "supports_narrative": score > 0.6,
            "nlp_analysis": "Fallback analysis - heuristic evaluation",
            "analysis_method": "fallback"
        }
    
    def generate_thread_report(self, scene_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive narrative thread analysis report.
        
        Args:
            scene_data: List of scene metadata dictionaries
            
        Returns:
            Complete thread analysis report
        """
        
        print("📊 Generating narrative thread report...")
        
        # Extract data
        dialogues = [scene.get("dialogue", "") for scene in scene_data]
        emotions = [scene.get("emotion", "neutral") for scene in scene_data]
        descriptions = [scene.get("description", "") for scene in scene_data]
        
        # Run analyses
        speaker_analysis = self.extract_speakers(dialogues)
        character_analysis = self.track_character_presence(descriptions)
        emotional_analysis = self.analyze_emotional_arc(emotions, descriptions)
        
        # Calculate overall thread coherence
        speaker_score = 1.0 if speaker_analysis.get("speaker_consistency", False) else 0.5
        character_score = 1.0 if character_analysis.get("character_continuity", False) else 0.5
        emotion_score = emotional_analysis.get("emotional_coherence_score", 0.5)
        
        overall_thread_score = (speaker_score + character_score + emotion_score) / 3.0
        
        # Determine thread quality
        if overall_thread_score >= 0.8:
            thread_quality = "excellent"
        elif overall_thread_score >= 0.6:
            thread_quality = "good"
        elif overall_thread_score >= 0.4:
            thread_quality = "fair"
        else:
            thread_quality = "poor"
        
        return {
            "thread_coherence_score": round(overall_thread_score, 3),
            "thread_quality": thread_quality,
            "speaker_analysis": speaker_analysis,
            "character_analysis": character_analysis,
            "emotional_analysis": emotional_analysis,
            "scene_count": len(scene_data),
            "has_dialogue": any(d.strip() for d in dialogues),
            "recommend_review": overall_thread_score < 0.6,
            "analysis_summary": {
                "speaker_consistency": speaker_analysis.get("speaker_consistency", False),
                "character_continuity": character_analysis.get("character_continuity", False),
                "emotional_flow": emotional_analysis.get("emotional_flow", "unclear"),
                "overall_assessment": thread_quality
            }
        }
