#!/usr/bin/env python3
"""
Narrative Coherence Analyzer

Validates story continuity across sequential manga panels using VLM and local NLP models.
Analyzes visual consistency, dialogue flow, emotional progression, and scene transitions.
"""

import os
import sys
import json
import base64
import requests
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class CoherenceAnalyzer:
    """Analyzes narrative coherence across sequential manga panels."""
    
    def __init__(self):
        # OpenRouter API configuration
        self.api_keys = [
            "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",
            "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"
        ]
        self.current_key_index = 0
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # VLM model for multi-image analysis
        self.vlm_model = "qwen/qwen2.5-vl-72b-instruct:free"
        
        # Local NLP models for text analysis (fallback to free OpenRouter if local unavailable)
        self.local_models = ["deepseek-r1:1.5b", "qwen3:1.7b"]
        self.fallback_nlp_model = "deepseek/deepseek-r1-0528:free"
        
    def encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API."""
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding image {image_path}: {e}")
            return ""
    
    def call_vlm_api(self, images: List[str], prompt: str, max_retries: int = 2) -> Optional[Dict[str, Any]]:
        """Call VLM API for multi-image analysis."""
        
        # Encode all images
        encoded_images = []
        for img_path in images:
            if not Path(img_path).exists():
                print(f"⚠️  Image not found: {img_path}")
                continue
            
            encoded = self.encode_image(img_path)
            if encoded:
                encoded_images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{encoded}"
                    }
                })
        
        if not encoded_images:
            return {"error": "No valid images to analyze", "success": False}
        
        for attempt in range(max_retries):
            try:
                api_key = self.api_keys[self.current_key_index]
                
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                
                # Build content with text prompt and all images
                content = [{"type": "text", "text": prompt}] + encoded_images
                
                payload = {
                    "model": self.vlm_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": content
                        }
                    ],
                    "max_tokens": 800,
                    "temperature": 0.1
                }
                
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=45)
                
                if response.status_code == 200:
                    result = response.json()
                    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                    return {"content": content, "success": True, "model": self.vlm_model}
                
                elif response.status_code == 429:
                    print(f"Rate limit hit, trying next key...")
                    self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                    time.sleep(3)
                    continue
                    
                else:
                    print(f"API error {response.status_code}: {response.text}")
                    continue
                    
            except Exception as e:
                print(f"VLM API call failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
        
        return {"error": "All VLM API attempts failed", "success": False}
    
    def call_local_nlp(self, prompt: str, model: str = None) -> Optional[str]:
        """Call local Ollama model for NLP analysis with OpenRouter fallback."""
        if model is None:
            model = self.local_models[0]  # Default to deepseek-r1:1.5b

        try:
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

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
            api_key = self.api_keys[self.current_key_index]

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
    
    def analyze_visual_coherence(self, panel_paths: List[str], scene_descriptions: List[str]) -> Dict[str, Any]:
        """
        Analyze visual coherence across sequential panels using VLM.
        
        Args:
            panel_paths: List of image file paths
            scene_descriptions: List of scene descriptions for context
            
        Returns:
            Dictionary with visual coherence analysis
        """
        
        print(f"🔍 Analyzing visual coherence across {len(panel_paths)} panels...")
        
        # Build comprehensive prompt for multi-image analysis
        descriptions_text = "\n".join([f"Panel {i+1}: {desc}" for i, desc in enumerate(scene_descriptions)])
        
        prompt = f"""Analyze these {len(panel_paths)} sequential manga panels for narrative coherence and visual consistency.

Expected Scene Descriptions:
{descriptions_text}

Please evaluate and respond in JSON format:
{{
  "visual_consistency": {{
    "background_continuity": true/false,
    "character_appearance": true/false,
    "lighting_consistency": true/false,
    "art_style_consistency": true/false
  }},
  "scene_transitions": {{
    "logical_progression": true/false,
    "location_changes": "none/gradual/abrupt",
    "time_progression": "consistent/unclear/inconsistent"
  }},
  "character_analysis": {{
    "character_count_stable": true/false,
    "outfit_consistency": true/false,
    "pose_progression": "natural/awkward/inconsistent"
  }},
  "overall_coherence": {{
    "coherence_score": 0.0-1.0,
    "visual_flow": "smooth/choppy/broken",
    "narrative_clarity": "clear/confusing/unclear"
  }},
  "issues_detected": ["list", "of", "specific", "issues"],
  "recommend_human_review": true/false,
  "detailed_analysis": "Brief explanation of findings"
}}

