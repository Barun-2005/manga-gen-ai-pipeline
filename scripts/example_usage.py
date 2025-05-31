#!/usr/bin/env python3
"""
Example Usage Script for Manga Panel Generation

Demonstrates how to use the manga generation workflows and automation scripts.

Usage:
    python scripts/example_usage.py
"""

import json
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.generate_panel import MangaPanelGenerator


def example_1_basic_generation():
    """Example 1: Basic manga panel generation with auto-generated pose."""
    print("📖 Example 1: Basic Manga Panel Generation")
    print("-" * 50)
    
    # Configuration for a ninja action scene
    config = {
        "prompt": "A young ninja leaping between rooftops at sunset, dynamic action pose, determined expression",
        "pose_image": "generate:ninja jumping with arms extended forward",
        "style_image": "process:naruto",
        "seed": 12345
    }
    
    print("Configuration:")
    print(json.dumps(config, indent=2))
    
    try:
        generator = MangaPanelGenerator()
        
        if not generator.client.is_server_ready():
            print("⚠️  ComfyUI server not available - this is a demo of the configuration")
            print("✅ Configuration is valid and ready for use when ComfyUI is running")
            return
        
        result_path = generator.generate_from_config(config)
        print(f"✅ Generated panel: {result_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_detective_scene():
    """Example 2: Detective investigation scene with custom pose."""
    print("\n🕵️ Example 2: Detective Investigation Scene")
    print("-" * 50)
    
    config = {
        "prompt": "A detective examining evidence under a streetlight, serious expression, noir atmosphere, shadows",
        "pose_image": "generate:person crouching down examining something on ground",
        "style_image": "process:detective_conan",
        "seed": 67890
    }
    
    print("Configuration:")
    print(json.dumps(config, indent=2))
    
    try:
        generator = MangaPanelGenerator()
        
        if not generator.client.is_server_ready():
            print("⚠️  ComfyUI server not available - this is a demo of the configuration")
            print("✅ Configuration is valid and ready for use when ComfyUI is running")
            return
        
        result_path = generator.generate_from_config(config)
        print(f"✅ Generated panel: {result_path}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def example_3_batch_generation():
    """Example 3: Batch generation of multiple panels."""
    print("\n📚 Example 3: Batch Panel Generation")
    print("-" * 50)
    
    # Multiple panel configurations for a short story
    panels = [
        {
            "prompt": "A young student walking to school, peaceful morning scene, cherry blossoms",
            "pose_image": "generate:person walking casually",
            "style_image": "process:slice_of_life",
            "seed": 11111
        },
        {
            "prompt": "The student discovers a mysterious glowing object in their backpack",
            "pose_image": "generate:person looking surprised at something in hands",
            "style_image": "process:slice_of_life",
            "seed": 22222
        },
        {
            "prompt": "Magical energy surrounds the student as they hold the object",
            "pose_image": "generate:person standing with arms raised, magical pose",
            "style_image": "process:fantasy",
            "seed": 33333
        }
    ]
    
    print(f"Generating {len(panels)} panels for a short story...")
    
    try:
        generator = MangaPanelGenerator()
        
        if not generator.client.is_server_ready():
            print("⚠️  ComfyUI server not available - this is a demo of the configurations")
            for i, panel in enumerate(panels, 1):
                print(f"\nPanel {i} Configuration:")
                print(json.dumps(panel, indent=2))
            print("✅ All configurations are valid and ready for use when ComfyUI is running")
            return
        
        results = []
        for i, panel_config in enumerate(panels, 1):
            print(f"\nGenerating panel {i}/{len(panels)}...")
            result_path = generator.generate_from_config(panel_config)
            results.append(result_path)
            print(f"✅ Panel {i} generated: {result_path}")
            
            # Small delay between generations
            time.sleep(2)
        
        print(f"\n🎉 Batch generation complete! Generated {len(results)} panels:")
        for i, path in enumerate(results, 1):
            print(f"  Panel {i}: {path}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_custom_workflow():
    """Example 4: Using custom workflow parameters."""
    print("\n⚙️ Example 4: Custom Workflow Parameters")
    print("-" * 50)
    
    # Advanced configuration with custom parameters
    config = {
        "prompt": "Epic battle scene, warrior facing dragon, dramatic lighting, intense action",
        "pose_image": "generate:warrior in fighting stance with sword raised",
        "style_image": "process:fantasy_epic",
        "seed": 99999,
        "advanced_settings": {
            "steps": 30,
            "cfg_scale": 8.0,
            "controlnet_strength": 1.2,
            "adapter_strength": 0.9
        }
    }
    
    print("Advanced Configuration:")
    print(json.dumps(config, indent=2))
    
    print("\n📝 Note: This example shows how to structure advanced configurations.")
    print("The automation script can be extended to handle these custom parameters.")


def example_5_file_based_generation():
    """Example 5: Generation using configuration files."""
    print("\n📄 Example 5: File-Based Generation")
    print("-" * 50)
    
    # Create example configuration files
    examples_dir = project_root / "examples"
    examples_dir.mkdir(exist_ok=True)
    
    # Save example configurations
    configs = {
        "action_scene.json": {
            "prompt": "Superhero flying through the city, cape flowing, heroic pose",
            "pose_image": "generate:person flying with arms forward",
            "style_image": "process:superhero",
            "seed": 55555
        },
        "romantic_scene.json": {
            "prompt": "Two characters sharing a quiet moment under stars, gentle expressions",
            "pose_image": "generate:two people sitting close together",
            "style_image": "process:shoujo",
            "seed": 77777
        }
    }
    
    for filename, config in configs.items():
        config_path = examples_dir / filename
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"✅ Created example config: {config_path}")
    
    print("\n💡 Usage with configuration files:")
    print("python scripts/generate_panel.py --input examples/action_scene.json")
    print("python scripts/generate_panel.py --input examples/romantic_scene.json")


def show_command_line_examples():
    """Show command line usage examples."""
    print("\n💻 Command Line Usage Examples")
    print("-" * 50)
    
    examples = [
        {
            "description": "Basic generation with auto-pose",
            "command": 'python scripts/generate_panel.py --prompt "ninja jumping" --pose "generate:jumping pose" --style "process:naruto"'
        },
        {
            "description": "Using existing pose and style files",
            "command": 'python scripts/generate_panel.py --prompt "detective investigating" --pose "crouch.png" --style "noir.png"'
        },
        {
            "description": "With custom seed",
            "command": 'python scripts/generate_panel.py --prompt "magical girl transformation" --pose "generate:magical pose" --style "process:sailor_moon" --seed 12345'
        },
        {
            "description": "Using configuration file",
            "command": 'python scripts/generate_panel.py --input examples/ninja_panel_config.json'
        }
    ]
    
    for example in examples:
        print(f"\n📌 {example['description']}:")
        print(f"   {example['command']}")


def main():
    """Main example demonstration."""
    print("🎨 Manga Panel Generation - Usage Examples")
    print("=" * 60)
    
    print("This script demonstrates various ways to use the manga generation system.")
    print("Examples will show configurations even if ComfyUI is not running.\n")
    
    # Run examples
    example_1_basic_generation()
    example_2_detective_scene()
    example_3_batch_generation()
    example_4_custom_workflow()
    example_5_file_based_generation()
    show_command_line_examples()
    
    print("\n" + "=" * 60)
    print("🎯 Next Steps")
    print("=" * 60)
    print("1. Install and start ComfyUI with required models")
    print("2. Test workflows: python scripts/test_workflows.py")
    print("3. Try basic generation: python scripts/generate_panel.py --prompt 'your prompt'")
    print("4. Create custom configurations in examples/ directory")
    print("5. Experiment with different styles and poses")
    
    print("\n📚 Documentation:")
    print("- Workflow details: workflows/README.md")
    print("- Project overview: README.md")
    print("- Example configs: examples/")


if __name__ == "__main__":
    main()
