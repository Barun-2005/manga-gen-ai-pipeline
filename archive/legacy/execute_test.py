#!/usr/bin/env python3
"""Execute the direct test inline."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Execute the test functions directly
def run_tests():
    """Run the tests inline."""
    
    print("🚀 Phase 18 Direct Testing Suite")
    print("=" * 50)
    
    # Test 1: File Structure
    print("=== Testing File Structure ===")
    
    required_files = [
        "config/settings.yaml",
        "core/config_manager.py", 
        "core/panel_generator.py",
        "image_gen/comfy_client.py",
        "scripts/generate_panel.py",
        "scripts/sanity_test.py",
        "scripts/setup_models.py"
    ]
    
    file_results = []
    for file_path in required_files:
        path = Path(file_path)
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"{status} {file_path}")
        file_results.append(exists)
    
    files_pass = all(file_results)
    
    # Test 2: Model Directories
    print("\n=== Testing Model Directory Structure ===")
    
    models_dir = Path("models")
    required_subdirs = [
        "checkpoints", "controlnet", "loras", 
        "t2i_adapter", "ipadapter", "vae", "embeddings"
    ]
    
    if not models_dir.exists():
        print(f"✗ Models directory doesn't exist: {models_dir}")
        models_pass = False
    else:
        model_results = []
        for subdir in required_subdirs:
            subdir_path = models_dir / subdir
            exists = subdir_path.exists()
            status = "✓" if exists else "✗"
            print(f"{status} {subdir_path}")
            model_results.append(exists)
        models_pass = all(model_results)
    
    # Test 3: Module Imports
    print("\n=== Testing Module Imports ===")
    
    import_results = []
    
    # Test config manager
    try:
        from core.config_manager import get_config
        print("✓ core.config_manager.get_config")
        import_results.append(True)
    except Exception as e:
        print(f"✗ core.config_manager.get_config - ERROR: {e}")
        import_results.append(False)
    
    # Test panel generator
    try:
        from core.panel_generator import EnhancedPanelGenerator
        print("✓ core.panel_generator.EnhancedPanelGenerator")
        import_results.append(True)
    except Exception as e:
        print(f"✗ core.panel_generator.EnhancedPanelGenerator - ERROR: {e}")
        import_results.append(False)
    
    # Test comfy client
    try:
        from image_gen.comfy_client import ComfyUIClient
        print("✓ image_gen.comfy_client.ComfyUIClient")
        import_results.append(True)
    except Exception as e:
        print(f"✗ image_gen.comfy_client.ComfyUIClient - ERROR: {e}")
        import_results.append(False)
    
    imports_pass = all(import_results)
    
    # Test 4: Configuration System
    print("\n=== Testing Configuration System ===")
    
    config_pass = False
    try:
        from core.config_manager import get_config
        
        # Test configuration loading
        config = get_config()
        print("✓ Configuration manager loaded successfully")
        
        # Test basic access
        test_value = config.get("comfyui.server.url", "default")
        print(f"✓ Basic config access works: {test_value}")
        
        # Test specific methods
        try:
            comfyui_url = config.get_comfyui_url()
            print(f"✓ ComfyUI URL method: {comfyui_url}")
        except Exception as e:
            print(f"⚠️  ComfyUI URL method error: {e}")
        
        try:
            comfyui_path = config.get_comfyui_installation_path()
            print(f"✓ ComfyUI Path method: {comfyui_path}")
        except Exception as e:
            print(f"⚠️  ComfyUI path method error: {e}")
        
        config_pass = True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    tests = [
        ("File Structure", files_pass),
        ("Model Directories", models_pass), 
        ("Module Imports", imports_pass),
        ("Configuration System", config_pass)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, result in tests:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Phase 18 is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

# Run the tests
if __name__ == "__main__":
    success = run_tests()
    print(f"\nTest execution completed. Success: {success}")