Focus on continuity between panels and flag any jarring transitions or inconsistencies."""
        
        # Call VLM API
        api_result = self.call_vlm_api(panel_paths, prompt)
        
        if not api_result.get("success", False):
            return {
                "error": api_result.get("error", "VLM analysis failed"),
                "visual_consistency": {
                    "background_continuity": False,
                    "character_appearance": False,
                    "lighting_consistency": False,
                    "art_style_consistency": False
                },
                "scene_transitions": {
                    "logical_progression": False,
                    "location_changes": "unclear",
                    "time_progression": "unclear"
                },
                "character_analysis": {
                    "character_count_stable": False,
                    "outfit_consistency": False,
                    "pose_progression": "unclear"
                },
                "overall_coherence": {
                    "coherence_score": 0.0,
                    "visual_flow": "broken",
                    "narrative_clarity": "unclear"
                },
                "issues_detected": ["VLM analysis failed"],
                "recommend_human_review": True,
                "analysis_method": "failed"
            }
        
        # Parse JSON response
        try:
            content = api_result.get("content", "")
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_content = content[json_start:json_end]
                analysis = json.loads(json_content)
                analysis["analysis_method"] = "vlm"
                analysis["model_used"] = self.vlm_model
                analysis["raw_response"] = content
                return analysis
            else:
                return self._parse_fallback_visual_response(content)
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse VLM response as JSON: {e}")
            return self._parse_fallback_visual_response(api_result.get("content", ""))
    
    def _parse_fallback_visual_response(self, content: str) -> Dict[str, Any]:
        """Parse non-JSON VLM response as fallback."""
        content_lower = content.lower()
        
        # Simple keyword-based analysis
        consistent = any(word in content_lower for word in ["consistent", "coherent", "smooth", "good"])
        issues = any(word in content_lower for word in ["inconsistent", "jarring", "abrupt", "problem"])
        
        return {
            "visual_consistency": {
                "background_continuity": consistent and not issues,
                "character_appearance": consistent,
                "lighting_consistency": True,  # Default assumption
                "art_style_consistency": True
            },
            "scene_transitions": {
                "logical_progression": consistent,
                "location_changes": "unclear",
                "time_progression": "unclear"
            },
            "character_analysis": {
                "character_count_stable": True,
                "outfit_consistency": consistent,
                "pose_progression": "unclear"
            },
            "overall_coherence": {
                "coherence_score": 0.7 if consistent else 0.4,
                "visual_flow": "unclear",
                "narrative_clarity": "unclear"
            },
            "issues_detected": ["Fallback parsing - manual review needed"],
            "recommend_human_review": True,
            "detailed_analysis": content[:200] + "..." if len(content) > 200 else content,
            "analysis_method": "fallback",
            "model_used": self.vlm_model
        }
    
    def analyze_sequence_coherence(self, panel_paths: List[str], scene_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Main coherence analysis function combining visual and narrative analysis.
        
        Args:
            panel_paths: List of panel image paths
            scene_data: List of scene metadata (descriptions, dialogue, emotions)
            
        Returns:
            Complete coherence analysis
        """
        
        if len(panel_paths) < 2:
            return {
                "error": "Need at least 2 panels for coherence analysis",
                "coherence_score": 0.0
            }
        
        print(f"📊 Starting coherence analysis for {len(panel_paths)} panels...")
        
        # Extract scene descriptions
        scene_descriptions = [scene.get("description", "") for scene in scene_data]
        
        # Visual coherence analysis using VLM
        visual_analysis = self.analyze_visual_coherence(panel_paths, scene_descriptions)
        
        # Narrative coherence analysis using local NLP
        narrative_analysis = self.analyze_narrative_coherence(scene_data)
        
        # Combine analyses
        combined_analysis = self._combine_analyses(visual_analysis, narrative_analysis, panel_paths, scene_data)
        
        return combined_analysis
    
    def analyze_narrative_coherence(self, scene_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze narrative coherence using local NLP models."""
        
        print("📝 Analyzing narrative coherence with local NLP...")
        
        # Extract dialogue and emotions
        dialogues = []
        emotions = []
        
        for scene in scene_data:
            dialogue = scene.get("dialogue", "")
            emotion = scene.get("emotion", "neutral")
            dialogues.append(dialogue)
            emotions.append(emotion)
        
        # Build prompt for narrative analysis
        narrative_prompt = f"""Analyze this manga sequence for narrative coherence:

Dialogues:
{chr(10).join([f"Panel {i+1}: {d}" for i, d in enumerate(dialogues)])}

Emotions:
{chr(10).join([f"Panel {i+1}: {e}" for i, e in enumerate(emotions)])}

Evaluate:
1. Dialogue flow and speaker consistency
2. Emotional progression logic
3. Narrative thread continuity

Respond with a coherence score (0.0-1.0) and brief analysis."""
        
        # Call local NLP model
        nlp_response = self.call_local_nlp(narrative_prompt)
        
        if nlp_response:
            return self._parse_narrative_response(nlp_response, dialogues, emotions)
        else:
            return self._default_narrative_analysis(dialogues, emotions)
    
    def _parse_narrative_response(self, response: str, dialogues: List[str], emotions: List[str]) -> Dict[str, Any]:
        """Parse local NLP response for narrative analysis."""
        
        # Extract score if present
        score = 0.5  # Default
        try:
            import re
            score_match = re.search(r'(\d+\.?\d*)', response)
            if score_match:
                score = min(1.0, max(0.0, float(score_match.group(1))))
        except:
            pass
        
        # Simple analysis based on content
        response_lower = response.lower()
        
        dialogue_flow = "natural" if "natural" in response_lower or "good" in response_lower else "unclear"
        emotion_progression = "consistent" if "consistent" in response_lower else "unclear"
        
        return {
            "dialogue_flow": dialogue_flow,
            "emotion_progression": emotion_progression,
            "narrative_score": score,
            "speaker_consistency": True,  # Default assumption
            "thread_continuity": score > 0.6,
            "nlp_analysis": response,
            "analysis_method": "local_nlp"
        }
    
    def _default_narrative_analysis(self, dialogues: List[str], emotions: List[str]) -> Dict[str, Any]:
        """Fallback narrative analysis when NLP fails."""
        
        # Simple heuristic analysis
        has_dialogue = any(d.strip() for d in dialogues)
        emotion_variety = len(set(emotions))
        
        score = 0.7 if has_dialogue else 0.5
        if emotion_variety > len(emotions) // 2:  # Too much emotion variety
            score -= 0.1
        
        return {
            "dialogue_flow": "unclear",
            "emotion_progression": "unclear",
            "narrative_score": score,
            "speaker_consistency": True,
            "thread_continuity": has_dialogue,
            "nlp_analysis": "Fallback analysis - NLP unavailable",
            "analysis_method": "fallback"
        }
    
    def _combine_analyses(self, visual: Dict[str, Any], narrative: Dict[str, Any], 
                         panel_paths: List[str], scene_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine visual and narrative analyses into final coherence report."""
        
        # Extract scores
        visual_score = visual.get("overall_coherence", {}).get("coherence_score", 0.0)
        narrative_score = narrative.get("narrative_score", 0.0)
        
        # Weighted combination (visual 60%, narrative 40%)
        combined_score = (visual_score * 0.6) + (narrative_score * 0.4)
        
        # Determine overall assessment
        if combined_score >= 0.8:
            overall_assessment = "excellent"
        elif combined_score >= 0.6:
            overall_assessment = "good"
        elif combined_score >= 0.4:
            overall_assessment = "fair"
        else:
            overall_assessment = "poor"
        
        # Combine recommendations
        recommend_review = (
            visual.get("recommend_human_review", False) or
            narrative.get("narrative_score", 1.0) < 0.5 or
            combined_score < 0.6
        )
        
        return {
            "coherence_score": round(combined_score, 3),
            "visual_consistency": visual.get("visual_consistency", {}),
            "dialogue_flow": narrative.get("dialogue_flow", "unclear"),
            "emotion_progression": narrative.get("emotion_progression", "unclear"),
            "location_shift": visual.get("scene_transitions", {}).get("location_changes", "unclear") != "none",
            "character_break": not visual.get("character_analysis", {}).get("character_count_stable", True),
            "overall_assessment": overall_assessment,
            "recommend_human_review": recommend_review,
            "detailed_analysis": {
                "visual_analysis": visual,
                "narrative_analysis": narrative,
                "panel_count": len(panel_paths),
                "scene_count": len(scene_data)
            },
            "issues_detected": visual.get("issues_detected", []) + 
                             (["Narrative flow issues"] if narrative_score < 0.5 else []),
            "analysis_timestamp": time.time()
        }
