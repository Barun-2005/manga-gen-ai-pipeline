import os
import sys
import json
import requests
import time

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'image_gen'))

from image_gen.comfy_client import load_workflow_template

def test_manga_workflow():
    """Test our actual manga workflow that's been causing crashes."""
    print("🎨 MANGA WORKFLOW CRASH TEST")
    print("=" * 50)
    
    # Check ComfyUI is running
    try:
        response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
        print(f"✅ ComfyUI responding: {response.status_code}")
    except Exception as e:
        print(f"❌ ComfyUI not responding: {e}")
        return False
    
    # Test 1: Load and validate our BW manga workflow
    print(f"\n📋 Test 1: BW Manga Workflow Structure")
    try:
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        print(f"✅ BW workflow loaded: {len(workflow)} nodes")
        
        # Replace placeholder with simple prompt first
        simple_prompt = "anime character"
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", simple_prompt
        )
        
        print(f"📝 Testing with simple prompt: '{simple_prompt}'")
        
        # Send to ComfyUI
        import uuid
        prompt_id = str(uuid.uuid4())
        
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }
        
        print(f"📤 Sending BW manga workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ BW workflow queued successfully")
            
            # Wait and check if ComfyUI survives
            print(f"⏳ Waiting 20 seconds...")
            time.sleep(20)
            
            # Check if still alive
            try:
                check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
                if check_response.status_code == 200:
                    print(f"✅ ComfyUI survived BW manga workflow!")
                else:
                    print(f"❌ ComfyUI not responding after BW workflow")
                    return False
            except Exception as e:
                print(f"❌ ComfyUI crashed with BW workflow: {e}")
                return False
        else:
            print(f"❌ Failed to queue BW workflow: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ BW workflow test failed: {e}")
        return False
    
    # Test 2: Test with complex prompt (what we think causes crashes)
    print(f"\n🔥 Test 2: Complex Prompt Test")
    try:
        # This is the type of complex prompt from our enhanced system
        complex_prompt = "manga panel featuring Protagonist: young anime character with dark hair, bright eyes, casual modern clothing, determined expression, showing happy facial expression with standing body pose, in scene: Scene 1 related to adventure story, high quality character art, consistent character design, clear facial features, proper anatomy, detailed background, professional manga illustration, publication quality"
        
        print(f"📝 Testing with complex prompt ({len(complex_prompt)} chars)")
        
        # Load fresh workflow
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", complex_prompt
        )
        
        prompt_id = str(uuid.uuid4())
        payload = {
            "prompt": workflow,
            "client_id": prompt_id
        }
        
        print(f"📤 Sending complex prompt workflow...")
        response = requests.post(
            "http://127.0.0.1:8188/prompt",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ Complex prompt workflow queued")
            
            # Wait longer for complex generation
            print(f"⏳ Waiting 30 seconds for complex generation...")
            time.sleep(30)
            
            # Check if ComfyUI survived
            try:
                check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
                if check_response.status_code == 200:
                    print(f"✅ ComfyUI survived complex prompt!")
                else:
                    print(f"❌ ComfyUI crashed with complex prompt")
                    return False
            except Exception as e:
                print(f"❌ ComfyUI crashed with complex prompt: {e}")
                return False
        else:
            print(f"❌ Failed to queue complex prompt: {response.status_code}")
            print(f"Error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Complex prompt test failed: {e}")
        return False
    
    # Test 3: Test our actual generate_panel function
    print(f"\n🎯 Test 3: Actual generate_panel Function")
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))
        from generate_panel import generate_panel
        
        output_path = "contest_package/output/workflow_test.png"
        
        print(f"🎨 Testing actual generate_panel function...")
        print(f"📁 Output: {output_path}")
        
        generate_panel(
            output_image=output_path,
            style="bw",
            emotion="happy",
            pose="standing"
        )
        
        # Check if file was created
        if os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ Panel generated successfully: {size:,} bytes")
            
            # Check if ComfyUI is still alive
            check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
            if check_response.status_code == 200:
                print(f"✅ ComfyUI survived actual generation!")
                return True
            else:
                print(f"❌ ComfyUI crashed during actual generation")
                return False
        else:
            print(f"❌ No output file created")
            return False
            
    except Exception as e:
        print(f"❌ Actual generation test failed: {e}")
        return False

def check_generated_images():
    """Check if any images were actually generated."""
    print(f"\n📸 CHECKING GENERATED IMAGES")
    print("=" * 40)
    
    # Check ComfyUI output directory
    comfyui_output = "ComfyUI-master/output"
    if os.path.exists(comfyui_output):
        image_files = []
        for ext in ['*.png', '*.jpg', '*.jpeg']:
            import glob
            image_files.extend(glob.glob(os.path.join(comfyui_output, ext)))
        
        if image_files:
            print(f"✅ Found {len(image_files)} generated images:")
            for img_file in sorted(image_files)[-5:]:  # Show last 5
                size = os.path.getsize(img_file)
                print(f"   - {os.path.basename(img_file)}: {size:,} bytes")
        else:
            print(f"⚠️  No images found in ComfyUI output directory")
    else:
        print(f"❌ ComfyUI output directory not found")

if __name__ == "__main__":
    print("🔍 TESTING MANGA WORKFLOW FOR CRASHES")
    print("=" * 60)
    
    success = test_manga_workflow()
    
    if success:
        print(f"\n🎉 SUCCESS: Manga workflow working correctly!")
        print(f"✅ ComfyUI integration is stable")
        print(f"✅ Complex prompts work fine")
        print(f"✅ Actual generation functions work")
    else:
        print(f"\n❌ FAILED: Found the crash point")
        print(f"🔧 Check ComfyUI console for specific errors")
    
    # Check what images were generated
    check_generated_images()
    
    print(f"\n📋 DIAGNOSIS COMPLETE")
    print("If successful, the crash issue was likely temporary or environmental")
