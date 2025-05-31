#!/usr/bin/env python3
"""
Manga Generation Demo

A simple demonstration of the complete manga generation pipeline.
This script shows how to use the three main functions:
1. generate_story() - LLM story generation
2. build_image_prompts() - Convert story to image prompts  
3. generate_image() - Create manga panel images

Usage:
    python demo.py
"""

import sys
from pathlib import Path

# Import our modules
from llm.story_generator import generate_story
from pipeline.prompt_builder import build_image_prompts
from image_gen.image_generator import generate_manga_sequence


def main():
    """Main demo function."""
    print("🎌 MANGA GENERATION DEMO")
    print("=" * 50)
    
    # Get user input
    print("Enter your manga story prompt:")
    user_prompt = input("> ").strip()
    
    if not user_prompt:
        user_prompt = "A young ninja discovers they have magical powers in a modern city"
        print(f"Using default prompt: {user_prompt}")
    
    print("\nSelect manga style:")
    print("1. Shonen (action, adventure, friendship)")
    print("2. Seinen (mature, complex)")
    print("3. Slice of Life (everyday, peaceful)")
    print("4. Fantasy (magical, mystical)")
    
    style_choice = input("Enter choice (1-4) or press Enter for default: ").strip()
    
    styles = {"1": "shonen", "2": "seinen", "3": "slice_of_life", "4": "fantasy"}
    style = styles.get(style_choice, "shonen")
    
    print(f"Selected style: {style}")
    print("=" * 50)
    
    # Step 1: Generate Story
    print("📝 Step 1: Generating story with LLM...")
    try:
        story_paragraphs = generate_story(user_prompt, style)
        print(f"✅ Generated {len(story_paragraphs)} story scenes")
        
        print("\n📖 Generated Story:")
        print("-" * 30)
        for i, paragraph in enumerate(story_paragraphs, 1):
            print(f"Scene {i}: {paragraph[:100]}...")
        
    except Exception as e:
        print(f"❌ Error generating story: {e}")
        return
    
    # Step 2: Build Image Prompts
    print(f"\n🎨 Step 2: Converting story to image prompts...")
    try:
        image_prompts = build_image_prompts(story_paragraphs)
        print(f"✅ Created {len(image_prompts)} image prompts")
        
        print("\n🖼️  Sample Image Prompt:")
        print("-" * 30)
        sample_prompt = image_prompts[0]
        if "| NEGATIVE:" in sample_prompt:
            positive, negative = sample_prompt.split("| NEGATIVE:")
            print(f"Positive: {positive.strip()[:100]}...")
            print(f"Negative: {negative.strip()[:50]}...")
        else:
            print(f"{sample_prompt[:150]}...")
        
    except Exception as e:
        print(f"❌ Error building prompts: {e}")
        return
    
    # Step 3: Generate Images
    print(f"\n🖌️  Step 3: Generating manga panel images...")
    print("Note: Creating placeholder images (ComfyUI not connected)")
    
    try:
        image_paths = generate_manga_sequence(image_prompts)
        print(f"✅ Generated {len(image_paths)} panel images")
        
        print("\n📁 Generated Files:")
        print("-" * 30)
        for i, path in enumerate(image_paths, 1):
            file_path = Path(path)
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"Panel {i}: {file_path.name} ({file_size:,} bytes)")
        
    except Exception as e:
        print(f"❌ Error generating images: {e}")
        return
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 MANGA GENERATION COMPLETE!")
    print("=" * 50)
    print(f"📝 Story: {len(story_paragraphs)} scenes generated")
    print(f"🎨 Prompts: {len(image_prompts)} image prompts created")
    print(f"🖼️  Images: {len(image_paths)} panels generated")
    
    output_dir = Path("output/images")
    print(f"\n📂 Check your manga panels in: {output_dir.absolute()}")
    
    print("\n💡 Next Steps:")
    print("1. Set up ComfyUI for actual image generation")
    print("2. Customize prompts in pipeline/prompt_builder.py")
    print("3. Try different story styles and prompts")
    print("4. Use the generated prompts with your favorite AI image generator")


def quick_test():
    """Quick test of all three main functions."""
    print("🧪 QUICK FUNCTION TEST")
    print("=" * 30)
    
    test_prompt = "A robot learns about friendship"
    
    # Test 1: Story Generation
    print("Testing generate_story()...")
    try:
        story = generate_story(test_prompt, "shonen")
        print(f"✅ Generated {len(story)} paragraphs")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 2: Prompt Building
    print("Testing build_image_prompts()...")
    try:
        prompts = build_image_prompts(story)
        print(f"✅ Generated {len(prompts)} prompts")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test 3: Image Generation (single image)
    print("Testing generate_image()...")
    try:
        from image_gen.image_generator import generate_image
        path = generate_image(prompts[0], 99)  # Use index 99 for test
        print(f"✅ Generated image: {Path(path).name}")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    print("🎉 All functions working correctly!")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        quick_test()
    else:
        main()
