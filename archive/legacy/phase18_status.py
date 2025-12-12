#!/usr/bin/env python3

"""
Phase 18 Status Report
Shows the current status of the Phase 18 migration
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("📋 PHASE 18 STATUS REPORT")
print("=" * 50)

# Check file structure
print("\n1. 📁 File Structure Status")
required_files = [
    "config/settings.yaml",
    "core/config_manager.py", 
    "core/panel_generator.py",
    "image_gen/comfy_client.py",
    "scripts/generate_panel.py",
    "scripts/sanity_test.py",
    "scripts/setup_models.py",
    "README_PHASE18.md",
    "PHASE18_SUMMARY.md"
]

file_count = 0
for file_path in required_files:
    path = Path(file_path)
    if path.exists():
        file_count += 1

print(f"   Status: {file_count}/{len(required_files)} files present")
if file_count == len(required_files):
    print("   ✅ All required files are present")
else:
    print("   ⚠️  Some files may be missing")

# Check model directories
print("\n2. 📂 Model Directory Status")
models_dir = Path("models")
required_subdirs = [
    "checkpoints", "controlnet", "loras", 
    "t2i_adapter", "ipadapter", "vae", "embeddings"
]

if models_dir.exists():
    dir_count = 0
    for subdir in required_subdirs:
        subdir_path = models_dir / subdir
        if subdir_path.exists():
            dir_count += 1
    
    print(f"   Status: {dir_count}/{len(required_subdirs)} directories present")
    if dir_count == len(required_subdirs):
        print("   ✅ All model directories are set up")
    else:
        print("   ⚠️  Some model directories may be missing")
else:
    print("   ❌ Models directory not found")

# Check configuration
print("\n3. ⚙️  Configuration Status")
try:
    import yaml
    config_file = Path("config/settings.yaml")
    
    if config_file.exists():
        with open(config_file, 'r') as f:
            settings = yaml.safe_load(f)
        
        required_sections = ['comfyui', 'models', 'generation']
        section_count = sum(1 for section in required_sections if section in settings)
        
        print(f"   Status: {section_count}/{len(required_sections)} config sections present")
        if section_count == len(required_sections):
            print("   ✅ Configuration file is complete")
        else:
            print("   ⚠️  Some configuration sections may be missing")
    else:
        print("   ❌ Configuration file not found")
        
except Exception as e:
    print(f"   ❌ Configuration error: {e}")

# Check core modules
print("\n4. 🧩 Core Modules Status")
module_status = []

try:
    from core.config_manager import get_config
    config = get_config()
    module_status.append("Config Manager")
except:
    pass

try:
    from core.panel_generator import EnhancedPanelGenerator
    generator = EnhancedPanelGenerator()
    module_status.append("Panel Generator")
except:
    pass

try:
    from image_gen.comfy_client import ComfyUIClient
    client = ComfyUIClient()
    module_status.append("ComfyUI Client")
except:
    pass

print(f"   Status: {len(module_status)}/3 core modules working")
if len(module_status) == 3:
    print("   ✅ All core modules are functional")
    for module in module_status:
        print(f"     ✓ {module}")
else:
    print("   ⚠️  Some core modules may have issues")

# Check workflow files
print("\n5. 📋 Workflow Files Status")
workflow_dir = Path("assets/workflows")
workflow_files = [
    "manga_graph.json",
    "improved_manga_workflow.json",
    "controlnet_workflow.json",
    "adapter_workflow.json"
]

if workflow_dir.exists():
    workflow_count = 0
    for workflow_file in workflow_files:
        workflow_path = workflow_dir / workflow_file
        if workflow_path.exists():
            workflow_count += 1
    
    print(f"   Status: {workflow_count}/{len(workflow_files)} workflow files present")
    if workflow_count == len(workflow_files):
        print("   ✅ All workflow files are present")
    else:
        print("   ⚠️  Some workflow files may be missing")
else:
    print("   ❌ Workflows directory not found")

# Overall status
print("\n" + "=" * 50)
print("🎯 OVERALL PHASE 18 STATUS")
print("=" * 50)

# Calculate overall readiness
readiness_score = 0
total_checks = 5

if file_count == len(required_files):
    readiness_score += 1

if models_dir.exists() and dir_count == len(required_subdirs):
    readiness_score += 1

try:
    if config_file.exists() and section_count == len(required_sections):
        readiness_score += 1
except:
    pass

if len(module_status) == 3:
    readiness_score += 1

if workflow_dir.exists() and workflow_count == len(workflow_files):
    readiness_score += 1

readiness_percentage = (readiness_score / total_checks) * 100

print(f"Readiness Score: {readiness_score}/{total_checks} ({readiness_percentage:.0f}%)")

if readiness_score == total_checks:
    print("\n🎉 PHASE 18 IS FULLY READY!")
    print("✅ All components are in place and functional")
    print("\nYou can now:")
    print("1. Download models: python scripts/setup_models.py")
    print("2. Start ComfyUI server")
    print("3. Test generation: python scripts/generate_panel.py --test")
    print("4. Run full test: python scripts/sanity_test.py")
    
elif readiness_score >= 4:
    print("\n✅ PHASE 18 IS MOSTLY READY!")
    print("🟡 Minor issues may exist but core functionality is available")
    print("\nRecommended actions:")
    print("1. Review any warnings above")
    print("2. Download models: python scripts/setup_models.py")
    print("3. Test the system: python scripts/sanity_test.py")
    
elif readiness_score >= 2:
    print("\n🟡 PHASE 18 IS PARTIALLY READY")
    print("⚠️  Some components need attention")
    print("\nRequired actions:")
    print("1. Review and fix the issues above")
    print("2. Ensure all files and directories are present")
    print("3. Test configuration and modules")
    
else:
    print("\n❌ PHASE 18 NEEDS SIGNIFICANT WORK")
    print("🔧 Multiple components require attention")
    print("\nRequired actions:")
    print("1. Check file structure and missing components")
    print("2. Verify configuration files")
    print("3. Test module imports and functionality")

print("\n" + "=" * 50)
print("📊 Status report complete")
print("=" * 50)