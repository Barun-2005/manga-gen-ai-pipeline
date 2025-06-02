#!/usr/bin/env python3
"""
Output System Verification Script

Verifies that the output system is working correctly:
- Tests meaningful naming
- Checks organized structure
- Validates no overwrites
- Confirms clean organization
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.output_manager import OutputManager

def verify_output_structure():
    """Verify the output directory structure."""
    
    print("🔍 Verifying Output Structure")
    print("=" * 50)
    
    # Check base outputs directory
    outputs_dir = Path("outputs")
    if not outputs_dir.exists():
        print("❌ Outputs directory does not exist")
        return False
    
    print(f"✅ Base outputs directory exists: {outputs_dir}")
    
    # List all subdirectories
    subdirs = [d for d in outputs_dir.iterdir() if d.is_dir()]
    print(f"📁 Found {len(subdirs)} subdirectories:")
    
    for subdir in sorted(subdirs):
        print(f"   - {subdir.name}")
        
        # Check if it's a run directory
        if subdir.name.startswith("run_") or "test" in subdir.name.lower():
            metadata_file = subdir / "metadata" / "run_info.json"
            if metadata_file.exists():
                print(f"     ✅ Has metadata")
            else:
                print(f"     ⚠️  No metadata")
            
            # Check structure
            expected_dirs = ["panels", "validation", "emotions", "metadata"]
            for expected in expected_dirs:
                if (subdir / expected).exists():
                    print(f"     ✅ Has {expected}/")
                else:
                    print(f"     ❌ Missing {expected}/")
    
    return True

def verify_meaningful_naming():
    """Verify that panel names are meaningful."""
    
    print("\n🏷️  Verifying Meaningful Naming")
    print("=" * 50)
    
    # Check test meaningful names directory
    test_dir = Path("outputs/test_meaningful_names")
    if not test_dir.exists():
        print("⚠️  Test meaningful names directory not found")
        return False
    
    panels = list(test_dir.glob("*.png"))
    print(f"📸 Found {len(panels)} panels with meaningful names:")
    
    meaningful_count = 0
    for panel in sorted(panels):
        name = panel.name
        print(f"   - {name}")
        
        # Check if name has meaningful content (not just numbers)
        if any(word in name.lower() for word in ["masterpiece", "ninja", "temple", "sword", "guardian"]):
            meaningful_count += 1
            print(f"     ✅ Meaningful name")
        else:
            print(f"     ⚠️  Generic name")
    
    success_rate = (meaningful_count / len(panels)) * 100 if panels else 0
    print(f"\n📊 Meaningful naming rate: {success_rate:.1f}%")
    
    return success_rate > 50

def verify_no_overwrites():
    """Verify that multiple runs don't overwrite each other."""
    
    print("\n🔒 Verifying No Overwrites")
    print("=" * 50)
    
    # Create multiple test runs to check versioning
    manager = OutputManager()
    
    # Create first run
    run1 = manager.create_new_run("overwrite_test")
    print(f"✅ Created run 1: {run1.name}")
    
    # Create second run with same name
    run2 = manager.create_new_run("overwrite_test")
    print(f"✅ Created run 2: {run2.name}")
    
    # Verify they're different
    if run1.name != run2.name:
        print(f"✅ Runs have different names (no overwrite)")
        print(f"   Run 1: {run1.name}")
        print(f"   Run 2: {run2.name}")
        return True
    else:
        print(f"❌ Runs have same name (overwrite risk)")
        return False

def verify_clean_organization():
    """Verify that the organization is clean and logical."""
    
    print("\n🧹 Verifying Clean Organization")
    print("=" * 50)
    
    outputs_dir = Path("outputs")
    
    # Check for loose files in outputs root
    loose_files = [f for f in outputs_dir.iterdir() if f.is_file()]
    if loose_files:
        print(f"⚠️  Found {len(loose_files)} loose files in outputs root:")
        for file in loose_files:
            print(f"   - {file.name}")
    else:
        print("✅ No loose files in outputs root")
    
    # Check for organized structure
    organized_dirs = 0
    total_dirs = 0
    
    for subdir in outputs_dir.iterdir():
        if subdir.is_dir():
            total_dirs += 1
            
            # Check if it follows organized structure
            has_panels = (subdir / "panels").exists()
            has_metadata = (subdir / "metadata").exists()
            
            if has_panels and has_metadata:
                organized_dirs += 1
                print(f"✅ {subdir.name} - Well organized")
            elif subdir.name in ["backup_validation_panels", "test_meaningful_names"]:
                print(f"📁 {subdir.name} - Legacy/test directory")
            else:
                print(f"⚠️  {subdir.name} - Not organized")
    
    organization_rate = (organized_dirs / total_dirs) * 100 if total_dirs else 100
    print(f"\n📊 Organization rate: {organization_rate:.1f}%")
    
    return organization_rate > 70

def verify_panel_accessibility():
    """Verify that panels are easily accessible and identifiable."""
    
    print("\n👁️  Verifying Panel Accessibility")
    print("=" * 50)
    
    # Find all panel directories
    outputs_dir = Path("outputs")
    panel_dirs = []
    
    for subdir in outputs_dir.iterdir():
        if subdir.is_dir():
            base_panels = subdir / "panels" / "base"
            enhanced_panels = subdir / "panels" / "enhanced"
            
            if base_panels.exists() or enhanced_panels.exists():
                panel_dirs.append(subdir)
    
    print(f"📁 Found {len(panel_dirs)} directories with panels:")
    
    total_base = 0
    total_enhanced = 0
    
    for panel_dir in panel_dirs:
        base_panels = list((panel_dir / "panels" / "base").glob("*.png"))
        enhanced_panels = list((panel_dir / "panels" / "enhanced").glob("*.png"))
        
        total_base += len(base_panels)
        total_enhanced += len(enhanced_panels)
        
        print(f"   📁 {panel_dir.name}:")
        print(f"      🎯 Base panels: {len(base_panels)}")
        print(f"      ✨ Enhanced panels: {len(enhanced_panels)}")
        
        # Show sample filenames
        if base_panels:
            print(f"      📄 Sample base: {base_panels[0].name}")
        if enhanced_panels:
            print(f"      📄 Sample enhanced: {enhanced_panels[0].name}")
    
    print(f"\n📊 Total panels found:")
    print(f"   🎯 Base: {total_base}")
    print(f"   ✨ Enhanced: {total_enhanced}")
    print(f"   📸 Total: {total_base + total_enhanced}")
    
    return total_base > 0 and total_enhanced > 0

def run_complete_verification():
    """Run complete output system verification."""
    
    print("🔍 OUTPUT SYSTEM VERIFICATION")
    print("=" * 70)
    
    tests = [
        ("Output Structure", verify_output_structure),
        ("Meaningful Naming", verify_meaningful_naming),
        ("No Overwrites", verify_no_overwrites),
        ("Clean Organization", verify_clean_organization),
        ("Panel Accessibility", verify_panel_accessibility)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results[test_name] = False
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
    
    if success_rate >= 80:
        print("🎉 OUTPUT SYSTEM VERIFICATION: ✅ PASSED")
        return True
    else:
        print("⚠️  OUTPUT SYSTEM VERIFICATION: ❌ NEEDS IMPROVEMENT")
        return False

def main():
    """Main verification function."""
    success = run_complete_verification()
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
