#!/usr/bin/env python3
"""
Coherence Evaluation Test Script

Quick test script for evaluating coherence of specific panel sequences.
Useful for testing and debugging the coherence analysis system.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.coherence_analyzer import CoherenceAnalyzer
from scripts.narrative_thread_tracker import NarrativeThreadTracker


def create_test_scene_data(panel_paths: List[str]) -> List[Dict[str, Any]]:
    """Create mock scene data for testing when metadata is not available."""
    
    test_scenes = []
    
    # Default test scenarios
    test_descriptions = [
        "A young samurai warrior stands at the edge of a cursed village with determination.",
        "The samurai encounters a mysterious old sage who offers guidance and wisdom.",
        "The warrior kneels respectfully before the sage, showing humility and resolve.",
        "The samurai climbs a treacherous mountain path toward their destiny.",
        "At the mountain peak, the warrior faces a massive stone guardian blocking their way."
    ]
    
    test_dialogues = [
        "I must find the Crystal Sword to save my village!",
        "Young warrior, only one pure of heart can wield its power.",
        "I will do whatever it takes to save my people.",
        "The path grows more dangerous, but I cannot turn back now!",
        "Who dares seek the Crystal Sword?"
    ]
    
    test_emotions = ["determined", "mystical", "respectful", "determined", "confrontational"]
    
    for i, panel_path in enumerate(panel_paths):
        scene_data = {
            "description": test_descriptions[i % len(test_descriptions)],
            "dialogue": test_dialogues[i % len(test_dialogues)],
            "emotion": test_emotions[i % len(test_emotions)],
            "scene_number": i + 1,
            "chapter_number": 1,
            "panel_path": panel_path
        }
        test_scenes.append(scene_data)
    
    return test_scenes


def test_sequence_coherence(panel_paths: List[str], scene_data: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Test coherence analysis on a specific sequence of panels."""
    
    print(f"🧪 Testing coherence analysis on {len(panel_paths)} panels...")
    
    # Validate panel paths
    valid_panels = []
    for panel_path in panel_paths:
        if Path(panel_path).exists():
            valid_panels.append(panel_path)
            print(f"   ✅ Found: {Path(panel_path).name}")
        else:
            print(f"   ❌ Missing: {panel_path}")
    
    if len(valid_panels) < 2:
        return {
            "error": f"Need at least 2 valid panels for testing (found {len(valid_panels)})",
            "valid_panels": len(valid_panels),
            "total_panels": len(panel_paths)
        }
    
    # Create test scene data if not provided
    if scene_data is None:
        print("📝 Creating test scene data...")
        scene_data = create_test_scene_data(valid_panels)
    
    # Initialize analyzers
    analyzer = CoherenceAnalyzer()
    thread_tracker = NarrativeThreadTracker()
    
    try:
        # Test visual coherence analysis
        print("\n🔍 Testing visual coherence analysis...")
        visual_result = analyzer.analyze_visual_coherence(valid_panels, [s["description"] for s in scene_data])
        print(f"   Visual coherence score: {visual_result.get('overall_coherence', {}).get('coherence_score', 0.0):.3f}")
        
        # Test narrative thread analysis
        print("\n📝 Testing narrative thread analysis...")
        thread_result = thread_tracker.generate_thread_report(scene_data)
        print(f"   Thread coherence score: {thread_result.get('thread_coherence_score', 0.0):.3f}")
        
        # Test full sequence analysis
        print("\n📊 Testing full sequence analysis...")
        full_result = analyzer.analyze_sequence_coherence(valid_panels, scene_data)
        print(f"   Overall coherence score: {full_result.get('coherence_score', 0.0):.3f}")
        
        # Compile test results
        test_results = {
            "test_timestamp": "2025-06-01T20:35:00",
            "panel_paths": valid_panels,
            "scene_count": len(scene_data),
            "visual_analysis": visual_result,
            "thread_analysis": thread_result,
            "full_analysis": full_result,
            "test_summary": {
                "visual_score": visual_result.get('overall_coherence', {}).get('coherence_score', 0.0),
                "thread_score": thread_result.get('thread_coherence_score', 0.0),
                "overall_score": full_result.get('coherence_score', 0.0),
                "recommend_review": full_result.get('recommend_human_review', False)
            }
        }
        
        return test_results
        
    except Exception as e:
        return {
            "error": f"Test failed: {e}",
            "panel_paths": valid_panels,
            "scene_count": len(scene_data) if scene_data else 0
        }


