import os
import sys
import json
import requests
import time
from pathlib import Path

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'image_gen'))

from image_gen.comfy_client import ComfyUIClient, load_workflow_template

def test_comfyui_connection():
    """Test basic ComfyUI connection."""
    print("🔍 COMFYUI CRASH DEBUG TEST")
    print("=" * 50)
    
    # Test 1: Basic connection
    print("\n📡 Test 1: Basic Connection")
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        print(f"   ✅ ComfyUI responding: {response.status_code}")
        print(f"   📊 System stats available")
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False
    
    # Test 2: Check available models
    print("\n🎨 Test 2: Model Availability")
    try:
        response = requests.get("http://127.0.0.1:8188/object_info", timeout=10)
        if response.status_code == 200:
            object_info = response.json()
            checkpoints = object_info.get("CheckpointLoaderSimple", {}).get("input", {}).get("required", {}).get("ckpt_name", [])
            if isinstance(checkpoints, list) and len(checkpoints) > 0:
                available_models = checkpoints[0] if isinstance(checkpoints[0], list) else []
                print(f"   ✅ Available models: {len(available_models)}")
                for model in available_models[:5]:  # Show first 5
                    print(f"      - {model}")
                
                # Check if our target model exists
                if "anything-v4.5-pruned.safetensors" in available_models:
                    print(f"   ✅ Target model 'anything-v4.5-pruned.safetensors' found")
                else:
                    print(f"   ❌ Target model 'anything-v4.5-pruned.safetensors' NOT found")
                    print(f"   🔧 Available models: {available_models[:3]}...")
            else:
                print(f"   ⚠️  Could not parse model list")
        else:
            print(f"   ❌ Object info request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Model check failed: {e}")
    
    # Test 3: Load and validate workflow
    print("\n📋 Test 3: Workflow Validation")
    try:
        workflow_path = "assets/workflows/bw_manga_workflow.json"
        if os.path.exists(workflow_path):
            workflow = load_workflow_template(workflow_path)
            print(f"   ✅ Workflow loaded: {len(workflow)} nodes")
            
            # Check for required nodes
            required_nodes = ["1", "2", "3", "4", "5", "6", "7"]
            missing_nodes = [node for node in required_nodes if node not in workflow]
            if missing_nodes:
                print(f"   ❌ Missing nodes: {missing_nodes}")
            else:
                print(f"   ✅ All required nodes present")
            
            # Check model reference
            checkpoint_node = workflow.get("4", {})
            model_name = checkpoint_node.get("inputs", {}).get("ckpt_name", "")
            print(f"   📦 Workflow model: {model_name}")
            
        else:
            print(f"   ❌ Workflow file not found: {workflow_path}")
            return False
    except Exception as e:
        print(f"   ❌ Workflow validation failed: {e}")
        return False
    
    # Test 4: Simple prompt test
    print("\n🧪 Test 4: Simple Prompt Test")
    try:
        client = ComfyUIClient()
        
        # Create minimal workflow with short prompt
        simple_prompt = "anime girl"
        
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        
        # Replace placeholder with simple prompt
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", simple_prompt
        )
        
        print(f"   📝 Testing with simple prompt: '{simple_prompt}'")
        print(f"   📤 Sending workflow to ComfyUI...")
        
        # Queue the prompt
        prompt_id = client.queue_prompt(workflow)
        print(f"   ✅ Prompt queued: {prompt_id}")
        
        # Wait a moment to see if ComfyUI crashes
        print(f"   ⏳ Waiting 10 seconds to check for crash...")
        time.sleep(10)
        
        # Check if ComfyUI is still responding
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            print(f"   ✅ ComfyUI still responding after prompt")
        else:
            print(f"   ❌ ComfyUI not responding after prompt")
            return False
        
        # Check prompt status
        try:
            history_response = requests.get(f"http://127.0.0.1:8188/history/{prompt_id}", timeout=5)
            if history_response.status_code == 200:
                history = history_response.json()
                if prompt_id in history:
                    print(f"   ✅ Prompt found in history")
                    status = history[prompt_id].get("status", {})
                    print(f"   📊 Status: {status}")
                else:
                    print(f"   ⚠️  Prompt not in history yet")
            else:
                print(f"   ⚠️  Could not check history: {history_response.status_code}")
        except Exception as e:
            print(f"   ⚠️  History check failed: {e}")
        
    except Exception as e:
        print(f"   ❌ Simple prompt test failed: {e}")
        return False
    
    # Test 5: Complex prompt test (what's causing crashes)
    print("\n🔥 Test 5: Complex Prompt Test (Crash Trigger)")
    try:
        # This is the type of prompt that might be causing crashes
        complex_prompt = "manga panel featuring Protagonist: young anime character with dark hair, bright eyes, casual modern clothing, determined expression, showing happy facial expression with standing body pose, in scene: Scene 1 related to A brave warrior discovers a magical sword and must face three challenges, manga panel showing young anime character with dark hair, bright eyes, casual modern clothing, determined expression with happy expression in standing pose, A brave warrior discovers a magical sword and must face three challenges theme, high quality character art, consistent character design, clear facial features, proper anatomy, detailed background, professional manga illustration, publication quality"
        
        print(f"   📝 Testing with complex prompt ({len(complex_prompt)} chars)")
        print(f"   📤 Sending complex workflow to ComfyUI...")
        
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", complex_prompt
        )
        
        # Queue the prompt
        prompt_id = client.queue_prompt(workflow)
        print(f"   ✅ Complex prompt queued: {prompt_id}")
        
        # Wait to see if this causes a crash
        print(f"   ⏳ Waiting 15 seconds to check for crash...")
        time.sleep(15)
        
        # Check if ComfyUI crashed
        try:
            response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ ComfyUI survived complex prompt!")
            else:
                print(f"   ❌ ComfyUI not responding after complex prompt")
                return False
        except Exception as e:
            print(f"   ❌ ComfyUI crashed after complex prompt: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ Complex prompt test failed: {e}")
        return False
    
    print(f"\n🎯 DEBUG SUMMARY")
    print("=" * 30)
    print(f"✅ All tests passed - ComfyUI integration appears stable")
    print(f"🔧 If crashes still occur, the issue may be:")
    print(f"   - Memory/resource exhaustion during generation")
    print(f"   - Specific prompt content triggering model issues")
    print(f"   - ComfyUI version compatibility problems")
    print(f"   - Custom node conflicts")
    
    return True

def test_actual_generation():
    """Test actual image generation to see where crash occurs."""
    print(f"\n🖼️  ACTUAL GENERATION TEST")
    print("=" * 40)
    
    try:
        from pipeline_v2.generate_panel import generate_panel
        
        output_path = "contest_package/output/debug_test.png"
        
        print(f"   🎨 Attempting actual panel generation...")
        print(f"   📁 Output: {output_path}")
        
        generate_panel(
            output_image=output_path,
            style="bw",
            emotion="happy",
            pose="standing"
        )
        
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"   ✅ Generation successful: {size:,} bytes")
            return True
        else:
            print(f"   ❌ No output file created")
            return False
            
    except Exception as e:
        print(f"   ❌ Generation failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting ComfyUI crash debug analysis...")
    
    connection_ok = test_comfyui_connection()
    
    if connection_ok:
        generation_ok = test_actual_generation()
        
        if generation_ok:
            print(f"\n🎉 SUCCESS: ComfyUI integration working correctly")
        else:
            print(f"\n⚠️  PARTIAL: Connection OK but generation failed")
    else:
        print(f"\n❌ FAILED: Basic ComfyUI connection/workflow issues")
    
    print(f"\n📋 Next steps based on results above...")
