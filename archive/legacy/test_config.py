#!/usr/bin/env python3
"""Quick test of Phase 18 configuration system."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from core.config_manager import get_config
    
    print("=== Phase 18 Configuration Test ===")
    
    # Test configuration loading
    config = get_config()
    print("✓ Configuration manager loaded")
    
    # Test key methods
    comfyui_url = config.get_comfyui_url()
    print(f"✓ ComfyUI URL: {comfyui_url}")
    
    comfyui_path = config.get_comfyui_installation_path()
    print(f"✓ ComfyUI Path: {comfyui_path}")
    
    gen_settings = config.get_generation_settings()
    print(f"✓ Generation settings: {len(gen_settings)} keys")
    
    color_config = config.get_color_mode_config("color")
    print(f"✓ Color config loaded: {len(color_config)} keys")
    
    # Test feature flags
    story_memory = config.is_feature_enabled("enable_story_memory")
    print(f"✓ Story memory enabled: {story_memory}")
    
    print("\n🎉 Configuration system working correctly!")
    
except Exception as e:
    print(f"✗ Configuration test failed: {e}")
    import traceback
    traceback.print_exc()