#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 PHASE 18 FINAL VALIDATION TEST")
print("=" * 50)

# Test 1: Check file structure
print("1. Checking file structure...")
required_files = [
    "config/settings.yaml",
    "core/config_manager.py",
    "core/panel_generator.py", 
    "image_gen/comfy_client.py",
    "scripts/generate_panel.py",
    "scripts/sanity_test.py",
    "scripts/setup_models.py"
]

file_count = 0
for file_path in required_files:
    path = Path(file_path)
    if path.exists():
        print(f"   ✓ {file_path}")
        file_count += 1
    else:
        print(f"   ✗ {file_path} - MISSING")

print(f"   Files: {file_count}/{len(required_files)} found")

# Test 2: Check model directories
print("\n2. Checking model directories...")
models_dir = Path("models")
required_subdirs = [
    "checkpoints", "controlnet", "loras", 
    "t2i_adapter", "ipadapter", "vae", "embeddings"
]

dir_count = 0
for subdir in required_subdirs:
    subdir_path = models_dir / subdir
    if subdir_path.exists():
        print(f"   ✓ {subdir_path}")
        dir_count += 1
    else:
        print(f"   ✗ {subdir_path} - MISSING")

print(f"   Directories: {dir_count}/{len(required_subdirs)} found")

# Test 3: Test configuration loading
print("\n3. Testing configuration system...")
config_success = False
try:
    import yaml
    
    # Test YAML loading
    config_file = Path("config/settings.yaml")
    if config_file.exists():
        with open(config_file, 'r') as f:
            settings = yaml.safe_load(f)
        print(f"   ✓ YAML loaded successfully ({len(settings)} sections)")
        
        # Test config manager import
        from core.config_manager import get_config
        print("   ✓ Config manager imported")
        
        # Test config creation
        config = get_config()
        print("   ✓ Config instance created")
        
        # Test basic access
        url = config.get("comfyui.server.url", "http://127.0.0.1:8188")
        print(f"   ✓ Basic config access: {url}")
        
        config_success = True
        
    else:
        print("   ✗ Config file missing")
        
except Exception as e:
    print(f"   ✗ Configuration error: {e}")

# Test 4: Test core module imports
print("\n4. Testing core module imports...")
import_success = 0
import_total = 3

# Test panel generator
try:
    from core.panel_generator import EnhancedPanelGenerator
    generator = EnhancedPanelGenerator()
    print("   ✓ EnhancedPanelGenerator")
    import_success += 1
except Exception as e:
    print(f"   ✗ EnhancedPanelGenerator: {e}")

# Test ComfyUI client
try:
    from image_gen.comfy_client import ComfyUIClient
    client = ComfyUIClient()
    print("   ✓ ComfyUIClient")
    import_success += 1
except Exception as e:
    print(f"   ✗ ComfyUIClient: {e}")

# Test workflow creation
try:
    from image_gen.comfy_client import create_basic_txt2img_workflow
    workflow = create_basic_txt2img_workflow("test prompt")
    print("   ✓ Workflow creation")
    import_success += 1
except Exception as e:
    print(f"   ✗ Workflow creation: {e}")

print(f"   Imports: {import_success}/{import_total} successful")

# Test 5: Test workflow files
print("\n5. Testing workflow files...")
workflow_dir = Path("assets/workflows")
workflow_files = [
    "manga_graph.json",
    "improved_manga_workflow.json", 
    "controlnet_workflow.json",
    "adapter_workflow.json"
]

workflow_count = 0
for workflow_file in workflow_files:
    workflow_path = workflow_dir / workflow_file
    if workflow_path.exists():
        print(f"   ✓ {workflow_file}")
        workflow_count += 1
    else:
        print(f"   ✗ {workflow_file} - MISSING")

print(f"   Workflows: {workflow_count}/{len(workflow_files)} found")

# Summary
print("\n" + "=" * 50)
print("PHASE 18 VALIDATION SUMMARY")
print("=" * 50)

total_score = 0
max_score = 5

# File structure score
if file_count == len(required_files):
    print("✅ File Structure: PASS")
    total_score += 1
else:
    print("❌ File Structure: FAIL")

# Directory structure score  
if dir_count == len(required_subdirs):
    print("✅ Model Directories: PASS")
    total_score += 1
else:
    print("❌ Model Directories: FAIL")

# Configuration score
if config_success:
    print("✅ Configuration System: PASS")
    total_score += 1
else:
    print("❌ Configuration System: FAIL")

# Import score
if import_success == import_total:
    print("✅ Core Module Imports: PASS")
    total_score += 1
else:
    print("❌ Core Module Imports: FAIL")

# Workflow score
if workflow_count == len(workflow_files):
    print("✅ Workflow Files: PASS")
    total_score += 1
else:
    print("❌ Workflow Files: FAIL")

print(f"\nOverall Score: {total_score}/{max_score}")

if total_score == max_score:
    print("\n🎉 PHASE 18 VALIDATION SUCCESSFUL!")
    print("✅ All systems are ready")
    print("\nNext steps:")
    print("1. Download models: python scripts/setup_models.py")
    print("2. Start ComfyUI server")
    print("3. Test generation: python scripts/generate_panel.py --test")
else:
    print(f"\n⚠️  PHASE 18 VALIDATION INCOMPLETE ({total_score}/{max_score})")
    print("❌ Some components need attention")
    print("Check the failed tests above and resolve issues")

print("\n" + "=" * 50)