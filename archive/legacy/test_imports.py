#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("Testing imports step by step...")

# Test 1: Basic Python modules
print("\n1. Testing basic modules...")
try:
    import yaml
    print("   ✓ yaml")
except ImportError as e:
    print(f"   ✗ yaml: {e}")

try:
    from dotenv import load_dotenv
    print("   ✓ dotenv")
except ImportError as e:
    print(f"   ✗ dotenv: {e}")

# Test 2: Check if config file exists and is valid YAML
print("\n2. Testing config file...")
config_file = Path("config/settings.yaml")
if config_file.exists():
    print("   ✓ config/settings.yaml exists")
    try:
        with open(config_file, 'r') as f:
            yaml.safe_load(f)
        print("   ✓ YAML syntax is valid")
    except Exception as e:
        print(f"   ✗ YAML syntax error: {e}")
else:
    print("   ✗ config/settings.yaml missing")

# Test 3: Try importing our config manager
print("\n3. Testing config manager import...")
try:
    from core.config_manager import ConfigManager
    print("   ✓ ConfigManager class imported")
    
    # Try creating instance
    config = ConfigManager()
    print("   ✓ ConfigManager instance created")
    
    # Test basic method
    test_val = config.get("comfyui.server.url", "default")
    print(f"   ✓ Basic get method works: {test_val}")
    
except Exception as e:
    print(f"   ✗ ConfigManager error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Try importing get_config function
print("\n4. Testing get_config function...")
try:
    from core.config_manager import get_config
    print("   ✓ get_config function imported")
    
    config = get_config()
    print("   ✓ get_config() executed successfully")
    
except Exception as e:
    print(f"   ✗ get_config error: {e}")
    import traceback
    traceback.print_exc()

print("\n✅ Import testing completed!")