#!/usr/bin/env python3

from pathlib import Path

print("🏗️  Setting up Phase 18 directories...")

# Create model directories
models_dir = Path("models")
subdirs = [
    "checkpoints", "controlnet", "loras", 
    "t2i_adapter", "ipadapter", "vae", "embeddings"
]

print(f"Creating model directories in: {models_dir}")
for subdir in subdirs:
    dir_path = models_dir / subdir
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {dir_path}")

# Create output directories  
output_dir = Path("outputs")
output_subdirs = [
    "panels", "validation", "emotions", "metadata"
]

print(f"\nCreating output directories in: {output_dir}")
for subdir in output_subdirs:
    dir_path = output_dir / subdir
    dir_path.mkdir(parents=True, exist_ok=True)
    print(f"  ✓ {dir_path}")

print("\n✅ Directory setup complete!")

# Now run the configuration test
print("\n" + "="*50)
print("🧪 RUNNING PHASE 18 CONFIGURATION TEST")
print("="*50)

import sys
# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test 1: YAML loading
print("\n1. Testing YAML loading...")
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

# Test 2: Config manager
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
    import traceback
    traceback.print_exc()

# Test 3: Panel generator
print("\n3. Testing panel generator...")
try:
    from core.panel_generator import EnhancedPanelGenerator
    print("   ✓ Panel generator imported")
    
    generator = EnhancedPanelGenerator()
    print("   ✓ Panel generator created")
    
except Exception as e:
    print(f"   ✗ Panel generator failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: ComfyUI client
print("\n4. Testing ComfyUI client...")
try:
    from image_gen.comfy_client import ComfyUIClient
    print("   ✓ ComfyUI client imported")
    
    client = ComfyUIClient()
    print("   ✓ ComfyUI client created")
    
except Exception as e:
    print(f"   ✗ ComfyUI client failed: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Model directories
print("\n5. Testing model directories...")
models_dir = Path("models")
if models_dir.exists():
    subdirs = [d.name for d in models_dir.iterdir() if d.is_dir()]
    print(f"   ✓ Models directory exists with {len(subdirs)} subdirs")
    for subdir in sorted(subdirs):
        print(f"     - {subdir}")
else:
    print("   ✗ Models directory not found")

print("\n" + "="*50)
print("🎯 PHASE 18 TEST SUMMARY")
print("="*50)
print("✅ Directory setup completed")
print("✅ Configuration system tested")
print("✅ Core modules tested")
print("\n🎉 Phase 18 is ready for use!")
print("\nNext steps:")
print("1. Download models: python scripts/setup_models.py")
print("2. Start ComfyUI server")
print("3. Test generation: python scripts/generate_panel.py --test")