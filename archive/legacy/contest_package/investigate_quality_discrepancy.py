import os
import sys
import json
import requests
import time
from pathlib import Path
from typing import Dict, Any, List

# Add project paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'image_gen'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pipeline_v2'))

from image_gen.comfy_client import load_workflow_template, ComfyUIClient
from story_generator import StoryGenerator

def analyze_workflow_differences():
    """Compare different workflow configurations to identify quality discrepancies."""
    print("🔍 WORKFLOW QUALITY DISCREPANCY INVESTIGATION")
    print("=" * 70)
    
    # Load and analyze different workflows
    workflows = {
        "bw_manga": "assets/workflows/bw_manga_workflow.json",
        "color_manga": "assets/workflows/color_manga_workflow.json",
        "original_manga": "assets/workflows/manga_graph.json"
    }
    
    workflow_analysis = {}
    
    for name, path in workflows.items():
        print(f"\n📋 Analyzing {name} workflow...")
        
        if not os.path.exists(path):
            print(f"   ❌ Workflow file not found: {path}")
            continue
        
        try:
            workflow = load_workflow_template(path)
            analysis = analyze_single_workflow(workflow, name)
            workflow_analysis[name] = analysis
            
            print(f"   ✅ Loaded: {len(workflow)} nodes")
            print(f"   📦 Model: {analysis['model']}")
            print(f"   ⚙️  Sampler: {analysis['sampler']} (steps: {analysis['steps']}, cfg: {analysis['cfg']})")
            print(f"   📐 Resolution: {analysis['resolution']}")
            
        except Exception as e:
            print(f"   ❌ Error analyzing workflow: {e}")
    
    return workflow_analysis

def analyze_single_workflow(workflow: Dict[str, Any], name: str) -> Dict[str, Any]:
    """Analyze a single workflow configuration."""
    
    analysis = {
        "name": name,
        "nodes": len(workflow),
        "model": "unknown",
        "sampler": "unknown",
        "steps": 0,
        "cfg": 0.0,
        "resolution": "unknown",
        "prompt_node": None,
        "negative_prompt_node": None,
        "issues": []
    }
    
    # Find key nodes and extract parameters
    for node_id, node_data in workflow.items():
        class_type = node_data.get("class_type", "")
        inputs = node_data.get("inputs", {})
        
        # Checkpoint loader
        if class_type == "CheckpointLoaderSimple":
            analysis["model"] = inputs.get("ckpt_name", "unknown")
        
        # KSampler
        elif class_type == "KSampler":
            analysis["sampler"] = inputs.get("sampler_name", "unknown")
            analysis["steps"] = inputs.get("steps", 0)
            analysis["cfg"] = inputs.get("cfg", 0.0)
        
        # Empty Latent Image (resolution)
        elif class_type == "EmptyLatentImage":
            width = inputs.get("width", 0)
            height = inputs.get("height", 0)
            analysis["resolution"] = f"{width}x{height}"
        
        # Text encode nodes (prompts)
        elif class_type == "CLIPTextEncode":
            text = inputs.get("text", "")
            if "PROMPT_PLACEHOLDER" in text or "positive" in text.lower():
                analysis["prompt_node"] = node_id
            elif "negative" in text.lower() or "bad" in text.lower():
                analysis["negative_prompt_node"] = node_id
    
    # Check for potential issues
    if analysis["model"] == "unknown":
        analysis["issues"].append("No model specified")
    if analysis["steps"] < 10:
        analysis["issues"].append(f"Very low steps: {analysis['steps']}")
    if analysis["cfg"] < 5.0:
        analysis["issues"].append(f"Very low CFG: {analysis['cfg']}")
    
    return analysis

