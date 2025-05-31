#!/usr/bin/env python3
"""
Workflow Testing Script

Tests the ComfyUI workflows for manga generation to ensure they're properly formatted
and contain all required nodes and connections.

Usage:
    python scripts/test_workflows.py
"""

import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def validate_workflow_json(workflow_path: Path) -> bool:
    """
    Validate that a workflow JSON file is properly formatted.
    
    Args:
        workflow_path: Path to workflow JSON file
        
    Returns:
        True if valid, False otherwise
    """
    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        if not isinstance(workflow, dict):
            print(f"❌ {workflow_path.name}: Not a valid JSON object")
            return False
        
        # Check for required structure
        node_count = len(workflow)
        if node_count == 0:
            print(f"❌ {workflow_path.name}: No nodes found")
            return False
        
        print(f"✅ {workflow_path.name}: Valid JSON with {node_count} nodes")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ {workflow_path.name}: JSON decode error - {e}")
        return False
    except Exception as e:
        print(f"❌ {workflow_path.name}: Error - {e}")
        return False


def check_required_nodes(workflow_path: Path, required_node_types: list) -> bool:
    """
    Check if workflow contains required node types.
    
    Args:
        workflow_path: Path to workflow JSON file
        required_node_types: List of required node class types
        
    Returns:
        True if all required nodes present, False otherwise
    """
    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        found_nodes = set()
        for node_id, node_data in workflow.items():
            if "class_type" in node_data:
                found_nodes.add(node_data["class_type"])
        
        missing_nodes = set(required_node_types) - found_nodes
        
        if missing_nodes:
            print(f"⚠️  {workflow_path.name}: Missing required nodes: {missing_nodes}")
            return False
        else:
            print(f"✅ {workflow_path.name}: All required nodes present")
            return True
            
    except Exception as e:
        print(f"❌ {workflow_path.name}: Error checking nodes - {e}")
        return False


def check_placeholders(workflow_path: Path, expected_placeholders: list) -> bool:
    """
    Check if workflow contains expected placeholder variables.
    
    Args:
        workflow_path: Path to workflow JSON file
        expected_placeholders: List of expected placeholder strings
        
    Returns:
        True if placeholders found, False otherwise
    """
    try:
        with open(workflow_path, 'r') as f:
            workflow_str = f.read()
        
        found_placeholders = []
        for placeholder in expected_placeholders:
            if f"{{{placeholder}}}" in workflow_str:
                found_placeholders.append(placeholder)
        
        missing_placeholders = set(expected_placeholders) - set(found_placeholders)
        
        if missing_placeholders:
            print(f"⚠️  {workflow_path.name}: Missing placeholders: {missing_placeholders}")
        
        if found_placeholders:
            print(f"✅ {workflow_path.name}: Found placeholders: {found_placeholders}")
        
        return len(missing_placeholders) == 0
        
    except Exception as e:
        print(f"❌ {workflow_path.name}: Error checking placeholders - {e}")
        return False


def test_main_workflow():
    """Test the main manga workflow."""
    print("\n🧪 Testing Main Manga Workflow")
    print("=" * 50)
    
    workflow_path = project_root / "workflows" / "manga" / "manga_controlnet_adapter_workflow.json"
    
    if not workflow_path.exists():
        print(f"❌ Workflow not found: {workflow_path}")
        return False
    
    # Validate JSON structure
    if not validate_workflow_json(workflow_path):
        return False
    
    # Check required nodes
    required_nodes = [
        "CheckpointLoaderSimple",
        "CLIPTextEncode",
        "EmptyLatentImage",
        "ControlNetLoader",
        "LoadImage",
        "ControlNetApply",
        "T2IAdapterLoader",
        "T2IAdapterApply",
        "KSampler",
        "VAEDecode",
        "SaveImage"
    ]
    
    return check_required_nodes(workflow_path, required_nodes)


def test_modular_workflows():
    """Test the modular workflow components."""
    print("\n🔧 Testing Modular Workflows")
    print("=" * 50)
    
    workflows_to_test = [
        {
            "name": "text_to_pose_image.json",
            "required_nodes": ["CheckpointLoaderSimple", "CLIPTextEncode", "KSampler", "OpenposePreprocessor", "SaveImage"],
            "placeholders": ["pose_description"]
        },
        {
            "name": "style_image_selector.json",
            "required_nodes": ["LoadImage", "ImageScale", "CannyEdgePreprocessor", "SaveImage"],
            "placeholders": ["style_name"]
        },
        {
            "name": "generate_manga_panel.json",
            "required_nodes": ["CheckpointLoaderSimple", "ControlNetLoader", "T2IAdapterLoader", "KSampler", "SaveImage"],
            "placeholders": ["prompt", "pose_image_path", "style_image_path", "seed", "timestamp"]
        }
    ]
    
    all_passed = True
    
    for workflow_info in workflows_to_test:
        workflow_path = project_root / "workflows" / "manga" / workflow_info["name"]
        
        print(f"\nTesting {workflow_info['name']}:")
        
        if not workflow_path.exists():
            print(f"❌ Workflow not found: {workflow_path}")
            all_passed = False
            continue
        
        # Validate JSON
        if not validate_workflow_json(workflow_path):
            all_passed = False
            continue
        
        # Check required nodes
        if not check_required_nodes(workflow_path, workflow_info["required_nodes"]):
            all_passed = False
        
        # Check placeholders
        if not check_placeholders(workflow_path, workflow_info["placeholders"]):
            all_passed = False
    
    return all_passed


def test_automation_script():
    """Test the automation script."""
    print("\n🤖 Testing Automation Script")
    print("=" * 50)
    
    script_path = project_root / "scripts" / "generate_panel.py"
    
    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False
    
    # Check if script is executable
    try:
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Check for required imports and classes
        required_elements = [
            "import json",
            "import requests",
            "class MangaPanelGenerator",
            "def load_workflow",
            "def substitute_placeholders",
            "def generate_manga_panel"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in script_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Script missing elements: {missing_elements}")
            return False
        
        print("✅ Automation script structure looks good")
        return True
        
    except Exception as e:
        print(f"❌ Error reading script: {e}")
        return False


def test_example_configs():
    """Test example configuration files."""
    print("\n📋 Testing Example Configurations")
    print("=" * 50)
    
    examples_dir = project_root / "examples"
    
    if not examples_dir.exists():
        print(f"❌ Examples directory not found: {examples_dir}")
        return False
    
    config_files = list(examples_dir.glob("*.json"))
    
    if not config_files:
        print("⚠️  No example configuration files found")
        return True
    
    all_valid = True
    
    for config_path in config_files:
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Check required fields
            required_fields = ["prompt", "pose_image", "style_image"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                print(f"❌ {config_path.name}: Missing fields: {missing_fields}")
                all_valid = False
            else:
                print(f"✅ {config_path.name}: Valid configuration")
                
        except Exception as e:
            print(f"❌ {config_path.name}: Error - {e}")
            all_valid = False
    
    return all_valid


def main():
    """Main test function."""
    print("🧪 ComfyUI Workflow Testing Suite")
    print("=" * 60)
    
    tests = [
        ("Main Workflow", test_main_workflow),
        ("Modular Workflows", test_modular_workflows),
        ("Automation Script", test_automation_script),
        ("Example Configs", test_example_configs)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error - {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Workflows are ready for use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