def run_test_scenarios():
    """Run predefined test scenarios to validate the system."""
    
    print("🧪 Running coherence evaluation test scenarios...\n")
    
    # Test Scenario 1: Visual mismatch
    print("📋 Test Scenario 1: Visual Mismatch Detection")
    test_scenes_1 = [
        {
            "description": "A samurai in a forest during daytime with bright sunlight",
            "dialogue": "The forest is peaceful today.",
            "emotion": "calm",
            "scene_number": 1,
            "chapter_number": 1,
            "panel_path": "test_panel_1.png"
        },
        {
            "description": "The same samurai suddenly in a dark cave at night",
            "dialogue": "How did I get here?",
            "emotion": "confused",
            "scene_number": 2,
            "chapter_number": 1,
            "panel_path": "test_panel_2.png"
        }
    ]
    
    analyzer = CoherenceAnalyzer()
    thread_tracker = NarrativeThreadTracker()
    
    # Test narrative analysis (doesn't require actual images)
    thread_result_1 = thread_tracker.generate_thread_report(test_scenes_1)
    print(f"   Thread coherence: {thread_result_1.get('thread_coherence_score', 0.0):.3f}")
    print(f"   Emotional flow: {thread_result_1.get('emotional_analysis', {}).get('emotional_flow', 'unknown')}")
    
    # Test Scenario 2: Dialogue flow broken
    print("\n📋 Test Scenario 2: Dialogue Flow Issues")
    test_scenes_2 = [
        {
            "description": "Two characters having a conversation",
            "dialogue": "Hello, how are you today?",
            "emotion": "friendly",
            "scene_number": 1,
            "chapter_number": 1,
            "panel_path": "test_panel_3.png"
        },
        {
            "description": "Same characters but completely different topic",
            "dialogue": "The weather on Mars is quite cold.",
            "emotion": "serious",
            "scene_number": 2,
            "chapter_number": 1,
            "panel_path": "test_panel_4.png"
        }
    ]
    
    thread_result_2 = thread_tracker.generate_thread_report(test_scenes_2)
    print(f"   Thread coherence: {thread_result_2.get('thread_coherence_score', 0.0):.3f}")
    print(f"   Speaker consistency: {thread_result_2.get('speaker_analysis', {}).get('speaker_consistency', False)}")
    
    # Test Scenario 3: Emotional inconsistency
    print("\n📋 Test Scenario 3: Emotional Inconsistency")
    test_scenes_3 = [
        {
            "description": "Character celebrating a victory",
            "dialogue": "We did it! We won!",
            "emotion": "joyful",
            "scene_number": 1,
            "chapter_number": 1,
            "panel_path": "test_panel_5.png"
        },
        {
            "description": "Same character immediately crying",
            "dialogue": "I'm so sad about everything.",
            "emotion": "devastated",
            "scene_number": 2,
            "chapter_number": 1,
            "panel_path": "test_panel_6.png"
        }
    ]
    
    thread_result_3 = thread_tracker.generate_thread_report(test_scenes_3)
    print(f"   Thread coherence: {thread_result_3.get('thread_coherence_score', 0.0):.3f}")
    print(f"   Emotional flow: {thread_result_3.get('emotional_analysis', {}).get('emotional_flow', 'unknown')}")
    
    # Test Scenario 4: Good coherence
    print("\n📋 Test Scenario 4: Good Coherence (Control)")
    test_scenes_4 = [
        {
            "description": "A warrior approaches a mountain temple",
            "dialogue": "I must reach the temple before sunset.",
            "emotion": "determined",
            "scene_number": 1,
            "chapter_number": 1,
            "panel_path": "test_panel_7.png"
        },
        {
            "description": "The warrior climbs the mountain path",
            "dialogue": "The path is steep, but I will persevere.",
            "emotion": "focused",
            "scene_number": 2,
            "chapter_number": 1,
            "panel_path": "test_panel_8.png"
        },
        {
            "description": "The warrior reaches the temple entrance",
            "dialogue": "Finally, I have arrived at the sacred temple.",
            "emotion": "relieved",
            "scene_number": 3,
            "chapter_number": 1,
            "panel_path": "test_panel_9.png"
        }
    ]
    
    thread_result_4 = thread_tracker.generate_thread_report(test_scenes_4)
    print(f"   Thread coherence: {thread_result_4.get('thread_coherence_score', 0.0):.3f}")
    print(f"   Character continuity: {thread_result_4.get('character_analysis', {}).get('character_continuity', False)}")
    print(f"   Emotional flow: {thread_result_4.get('emotional_analysis', {}).get('emotional_flow', 'unknown')}")
    
    print(f"\n✅ Test scenarios completed!")
    
    return {
        "scenario_1_visual_mismatch": thread_result_1,
        "scenario_2_dialogue_break": thread_result_2,
        "scenario_3_emotion_inconsistency": thread_result_3,
        "scenario_4_good_coherence": thread_result_4
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test narrative coherence evaluation on specific panel sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Test specific panel sequence
    python scripts/test_coherence_eval.py --seq "panel1.png" "panel2.png" "panel3.png"
    
    # Run predefined test scenarios
    python scripts/test_coherence_eval.py --test-scenarios
    
    # Test with custom scene data
    python scripts/test_coherence_eval.py --seq "panel1.png" "panel2.png" --scene-data scenes.json
        """
    )
    
    parser.add_argument(
        "--seq",
        nargs="+",
        help="Sequence of panel paths to test"
    )
    
    parser.add_argument(
        "--scene-data",
        help="JSON file with scene metadata (optional)"
    )
    
    parser.add_argument(
        "--test-scenarios",
        action="store_true",
        help="Run predefined test scenarios"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for test results (JSON)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.test_scenarios:
            # Run predefined test scenarios
            results = run_test_scenarios()
            
        elif args.seq:
            # Test specific sequence
            scene_data = None
            if args.scene_data and Path(args.scene_data).exists():
                with open(args.scene_data, 'r', encoding='utf-8') as f:
                    scene_data = json.load(f)
            
            results = test_sequence_coherence(args.seq, scene_data)
            
            # Print results
            if "error" not in results:
                summary = results.get("test_summary", {})
                print(f"\n🎯 Test Results:")
                print(f"   📊 Overall Score: {summary.get('overall_score', 0.0):.3f}")
                print(f"   👁️  Visual Score: {summary.get('visual_score', 0.0):.3f}")
                print(f"   🧵 Thread Score: {summary.get('thread_score', 0.0):.3f}")
                print(f"   🔍 Review Needed: {'Yes' if summary.get('recommend_review', False) else 'No'}")
            else:
                print(f"❌ Test failed: {results['error']}")
        
        else:
            parser.print_help()
            return 1
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2)
            print(f"📁 Test results saved: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
