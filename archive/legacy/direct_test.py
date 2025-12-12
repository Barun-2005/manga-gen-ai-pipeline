#!/usr/bin/env python3
"""Direct test of Phase 18 components."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test the configuration system."""
    print("=== Testing Configuration System ===")
    
    try:
        from core.config_manager import get_config
        
        # Test configuration loading
        config = get_config()
        print("✓ Configuration manager loaded successfully")
        
        # Test basic access
        test_value = config.get("comfyui.server.url", "default")
        print(f"✓ Basic config access works: {test_value}")
        
        # Test ComfyUI URL method
        try:
            comfyui_url = config.get_comfyui_url()
            print(f"✓ ComfyUI URL: {comfyui_url}")
        except Exception as e:
            print(f"⚠️  ComfyUI URL method error: {e}")
        
        # Test ComfyUI path method
        try:
            comfyui_path = config.get_comfyui_installation_path()
            print(f"✓ ComfyUI Path: {comfyui_path}")
        except Exception as e:
            print(f"⚠️  ComfyUI path method error: {e}")
        
        # Test generation settings
        try:
            gen_settings = config.get_generation_settings()
            print(f"✓ Generation settings loaded: {len(gen_settings)} keys")
        except Exception as e:
            print(f"⚠️  Generation settings error: {e}")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_structure():
    """Test that required files exist."""
    print("\n=== Testing File Structure ===")
    
    required_files = [
        "config/settings.yaml",
        "core/config_manager.py",
        "core/panel_generator.py",
        "image_gen/comfy_client.py",
        "scripts/generate_panel.py",
        "scripts/sanity_test.py",
        "scripts/setup_models.py"
    ]
    
    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path}")
        else:
            print(f"✗ {file_path} - MISSING")
            all_exist = False
    
    return all_exist

def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Module Imports ===")
    
    modules_to_test = [
        ("core.config_manager", "get_config"),
        ("core.panel_generator", "EnhancedPanelGenerator"),
        ("image_gen.comfy_client", "ComfyUIClient"),
    ]
    
    all_imported = True
    for module_name, class_name in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print(f"✓ {module_name}.{class_name}")
        except Exception as e:
            print(f"✗ {module_name}.{class_name} - ERROR: {e}")
            all_imported = False
    
    return all_imported

def test_model_directories():
    """Test model directory structure."""
    print("\n=== Testing Model Directory Structure ===")
    
    models_dir = Path("models")
    required_subdirs = [
        "checkpoints", "controlnet", "loras", 
        "t2i_adapter", "ipadapter", "vae", "embeddings"
    ]
    
    if not models_dir.exists():
        print(f"✗ Models directory doesn't exist: {models_dir}")
        return False
    
    all_exist = True
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            print(f"✓ {subdir_path}")
        else:
            print(f"✗ {subdir_path} - MISSING")
            all_exist = False
    
    return all_exist

def main():
    """Run all tests."""
    print("🚀 Phase 18 Direct Testing Suite")
    print("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Module Imports", test_imports),
        ("Configuration System", test_configuration),
        ("Model Directories", test_model_directories),
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 18 is ready.")
    else:
        print("⚠️  Some tests failed. Check the output above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)