"""
Story Generator Module

Handles LLM API interactions via OpenRouter for generating manga stories.
Accepts vague prompts and returns structured story text.
"""

import os
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class StoryGenerator:
    """
    Generates manga stories using OpenRouter LLM API.
    """

    def __init__(self, model: str = "deepseek/deepseek-r1-0528:free"):
        """
        Initialize the story generator.

        Args:
            model: The LLM model to use via OpenRouter
        """
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = model

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment variables")

    def generate_story(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7
    ) -> str:
        """
        Generate a manga story from a vague prompt.

        Args:
            prompt: The input prompt describing the desired story
            max_tokens: Maximum tokens for the response
            temperature: Creativity level (0.0 to 1.0)

        Returns:
            Generated story text
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a creative manga story writer. Generate engaging stories with clear scenes, dialogue, and visual descriptions suitable for manga panels."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()
            return data["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"Error calling OpenRouter API: {e}")
        except KeyError as e:
            raise Exception(f"Unexpected API response format: {e}")

    def generate_structured_story(
        self,
        prompt: str,
        acts: int = 3,
        scenes_per_act: int = 3
    ) -> Dict[str, Any]:
        """
        Generate a structured manga story with acts and scenes.

        Args:
            prompt: The input prompt
            acts: Number of acts in the story
            scenes_per_act: Number of scenes per act

        Returns:
            Structured story data with acts, scenes, and metadata
        """
        structured_prompt = f"""
        Create a manga story based on: {prompt}

        Structure the story with {acts} acts and {scenes_per_act} scenes per act.
        For each scene, provide:
        - Scene description
        - Character dialogue
        - Visual elements for manga panels
        - Mood/atmosphere

        Format as a clear narrative with scene breaks.
        """

        story_text = self.generate_story(structured_prompt)

        # TODO: Parse the story text into structured format
        # For now, return basic structure
        return {
            "title": "Generated Manga Story",
            "prompt": prompt,
            "story_text": story_text,
            "acts": acts,
            "scenes_per_act": scenes_per_act,
            "metadata": {
                "model": self.model,
                "generated_at": None  # TODO: Add timestamp
            }
        }


def generate_story(prompt: str, style: str = "shonen") -> List[str]:
    """
    Sends the user's prompt to the OpenRouter API and returns a list of story paragraphs.

    Args:
        prompt: The user's story prompt
        style: The manga style (shonen, seinen, slice_of_life, fantasy)

    Returns:
        List of story paragraphs, each representing a scene/panel
    """
    try:
        generator = StoryGenerator()

        # Create a structured prompt based on style
        style_prompt = f"""
        Create a manga story in {style} style based on: {prompt}

        Structure the story as exactly 6 distinct scenes/panels.
        Each scene should be a separate paragraph that can be visualized as a manga panel.
        Focus on visual descriptions, character actions, and dialogue.
        Make each scene vivid and suitable for image generation.

        Format: Return exactly 6 paragraphs, each describing one scene.
        """

        # Generate the story
        story_text = generator.generate_story(style_prompt, max_tokens=1500, temperature=0.8)

        # Split into paragraphs and clean up
        paragraphs = [p.strip() for p in story_text.split('\n\n') if p.strip()]

        # Ensure we have exactly 6 paragraphs
        if len(paragraphs) < 6:
            # Pad with additional scenes if needed
            while len(paragraphs) < 6:
                paragraphs.append(f"Scene {len(paragraphs) + 1}: The story continues with dramatic tension.")
        elif len(paragraphs) > 6:
            # Take only the first 6 paragraphs
            paragraphs = paragraphs[:6]

        return paragraphs

    except Exception as e:
        print(f"Error generating story: {e}")
        # Return placeholder paragraphs for testing
        return [
            f"Scene 1: A young protagonist begins their journey in a {style} manga world.",
            f"Scene 2: They encounter their first challenge and show determination.",
            f"Scene 3: A mysterious character appears and changes everything.",
            f"Scene 4: The protagonist faces a difficult choice.",
            f"Scene 5: An intense confrontation tests their resolve.",
            f"Scene 6: The story concludes with growth and new possibilities."
        ]


def generate_manga_story(prompt: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to generate a manga story.

    Args:
        prompt: Story prompt
        **kwargs: Additional arguments for StoryGenerator

    Returns:
        Generated story data
    """
    generator = StoryGenerator()
    return generator.generate_structured_story(prompt, **kwargs)


if __name__ == "__main__":
    # Example usage
    test_prompt = "A young ninja discovers they have magical powers in a modern city"

    # Test the new generate_story function
    story_paragraphs = generate_story(test_prompt, "shonen")
    print("Generated story paragraphs:")
    for i, paragraph in enumerate(story_paragraphs, 1):
        print(f"Scene {i}: {paragraph[:100]}...")

    # Test the original function
    story = generate_manga_story(test_prompt)
    print(f"\nOriginal function result: {story['story_text'][:200]}...")
