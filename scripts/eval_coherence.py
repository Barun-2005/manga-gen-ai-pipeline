#!/usr/bin/env python3
"""
Narrative Coherence Evaluator

Main script for analyzing narrative coherence across sequential manga panels.
Combines visual and narrative analysis using VLM and local NLP models.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.coherence_analyzer import CoherenceAnalyzer
from scripts.narrative_thread_tracker import NarrativeThreadTracker


class CoherenceEvaluator:
    """Main coherence evaluation orchestrator."""
    
    def __init__(self):
        self.analyzer = CoherenceAnalyzer()
        self.thread_tracker = NarrativeThreadTracker()
    
    def load_manga_data(self, manga_dir: str) -> Tuple[List[str], List[Dict[str, Any]]]:
        """
        Load manga panel paths and scene data from manga directory.
        
        Args:
            manga_dir: Path to manga output directory
            
        Returns:
            Tuple of (panel_paths, scene_data)
        """
        
        manga_path = Path(manga_dir)
        
        # Load manga results
        results_file = manga_path / "manga_results.json"
        if not results_file.exists():
            raise FileNotFoundError(f"manga_results.json not found in {manga_dir}")
        
        with open(results_file, 'r', encoding='utf-8') as f:
            manga_results = json.load(f)
        
        # Extract panel paths and scene data
        panel_paths = []
        scene_data = []
        
        for chapter in manga_results.get("chapters", []):
            for scene in chapter.get("scenes", []):
                # Prefer bubble panel (final output) over original panel
                bubble_path = scene.get("bubble_panel_path", "")
                original_path = scene.get("panel_path", "")
                
                # Check for moved bubble panel (after cleanup)
                if bubble_path and not Path(bubble_path).exists():
                    moved_bubble_path = bubble_path.replace("\\with_bubbles\\", "\\").replace("/with_bubbles/", "/")
                    if Path(moved_bubble_path).exists():
                        bubble_path = moved_bubble_path
                
                # Use bubble panel if available, otherwise original
                panel_path = bubble_path if bubble_path and Path(bubble_path).exists() else original_path
                
                if panel_path and Path(panel_path).exists():
                    panel_paths.append(panel_path)
                    scene_data.append({
                        "description": scene.get("description", ""),
                        "dialogue": scene.get("dialogue", ""),
                        "emotion": scene.get("emotion", "neutral"),
                        "scene_number": scene.get("scene_number", 0),
                        "chapter_number": chapter.get("chapter_number", 0),
                        "panel_path": panel_path
                    })
                else:
                    print(f"⚠️  Panel not found: {panel_path}")
        
        return panel_paths, scene_data
    
    def create_sequences(self, panel_paths: List[str], scene_data: List[Dict[str, Any]], 
                        sequence_length: int = 3) -> List[Tuple[List[str], List[Dict[str, Any]]]]:
        """
        Create overlapping sequences of panels for coherence analysis.
        
        Args:
            panel_paths: List of all panel paths
            scene_data: List of all scene data
            sequence_length: Length of each sequence (3-5 panels)
            
        Returns:
            List of (panel_sequence, scene_sequence) tuples
        """
        
        sequences = []
        
        # Create overlapping sequences
        for i in range(len(panel_paths) - sequence_length + 1):
            panel_seq = panel_paths[i:i + sequence_length]
            scene_seq = scene_data[i:i + sequence_length]
            sequences.append((panel_seq, scene_seq))
        
        # If we have fewer panels than sequence_length, use all available
        if len(panel_paths) < sequence_length and len(panel_paths) >= 2:
            sequences.append((panel_paths, scene_data))
        
        return sequences
    
    def evaluate_manga_coherence(self, manga_dir: str, sequence_length: int = 3) -> Dict[str, Any]:
        """
        Evaluate coherence across entire manga.
        
        Args:
            manga_dir: Path to manga output directory
            sequence_length: Length of sequences to analyze (3-5)
            
        Returns:
            Complete coherence evaluation results
        """
        
        print(f"🎯 Evaluating narrative coherence for: {manga_dir}")
        print(f"📏 Sequence length: {sequence_length} panels")
        
        # Load manga data
        try:
            panel_paths, scene_data = self.load_manga_data(manga_dir)
            print(f"📊 Loaded {len(panel_paths)} panels for analysis")
        except Exception as e:
            return {
                "error": f"Failed to load manga data: {e}",
                "coherence_score": 0.0,
                "analysis_timestamp": datetime.now().isoformat()
            }
        
        if len(panel_paths) < 2:
            return {
                "error": "Need at least 2 panels for coherence analysis",
                "coherence_score": 0.0,
                "panel_count": len(panel_paths)
            }
        
        # Create sequences
        sequences = self.create_sequences(panel_paths, scene_data, sequence_length)
        print(f"🔍 Created {len(sequences)} sequences for analysis")
        
        # Analyze each sequence
        sequence_results = []
        total_coherence = 0.0
        
        for i, (panel_seq, scene_seq) in enumerate(sequences):
            print(f"\n📋 Analyzing sequence {i+1}/{len(sequences)}...")
            
            try:
                # Analyze sequence coherence
                coherence_result = self.analyzer.analyze_sequence_coherence(panel_seq, scene_seq)
                coherence_result["sequence_id"] = i + 1
                coherence_result["panel_range"] = f"{scene_seq[0]['scene_number']}-{scene_seq[-1]['scene_number']}"
                
                sequence_results.append(coherence_result)
                total_coherence += coherence_result.get("coherence_score", 0.0)
                
                print(f"   ✅ Sequence {i+1} coherence: {coherence_result.get('coherence_score', 0.0):.3f}")
                
            except Exception as e:
                print(f"   ❌ Sequence {i+1} analysis failed: {e}")
                sequence_results.append({
                    "sequence_id": i + 1,
                    "error": str(e),
                    "coherence_score": 0.0
                })
        
        # Calculate overall coherence
        avg_coherence = total_coherence / len(sequences) if sequences else 0.0
        
        # Analyze narrative threads across entire manga
        print(f"\n📝 Analyzing narrative threads...")
        thread_analysis = self.thread_tracker.generate_thread_report(scene_data)
        
        # Combine results
        overall_results = {
            "manga_directory": manga_dir,
            "analysis_timestamp": datetime.now().isoformat(),
            "overall_coherence_score": round(avg_coherence, 3),
            "sequence_length": sequence_length,
            "total_sequences": len(sequences),
            "total_panels": len(panel_paths),
            "sequence_results": sequence_results,
            "thread_analysis": thread_analysis,
            "summary": self._generate_summary(avg_coherence, sequence_results, thread_analysis),
            "recommendations": self._generate_recommendations(sequence_results, thread_analysis)
        }
        
        return overall_results
    
    def _generate_summary(self, avg_coherence: float, sequence_results: List[Dict[str, Any]], 
                         thread_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary of coherence analysis."""
        
        # Count sequences by quality
        excellent_sequences = sum(1 for seq in sequence_results if seq.get("coherence_score", 0) >= 0.8)
        good_sequences = sum(1 for seq in sequence_results if 0.6 <= seq.get("coherence_score", 0) < 0.8)
        poor_sequences = sum(1 for seq in sequence_results if seq.get("coherence_score", 0) < 0.6)
        
        # Determine overall grade
        if avg_coherence >= 0.8:
            grade = "Excellent"
            grade_emoji = "🌟"
        elif avg_coherence >= 0.6:
            grade = "Good"
            grade_emoji = "✅"
        elif avg_coherence >= 0.4:
            grade = "Fair"
            grade_emoji = "⚠️"
        else:
            grade = "Poor"
            grade_emoji = "❌"
        
        # Thread quality
        thread_score = thread_analysis.get("thread_coherence_score", 0.0)
        thread_quality = thread_analysis.get("thread_quality", "unknown")
        
        return {
            "overall_grade": grade,
            "grade_emoji": grade_emoji,
            "coherence_score": avg_coherence,
            "thread_score": thread_score,
            "thread_quality": thread_quality,
            "sequence_distribution": {
                "excellent": excellent_sequences,
                "good": good_sequences,
                "poor": poor_sequences
            },
            "visual_consistency": sum(1 for seq in sequence_results 
                                    if seq.get("visual_consistency", {}).get("background_continuity", False)),
            "dialogue_flow_good": sum(1 for seq in sequence_results 
                                    if seq.get("dialogue_flow") == "natural"),
            "recommend_human_review": avg_coherence < 0.6 or thread_score < 0.6
        }
    
    def _generate_recommendations(self, sequence_results: List[Dict[str, Any]], 
                                thread_analysis: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations."""
        
        recommendations = []
        
        # Check for visual issues
        visual_issues = sum(1 for seq in sequence_results 
                          if not seq.get("visual_consistency", {}).get("background_continuity", True))
        if visual_issues > 0:
            recommendations.append(f"{visual_issues} sequences have visual continuity issues")
        
        # Check for dialogue issues
        dialogue_issues = sum(1 for seq in sequence_results 
                            if seq.get("dialogue_flow") in ["confused", "unclear"])
        if dialogue_issues > 0:
            recommendations.append(f"{dialogue_issues} sequences have dialogue flow problems")
        
        # Check thread analysis
        if not thread_analysis.get("speaker_analysis", {}).get("speaker_consistency", True):
            recommendations.append("Speaker consistency issues detected across narrative")
        
        if not thread_analysis.get("character_analysis", {}).get("character_continuity", True):
            recommendations.append("Character continuity breaks detected")
        
        emotional_flow = thread_analysis.get("emotional_analysis", {}).get("emotional_flow", "")
        if emotional_flow == "jarring":
            recommendations.append("Emotional transitions are too abrupt")
        
        # Overall recommendations
        avg_score = sum(seq.get("coherence_score", 0) for seq in sequence_results) / len(sequence_results) if sequence_results else 0
        if avg_score < 0.4:
            recommendations.append("Overall coherence is poor - consider major revisions")
        elif avg_score < 0.6:
            recommendations.append("Moderate coherence issues - review flagged sequences")
        
        if not recommendations:
            recommendations.append("Narrative coherence is good - no major issues detected")
        
        return recommendations


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate narrative coherence across manga sequences",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/eval_coherence.py outputs/quality_manga_20250601_202543
    python scripts/eval_coherence.py outputs/final_manga_20250601_173550 --sequence-length 5
        """
    )
    
    parser.add_argument(
        "manga_dir",
        help="Path to manga output directory"
    )
    
    parser.add_argument(
        "--sequence-length",
        type=int,
        default=3,
        choices=[3, 4, 5],
        help="Length of sequences to analyze (3-5 panels, default: 3)"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for coherence results (default: coherence_results.json in manga dir)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize evaluator
        evaluator = CoherenceEvaluator()
        
        # Evaluate coherence
        results = evaluator.evaluate_manga_coherence(args.manga_dir, args.sequence_length)
        
        # Save results
        output_file = args.output or Path(args.manga_dir) / "coherence_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        summary = results.get("summary", {})
        print(f"\n🎯 Narrative Coherence Analysis Complete!")
        print(f"   {summary.get('grade_emoji', '❓')} Overall Grade: {summary.get('overall_grade', 'Unknown')}")
        print(f"   📊 Coherence Score: {summary.get('coherence_score', 0.0):.3f}")
        print(f"   🧵 Thread Score: {summary.get('thread_score', 0.0):.3f}")
        print(f"   📁 Results saved: {output_file}")
        
        # Show recommendations
        recommendations = results.get("recommendations", [])
        if recommendations:
            print(f"\n💡 Recommendations:")
            for rec in recommendations[:3]:  # Show top 3
                print(f"   • {rec}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Coherence evaluation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
