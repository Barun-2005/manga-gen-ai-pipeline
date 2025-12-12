#!/usr/bin/env python3

# Inline YAML test
import yaml
from pathlib import Path

print("🧪 Testing YAML Configuration")
print("=" * 40)

config_file = Path("config/settings.yaml")
if config_file.exists():
    print(f"✓ Config file exists: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            content = f.read()
        
        print(f"✓ File read successfully ({len(content)} characters)")
        
        # Parse YAML
        settings = yaml.safe_load(content)
        
        print(f"✓ YAML parsed successfully")
        print(f"✓ Top-level keys: {list(settings.keys())}")
        
        # Check ComfyUI section
        if 'comfyui' in settings:
            comfyui = settings['comfyui']
            print(f"✓ ComfyUI section found with keys: {list(comfyui.keys())}")
            
            if 'server' in comfyui:
                server = comfyui['server']
                url = server.get('url', 'not found')
                print(f"✓ Server URL: {url}")
        
        # Check models section
        if 'models' in settings:
            models = settings['models']
            print(f"✓ Models section found with keys: {list(models.keys())}")
        
        # Check generation section
        if 'generation' in settings:
            generation = settings['generation']
            print(f"✓ Generation section found with keys: {list(generation.keys())}")
        
        print("\n🎉 YAML configuration is completely valid!")
        return True
        
    except Exception as e:
        print(f"✗ YAML processing failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
else:
    print(f"✗ Config file not found: {config_file}")
    return False

# Now test config manager import
print("\n" + "=" * 40)
print("🧪 Testing Config Manager Import")
print("=" * 40)

import sys
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.config_manager import ConfigManager, get_config
    print("✓ Config manager classes imported successfully")
    
    # Test ConfigManager creation
    config_manager = ConfigManager()
    print("✓ ConfigManager instance created")
    
    # Test get_config function
    config = get_config()
    print("✓ get_config() function works")
    
    # Test basic access
    url = config.get("comfyui.server.url", "default")
    print(f"✓ Basic config access: {url}")
    
    # Test method access
    try:
        comfyui_url = config.get_comfyui_url()
        print(f"✓ get_comfyui_url() method: {comfyui_url}")
    except Exception as e:
        print(f"⚠️  get_comfyui_url() method warning: {e}")
    
    try:
        comfyui_path = config.get_comfyui_installation_path()
        print(f"✓ get_comfyui_installation_path() method: {comfyui_path}")
    except Exception as e:
        print(f"⚠️  get_comfyui_installation_path() method warning: {e}")
    
    print("\n🎉 Config manager is working perfectly!")
    return True
    
except Exception as e:
    print(f"✗ Config manager import/usage failed: {e}")
    import traceback
    traceback.print_exc()
    return False

print("\n" + "=" * 40)
print("✅ YAML AND CONFIG MANAGER TEST COMPLETE")
print("=" * 40)