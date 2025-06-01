#!/usr/bin/env python3
"""
MangaGen Self-Test Script

Comprehensive testing script that:
1. Checks if all required folders exist
2. Runs a dummy generation with test inputs
3. Verifies output files are saved correctly
4. Tests all major pipeline components

Usage:
    python scripts/self_test.py
"""

import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_directory_structure() -> bool:
    """
    Check if all required directories exist.
    
    Returns:
        True if all directories exist, False otherwise
    """
    print("🔍 Checking directory structure...")
    
    required_dirs = [
        "workflows/manga",
        "assets/styles", 
        "scripts",
        "examples",
        "outputs",
        "manga_archive",
        "llm",
        "image_gen",
        "pipeline"
    ]
    
    missing_dirs = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        print(f"\n⚠️  Missing directories: {missing_dirs}")
        return False
    
    print("✅ All required directories exist")
    return True


def check_dependencies() -> bool:
    """
    Check if all required Python modules can be imported.
    
    Returns:
        True if all dependencies are available, False otherwise
    """
    print("\n🔍 Checking dependencies...")
    
    required_modules = [
        ("requests", "HTTP requests"),
        ("PIL", "Image processing"),
        ("pathlib", "Path handling"),
        ("json", "JSON processing"),
        ("dotenv", "Environment variables")
    ]
    
    missing_modules = []
    
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name} - {description}")
        except ImportError:
            print(f"  ❌ {module_name} - MISSING ({description})")
            missing_modules.append(module_name)
    
    if missing_modules:
        print(f"\n⚠️  Missing modules: {missing_modules}")
        print("Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True


def test_llm_module() -> bool:
    """
    Test the LLM story generation module.
    
    Returns:
        True if LLM module works, False otherwise
    """
    print("\n🔍 Testing LLM module...")
    
    try:
        from llm.story_generator import generate_story
        
        # Test with a simple prompt
        test_prompt = "A robot learns to paint"
        print(f"  Testing with prompt: '{test_prompt}'")
        
        # This should return a list of story paragraphs
        story_result = generate_story(test_prompt, style="slice_of_life")
        
        if isinstance(story_result, list) and len(story_result) > 0:
            print(f"  ✅ Generated {len(story_result)} story segments")
            print(f"  📝 First segment: {story_result[0][:50]}...")
            return True
        else:
            print(f"  ❌ Invalid story result: {type(story_result)}")
            return False
            
    except Exception as e:
        print(f"  ❌ LLM module error: {e}")
        return False


def test_prompt_builder() -> bool:
    """
    Test the prompt building module.
    
    Returns:
        True if prompt builder works, False otherwise
    """
    print("\n🔍 Testing prompt builder...")
    
    try:
        from pipeline.prompt_builder import build_image_prompts
        
        # Test story segments
        test_story = [
            "A young artist sits in a quiet studio, paintbrush in hand.",
            "Sunlight streams through the window, illuminating the canvas.",
            "The artist begins to paint, lost in creative flow."
        ]
        
        print(f"  Testing with {len(test_story)} story segments")
        
        # Build image prompts
        prompts = build_image_prompts(test_story)
        
        if isinstance(prompts, list) and len(prompts) > 0:
            print(f"  ✅ Generated {len(prompts)} image prompts")
            print(f"  🎨 First prompt: {prompts[0][:50]}...")
            return True
        else:
            print(f"  ❌ Invalid prompts result: {type(prompts)}")
            return False
            
    except Exception as e:
        print(f"  ❌ Prompt builder error: {e}")
        return False


def test_image_generation() -> bool:
    """
    Test image generation (with fallback to placeholder).
    
    Returns:
        True if image generation works, False otherwise
    """
    print("\n🔍 Testing image generation...")
    
    try:
        from image_gen.image_generator import generate_image
        
        test_prompt = "manga style, simple test scene, black and white | NEGATIVE: blurry, low quality"
        test_index = 999  # Use high index to avoid conflicts
        
        print(f"  Testing with prompt: {test_prompt[:50]}...")
        
        # Generate test image
        image_path = generate_image(test_prompt, test_index)
        
        if image_path and Path(image_path).exists():
            file_size = Path(image_path).stat().st_size
            print(f"  ✅ Generated image: {image_path}")
            print(f"  📊 File size: {file_size:,} bytes")
            
            # Clean up test file
            try:
                Path(image_path).unlink()
                print(f"  🧹 Cleaned up test file")
            except:
                pass
                
            return True
        else:
            print(f"  ❌ Image generation failed: {image_path}")
            return False
            
    except Exception as e:
        print(f"  ❌ Image generation error: {e}")
        return False


def test_full_pipeline() -> bool:
    """
    Test the complete manga generation pipeline.
    
    Returns:
        True if full pipeline works, False otherwise
    """
    print("\n🔍 Testing full pipeline...")
    
    try:
        # Import pipeline components
        from llm.story_generator import generate_story
        from pipeline.prompt_builder import build_image_prompts
        from image_gen.image_generator import generate_image
        
        # Test prompt
        test_prompt = "A cat discovers a magical garden"
        print(f"  Testing full pipeline with: '{test_prompt}'")
        
        # Step 1: Generate story
        print("  📝 Step 1: Generating story...")
        story = generate_story(test_prompt, style="fantasy")
        
        if not story or len(story) == 0:
            print("  ❌ Story generation failed")
            return False
        
        print(f"  ✅ Generated {len(story)} story segments")
        
        # Step 2: Build image prompts
        print("  🎨 Step 2: Building image prompts...")
        prompts = build_image_prompts(story[:2])  # Test with first 2 segments only
        
        if not prompts or len(prompts) == 0:
            print("  ❌ Prompt building failed")
            return False
            
        print(f"  ✅ Generated {len(prompts)} image prompts")
        
        # Step 3: Generate one test image
        print("  🖼️  Step 3: Generating test image...")
        image_path = generate_image(prompts[0], 998)
        
        if image_path and Path(image_path).exists():
            print(f"  ✅ Generated test image: {image_path}")
            
            # Clean up
            try:
                Path(image_path).unlink()
                print("  🧹 Cleaned up test image")
            except:
                pass
                
            return True
        else:
            print("  ❌ Test image generation failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Full pipeline error: {e}")
        return False


def main():
    """Main test runner."""
    print("MangaGen Self-Test Suite")
    print("=" * 40)
    
    tests = [
        ("Directory Structure", check_directory_structure),
        ("Dependencies", check_dependencies),
        ("LLM Module", test_llm_module),
        ("Prompt Builder", test_prompt_builder),
        ("Image Generation", test_image_generation),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"\n❌ {test_name} test failed")
        except Exception as e:
            print(f"\n💥 {test_name} test crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! MangaGen is ready to use.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
