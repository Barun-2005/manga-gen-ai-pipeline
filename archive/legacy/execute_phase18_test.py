#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🚀 EXECUTING PHASE 18 COMPREHENSIVE TEST")
print("=" * 60)

# Test 1: File Structure
print("📁 Testing file structure...")

required_files = [
    "config/settings.yaml",
    "core/config_manager.py",
    "core/panel_generator.py",
    "image_gen/comfy_client.py",
    "scripts/generate_panel.py",
    "scripts/sanity_test.py",
    "scripts/setup_models.py",
    "README_PHASE18.md"
]

file_results = []
for file_path in required_files:
    path = Path(file_path)
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"   {status} {file_path}")
    file_results.append(exists)

files_pass = all(file_results)
print(f"   Result: {sum(file_results)}/{len(file_results)} files found")

# Test 2: YAML Configuration
print("\n⚙️  Testing YAML configuration...")

yaml_pass = False
try:
    import yaml
    config_file = Path("config/settings.yaml")
    
    if config_file.exists():
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        
        print(f"   ✓ YAML loaded ({len(settings)} sections)")
        
        # Check required sections
        required_sections = ['comfyui', 'models', 'generation']
        section_results = []
        for section in required_sections:
            if section in settings:
                print(f"   ✓ Section '{section}' found")
                section_results.append(True)
            else:
                print(f"   ✗ Section '{section}' missing")
                section_results.append(False)
        
        yaml_pass = all(section_results)
    else:
        print("   ✗ Config file not found")
        
except Exception as e:
    print(f"   ✗ YAML configuration failed: {e}")

# Test 3: Configuration Manager
print("\n🔧 Testing configuration manager...")

config_pass = False
try:
    from core.config_manager import get_config
    print("   ✓ Config manager imported")
    
    config = get_config()
    print("   ✓ Config instance created")
    
    # Test basic access
    url = config.get("comfyui.server.url", "default")
    print(f"   ✓ Basic access: {url}")
    
    # Test specific methods
    try:
        comfyui_url = config.get_comfyui_url()
        print(f"   ✓ ComfyUI URL: {comfyui_url}")
    except Exception as e:
        print(f"   ⚠️  ComfyUI URL warning: {e}")
    
    try:
        gen_settings = config.get_generation_settings()
        print(f"   ✓ Generation settings: {len(gen_settings)} keys")
    except Exception as e:
        print(f"   ⚠️  Generation settings warning: {e}")
    
    config_pass = True
    
except Exception as e:
    print(f"   ✗ Config manager failed: {e}")

# Test 4: Core Modules
print("\n🧩 Testing core modules...")

module_results = []

# Test panel generator
try:
    from core.panel_generator import EnhancedPanelGenerator
    generator = EnhancedPanelGenerator()
    print("   ✓ EnhancedPanelGenerator")
    module_results.append(True)
except Exception as e:
    print(f"   ✗ EnhancedPanelGenerator: {e}")
    module_results.append(False)

# Test ComfyUI client
try:
    from image_gen.comfy_client import ComfyUIClient
    client = ComfyUIClient()
    print("   ✓ ComfyUIClient")
    module_results.append(True)
except Exception as e:
    print(f"   ✗ ComfyUIClient: {e}")
    module_results.append(False)

# Test workflow creation
try:
    from image_gen.comfy_client import create_basic_txt2img_workflow
    workflow = create_basic_txt2img_workflow("test prompt")
    print("   ✓ Workflow creation")
    module_results.append(True)
except Exception as e:
    print(f"   ✗ Workflow creation: {e}")
    module_results.append(False)

modules_pass = all(module_results)
print(f"   Result: {sum(module_results)}/{len(module_results)} modules working")

# Test 5: Model Directories
print("\n📂 Testing model directories...")

models_dir = Path("models")
required_subdirs = [
    "checkpoints", "controlnet", "loras", 
    "t2i_adapter", "ipadapter", "vae", "embeddings"
]

dir_results = []
if models_dir.exists():
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        exists = subdir_path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {subdir}")
        dir_results.append(exists)
else:
    print(f"   ✗ Models directory not found: {models_dir}")
    dir_results = [False] * len(required_subdirs)

dirs_pass = all(dir_results)
print(f"   Result: {sum(dir_results)}/{len(dir_results)} directories found")

# Test 6: Workflow Files
print("\n📋 Testing workflow files...")

workflow_dir = Path("assets/workflows")
workflow_files = [
    "manga_graph.json",
    "improved_manga_workflow.json",
    "controlnet_workflow.json",
    "adapter_workflow.json"
]

workflow_results = []
for workflow_file in workflow_files:
    workflow_path = workflow_dir / workflow_file
    if workflow_path.exists():
        print(f"   ✓ {workflow_file}")
        
        # Validate JSON
        try:
            import json
            with open(workflow_path, 'r') as f:
                json.load(f)
            workflow_results.append(True)
        except Exception as e:
            print(f"     ✗ Invalid JSON: {e}")
            workflow_results.append(False)
    else:
        print(f"   ✗ {workflow_file} - MISSING")
        workflow_results.append(False)

workflows_pass = all(workflow_results)
print(f"   Result: {sum(workflow_results)}/{len(workflow_results)} workflows valid")

# Summary
print("\n" + "=" * 60)
print("📊 PHASE 18 TEST SUMMARY")
print("=" * 60)

tests = [
    ("File Structure", files_pass),
    ("YAML Configuration", yaml_pass),
    ("Configuration Manager", config_pass),
    ("Core Modules", modules_pass),
    ("Model Directories", dirs_pass),
    ("Workflow Files", workflows_pass)
]

passed = 0
total = len(tests)

for test_name, result in tests:
    status = "✅ PASS" if result else "❌ FAIL"
    print(f"{status} {test_name}")
    if result:
        passed += 1

print(f"\nOverall Score: {passed}/{total} tests passed")

if passed == total:
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Phase 18 migration is complete and ready")
    print("\nNext steps:")
    print("1. Download models: python scripts/setup_models.py")
    print("2. Start ComfyUI server")
    print("3. Test generation: python scripts/generate_panel.py --test")
    success = True
else:
    print(f"\n⚠️  {total - passed} TESTS FAILED")
    print("❌ Phase 18 migration needs attention")
    print("Review the failed tests above and resolve issues")
    success = False

print("\n" + "=" * 60)
print(f"Test execution completed. Success: {success}")
print("=" * 60)