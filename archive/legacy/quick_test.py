#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Quick Phase 18 Test")
print("=" * 30)

# Step 1: Test YAML loading
print("1. Testing YAML loading...")
try:
    import yaml
    config_file = Path("config/settings.yaml")
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            settings = yaml.safe_load(f)
        print(f"   ✓ YAML loaded: {len(settings)} top-level keys")
        
        # Check key sections
        if 'comfyui' in settings:
            print("   ✓ ComfyUI section found")
        if 'models' in settings:
            print("   ✓ Models section found")
        if 'generation' in settings:
            print("   ✓ Generation section found")
            
    else:
        print("   ✗ Config file not found")
        
except Exception as e:
    print(f"   ✗ YAML loading failed: {e}")

# Step 2: Test config manager
print("\n2. Testing config manager...")
try:
    from core.config_manager import ConfigManager, get_config
    print("   ✓ Config manager imported")
    
    # Create instance
    config = get_config()
    print("   ✓ Config instance created")
    
    # Test basic access
    url = config.get("comfyui.server.url", "default")
    print(f"   ✓ Basic access works: {url}")
    
    # Test method access
    try:
        comfyui_url = config.get_comfyui_url()
        print(f"   ✓ Method access works: {comfyui_url}")
    except Exception as e:
        print(f"   ⚠️  Method access warning: {e}")
    
except Exception as e:
    print(f"   ✗ Config manager failed: {e}")

# Step 3: Test panel generator
print("\n3. Testing panel generator...")
try:
    from core.panel_generator import EnhancedPanelGenerator
    print("   ✓ Panel generator imported")
    
    generator = EnhancedPanelGenerator()
    print("   ✓ Panel generator created")
    
except Exception as e:
    print(f"   ✗ Panel generator failed: {e}")

# Step 4: Test ComfyUI client
print("\n4. Testing ComfyUI client...")
try:
    from image_gen.comfy_client import ComfyUIClient
    print("   ✓ ComfyUI client imported")
    
    client = ComfyUIClient()
    print("   ✓ ComfyUI client created")
    
except Exception as e:
    print(f"   ✗ ComfyUI client failed: {e}")

# Step 5: Test model directories
print("\n5. Testing model directories...")
models_dir = Path("models")
if models_dir.exists():
    subdirs = [d.name for d in models_dir.iterdir() if d.is_dir()]
    print(f"   ✓ Models directory exists with {len(subdirs)} subdirs")
    for subdir in sorted(subdirs):
        print(f"     - {subdir}")
else:
    print("   ✗ Models directory not found")

print("\n✅ Quick test completed!")