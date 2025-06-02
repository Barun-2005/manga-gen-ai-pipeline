#!/usr/bin/env python3
"""
Scene Generation CLI Tool

Command-line interface for generating multi-panel scenes with visual coherence.
Supports 3-5 panel sequences with character consistency and reference chaining.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.scene_manager import SceneManager, CharacterDescriptor, SceneSettings, create_sample_scene
from core.scene_generator import SceneAwareGenerator
from core.scene_validator import SceneValidator
from core.output_manager import OutputManager


def parse_prompts_file(file_path: str) -> List[str]:
    """Parse prompts from a text file."""
    prompts = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                prompts.append(line)
    return prompts


def create_scene_from_args(args) -> tuple:
    """Create scene metadata from command line arguments."""
    
    # Create character descriptors
    characters = []
    if args.character_name and args.character_appearance:
        character = CharacterDescriptor(
            name=args.character_name,
            appearance=args.character_appearance,
            clothing=args.character_clothing or "casual outfit",
            age_group=args.character_age or "adult",
            hair_style=args.character_hair or "medium length hair",
            distinctive_features=args.character_features or "none"
        )
        characters.append(character)
    else:
        # Use sample character
        characters, _ = create_sample_scene()
    
    # Create scene settings
    settings = SceneSettings(
        location=args.location or "ancient temple",
        time_of_day=args.time_of_day or "evening",
        weather=args.weather or "clear",
        lighting=args.lighting or "dramatic shadows",
        mood=args.mood or "mysterious",
        background_elements=args.background_elements.split(',') if args.background_elements else ["stone pillars", "ancient symbols"]
    )
    
    return characters, settings


def generate_scene_sequence(
    scene_name: str,
    prompts: List[str],
    output_dir: str,
    characters: List[CharacterDescriptor],
    settings: SceneSettings,
    character_focus: Optional[List[str]] = None,
    emotions: Optional[List[str]] = None,
    color_mode: Optional[str] = None
) -> bool:
    """Generate a complete scene sequence."""
    
    print(f"🎬 Generating Scene: {scene_name}")
    print(f"📋 Panels: {len(prompts)}")
    print(f"🎨 Color mode: {color_mode or 'default'}")
    print(f"📁 Output: {output_dir}")
    print("-" * 50)
    
    # Initialize components
    output_manager = OutputManager()
    run_dir = output_manager.create_new_run(f"scene_{scene_name.replace(' ', '_')}")
    
    scene_generator = SceneAwareGenerator()
    
    # Check ComfyUI availability
    if not scene_generator.check_comfyui_status():
        print("❌ ComfyUI not accessible. Please ensure ComfyUI is running at http://127.0.0.1:8188")
        return False
    
    # Create scene in scene manager
    scene_manager = SceneManager(str(run_dir.parent))
    scene_id = scene_manager.create_scene(scene_name, characters, settings, len(prompts))

    # Set the scene manager in the generator
    scene_generator.scene_manager = scene_manager

    # Generate scene panels
    scene_output_dir = run_dir / "scene" / "panels"
    generated_paths = []
    
    for i, prompt in enumerate(prompts):
        print(f"\n🎨 Generating Panel {i+1}/{len(prompts)}")
        
        # Get panel metadata
        char_focus = character_focus[i] if character_focus and i < len(character_focus) else None
        emotion = emotions[i] if emotions and i < len(emotions) else "neutral"
        
        # Reference previous panel (except for first panel)
        reference_panel_index = i - 1 if i > 0 else None
        
        # Add panel to scene
        panel_ref = scene_manager.add_panel_to_scene(
            panel_index=i,
            prompt=prompt,
            character_focus=char_focus,
            emotion=emotion,
            reference_panel_index=reference_panel_index
        )
        
        # Generate output path
        panel_path = output_manager.get_scene_panel_path(i, scene_name)
        
        # Generate panel
        success = scene_generator.generate_scene_panel(panel_ref, str(panel_path))
        
        if success:
            generated_paths.append(str(panel_path))
            print(f"   ✅ Generated: {panel_path.name}")
        else:
            print(f"   ❌ Failed to generate panel {i+1}")
    
    # Save scene metadata
    scene_info_path = scene_manager.save_scene_metadata(run_dir)

    # Run comprehensive scene validation
    print(f"\n🔍 Running Scene Validation")
    scene_validator = SceneValidator()
    validation_results = scene_validator.validate_scene_coherence(
        generated_paths, scene_manager.scene_metadata, color_mode or "color"
    )

    # Save comprehensive validation results
    output_manager.save_validation_results(validation_results, "scene_validation")
    report_path = output_manager.save_scene_validation_report(validation_results)
    
    # Print summary
    print(f"\n🎉 Scene Generation Complete!")
    print(f"📊 Generated: {len(generated_paths)}/{len(prompts)} panels")
    print(f"📁 Output directory: {run_dir}")
    print(f"📄 Scene metadata: {scene_info_path}")
    print(f"📋 Validation report: {report_path}")

    # Print validation summary
    coherence_score = validation_results.get('overall_coherence_score', 0.0)
    assessment = validation_results.get('overall_assessment', 'Unknown')
    print(f"🔍 Scene Coherence: {coherence_score:.3f} - {assessment}")

    component_scores = validation_results.get('component_scores', {})
    if component_scores:
        print(f"   Character Consistency: {component_scores.get('character_consistency', 0.0):.3f}")
        print(f"   Location Continuity: {component_scores.get('location_continuity', 0.0):.3f}")
        print(f"   Visual Flow: {component_scores.get('visual_flow', 0.0):.3f}")
        print(f"   Lighting Consistency: {component_scores.get('lighting_consistency', 0.0):.3f}")

    if generated_paths:
        print(f"\n🖼️  Generated Panels:")
        for path in generated_paths:
            print(f"   - {Path(path).name}")

    # Success criteria: at least 70% of panels generated and coherence > 0.6
    success = len(generated_paths) >= len(prompts) * 0.7 and coherence_score > 0.6

    if success:
        print(f"\n✅ Scene generation successful with good coherence!")
    else:
        print(f"\n⚠️ Scene generation completed but may need improvement")
        if coherence_score <= 0.6:
            print(f"   - Coherence score below threshold (0.6): {coherence_score:.3f}")
        if len(generated_paths) < len(prompts):
            print(f"   - Some panels failed to generate: {len(generated_paths)}/{len(prompts)}")

    return success


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(
        description="Generate multi-panel manga scenes with visual coherence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from prompt list
  python scripts/generate_scene.py --prompts "ninja approaches temple" "ninja examines symbols" "ninja finds chamber" --scene-name "Temple Discovery"
  
  # Generate from file
  python scripts/generate_scene.py --prompt-file assets/prompts/scene_prompts.txt --scene-name "Adventure Scene"
  
  # With character details
  python scripts/generate_scene.py --prompts "hero walks forward" "hero looks around" --character-name "hero" --character-appearance "young warrior with sword"
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--prompts', nargs='+', help='List of prompts for each panel')
    input_group.add_argument('--prompt-file', help='File containing prompts (one per line)')
    
    # Scene configuration
    parser.add_argument('--scene-name', required=True, help='Name for the scene')
    parser.add_argument('--output-dir', help='Output directory (auto-generated if not specified)')
    
    # Character configuration
    parser.add_argument('--character-name', help='Main character name')
    parser.add_argument('--character-appearance', help='Character physical description')
    parser.add_argument('--character-clothing', help='Character clothing description')
    parser.add_argument('--character-age', choices=['child', 'teen', 'adult', 'elderly'], help='Character age group')
    parser.add_argument('--character-hair', help='Character hair description')
    parser.add_argument('--character-features', help='Character distinctive features')
    
    # Scene settings
    parser.add_argument('--location', help='Scene location (e.g., temple, forest, city)')
    parser.add_argument('--time-of-day', choices=['morning', 'noon', 'evening', 'night'], help='Time of day')
    parser.add_argument('--weather', choices=['sunny', 'cloudy', 'rainy', 'stormy'], help='Weather conditions')
    parser.add_argument('--lighting', help='Lighting description (e.g., dramatic, soft, bright)')
    parser.add_argument('--mood', help='Scene mood (e.g., mysterious, peaceful, tense)')
    parser.add_argument('--background-elements', help='Comma-separated background elements')
    
    # Panel metadata
    parser.add_argument('--character-focus', nargs='+', help='Character focus for each panel')
    parser.add_argument('--emotions', nargs='+', help='Emotions for each panel')

    # Color mode options
    parser.add_argument('--color-mode', choices=['color', 'black_and_white'],
                       help='Color mode for manga generation (color or black_and_white)')

    args = parser.parse_args()
    
    # Get prompts
    if args.prompts:
        prompts = args.prompts
    else:
        prompts = parse_prompts_file(args.prompt_file)
    
    if not prompts:
        print("❌ No prompts provided")
        return 1
    
    if len(prompts) < 2 or len(prompts) > 5:
        print("❌ Scene must have 2-5 panels")
        return 1
    
    # Create scene metadata
    characters, settings = create_scene_from_args(args)
    
    # Generate scene
    success = generate_scene_sequence(
        scene_name=args.scene_name,
        prompts=prompts,
        output_dir=args.output_dir or "outputs/scenes",
        characters=characters,
        settings=settings,
        character_focus=args.character_focus,
        emotions=args.emotions,
        color_mode=args.color_mode
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
