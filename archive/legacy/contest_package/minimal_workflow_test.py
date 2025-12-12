import os
import sys
import json
import requests
import time

def create_minimal_workflow():
    """Create the most basic possible workflow."""
    return {
        "1": {
            "inputs": {
                "text": "simple test",
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
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "4": {
            "inputs": {
                "seed": 42,
                "steps": 10,  # Reduced steps
                "cfg": 7.0,
                "sampler_name": "euler",  # Simple sampler
                "scheduler": "normal",    # Simple scheduler
                "denoise": 1.0,
                "model": ["2", 0],
                "positive": ["1", 0],
                "negative": ["1", 0],  # Use same as positive for simplicity
                "latent_image": ["3", 0]
            },
            "class_type": "KSampler"
        },
        "5": {
            "inputs": {
                "samples": ["4", 0],
                "vae": ["2", 2]
            },
            "class_type": "VAEDecode"
        },
        "6": {
            "inputs": {
                "filename_prefix": "minimal_test",
                "images": ["5", 0]
            },
            "class_type": "SaveImage"
        }
    }

def test_minimal_workflow():
    """Test with absolute minimal workflow."""
    print("🧪 MINIMAL WORKFLOW TEST")
    print("=" * 40)
    
    # Check ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        print(f"✅ ComfyUI responding: {response.status_code}")
    except Exception as e:
        print(f"❌ ComfyUI not responding: {e}")
        return False
    
    # Create minimal workflow
    workflow = create_minimal_workflow()
    print(f"📋 Created minimal workflow with {len(workflow)} nodes")
    
    # Send to ComfyUI
    try:
        import uuid
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }
        
        print(f"📤 Sending minimal workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Workflow queued successfully")
            
            # Wait and check if ComfyUI survives
            print(f"⏳ Waiting 15 seconds...")
            time.sleep(15)
            
            # Check if still alive
            try:
                check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
                if check_response.status_code == 200:
                    print(f"✅ ComfyUI survived minimal workflow!")
                    return True
                else:
                    print(f"❌ ComfyUI not responding after minimal workflow")
                    return False
            except Exception as e:
                print(f"❌ ComfyUI crashed with minimal workflow: {e}")
                return False
        else:
            print(f"❌ Failed to queue workflow: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending workflow: {e}")
        return False

def test_even_simpler():
    """Test with proper minimal workflow that has outputs."""
    print(f"\n🔬 ULTRA-MINIMAL TEST (with outputs)")
    print("=" * 40)

    # Proper minimal workflow with outputs
    ultra_minimal = {
        "1": {
            "inputs": {
                "ckpt_name": "anything-v4.5-pruned.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "2": {
            "inputs": {
                "text": "simple test",
                "clip": ["1", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "3": {
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "4": {
            "inputs": {
                "seed": 42,
                "steps": 5,  # Very few steps
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["2", 0],  # Same as positive
                "latent_image": ["3", 0]
            },
            "class_type": "KSampler"
        },
        "5": {
            "inputs": {
                "samples": ["4", 0],
                "vae": ["1", 2]
            },
            "class_type": "VAEDecode"
        },
        "6": {
            "inputs": {
                "filename_prefix": "ultra_minimal",
                "images": ["5", 0]
            },
            "class_type": "SaveImage"
        }
    }
    
    try:
        import uuid
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": ultra_minimal,
            "client_id": prompt_id
        }
        
        print(f"📤 Sending ultra-minimal workflow (complete with outputs)...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            print(f"✅ Ultra-minimal workflow queued")

            time.sleep(15)  # Give it time to process

            check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
            if check_response.status_code == 200:
                print(f"✅ ComfyUI survived ultra-minimal workflow!")
                return True
            else:
                print(f"❌ ComfyUI crashed with ultra-minimal workflow")
                return False
        else:
            print(f"❌ Failed to queue ultra-minimal: {response.status_code}")
            if response.text:
                print(f"Error details: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Ultra-minimal test failed: {e}")
        return False

def check_comfyui_logs():
    """Check if we can get any error info from ComfyUI."""
    print(f"\n📋 CHECKING COMFYUI STATUS")
    print("=" * 35)
    
    try:
        # Try to get queue status
        response = requests.get("http://127.0.0.1:8188/queue", timeout=5)
        if response.status_code == 200:
            queue_data = response.json()
            print(f"📊 Queue status: {len(queue_data.get('queue_running', []))} running, {len(queue_data.get('queue_pending', []))} pending")
        
        # Try to get system stats
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        if response.status_code == 200:
            stats = response.json()
            print(f"💾 System stats available")
            
        return True
    except Exception as e:
        print(f"❌ Cannot get ComfyUI status: {e}")
        return False

if __name__ == "__main__":
    print("🔍 COMFYUI CRASH ISOLATION TEST")
    print("=" * 50)
    
    # Check initial status
    if not check_comfyui_logs():
        print("❌ ComfyUI not responding - start ComfyUI first")
        exit(1)
    
    # Test ultra-minimal first
    ultra_success = test_even_simpler()
    
    if ultra_success:
        print(f"\n✅ Ultra-minimal works, testing minimal...")
        minimal_success = test_minimal_workflow()
        
        if minimal_success:
            print(f"\n🎉 SUCCESS: Both minimal workflows work!")
            print(f"🔧 Issue likely in our complex workflow or prompt content")
        else:
            print(f"\n⚠️  Ultra-minimal works but minimal fails")
            print(f"🔧 Issue likely in KSampler or VAE nodes")
    else:
        print(f"\n❌ Even ultra-minimal fails")
        print(f"🔧 Issue likely in basic ComfyUI setup or model loading")
    
    print(f"\n📋 DIAGNOSIS COMPLETE")
    print("Check ComfyUI console for specific error messages")
