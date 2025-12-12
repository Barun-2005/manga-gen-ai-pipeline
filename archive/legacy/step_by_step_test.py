#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔬 STEP-BY-STEP PHASE 18 TEST")
print("=" * 50)

# Step 1: Test basic dependencies
print("\nStep 1: Testing basic dependencies...")
try:
    import yaml
    print("   ✓ PyYAML imported")
except ImportError:
    print("   ✗ PyYAML not available")

try:
    from dotenv import load_dotenv
    print("   ✓ python-dotenv imported")
except ImportError:
    print("   ✗ python-dotenv not available")

# Step 2: Test YAML file
print("\nStep 2: Testing YAML configuration file...")
config_file = Path("config/settings.yaml")
if config_file.exists():
    print(f"   ✓ Config file exists: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            settings = yaml.safe_load(f)
        print(f"   ✓ YAML parsed successfully ({len(settings)} sections)")
        
        # Check required sections
        required_sections = ['comfyui', 'models', 'generation']
        for section in required_sections:
            if section in settings:
                print(f"   ✓ Section '{section}' found")
            else:
                print(f"   ✗ Section '{section}' missing")
                
    except Exception as e:
        print(f"   ✗ YAML parsing failed: {e}")
else:
    print(f"   ✗ Config file not found: {config_file}")

# Step 3: Test config manager file
print("\nStep 3: Testing config manager file...")
config_manager_file = Path("core/config_manager.py")
if config_manager_file.exists():
    print(f"   ✓ Config manager file exists: {config_manager_file}")
    
    # Try to import
    try:
        from core.config_manager import ConfigManager
        print("   ✓ ConfigManager class imported")
        
        # Try to create instance
        config_manager = ConfigManager()
        print("   ✓ ConfigManager instance created")
        
        # Test basic method
        test_val = config_manager.get("comfyui.server.url", "default")
        print(f"   ✓ Basic get() method works: {test_val}")
        
    except Exception as e:
        print(f"   ✗ ConfigManager error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Config manager file not found: {config_manager_file}")

# Step 4: Test get_config function
print("\nStep 4: Testing get_config function...")
try:
    from core.config_manager import get_config
    print("   ✓ get_config function imported")
    
    config = get_config()
    print("   ✓ get_config() executed successfully")
    
    # Test specific methods
    try:
        url = config.get_comfyui_url()
        print(f"   ✓ get_comfyui_url(): {url}")
    except Exception as e:
        print(f"   ⚠️  get_comfyui_url() warning: {e}")
    
except Exception as e:
    print(f"   ✗ get_config function error: {e}")

# Step 5: Test panel generator
print("\nStep 5: Testing panel generator...")
panel_gen_file = Path("core/panel_generator.py")
if panel_gen_file.exists():
    print(f"   ✓ Panel generator file exists: {panel_gen_file}")
    
    try:
        from core.panel_generator import EnhancedPanelGenerator
        print("   ✓ EnhancedPanelGenerator imported")
        
        generator = EnhancedPanelGenerator()
        print("   ✓ EnhancedPanelGenerator instance created")
        
    except Exception as e:
        print(f"   ✗ EnhancedPanelGenerator error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ Panel generator file not found: {panel_gen_file}")

# Step 6: Test ComfyUI client
print("\nStep 6: Testing ComfyUI client...")
comfy_client_file = Path("image_gen/comfy_client.py")
if comfy_client_file.exists():
    print(f"   ✓ ComfyUI client file exists: {comfy_client_file}")
    
    try:
        from image_gen.comfy_client import ComfyUIClient
        print("   ✓ ComfyUIClient imported")
        
        client = ComfyUIClient()
        print("   ✓ ComfyUIClient instance created")
        
    except Exception as e:
        print(f"   ✗ ComfyUIClient error: {e}")
        import traceback
        traceback.print_exc()
else:
    print(f"   ✗ ComfyUI client file not found: {comfy_client_file}")

# Step 7: Test model directories
print("\nStep 7: Testing model directory structure...")
models_dir = Path("models")
required_subdirs = ["checkpoints", "controlnet", "loras", "t2i_adapter", "ipadapter", "vae", "embeddings"]

if models_dir.exists():
    print(f"   ✓ Models directory exists: {models_dir}")
    
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            print(f"   ✓ {subdir_path}")
        else:
            print(f"   ✗ {subdir_path} missing")
else:
    print(f"   ✗ Models directory not found: {models_dir}")

# Step 8: Test scripts
print("\nStep 8: Testing script files...")
script_files = [
    "scripts/generate_panel.py",
    "scripts/sanity_test.py", 
    "scripts/setup_models.py"
]

for script_file in script_files:
    script_path = Path(script_file)
    if script_path.exists():
        print(f"   ✓ {script_file}")
    else:
        print(f"   ✗ {script_file} missing")

print("\n" + "=" * 50)
print("🎯 STEP-BY-STEP TEST COMPLETE")
print("=" * 50)
print("\nIf all steps show ✓, Phase 18 is ready!")
print("If any steps show ✗, those components need attention.")