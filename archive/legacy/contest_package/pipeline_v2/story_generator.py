import os
import sys
import json
import requests
from typing import Dict, Any, List, Optional
from pathlib import Path

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config_manager import ConfigManager

class StoryGenerator:
    """
    Story generator for manga creation using free LLM models.
    
    Creates structured stories with:
    - Character descriptions for consistency
    - Scene-by-scene breakdown
    - Emotion and pose specifications
    - Dialogue for each panel
    """
    
    def __init__(self):
        """Initialize the story generator."""
        self.config_manager = ConfigManager()
        
        # Use free DeepSeek R1 model
        self.model = "deepseek/deepseek-r1-0528:free"
        self.api_key = os.getenv("OPENROUTER_KEY") or os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            raise ValueError("OPENROUTER_KEY not found in environment variables")
        
        print("✅ Story generator initialized with DeepSeek R1 free model")
    
    def generate_manga_story(self, user_prompt: str, panels: int = 4) -> Dict[str, Any]:
        """
        Generate a complete manga story structure from user prompt.
        
        Args:
            user_prompt: User's story idea
            panels: Number of panels to generate (3-5)
            
        Returns:
            Structured story data with character consistency
        """
        print(f"📝 Generating {panels}-panel manga story from: '{user_prompt}'")
        
        # Create detailed story prompt
        story_prompt = self._build_story_prompt(user_prompt, panels)
        
        # Generate story using LLM
        story_response = self._call_llm(story_prompt)
        
        if not story_response:
            return self._create_fallback_story(user_prompt, panels)
        
        # Parse and structure the response
        story_data = self._parse_story_response(story_response, user_prompt, panels)
        
        print(f"✅ Generated story: '{story_data['title']}'")
        print(f"   Character: {story_data['character']['name']}")
        print(f"   Panels: {len(story_data['panels'])}")
        
        return story_data
    
    def _build_story_prompt(self, user_prompt: str, panels: int) -> str:
        """Build a detailed prompt for story generation."""
        
        prompt = f"""Create a {panels}-panel manga story based on: "{user_prompt}"

REQUIREMENTS:
1. Create ONE main character with consistent appearance
2. Design {panels} sequential panels that tell a complete story
3. Each panel needs specific visual and dialogue details
4. Ensure character consistency across all panels

OUTPUT FORMAT (JSON):
{{
    "title": "Story title",
    "character": {{
        "name": "Character name",
        "appearance": "Detailed physical description (hair, eyes, clothing, age, etc.)",
        "personality": "Brief personality traits"
    }},
    "panels": [
        {{
            "panel_number": 1,
            "scene_description": "Detailed scene setting and environment",
            "character_emotion": "happy/angry/surprised/sad/neutral",
            "character_pose": "standing/sitting/running/jumping/arms_crossed",
            "visual_prompt": "Detailed visual description for image generation",
            "dialogue": ["Character dialogue line 1", "Character dialogue line 2"],
            "narrative_purpose": "What this panel accomplishes in the story"
        }}
    ]
}}

VISUAL PROMPT GUIDELINES (ULTRA-SIMPLE FOR CLEAR IMAGES):
- Keep prompts EXTREMELY SHORT (under 30 characters)
- Use ONLY: "anime [character_type] with [emotion] expression"
- Character types: "girl", "boy", "character"
- Emotions: "happy", "sad", "angry", "surprised"
- NO backgrounds, NO poses, NO scene descriptions
- NO magical effects, NO complex details
- FOCUS: Clear character face with recognizable emotion
- Example: "anime girl with happy expression"

Generate a complete, engaging story with rich visual details for each panel."""

        return prompt
    
    def _call_llm(self, prompt: str) -> Optional[str]:
        """Call the LLM API to generate story content."""
        
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=data,
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                print(f"⚠️ LLM API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"⚠️ LLM call failed: {e}")
            return None
    
    def _parse_story_response(self, response: str, user_prompt: str, panels: int) -> Dict[str, Any]:
        """Parse LLM response into structured story data."""
        
        try:
            # Try to extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                story_data = json.loads(json_str)
                
                # Validate structure
                if self._validate_story_structure(story_data, panels):
                    return story_data
            
            print("⚠️ Failed to parse LLM response, using fallback")
            return self._create_fallback_story(user_prompt, panels)
            
        except Exception as e:
            print(f"⚠️ Story parsing error: {e}")
            return self._create_fallback_story(user_prompt, panels)
    
    def _validate_story_structure(self, story_data: Dict[str, Any], expected_panels: int) -> bool:
        """Validate that story data has required structure."""
        
        required_keys = ["title", "character", "panels"]
        if not all(key in story_data for key in required_keys):
            return False
        
        character_keys = ["name", "appearance", "personality"]
        if not all(key in story_data["character"] for key in character_keys):
            return False
        
        if len(story_data["panels"]) != expected_panels:
            return False
        
        panel_keys = ["panel_number", "scene_description", "character_emotion", 
                     "character_pose", "visual_prompt", "dialogue", "narrative_purpose"]
        
        for panel in story_data["panels"]:
            if not all(key in panel for key in panel_keys):
                return False
        
        return True
    
    def _create_fallback_story(self, user_prompt: str, panels: int) -> Dict[str, Any]:
        """Create a fallback story if LLM generation fails."""
        
        print("🔧 Creating fallback story structure")
        
        # Extract key themes from user prompt
        themes = self._extract_themes(user_prompt)
        
        story_data = {
            "title": f"Story: {user_prompt[:30]}...",
            "character": {
                "name": "Protagonist",
                "appearance": "young anime character with dark hair, bright eyes, casual modern clothing, determined expression",
                "personality": "brave, curious, determined"
            },
            "panels": []
        }
        
        # Create basic story progression
        emotions = ["neutral", "surprised", "determined", "happy"][:panels]
        poses = ["standing", "arms_crossed", "running", "jumping"][:panels]
        
        for i in range(panels):
            panel = {
                "panel_number": i + 1,
                "scene_description": f"Scene {i+1} related to {themes}",
                "character_emotion": emotions[i],
                "character_pose": poses[i],
                "visual_prompt": f"manga panel showing {story_data['character']['appearance']} with {emotions[i]} expression in {poses[i]} pose, {themes} theme",
                "dialogue": [f"Panel {i+1} dialogue about {themes}"],
                "narrative_purpose": f"Advance story progression for {themes}"
            }
            story_data["panels"].append(panel)
        
        return story_data
    
    def _extract_themes(self, prompt: str) -> str:
        """Extract key themes from user prompt for fallback story."""
        
        # Simple keyword extraction
        keywords = prompt.lower().split()
        themes = " ".join(keywords[:3])  # Use first 3 words as theme
        
        return themes if themes else "adventure"
