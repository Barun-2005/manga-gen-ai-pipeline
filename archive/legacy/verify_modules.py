#!/usr/bin/env python3

# Direct verification of core modules
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 CORE MODULES VERIFICATION")
print("=" * 50)

# Test 1: Panel Generator
print("1. Testing Enhanced Panel Generator...")
try:
    from core.panel_generator import EnhancedPanelGenerator
    print("   ✓ EnhancedPanelGenerator imported")
    
    # Create instance
    generator = EnhancedPanelGenerator()
    print("   ✓ EnhancedPanelGenerator instance created")
    
    # Check if it has expected methods
    if hasattr(generator, 'generate_panel'):
        print("   ✓ generate_panel method exists")
    
    if hasattr(generator, 'config'):
        print("   ✓ config attribute exists")
    
except Exception as e:
    print(f"   ✗ EnhancedPanelGenerator failed: {e}")
    import traceback
    traceback.print_exc()

# Test 2: ComfyUI Client
print("\n2. Testing ComfyUI Client...")
try:
    from image_gen.comfy_client import ComfyUIClient
    print("   ✓ ComfyUIClient imported")
    
    # Create instance
    client = ComfyUIClient()
    print("   ✓ ComfyUIClient instance created")
    
    # Check if it has expected methods
    if hasattr(client, 'generate_images'):
        print("   ✓ generate_images method exists")
    
    if hasattr(client, 'is_server_ready'):
        print("   ✓ is_server_ready method exists")
    
except Exception as e:
    print(f"   ✗ ComfyUIClient failed: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Workflow Creation
print("\n3. Testing workflow creation...")
try:
    from image_gen.comfy_client import create_basic_txt2img_workflow
    print("   ✓ create_basic_txt2img_workflow imported")
    
    # Create a test workflow
    workflow = create_basic_txt2img_workflow(
        prompt="test manga character",
        negative_prompt="bad quality",
        width=512,
        height=768
    )
    print("   ✓ Basic workflow created successfully")
    
    # Check workflow structure
    if isinstance(workflow, dict):
        print(f"   ✓ Workflow is dict with {len(workflow)} nodes")
    
except Exception as e:
    print(f"   ✗ Workflow creation failed: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Check workflow files
print("\n4. Testing workflow files...")
workflow_dir = Path("assets/workflows")
workflow_files = [
    "manga_graph.json",
    "improved_manga_workflow.json",
    "controlnet_workflow.json", 
    "adapter_workflow.json"
]

for workflow_file in workflow_files:
    workflow_path = workflow_dir / workflow_file
    if workflow_path.exists():
        print(f"   ✓ {workflow_file}")
        
        # Try to load and validate JSON
        try:
            import json
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            print(f"     ✓ Valid JSON with {len(workflow_data)} nodes")
        except Exception as e:
            print(f"     ✗ JSON parsing failed: {e}")
    else:
        print(f"   ✗ {workflow_file} - MISSING")

# Test 5: Model directory structure
print("\n5. Testing model directory structure...")
models_dir = Path("models")
required_subdirs = [
    "checkpoints", "controlnet", "loras", 
    "t2i_adapter", "ipadapter", "vae", "embeddings"
]

if models_dir.exists():
    print(f"   ✓ Models directory exists: {models_dir}")
    
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            print(f"   ✓ {subdir}")
        else:
            print(f"   ✗ {subdir} - MISSING")
else:
    print(f"   ✗ Models directory not found: {models_dir}")

print("\n" + "=" * 50)
print("✅ CORE MODULES VERIFICATION COMPLETE")
print("=" * 50)
print("🎉 Core module verification finished!")
print("\nNext steps:")
print("1. Download models: python scripts/setup_models.py")
print("2. Start ComfyUI server")
print("3. Test generation: python scripts/generate_panel.py --test")