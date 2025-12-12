#!/usr/bin/env python3

"""
Phase 18 Comprehensive Test Runner
Executes all validation tests for the Phase 18 migration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_file_structure():
    """Test that all required files exist."""
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
    
    missing_files = []
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"   ✓ {file_path}")
        else:
            print(f"   ✗ {file_path} - MISSING")
            missing_files.append(file_path)
    
    return len(missing_files) == 0

def test_yaml_configuration():
    """Test YAML configuration loading."""
    print("\n⚙️  Testing YAML configuration...")
    
    try:
        import yaml
        config_file = Path("config/settings.yaml")
        
        if not config_file.exists():
            print("   ✗ Config file not found")
            return False
        
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        
        print(f"   ✓ YAML loaded ({len(settings)} sections)")
        
        # Check required sections
        required_sections = ['comfyui', 'models', 'generation']
        for section in required_sections:
            if section in settings:
                print(f"   ✓ Section '{section}' found")
            else:
                print(f"   ✗ Section '{section}' missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"   ✗ YAML configuration failed: {e}")
        return False

def test_config_manager():
    """Test configuration manager functionality."""
    print("\n🔧 Testing configuration manager...")
    
    try:
        from core.config_manager import get_config
        print("   ✓ Config manager imported")
        
        config = get_config()
        print("   ✓ Config instance created")
        
        # Test basic access
        url = config.get("comfyui.server.url", "default")
        print(f"   ✓ Basic access: {url}")
        
        # Test specific methods
        comfyui_url = config.get_comfyui_url()
        print(f"   ✓ ComfyUI URL: {comfyui_url}")
        
        gen_settings = config.get_generation_settings()
        print(f"   ✓ Generation settings: {len(gen_settings)} keys")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Config manager failed: {e}")
        return False

def test_core_modules():
    """Test core module imports and instantiation."""
    print("\n🧩 Testing core modules...")
    
    success_count = 0
    total_tests = 3
    
    # Test panel generator
    try:
        from core.panel_generator import EnhancedPanelGenerator
        generator = EnhancedPanelGenerator()
        print("   ✓ EnhancedPanelGenerator")
        success_count += 1
    except Exception as e:
        print(f"   ✗ EnhancedPanelGenerator: {e}")
    
    # Test ComfyUI client
    try:
        from image_gen.comfy_client import ComfyUIClient
        client = ComfyUIClient()
        print("   ✓ ComfyUIClient")
        success_count += 1
    except Exception as e:
        print(f"   ✗ ComfyUIClient: {e}")
    
    # Test workflow creation
    try:
        from image_gen.comfy_client import create_basic_txt2img_workflow
        workflow = create_basic_txt2img_workflow("test prompt")
        print("   ✓ Workflow creation")
        success_count += 1
    except Exception as e:
        print(f"   ✗ Workflow creation: {e}")
    
    print(f"   Result: {success_count}/{total_tests} modules working")
    return success_count == total_tests

def test_model_directories():
    """Test model directory structure."""
    print("\n📂 Testing model directories...")
    
    models_dir = Path("models")
    required_subdirs = [
        "checkpoints", "controlnet", "loras", 
        "t2i_adapter", "ipadapter", "vae", "embeddings"
    ]
    
    if not models_dir.exists():
        print(f"   ✗ Models directory not found: {models_dir}")
        return False
    
    missing_dirs = []
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            print(f"   ✓ {subdir}")
        else:
            print(f"   ✗ {subdir} - MISSING")
            missing_dirs.append(subdir)
    
    return len(missing_dirs) == 0

def test_workflow_files():
    """Test workflow file existence and validity."""
    print("\n📋 Testing workflow files...")
    
    workflow_dir = Path("assets/workflows")
    workflow_files = [
        "manga_graph.json",
        "improved_manga_workflow.json",
        "controlnet_workflow.json",
        "adapter_workflow.json"
    ]
    
    missing_files = []
    for workflow_file in workflow_files:
        workflow_path = workflow_dir / workflow_file
        if workflow_path.exists():
            print(f"   ✓ {workflow_file}")
            
            # Validate JSON
            try:
                import json
                with open(workflow_path, 'r') as f:
                    json.load(f)
                print(f"     ✓ Valid JSON")
            except Exception as e:
                print(f"     ✗ Invalid JSON: {e}")
                missing_files.append(workflow_file)
        else:
            print(f"   ✗ {workflow_file} - MISSING")
            missing_files.append(workflow_file)
    
    return len(missing_files) == 0

def main():
    """Run all Phase 18 tests."""
    print("🚀 PHASE 18 COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("File Structure", test_file_structure),
        ("YAML Configuration", test_yaml_configuration),
        ("Configuration Manager", test_config_manager),
        ("Core Modules", test_core_modules),
        ("Model Directories", test_model_directories),
        ("Workflow Files", test_workflow_files)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
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
        return True
    else:
        print(f"\n⚠️  {total - passed} TESTS FAILED")
        print("❌ Phase 18 migration needs attention")
        print("Review the failed tests above and resolve issues")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)