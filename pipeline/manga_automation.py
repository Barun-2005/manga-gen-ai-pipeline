"""
Full Manga Generation Automation

This module provides automation for complete manga generation from vague prompts:
1. Full story generation and structuring
2. Chapter splitting and panel planning
3. Dialog and narration assignment
4. Automated prompt-to-panel generation loops

Designed for end-to-end manga creation with minimal human intervention.
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

# Import our existing modules
from llm.story_generator import StoryGenerator
from pipeline.automation_stubs import generate_pose_from_text, assign_style_automatically
from scripts.generate_from_prompt import generate_manga_panel


class MangaStoryStructurer:
    """
    Handles story structuring and chapter planning for manga generation.
    """
    
    def __init__(self, model: str = "deepseek/deepseek-r1-distill-llama-70b"):
        """Initialize the story structurer."""
        self.story_generator = StoryGenerator(model)
        
    def generate_full_story(self, prompt: str, target_chapters: int = 3) -> Dict[str, Any]:
        """
        Generate a complete manga story from a vague prompt.
        
        Args:
            prompt: Vague story prompt (e.g., "ninja discovers magic")
            target_chapters: Number of chapters to generate
            
        Returns:
            Structured story with chapters and scenes
        """
        print(f"📖 Generating full story from: '{prompt}'")
        
        # Create detailed story prompt
        story_prompt = f"""
        Create a complete manga story based on: {prompt}
        
        Structure this as a {target_chapters}-chapter manga with the following:
        - Clear character development arc
        - Engaging plot with conflict and resolution
        - Visual scenes suitable for manga panels
        - Dialogue and action sequences
        - Proper pacing for manga format
        
        For each chapter, provide:
        - Chapter title
        - 4-6 key scenes
        - Character interactions
        - Visual highlights
        
        Format as a structured narrative with clear chapter breaks.
        """
        
        try:
            story_text = self.story_generator.generate_story(
                story_prompt, 
                max_tokens=3000, 
                temperature=0.8
            )
            
            # Parse into structured format
            structured_story = self._parse_story_structure(story_text, target_chapters)
            structured_story["original_prompt"] = prompt
            structured_story["generation_time"] = datetime.now().isoformat()
            
            print(f"✅ Generated {len(structured_story['chapters'])} chapters")
            return structured_story
            
        except Exception as e:
            print(f"❌ Story generation failed: {e}")
            return self._create_fallback_story(prompt, target_chapters)
    
    def _parse_story_structure(self, story_text: str, target_chapters: int) -> Dict[str, Any]:
        """Parse generated story text into structured format."""
        # Basic parsing - split by chapter indicators
        chapters = []
        current_chapter = {"title": "", "scenes": []}
        
        lines = story_text.split('\n')
        scene_count = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect chapter headers
            if any(indicator in line.lower() for indicator in ["chapter", "part", "act"]):
                if current_chapter["scenes"]:
                    chapters.append(current_chapter)
                current_chapter = {"title": line, "scenes": []}
            elif line and len(line) > 20:  # Likely a scene description
                current_chapter["scenes"].append({
                    "scene_number": scene_count + 1,
                    "description": line,
                    "estimated_panels": self._estimate_panel_count(line)
                })
                scene_count += 1
        
        # Add final chapter
        if current_chapter["scenes"]:
            chapters.append(current_chapter)
        
        # Ensure we have the target number of chapters
        while len(chapters) < target_chapters:
            chapters.append({
                "title": f"Chapter {len(chapters) + 1}",
                "scenes": [{"scene_number": scene_count + 1, "description": "Story continues...", "estimated_panels": 2}]
            })
            scene_count += 1
        
        return {
            "title": "Generated Manga",
            "chapters": chapters[:target_chapters],
            "total_scenes": scene_count,
            "estimated_total_panels": sum(
                sum(scene["estimated_panels"] for scene in chapter["scenes"]) 
                for chapter in chapters[:target_chapters]
            )
        }
    
    def _estimate_panel_count(self, scene_description: str) -> int:
        """Estimate number of panels needed for a scene."""
        word_count = len(scene_description.split())
        
        # Basic estimation based on content
        if word_count < 20:
            return 1
        elif word_count < 50:
            return 2
        elif word_count < 100:
            return 3
        else:
            return 4
    
    def _create_fallback_story(self, prompt: str, target_chapters: int) -> Dict[str, Any]:
        """Create a fallback story structure when generation fails."""
        chapters = []
        for i in range(target_chapters):
            chapters.append({
                "title": f"Chapter {i + 1}",
                "scenes": [
                    {
                        "scene_number": i * 3 + j + 1,
                        "description": f"Scene from chapter {i + 1} based on: {prompt}",
                        "estimated_panels": 2
                    }
                    for j in range(3)
                ]
            })
        
        return {
            "title": "Fallback Manga Story",
            "chapters": chapters,
            "total_scenes": target_chapters * 3,
            "estimated_total_panels": target_chapters * 6,
            "original_prompt": prompt,
            "generation_time": datetime.now().isoformat(),
            "fallback": True
        }


class DialogAssigner:
    """
    Handles dialog and narration assignment for manga scenes.
    """
    
    def __init__(self, model: str = "deepseek/deepseek-r1-distill-llama-70b"):
        """Initialize the dialog assigner."""
        self.story_generator = StoryGenerator(model)
    
    def assign_dialog_and_narration(self, scene_description: str) -> Dict[str, Any]:
        """
        Assign dialog and narration to a scene for manga panel creation.
        
        Args:
            scene_description: Description of the scene
            
        Returns:
            Dictionary with dialog, narration, and panel breakdown
        """
        dialog_prompt = f"""
        For this manga scene: {scene_description}
        
        Create appropriate dialog and narration:
        - Character dialogue (if any)
        - Narrative text boxes
        - Sound effects (if appropriate)
        - Panel descriptions
        
        Format as manga-ready content with clear speaker attribution.
        """
        
        try:
            dialog_content = self.story_generator.generate_story(
                dialog_prompt,
                max_tokens=800,
                temperature=0.7
            )
            
            return {
                "scene_description": scene_description,
                "dialog_content": dialog_content,
                "has_dialog": ":" in dialog_content or '"' in dialog_content,
                "estimated_text_density": len(dialog_content.split()) / 100,  # Rough metric
                "processing_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ Dialog assignment failed: {e}")
            return {
                "scene_description": scene_description,
                "dialog_content": f"[Scene: {scene_description}]",
                "has_dialog": False,
                "estimated_text_density": 0.1,
                "processing_time": datetime.now().isoformat(),
                "fallback": True
            }


class MangaPanelPipeline:
    """
    Automated pipeline for converting story scenes to manga panels.
    """
    
    def __init__(self):
        """Initialize the panel pipeline."""
        self.structurer = MangaStoryStructurer()
        self.dialog_assigner = DialogAssigner()
    
    def generate_full_manga(
        self, 
        prompt: str, 
        chapters: int = 3,
        output_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete manga from a vague prompt.
        
        Args:
            prompt: Vague story prompt
            chapters: Number of chapters
            output_dir: Output directory (auto-generated if None)
            
        Returns:
            Complete manga generation results
        """
        print("🎨 Starting full manga generation...")
        print(f"📝 Prompt: '{prompt}'")
        print(f"📚 Target chapters: {chapters}")
        
        # Create output directory
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"outputs/manga_{timestamp}"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Generate story structure
        print("\n📖 Step 1: Generating story structure...")
        story_structure = self.structurer.generate_full_story(prompt, chapters)
        
        # Save story structure
        with open(output_path / "story_structure.json", 'w') as f:
            json.dump(story_structure, f, indent=2)
        
        # Step 2: Process each chapter
        manga_results = {
            "prompt": prompt,
            "story_structure": story_structure,
            "chapters": [],
            "total_panels_generated": 0,
            "generation_time": datetime.now().isoformat(),
            "output_directory": str(output_path)
        }
        
        for chapter_idx, chapter in enumerate(story_structure["chapters"]):
            print(f"\n📚 Processing {chapter['title']}...")
            chapter_results = self._process_chapter(chapter, chapter_idx + 1, output_path)
            manga_results["chapters"].append(chapter_results)
            manga_results["total_panels_generated"] += chapter_results["panels_generated"]
        
        # Save final results
        with open(output_path / "manga_results.json", 'w') as f:
            json.dump(manga_results, f, indent=2)
        
        print(f"\n🎉 Manga generation complete!")
        print(f"📁 Output: {output_path}")
        print(f"🖼️  Total panels: {manga_results['total_panels_generated']}")
        
        return manga_results
    
    def _process_chapter(self, chapter: Dict[str, Any], chapter_num: int, output_path: Path) -> Dict[str, Any]:
        """Process a single chapter into manga panels."""
        chapter_dir = output_path / f"chapter_{chapter_num:02d}"
        chapter_dir.mkdir(exist_ok=True)
        
        chapter_results = {
            "title": chapter["title"],
            "scenes": [],
            "panels_generated": 0
        }
        
        for scene_idx, scene in enumerate(chapter["scenes"]):
            print(f"  🎬 Scene {scene_idx + 1}: {scene['description'][:50]}...")
            
            # Assign dialog and narration
            dialog_data = self.dialog_assigner.assign_dialog_and_narration(scene["description"])
            
            # Generate panel(s) for this scene
            panel_prompt = f"{scene['description']} {dialog_data['dialog_content']}"
            
            try:
                panel_path = generate_manga_panel(
                    text_prompt=panel_prompt,
                    pose_override=None,  # Auto-detect
                    style_override=None,  # Auto-detect
                    seed=None
                )
                
                # Move panel to chapter directory
                if panel_path and Path(panel_path).exists():
                    final_panel_path = chapter_dir / f"scene_{scene_idx + 1:02d}.png"
                    Path(panel_path).rename(final_panel_path)
                    
                    scene_result = {
                        "scene_number": scene_idx + 1,
                        "description": scene["description"],
                        "dialog_data": dialog_data,
                        "panel_path": str(final_panel_path),
                        "generation_success": True
                    }
                    chapter_results["panels_generated"] += 1
                else:
                    scene_result = {
                        "scene_number": scene_idx + 1,
                        "description": scene["description"],
                        "dialog_data": dialog_data,
                        "panel_path": None,
                        "generation_success": False,
                        "error": "Panel generation failed"
                    }
                
            except Exception as e:
                scene_result = {
                    "scene_number": scene_idx + 1,
                    "description": scene["description"],
                    "dialog_data": dialog_data,
                    "panel_path": None,
                    "generation_success": False,
                    "error": str(e)
                }
            
            chapter_results["scenes"].append(scene_result)
        
        return chapter_results


# Convenience function for easy usage
def generate_manga_from_prompt(prompt: str, chapters: int = 3) -> str:
    """
    Generate a complete manga from a simple prompt.
    
    Args:
        prompt: Story prompt (e.g., "ninja discovers magic")
        chapters: Number of chapters to generate
        
    Returns:
        Path to the generated manga directory
    """
    pipeline = MangaPanelPipeline()
    results = pipeline.generate_full_manga(prompt, chapters)
    return results["output_directory"]
