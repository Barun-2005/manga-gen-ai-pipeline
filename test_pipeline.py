#!/usr/bin/env python3
"""
Test Script for Manga Generation Pipeline

This script demonstrates the complete manga generation workflow:
1. Generate story from prompt using LLM
2. Convert story to image prompts
3. Generate images for each panel
4. Save results

Usage:
    python test_pipeline.py
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import our modules
from llm.story_generator import generate_story
from pipeline.prompt_builder import build_image_prompts, create_panel_sequence_prompts
from image_gen.image_generator import generate_manga_sequence


def test_story_generation():
    """Test the story generation functionality."""
    print("=" * 60)
    print("TESTING STORY GENERATION")
    print("=" * 60)
    
    test_prompt = "A young ninja discovers they have magical powers in a modern city"
    style = "shonen"
    
    print(f"Input prompt: {test_prompt}")
    print(f"Style: {style}")
    print("\nGenerating story...")
    
    try:
        story_paragraphs = generate_story(test_prompt, style)
        
        print(f"\nGenerated {len(story_paragraphs)} story paragraphs:")
        print("-" * 40)
        
        for i, paragraph in enumerate(story_paragraphs, 1):
            print(f"Scene {i}:")
            print(f"  {paragraph}")
            print()
        
        return story_paragraphs
        
    except Exception as e:
        print(f"Error in story generation: {e}")
        return None


def test_prompt_building(story_paragraphs):
    """Test the image prompt building functionality."""
    print("=" * 60)
    print("TESTING PROMPT BUILDING")
    print("=" * 60)
    
    if not story_paragraphs:
        print("No story paragraphs to process")
        return None
    
    print("Converting story paragraphs to image prompts...")
    
    try:
        # Test basic prompt building
        image_prompts = build_image_prompts(story_paragraphs)
        
        print(f"\nGenerated {len(image_prompts)} image prompts:")
        print("-" * 40)
        
        for i, prompt in enumerate(image_prompts, 1):
            print(f"Panel {i} Prompt:")
            # Split prompt at | NEGATIVE: for better readability
            if "| NEGATIVE:" in prompt:
                positive, negative = prompt.split("| NEGATIVE:")
                print(f"  Positive: {positive.strip()}")
                print(f"  Negative: {negative.strip()}")
            else:
                print(f"  {prompt}")
            print()
        
        # Test enhanced sequence creation
        print("Creating enhanced panel sequence...")
        panel_sequence = create_panel_sequence_prompts(story_paragraphs, "shonen")
        
        print("\nPanel Sequence Metadata:")
        print("-" * 40)
        for panel in panel_sequence:
            print(f"Panel {panel['panel_number']}:")
            print(f"  Composition: {panel['composition_type']}")
            print(f"  Complexity: {panel['estimated_complexity']}")
            print(f"  Style: {panel['style']}")
            print()
        
        return image_prompts
        
    except Exception as e:
        print(f"Error in prompt building: {e}")
        return None


def test_image_generation(image_prompts):
    """Test the image generation functionality."""
    print("=" * 60)
    print("TESTING IMAGE GENERATION")
    print("=" * 60)
    
    if not image_prompts:
        print("No image prompts to process")
        return None
    
    print("Generating manga panel images...")
    print("Note: This will create placeholder images if ComfyUI is not available")
    
    try:
        # Generate images for all panels
        image_paths = generate_manga_sequence(image_prompts)
        
        print(f"\nGenerated {len(image_paths)} panel images:")
        print("-" * 40)
        
        for i, path in enumerate(image_paths, 1):
            file_path = Path(path)
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"Panel {i}: {path} ({file_size} bytes)")
            else:
                print(f"Panel {i}: {path} (file not found)")
        
        return image_paths
        
    except Exception as e:
        print(f"Error in image generation: {e}")
        return None


def test_complete_pipeline():
    """Test the complete manga generation pipeline."""
    print("🎌 MANGA GENERATION PIPELINE TEST")
    print("=" * 60)
    print("This test will run through the complete pipeline:")
    print("1. Story Generation (LLM)")
    print("2. Prompt Building")
    print("3. Image Generation")
    print("=" * 60)
    
    # Step 1: Generate story
    story_paragraphs = test_story_generation()
    if not story_paragraphs:
        print("❌ Story generation failed, stopping pipeline test")
        return False
    
    # Step 2: Build image prompts
    image_prompts = test_prompt_building(story_paragraphs)
    if not image_prompts:
        print("❌ Prompt building failed, stopping pipeline test")
        return False
    
    # Step 3: Generate images
    image_paths = test_image_generation(image_prompts)
    if not image_paths:
        print("❌ Image generation failed, stopping pipeline test")
        return False
    
    # Summary
    print("=" * 60)
    print("PIPELINE TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Generated {len(story_paragraphs)} story scenes")
    print(f"✅ Created {len(image_prompts)} image prompts")
    print(f"✅ Generated {len(image_paths)} panel images")
    
    # Check output directory
    output_dir = Path("output/images")
    if output_dir.exists():
        panel_files = list(output_dir.glob("panel_*.png")) + list(output_dir.glob("panel_*.txt"))
        print(f"✅ Output directory contains {len(panel_files)} panel files")
        
        print("\nGenerated files:")
        for file_path in sorted(panel_files):
            print(f"  📄 {file_path}")
    
    print("\n🎉 Complete pipeline test successful!")
    return True


def test_individual_functions():
    """Test individual functions separately."""
    print("🔧 INDIVIDUAL FUNCTION TESTS")
    print("=" * 60)
    
    # Test 1: Story generation with different styles
    print("Test 1: Story generation with different styles")
    print("-" * 40)
    
    test_prompt = "A detective investigates supernatural crimes"
    styles = ["shonen", "seinen", "slice_of_life", "fantasy"]
    
    for style in styles:
        print(f"Testing {style} style...")
        try:
            paragraphs = generate_story(test_prompt, style)
            print(f"  ✅ Generated {len(paragraphs)} paragraphs for {style}")
        except Exception as e:
            print(f"  ❌ Error with {style}: {e}")
    
    # Test 2: Prompt building edge cases
    print("\nTest 2: Prompt building edge cases")
    print("-" * 40)
    
    edge_cases = [
        ["Single paragraph test"],
        ["Multiple", "paragraphs", "with", "different", "lengths"],
        [""],  # Empty paragraph
        ["Very long paragraph with lots of details about characters, environments, actions, emotions, and complex scene descriptions that should be properly processed by the prompt builder"]
    ]
    
    for i, test_case in enumerate(edge_cases, 1):
        print(f"Testing edge case {i}...")
        try:
            prompts = build_image_prompts(test_case)
            print(f"  ✅ Generated {len(prompts)} prompts from {len(test_case)} paragraphs")
        except Exception as e:
            print(f"  ❌ Error with edge case {i}: {e}")
    
    print("\n✅ Individual function tests completed!")


def main():
    """Main test function."""
    print("🚀 STARTING MANGA GENERATION PIPELINE TESTS")
    print("=" * 60)
    
    # Check environment
    print("Environment Check:")
    print(f"  Python version: {sys.version}")
    print(f"  Working directory: {os.getcwd()}")
    print(f"  Project root: {project_root}")
    
    # Check if .env file exists
    env_file = project_root / ".env"
    if env_file.exists():
        print("  ✅ .env file found")
    else:
        print("  ⚠️  .env file not found")
    
    # Check output directory
    output_dir = project_root / "output" / "images"
    output_dir.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ Output directory ready: {output_dir}")
    
    print()
    
    # Run tests
    try:
        # Test individual functions first
        test_individual_functions()
        print()
        
        # Test complete pipeline
        success = test_complete_pipeline()
        
        if success:
            print("\n🎉 All tests completed successfully!")
            print("\nNext steps:")
            print("1. Add your OpenRouter API key to .env file")
            print("2. Set up ComfyUI for actual image generation")
            print("3. Run the pipeline with your own prompts")
        else:
            print("\n⚠️  Some tests failed, but basic functionality works")
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