def test_prompt_generation():
    """Test the story generation and prompt creation process."""
    print(f"\n📝 TESTING STORY GENERATION & PROMPT CREATION")
    print("=" * 60)
    
    try:
        story_generator = StoryGenerator()
        
        # Test with simple prompt
        test_prompt = "A young anime character with a happy expression"
        
        print(f"🧪 Testing story generation...")
        print(f"   Input: '{test_prompt}'")
        
        story_data = story_generator.generate_manga_story(test_prompt, panels=1)
        
        if story_data and story_data.get("panels"):
            panel_data = story_data["panels"][0]
            
            print(f"✅ Story generated successfully:")
            print(f"   📚 Title: {story_data['title']}")
            print(f"   🎭 Character: {story_data['character']['name']}")
            print(f"   📝 Character Description: {story_data['character']['appearance']}")
            
            print(f"\n📋 Panel Data:")
            print(f"   🎭 Emotion: {panel_data['character_emotion']}")
            print(f"   🤸 Pose: {panel_data['character_pose']}")
            print(f"   🖼️  Visual Prompt: {panel_data['visual_prompt']}")
            print(f"   💬 Dialogue: {panel_data['dialogue']}")
            
            # Check prompt length and content
            visual_prompt = panel_data['visual_prompt']
            print(f"\n🔍 Prompt Analysis:")
            print(f"   📏 Length: {len(visual_prompt)} characters")
            
            # Check for problematic content
            issues = []
            if len(visual_prompt) > 500:
                issues.append("Very long prompt (>500 chars)")
            if "PROMPT_PLACEHOLDER" in visual_prompt:
                issues.append("Contains placeholder text")
            if not any(word in visual_prompt.lower() for word in ["anime", "manga", "character", "girl", "boy"]):
                issues.append("No character-related keywords")
            
            if issues:
                print(f"   ⚠️  Potential Issues:")
                for issue in issues:
                    print(f"      - {issue}")
            else:
                print(f"   ✅ Prompt appears well-formed")
            
            return story_data
        else:
            print(f"❌ Story generation failed")
            return None
            
    except Exception as e:
        print(f"❌ Story generation test failed: {e}")
        return None

def test_direct_vs_story_prompts():
    """Compare direct simple prompts vs story-generated prompts."""
    print(f"\n🎯 DIRECT VS STORY PROMPT COMPARISON")
    print("=" * 60)
    
    # Test scenarios
    test_cases = [
        {
            "name": "direct_simple",
            "type": "direct",
            "prompt": "anime girl with happy expression"
        },
        {
            "name": "direct_detailed", 
            "type": "direct",
            "prompt": "high quality anime character portrait, detailed face, clear eyes, natural expression, professional artwork"
        },
        {
            "name": "story_generated",
            "type": "story",
            "prompt": "A cheerful anime character discovers something amazing"
        }
    ]
    
    results = []
    
    for test_case in test_cases:
        print(f"\n📋 Testing: {test_case['name']}")
        print(f"   Type: {test_case['type']}")
        print(f"   Input: {test_case['prompt']}")
        
        if test_case['type'] == 'direct':
            final_prompt = test_case['prompt']
        else:
            # Generate story and extract prompt
            try:
                story_generator = StoryGenerator()
                story_data = story_generator.generate_manga_story(test_case['prompt'], panels=1)
                
                if story_data and story_data.get("panels"):
                    final_prompt = story_data["panels"][0]['visual_prompt']
                else:
                    print(f"   ❌ Story generation failed")
                    continue
            except Exception as e:
                print(f"   ❌ Story generation error: {e}")
                continue
        
        print(f"   📝 Final Prompt ({len(final_prompt)} chars): {final_prompt[:100]}...")
        
        # Test this prompt with ComfyUI
        success = test_prompt_with_comfyui(final_prompt, test_case['name'])
        
        results.append({
            "name": test_case['name'],
            "type": test_case['type'],
            "prompt": final_prompt,
            "success": success
        })
    
    # Analyze results
    print(f"\n📊 PROMPT COMPARISON RESULTS:")
    print("=" * 40)
    
    for result in results:
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        print(f"{result['name']}: {status}")
        print(f"   Type: {result['type']}")
        print(f"   Length: {len(result['prompt'])} chars")
    
    # Identify patterns
    direct_success = [r for r in results if r['type'] == 'direct' and r['success']]
    story_success = [r for r in results if r['type'] == 'story' and r['success']]
    
    print(f"\n🔍 PATTERN ANALYSIS:")
    print(f"   Direct prompts successful: {len(direct_success)}")
    print(f"   Story prompts successful: {len(story_success)}")
    
    if len(direct_success) > len(story_success):
        print(f"   🎯 FINDING: Direct prompts work better than story-generated prompts")
        print(f"   🔧 RECOMMENDATION: Issue likely in story-to-prompt conversion")
    elif len(story_success) > len(direct_success):
        print(f"   🎯 FINDING: Story prompts work better than direct prompts")
        print(f"   🔧 RECOMMENDATION: Issue likely in workflow configuration")
    else:
        print(f"   🎯 FINDING: Both prompt types have similar success rates")
        print(f"   🔧 RECOMMENDATION: Issue likely in ComfyUI parameters or model")
    
    return results

