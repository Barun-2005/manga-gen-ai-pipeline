#!/usr/bin/env python3
"""
Organized Panel Generation Script

Generates manga panels using the output manager for clean, organized results.
Handles both base and enhanced prompts with proper naming and versioning.
"""

import sys
import argparse
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.output_manager import OutputManager
from scripts.generate_panel import ComfyUIGenerator

def generate_organized_panels(base_prompts_file: str, enhanced_prompts_file: str, 
                            run_name: str = None) -> bool:
    """Generate both base and enhanced panels with organized output."""
    
    print("🎨 Organized Panel Generation")
    print("=" * 50)
    
    # Initialize output manager
    output_manager = OutputManager()
    run_dir = output_manager.create_new_run(run_name)
    
    print(f"📁 Run directory: {run_dir}")
    
    # Initialize generator
    generator = ComfyUIGenerator()
    
    # Check ComfyUI availability
    if not generator.check_comfyui_status():
        print("❌ ComfyUI not accessible. Please ensure ComfyUI is running.")
        return False
    
    success = True
    
    # Generate base panels
    if Path(base_prompts_file).exists():
        print(f"\n🎯 Generating Base Panels from: {base_prompts_file}")
        success &= _generate_panel_set(generator, output_manager, base_prompts_file, "base")
    else:
        print(f"⚠️  Base prompts file not found: {base_prompts_file}")
    
    # Generate enhanced panels
    if Path(enhanced_prompts_file).exists():
        print(f"\n✨ Generating Enhanced Panels from: {enhanced_prompts_file}")
        success &= _generate_panel_set(generator, output_manager, enhanced_prompts_file, "enhanced")
    else:
        print(f"⚠️  Enhanced prompts file not found: {enhanced_prompts_file}")
    
    # Print summary
    summary = output_manager.get_run_summary()
    print(f"\n📊 Generation Complete!")
    print(f"   Run: {summary['run_name']}")
    print(f"   Base panels: {summary['panels']['base']}")
    print(f"   Enhanced panels: {summary['panels']['enhanced']}")
    print(f"   Location: {summary['run_directory']}")
    
    return success

def _generate_panel_set(generator: ComfyUIGenerator, output_manager: OutputManager, 
                       prompt_file: str, panel_type: str) -> bool:
    """Generate a set of panels (base or enhanced)."""
    
    # Read prompts
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompts = [line.strip() for line in f.readlines() if line.strip()]
    
    if not prompts:
        print(f"   No prompts found in {prompt_file}")
        return False
    
    print(f"   Processing {len(prompts)} prompts...")
    
    success_count = 0
    for i, prompt in enumerate(prompts):
        # Extract meaningful summary from prompt
        prompt_parts = prompt.split(',')
        if len(prompt_parts) > 1:
            # Look for the main subject after the quality tags
            main_prompt = prompt_parts[-1].strip()  # Last part usually has the main content
            if len(main_prompt) < 10 and len(prompt_parts) > 2:
                main_prompt = prompt_parts[-2].strip()  # Try second to last
        else:
            main_prompt = prompt_parts[0].strip()
        
        # Clean and shorten for filename
        prompt_summary = main_prompt[:40]
        
        # Get organized output path
        output_path = output_manager.get_panel_path(panel_type, i+1, prompt_summary)
        
        print(f"   [{i+1:02d}/{len(prompts):02d}] Generating: {output_path.name}")
        
        if generator.generate_panel(prompt, str(output_path)):
            success_count += 1
        else:
            print(f"      ❌ Failed to generate panel {i+1}")
    
    print(f"   ✅ Generated {success_count}/{len(prompts)} panels")
    return success_count == len(prompts)

def cleanup_old_outputs(keep_recent: int = 3):
    """Clean up old output runs."""
    print(f"🧹 Cleaning up old runs (keeping {keep_recent} most recent)...")
    
    output_manager = OutputManager()
    output_manager.cleanup_old_runs(keep_recent)

def list_recent_runs(limit: int = 10):
    """List recent generation runs."""
    print("📋 Recent Generation Runs:")
    print("-" * 50)
    
    output_manager = OutputManager()
    runs = output_manager.list_recent_runs(limit)
    
    if not runs:
        print("   No runs found")
        return
    
    for i, run in enumerate(runs, 1):
        print(f"{i:2d}. {run['run_name']}")
        print(f"    Created: {run['created_at']}")
        print(f"    Base panels: {run['panels_base']}")
        print(f"    Enhanced panels: {run['panels_enhanced']}")
        print(f"    Path: {run['path']}")
        print()

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Generate organized manga panels")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate panels")
    gen_parser.add_argument("--base-prompts", type=str, default="assets/prompts/base_prompts.txt",
                           help="Base prompts file")
    gen_parser.add_argument("--enhanced-prompts", type=str, default="assets/prompts/enhanced_prompts.txt",
                           help="Enhanced prompts file")
    gen_parser.add_argument("--run-name", type=str, help="Name for this generation run")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List recent runs")
    list_parser.add_argument("--limit", type=int, default=10, help="Number of runs to show")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Clean up old runs")
    cleanup_parser.add_argument("--keep", type=int, default=3, help="Number of recent runs to keep")
    
    args = parser.parse_args()
    
    if args.command == "generate":
        success = generate_organized_panels(
            args.base_prompts, 
            args.enhanced_prompts, 
            args.run_name
        )
        return 0 if success else 1
    
    elif args.command == "list":
        list_recent_runs(args.limit)
        return 0
    
    elif args.command == "cleanup":
        cleanup_old_outputs(args.keep)
        return 0
    
    else:
        # Default: generate with default settings
        print("No command specified, running generation with defaults...")
        success = generate_organized_panels(
            "assets/prompts/base_prompts.txt",
            "assets/prompts/enhanced_prompts.txt"
        )
        return 0 if success else 1

if __name__ == "__main__":
    exit(main())
