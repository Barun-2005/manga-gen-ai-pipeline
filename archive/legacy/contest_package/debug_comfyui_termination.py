import os
import sys
import json
import requests
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'image_gen'))

from image_gen.comfy_client import load_workflow_template

def test_prompt_length_limits():
    """Test ComfyUI with progressively longer prompts to find the breaking point."""
    print("🔍 COMFYUI PROMPT LENGTH LIMIT TEST")
    print("=" * 50)
    
    # Check ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        print(f"✅ ComfyUI responding: {response.status_code}")
    except Exception as e:
        print(f"❌ ComfyUI not responding: {e}")
        return False
    
    # Test prompts of increasing length
    test_prompts = [
        ("minimal", "girl"),
        ("short", "anime girl"),
        ("medium", "anime girl with dark hair"),
        ("long", "anime girl with dark hair, bright eyes, happy expression"),
        ("very_long", "anime girl with dark hair, bright eyes, happy expression, standing pose, detailed artwork"),
        ("extreme", "manga panel featuring anime girl with dark hair, bright eyes, casual clothing, happy facial expression, standing body pose, detailed character art, high quality"),
        ("our_length", "manga panel featuring Protagonist: young anime character with dark hair, bright eyes, casual modern clothing, determined expression, showing happy facial expression with standing body pose, in scene: Scene 1 related to adventure story, high quality character art, consistent character design, clear facial features, proper anatomy, detailed background, professional manga illustration, publication quality")
    ]
    
    for prompt_name, prompt_text in test_prompts:
        print(f"\n📝 Testing {prompt_name} prompt ({len(prompt_text)} chars):")
        print(f"   Text: '{prompt_text[:60]}{'...' if len(prompt_text) > 60 else ''}'")
        
        success = test_single_prompt(prompt_text, prompt_name)
        
        if not success:
            print(f"❌ BREAKING POINT FOUND: {prompt_name} prompt ({len(prompt_text)} chars)")
            return prompt_name, len(prompt_text)
        else:
            print(f"✅ {prompt_name} prompt works")
    
    print(f"✅ All prompt lengths work - issue is not prompt length")
    return None, None

def test_single_prompt(prompt_text, prompt_name):
    """Test a single prompt and check if ComfyUI survives."""
    try:
        # Load workflow
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        
        # Replace placeholder
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", prompt_text
        )
        
        # Send to ComfyUI
        import uuid
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }
        
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code != 200:
            print(f"   ❌ Failed to queue: {response.status_code}")
            return False
        
        # Wait and check if ComfyUI survives
        time.sleep(10)
        
        try:
            check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
            return check_response.status_code == 200
        except:
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_workflow_structure():
    """Test if the workflow JSON structure is valid."""
    print(f"\n🔧 WORKFLOW STRUCTURE VALIDATION")
    print("=" * 40)
    
    try:
        # Load and validate BW workflow
        bw_workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        print(f"✅ BW workflow loaded: {len(bw_workflow)} nodes")
        
        # Check required nodes and connections
        required_nodes = ["1", "2", "3", "4", "5", "6", "7"]
        missing_nodes = [node for node in required_nodes if node not in bw_workflow]
        
        if missing_nodes:
            print(f"❌ Missing nodes: {missing_nodes}")
            return False
        
        # Validate node connections
        connection_issues = []
        
        # Node 1 (CLIP Text Encode) should connect to Node 4 (Checkpoint)
        if bw_workflow["1"]["inputs"]["clip"][0] != "4":
            connection_issues.append("Node 1 clip input should connect to Node 4")
        
        # Node 3 (KSampler) should connect to model from Node 4
        if bw_workflow["3"]["inputs"]["model"][0] != "4":
            connection_issues.append("Node 3 model input should connect to Node 4")
        
        # Node 6 (VAE Decode) should connect to VAE from Node 4
        if bw_workflow["6"]["inputs"]["vae"][0] != "4":
            connection_issues.append("Node 6 VAE input should connect to Node 4")
        
        if connection_issues:
            print(f"❌ Connection issues found:")
            for issue in connection_issues:
                print(f"   - {issue}")
            return False
        
        print(f"✅ Workflow structure is valid")
        
        # Check model reference
        model_name = bw_workflow["4"]["inputs"]["ckpt_name"]
        print(f"📦 Model reference: {model_name}")
        
        # Verify model exists
        model_path = f"ComfyUI-master/models/checkpoints/{model_name}"
        if os.path.exists(model_path):
            print(f"✅ Model file exists")
        else:
            print(f"❌ Model file not found: {model_path}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow validation failed: {e}")
        return False

