"""
Main Manga Generation Pipeline

Orchestrates the complete manga generation process:
LLM story generation → prompt building → ComfyUI image generation → PDF compilation
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Import our modules
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm.story_generator import StoryGenerator
from llm.prompt_templates import get_act_prompt, get_genre_modifier
from image_gen.comfy_client import ComfyUIClient
from image_gen.prompt_builder import PromptBuilder, create_story_prompts
from pipeline.utils import setup_logging, set_seed, save_json, load_json


class MangaGenerator:
    """
    Main pipeline for generating complete manga from text prompts.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the manga generator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or self._load_default_config()
        self.logger = setup_logging(self.config.get("log_level", "INFO"))
        
        # Initialize components
        self.story_generator = StoryGenerator(
            model=self.config.get("llm_model", "anthropic/claude-3-sonnet")
        )
        self.comfy_client = ComfyUIClient(
            base_url=self.config.get("comfyui_url"),
            timeout=self.config.get("comfyui_timeout", 300)
        )
        self.prompt_builder = PromptBuilder()
        
        # Setup output directories
        self.output_dir = Path(self.config.get("output_dir", "output"))
        self.images_dir = self.output_dir / "images"
        self.manga_dir = self.output_dir / "manga"
        
        self._create_output_dirs()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration."""
        return {
            "llm_model": "anthropic/claude-3-sonnet",
            "comfyui_url": "http://127.0.0.1:8188",
            "comfyui_timeout": 300,
            "output_dir": "output",
            "log_level": "INFO",
            "image_width": 512,
            "image_height": 768,
            "panels_per_page": 4,
            "seed": -1
        }
    
    def _create_output_dirs(self) -> None:
        """Create necessary output directories."""
        self.output_dir.mkdir(exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.manga_dir.mkdir(exist_ok=True)
    
    def generate_story(
        self, 
        prompt: str, 
        genre: str = "shonen",
        acts: int = 3,
        scenes_per_act: int = 3
    ) -> Dict[str, Any]:
        """
        Generate story using LLM.
        
        Args:
            prompt: Initial story prompt
            genre: Story genre
            acts: Number of acts
            scenes_per_act: Scenes per act
            
        Returns:
            Generated story data
        """
        self.logger.info(f"Generating story for prompt: {prompt}")
        
        # Get genre modifiers
        genre_info = get_genre_modifier(genre)
        
        # Generate structured story
        story_data = self.story_generator.generate_structured_story(
            prompt=prompt,
            acts=acts,
            scenes_per_act=scenes_per_act
        )
        
        # Add genre information
        story_data["genre"] = genre
        story_data["genre_info"] = genre_info
        
        self.logger.info("Story generation completed")
        return story_data
    
    def generate_prompts(self, story_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Generate image prompts from story data.
        
        Args:
            story_data: Story data from LLM
            
        Returns:
            List of prompt dictionaries
        """
        self.logger.info("Generating image prompts from story")
        
        # Create prompts for each scene
        prompt_pairs = create_story_prompts(story_data)
        
        prompts = []
        for i, (positive, negative) in enumerate(prompt_pairs):
            prompts.append({
                "scene_index": i,
                "positive_prompt": positive,
                "negative_prompt": negative,
                "width": self.config["image_width"],
                "height": self.config["image_height"]
            })
        
        self.logger.info(f"Generated {len(prompts)} image prompts")
        return prompts
    
    def generate_images(self, prompts: List[Dict[str, str]]) -> List[str]:
        """
        Generate images using ComfyUI.
        
        Args:
            prompts: List of prompt dictionaries
            
        Returns:
            List of generated image file paths
        """
        self.logger.info("Starting image generation with ComfyUI")
        
        if not self.comfy_client.is_server_ready():
            raise Exception("ComfyUI server is not ready")
        
        generated_images = []
        
        for i, prompt_data in enumerate(prompts):
            self.logger.info(f"Generating image {i+1}/{len(prompts)}")
            
            # Create workflow (placeholder - needs actual ComfyUI workflow)
            workflow = self._create_workflow(prompt_data)
            
            # Generate image
            try:
                image_paths = self.comfy_client.generate_images(
                    workflow=workflow,
                    output_dir=str(self.images_dir)
                )
                generated_images.extend(image_paths)
                
            except Exception as e:
                self.logger.error(f"Error generating image {i+1}: {e}")
                # Continue with other images
        
        self.logger.info(f"Generated {len(generated_images)} images")
        return generated_images
    
    def _create_workflow(self, prompt_data: Dict[str, str]) -> Dict[str, Any]:
        """
        Create ComfyUI workflow from prompt data.
        
        Args:
            prompt_data: Prompt information
            
        Returns:
            ComfyUI workflow dictionary
        """
        # TODO: Implement actual ComfyUI workflow creation
        # This is a placeholder that should be replaced with real workflow
        
        workflow = {
            "prompt": prompt_data["positive_prompt"],
            "negative_prompt": prompt_data["negative_prompt"],
            "width": prompt_data["width"],
            "height": prompt_data["height"],
            "seed": self.config["seed"]
        }
        
        return workflow
    
    def compile_manga(
        self, 
        image_paths: List[str], 
        story_data: Dict[str, Any],
        output_filename: str = None
    ) -> str:
        """
        Compile images into final manga format.
        
        Args:
            image_paths: List of generated image paths
            story_data: Original story data
            output_filename: Output file name (optional)
            
        Returns:
            Path to compiled manga file
        """
        self.logger.info("Compiling manga from generated images")
        
        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"manga_{timestamp}.pdf"
        
        output_path = self.manga_dir / output_filename
        
        # TODO: Implement actual PDF compilation
        # For now, just create a metadata file
        
        manga_metadata = {
            "title": story_data.get("title", "Generated Manga"),
            "generated_at": datetime.now().isoformat(),
            "story_prompt": story_data.get("prompt", ""),
            "genre": story_data.get("genre", ""),
            "image_count": len(image_paths),
            "image_paths": image_paths,
            "config": self.config
        }
        
        metadata_path = output_path.with_suffix(".json")
        save_json(manga_metadata, str(metadata_path))
        
        self.logger.info(f"Manga metadata saved to: {metadata_path}")
        return str(metadata_path)
    
    def generate_complete_manga(
        self, 
        prompt: str,
        genre: str = "shonen",
        output_filename: str = None
    ) -> Dict[str, Any]:
        """
        Complete manga generation pipeline.
        
        Args:
            prompt: Initial story prompt
            genre: Story genre
            output_filename: Output filename (optional)
            
        Returns:
            Generation results and metadata
        """
        self.logger.info("Starting complete manga generation pipeline")
        
        # Set seed if specified
        if self.config["seed"] != -1:
            set_seed(self.config["seed"])
        
        try:
            # Step 1: Generate story
            story_data = self.generate_story(prompt, genre)
            
            # Step 2: Generate image prompts
            prompts = self.generate_prompts(story_data)
            
            # Step 3: Generate images
            image_paths = self.generate_images(prompts)
            
            # Step 4: Compile manga
            manga_path = self.compile_manga(image_paths, story_data, output_filename)
            
            # Prepare results
            results = {
                "success": True,
                "story_data": story_data,
                "image_count": len(image_paths),
                "image_paths": image_paths,
                "manga_path": manga_path,
                "generation_time": datetime.now().isoformat()
            }
            
            self.logger.info("Manga generation completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"Error in manga generation pipeline: {e}")
            return {
                "success": False,
                "error": str(e),
                "generation_time": datetime.now().isoformat()
            }


def main():
    """Main entry point for command-line usage."""
    parser = argparse.ArgumentParser(description="Generate manga from text prompts")
    parser.add_argument("prompt", help="Story prompt for manga generation")
    parser.add_argument("--genre", default="shonen", help="Manga genre")
    parser.add_argument("--output", help="Output filename")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument("--seed", type=int, default=-1, help="Random seed")
    
    args = parser.parse_args()
    
    # Load configuration
    config = None
    if args.config and os.path.exists(args.config):
        config = load_json(args.config)
    
    if not config:
        config = {}
    
    # Override with command line arguments
    if args.seed != -1:
        config["seed"] = args.seed
    
    # Initialize generator
    generator = MangaGenerator(config)
    
    # Generate manga
    results = generator.generate_complete_manga(
        prompt=args.prompt,
        genre=args.genre,
        output_filename=args.output
    )
    
    # Print results
    if results["success"]:
        print(f"Manga generation successful!")
        print(f"Generated {results['image_count']} images")
        print(f"Output saved to: {results['manga_path']}")
    else:
        print(f"Manga generation failed: {results['error']}")


if __name__ == "__main__":
    main()
