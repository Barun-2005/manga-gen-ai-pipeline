#!/usr/bin/env python3

import yaml
from pathlib import Path

print("Testing YAML loading...")

config_file = Path("config/settings.yaml")
if config_file.exists():
    print(f"✓ Config file exists: {config_file}")
    
    try:
        with open(config_file, 'r') as f:
            settings = yaml.safe_load(f)
        
        print(f"✓ YAML loaded successfully")
        print(f"✓ Top-level keys: {list(settings.keys())}")
        
        # Check ComfyUI section
        if 'comfyui' in settings:
            comfyui = settings['comfyui']
            print(f"✓ ComfyUI section: {list(comfyui.keys())}")
            
            if 'server' in comfyui:
                server = comfyui['server']
                print(f"✓ Server config: {server}")
        
        # Check models section
        if 'models' in settings:
            models = settings['models']
            print(f"✓ Models section: {list(models.keys())}")
        
        print("\n🎉 YAML configuration is valid!")
        
    except Exception as e:
        print(f"✗ YAML loading failed: {e}")
        import traceback
        traceback.print_exc()
        
else:
    print(f"✗ Config file not found: {config_file}")