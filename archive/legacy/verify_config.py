#!/usr/bin/env python3

# Direct verification of configuration system
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 CONFIGURATION SYSTEM VERIFICATION")
print("=" * 50)

# Test 1: Check YAML file exists and is valid
print("1. Checking YAML configuration file...")
config_file = Path("config/settings.yaml")

if config_file.exists():
    print(f"   ✓ File exists: {config_file}")
    
    # Read and parse YAML
    try:
        import yaml
        with open(config_file, 'r', encoding='utf-8') as f:
            settings = yaml.safe_load(f)
        
        print(f"   ✓ YAML parsed successfully")
        print(f"   ✓ Found {len(settings)} top-level sections")
        
        # Check specific sections
        if 'comfyui' in settings:
            print("   ✓ ComfyUI section present")
            comfyui = settings['comfyui']
            if 'server' in comfyui and 'url' in comfyui['server']:
                url = comfyui['server']['url']
                print(f"   ✓ ComfyUI URL configured: {url}")
        
        if 'models' in settings:
            print("   ✓ Models section present")
        
        if 'generation' in settings:
            print("   ✓ Generation section present")
            
    except Exception as e:
        print(f"   ✗ YAML parsing failed: {e}")
        sys.exit(1)
else:
    print(f"   ✗ Config file not found: {config_file}")
    sys.exit(1)

# Test 2: Import config manager
print("\n2. Testing config manager import...")
try:
    from core.config_manager import ConfigManager, get_config
    print("   ✓ Config manager imported successfully")
except Exception as e:
    print(f"   ✗ Config manager import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Create config instance
print("\n3. Testing config manager instantiation...")
try:
    config = get_config()
    print("   ✓ Config instance created successfully")
except Exception as e:
    print(f"   ✗ Config instantiation failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 4: Test basic config access
print("\n4. Testing basic configuration access...")
try:
    # Test basic get method
    url = config.get("comfyui.server.url", "default")
    print(f"   ✓ Basic get() method: {url}")
    
    # Test nested access
    timeout = config.get("comfyui.server.timeout", 300)
    print(f"   ✓ Nested access: timeout = {timeout}")
    
    # Test non-existent key with default
    missing = config.get("non.existent.key", "default_value")
    print(f"   ✓ Default value handling: {missing}")
    
except Exception as e:
    print(f"   ✗ Basic config access failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 5: Test specific config methods
print("\n5. Testing specific configuration methods...")
try:
    # Test ComfyUI URL method
    comfyui_url = config.get_comfyui_url()
    print(f"   ✓ get_comfyui_url(): {comfyui_url}")
    
    # Test ComfyUI path method
    comfyui_path = config.get_comfyui_installation_path()
    print(f"   ✓ get_comfyui_installation_path(): {comfyui_path}")
    
    # Test generation settings
    gen_settings = config.get_generation_settings()
    print(f"   ✓ get_generation_settings(): {len(gen_settings)} keys")
    
    # Test color mode config
    color_config = config.get_color_mode_config("color")
    print(f"   ✓ get_color_mode_config(): {len(color_config)} keys")
    
except Exception as e:
    print(f"   ✗ Specific config methods failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 50)
print("✅ CONFIGURATION SYSTEM VERIFICATION COMPLETE")
print("=" * 50)
print("🎉 All configuration tests passed!")
print("✅ YAML file is valid")
print("✅ Config manager imports correctly")
print("✅ Config instance creates successfully")
print("✅ Basic config access works")
print("✅ Specific config methods work")
print("\nConfiguration system is ready for Phase 18!")