def test_prompt_with_comfyui(prompt: str, test_name: str) -> bool:
    """Test a specific prompt with ComfyUI and check if it generates quality images."""
    
    try:
        # Load BW workflow
        workflow = load_workflow_template("assets/workflows/bw_manga_workflow.json")
        
        # Replace placeholder
        workflow["1"]["inputs"]["text"] = workflow["1"]["inputs"]["text"].replace(
            "PROMPT_PLACEHOLDER", prompt
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
        
        print(f"   📤 Queued successfully, waiting for generation...")
        
        # Wait for generation
        time.sleep(20)
        
        # Check if ComfyUI is still alive
        try:
            check_response = requests.get("http://127.0.0.1:8188/system_stats", timeout=5)
            if check_response.status_code != 200:
                print(f"   ❌ ComfyUI not responding")
                return False
        except:
            print(f"   ❌ ComfyUI connection failed")
            return False
        
        # Look for recent images
        output_dir = Path("ComfyUI-master/output")
        if output_dir.exists():
            recent_files = []
            for img_file in output_dir.glob("*.png"):
                if time.time() - img_file.stat().st_mtime < 30:  # Last 30 seconds
                    recent_files.append(img_file)
            
            if recent_files:
                latest_file = max(recent_files, key=lambda x: x.stat().st_mtime)
                size = latest_file.stat().st_size
                
                # Copy for analysis
                analysis_path = f"contest_package/output/prompt_test_{test_name}.png"
                import shutil
                shutil.copy2(latest_file, analysis_path)
                
                print(f"   ✅ Generated: {latest_file.name} ({size:,} bytes)")
                
                # Quick quality check
                if size > 500000:  # At least 500KB indicates substantial content
                    print(f"   ✅ File size indicates quality content")
                    return True
                else:
                    print(f"   ⚠️  Small file size may indicate poor quality")
                    return False
            else:
                print(f"   ❌ No recent images found")
                return False
        else:
            print(f"   ❌ ComfyUI output directory not found")
            return False
            
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Main investigation function."""
    print("🔍 INVESTIGATING MANGA GENERATION QUALITY DISCREPANCY")
    print("=" * 80)
    print("Comparing high-quality vs poor-quality image generation workflows")
    print()
    
    # Step 1: Analyze workflow configurations
    workflow_analysis = analyze_workflow_differences()
    
    # Step 2: Test story generation process
    story_data = test_prompt_generation()
    
    # Step 3: Compare direct vs story prompts
    prompt_results = test_direct_vs_story_prompts()
    
    # Step 4: Final analysis and recommendations
    print(f"\n🎯 INVESTIGATION SUMMARY")
    print("=" * 50)
    
    print(f"📋 Workflow Analysis:")
    for name, analysis in workflow_analysis.items():
        issues = len(analysis.get('issues', []))
        print(f"   {name}: {issues} issues found")
    
    print(f"\n📝 Story Generation:")
    if story_data:
        print(f"   ✅ Working - generates structured prompts")
    else:
        print(f"   ❌ Failed - may be source of quality issues")
    
    print(f"\n🎯 Prompt Testing:")
    if prompt_results:
        direct_success = len([r for r in prompt_results if r['type'] == 'direct' and r['success']])
        story_success = len([r for r in prompt_results if r['type'] == 'story' and r['success']])
        print(f"   Direct prompts: {direct_success} successful")
        print(f"   Story prompts: {story_success} successful")
    
    print(f"\n🔧 RECOMMENDATIONS:")
    print(f"   1. Check workflow parameter differences")
    print(f"   2. Validate story-to-prompt conversion")
    print(f"   3. Test with simplified prompts")
    print(f"   4. Compare successful vs failed image characteristics")

if __name__ == "__main__":
    main()
