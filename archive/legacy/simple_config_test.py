#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🧪 Simple Configuration Test")
print("=" * 40)

# Test basic file existence
print("1. Checking required files...")
required_files = [
    "config/settings.yaml",
    "core/config_manager.py"
]

for file_path in required_files:
    path = Path(file_path)
    exists = path.exists()
    status = "✓" if exists else "✗"
    print(f"   {status} {file_path}")

# Test configuration import
print("\n2. Testing configuration import...")
try:
    from core.config_manager import get_config
    print("   ✓ Successfully imported get_config")
    
    # Test configuration loading
    config = get_config()
    print("   ✓ Configuration manager created")
    
    # Test basic access
    test_value = config.get("comfyui.server.url", "http://127.0.0.1:8188")
    print(f"   ✓ Basic config access: {test_value}")
    
    # Test ComfyUI URL method
    try:
        url = config.get_comfyui_url()
        print(f"   ✓ ComfyUI URL method: {url}")
    except Exception as e:
        print(f"   ⚠️  ComfyUI URL method warning: {e}")
    
    print("\n✅ Configuration system is working!")
    
except Exception as e:
    print(f"   ✗ Configuration import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing panel generator import...")
try:
    from core.panel_generator import EnhancedPanelGenerator
    print("   ✓ Successfully imported EnhancedPanelGenerator")
    
    # Try to create instance
    generator = EnhancedPanelGenerator()
    print("   ✓ Panel generator created successfully")
    
except Exception as e:
    print(f"   ✗ Panel generator import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n4. Testing ComfyUI client import...")
try:
    from image_gen.comfy_client import ComfyUIClient
    print("   ✓ Successfully imported ComfyUIClient")
    
    # Try to create instance
    client = ComfyUIClient()
    print("   ✓ ComfyUI client created successfully")
    
except Exception as e:
    print(f"   ✗ ComfyUI client import failed: {e}")
    import traceback
    traceback.print_exc()

print("\n🎯 Test completed!")