def test_minimal_working_workflow():
    """Create and test a minimal workflow that should definitely work."""
    print(f"\n🧪 MINIMAL WORKING WORKFLOW TEST")
    print("=" * 40)
    
    # Create absolute minimal workflow
    minimal_workflow = {
        "1": {
            "inputs": {
                "text": "simple test image",
                "clip": ["2", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "2": {
            "inputs": {
                "ckpt_name": "anything-v4.5-pruned.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "3": {
            "inputs": {
                "text": "blurry, bad quality",
                "clip": ["2", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "4": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "5": {
            "inputs": {
                "seed": 42,
                "steps": 10,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["2", 0],
                "positive": ["1", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            },
            "class_type": "KSampler"
        },
        "6": {
            "inputs": {
                "samples": ["5", 0],
                "vae": ["2", 2]
            },
            "class_type": "VAEDecode"
        },
        "7": {
            "inputs": {
                "filename_prefix": "minimal_test",
                "images": ["6", 0]
            },
            "class_type": "SaveImage"
        }
    }
    
    try:
        import uuid
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": minimal_workflow,
            "client_id": prompt_id
        }
        
        print(f"📤 Sending minimal workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Minimal workflow queued")
            
            # Wait longer for generation
            print(f"⏳ Waiting 30 seconds for generation...")
            time.sleep(30)
            
            # Check if ComfyUI survived
            try:
                check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
                if check_response.status_code == 200:
                    print(f"✅ ComfyUI survived minimal workflow")
                    
                    # Check if image was generated
                    output_dir = Path("ComfyUI-master/output")
                    recent_files = []
                    if output_dir.exists():
                        for img_file in output_dir.glob("minimal_test_*.png"):
                            if time.time() - img_file.stat().st_mtime < 60:  # Last minute
                                recent_files.append(img_file)
                    
                    if recent_files:
                        latest_file = max(recent_files, key=lambda x: x.stat().st_mtime)
                        size = latest_file.stat().st_size
                        print(f"✅ Image generated: {latest_file.name} ({size:,} bytes)")
                        return True
                    else:
                        print(f"⚠️  No recent image found")
                        return False
                else:
                    print(f"❌ ComfyUI not responding after minimal workflow")
                    return False
            except Exception as e:
                print(f"❌ ComfyUI crashed: {e}")
                return False
        else:
            print(f"❌ Failed to queue minimal workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Minimal workflow test failed: {e}")
        return False

def main():
    """Main debug function."""
    print("🔍 COMFYUI TERMINATION DEBUG")
    print("=" * 60)
    print("Systematically testing to find the exact cause of ComfyUI termination")
    print()
    
    # Test 1: Workflow structure validation
    workflow_valid = test_workflow_structure()
    
    if not workflow_valid:
        print(f"\n❌ ISSUE FOUND: Workflow structure is invalid")
        return
    
    # Test 2: Minimal working workflow
    minimal_works = test_minimal_working_workflow()
    
    if not minimal_works:
        print(f"\n❌ ISSUE FOUND: Even minimal workflow fails")
        return
    
    # Test 3: Prompt length limits
    breaking_point, breaking_length = test_prompt_length_limits()
    
    if breaking_point:
        print(f"\n❌ ISSUE FOUND: Prompt length limit at {breaking_length} characters")
        print(f"🔧 SOLUTION: Reduce prompt length or split into multiple parts")
    else:
        print(f"\n✅ NO ISSUES FOUND: ComfyUI should be working correctly")
        print(f"🔧 The termination issue may be intermittent or environmental")

if __name__ == "__main__":
    main()
