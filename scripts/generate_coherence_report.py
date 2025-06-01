#!/usr/bin/env python3
"""
Coherence Report Generator

Generates comprehensive HTML and Markdown reports for narrative coherence analysis.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.eval_coherence import CoherenceEvaluator


class CoherenceReporter:
    """Generates comprehensive coherence analysis reports."""
    
    def __init__(self):
        self.evaluator = CoherenceEvaluator()
    
    def generate_markdown_report(self, coherence_results: Dict[str, Any], output_path: str):
        """Generate markdown coherence report."""
        
        summary = coherence_results.get("summary", {})
        thread_analysis = coherence_results.get("thread_analysis", {})
        sequence_results = coherence_results.get("sequence_results", [])
        
        title = Path(coherence_results.get("manga_directory", "Unknown")).name
        timestamp = coherence_results.get("analysis_timestamp", "Unknown")
        
        md_content = f"""# Narrative Coherence Report: {title}

**Analysis Date:** {timestamp}
**Overall Grade:** {summary.get('overall_grade', 'Unknown')} {summary.get('grade_emoji', '')}
**Coherence Score:** {summary.get('coherence_score', 0.0):.3f}
**Thread Quality:** {thread_analysis.get('thread_quality', 'Unknown')}

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Overall Coherence | {summary.get('coherence_score', 0.0):.3f} |
| Thread Score | {summary.get('thread_score', 0.0):.3f} |
| Total Sequences | {coherence_results.get('total_sequences', 0)} |
| Total Panels | {coherence_results.get('total_panels', 0)} |

## Sequence Quality Distribution

| Quality Level | Count |
|---------------|-------|
| 🌟 Excellent (≥0.8) | {summary.get('sequence_distribution', {}).get('excellent', 0)} |
| ✅ Good (0.6-0.8) | {summary.get('sequence_distribution', {}).get('good', 0)} |
| ⚠️ Poor (<0.6) | {summary.get('sequence_distribution', {}).get('poor', 0)} |

## Narrative Thread Analysis

### Speaker Analysis
- **Speakers Detected:** {', '.join(thread_analysis.get('speaker_analysis', {}).get('speakers_detected', []))}
- **Speaker Consistency:** {'✅ Yes' if thread_analysis.get('speaker_analysis', {}).get('speaker_consistency', False) else '❌ No'}
- **Dialogue Threading:** {thread_analysis.get('speaker_analysis', {}).get('dialogue_threading', 'Unknown')}

### Character Analysis
- **Characters Detected:** {', '.join(thread_analysis.get('character_analysis', {}).get('characters_detected', []))}
- **Character Continuity:** {'✅ Yes' if thread_analysis.get('character_analysis', {}).get('character_continuity', False) else '❌ No'}
- **Character Progression:** {thread_analysis.get('character_analysis', {}).get('character_progression', 'Unknown')}

### Emotional Analysis
- **Emotional Flow:** {thread_analysis.get('emotional_analysis', {}).get('emotional_flow', 'Unknown')}
- **Emotion Variety:** {thread_analysis.get('emotional_analysis', {}).get('emotion_variety', 'Unknown')}
- **Emotional Score:** {thread_analysis.get('emotional_analysis', {}).get('emotional_coherence_score', 0.0):.3f}

## Recommendations

"""
        
        # Add recommendations
        recommendations = coherence_results.get("recommendations", [])
        for i, rec in enumerate(recommendations, 1):
            md_content += f"{i}. {rec}\n"
        
        # Add sequence details
        md_content += "\n## Sequence Analysis Details\n\n"
        
        for seq in sequence_results[:10]:  # Limit to top 10 sequences
            seq_id = seq.get("sequence_id", "Unknown")
            score = seq.get("coherence_score", 0.0)
            assessment = seq.get("overall_assessment", "unknown")
            panel_range = seq.get("panel_range", "unknown")
            
            status_emoji = "🌟" if score >= 0.8 else "✅" if score >= 0.6 else "⚠️"
            
            md_content += f"### {status_emoji} Sequence {seq_id} (Panels {panel_range})\n"
            md_content += f"- **Score:** {score:.3f}\n"
            md_content += f"- **Assessment:** {assessment.title()}\n"
            
            # Add specific issues if any
            issues = seq.get("issues_detected", [])
            if issues:
                md_content += f"- **Issues:** {', '.join(issues)}\n"
            
            md_content += "\n"
        
        # Save markdown report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
        
        print(f"📄 Markdown report saved: {output_path}")
    
    def generate_html_report(self, coherence_results: Dict[str, Any], output_path: str):
        """Generate HTML coherence report with styling."""
        
        summary = coherence_results.get("summary", {})
        thread_analysis = coherence_results.get("thread_analysis", {})
        sequence_results = coherence_results.get("sequence_results", [])
        
        title = Path(coherence_results.get("manga_directory", "Unknown")).name
        grade_emoji = summary.get('grade_emoji', '❓')
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Narrative Coherence Report: {title}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; border-bottom: 2px solid #eee; padding-bottom: 20px; margin-bottom: 30px; }}
        .grade {{ font-size: 3em; margin: 20px 0; }}
        .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric-card {{ background: #f8f9fa; padding: 20px; border-radius: 8px; text-align: center; }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #333; border-bottom: 1px solid #ddd; padding-bottom: 10px; }}
        .sequence-card {{ background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #007bff; }}
        .thread-analysis {{ background: #e7f3ff; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .recommendation {{ background: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 4px solid #ffc107; }}
        .score-excellent {{ color: #28a745; }}
        .score-good {{ color: #007bff; }}
        .score-poor {{ color: #dc3545; }}
        .progress-bar {{ width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #dc3545 0%, #ffc107 50%, #28a745 100%); transition: width 0.3s; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Narrative Coherence Report</h1>
            <h2>{title}</h2>
            <div class="grade">{grade_emoji} {summary.get('overall_grade', 'Unknown')}</div>
            <p><strong>Coherence Score:</strong> {summary.get('coherence_score', 0.0):.3f}</p>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {summary.get('coherence_score', 0.0) * 100}%"></div>
            </div>
        </div>
        
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-value">{summary.get('coherence_score', 0.0):.3f}</div>
                <div class="metric-label">Overall Coherence</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{summary.get('thread_score', 0.0):.3f}</div>
                <div class="metric-label">Thread Quality</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{coherence_results.get('total_sequences', 0)}</div>
                <div class="metric-label">Sequences Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{coherence_results.get('total_panels', 0)}</div>
                <div class="metric-label">Total Panels</div>
            </div>
        </div>
        
        <div class="thread-analysis">
            <h2>🧵 Narrative Thread Analysis</h2>
            <div class="metric-grid">
                <div>
                    <h4>Speaker Analysis</h4>
                    <p><strong>Consistency:</strong> {'✅ Yes' if thread_analysis.get('speaker_analysis', {}).get('speaker_consistency', False) else '❌ No'}</p>
                    <p><strong>Threading:</strong> {thread_analysis.get('speaker_analysis', {}).get('dialogue_threading', 'Unknown')}</p>
                </div>
                <div>
                    <h4>Character Analysis</h4>
                    <p><strong>Continuity:</strong> {'✅ Yes' if thread_analysis.get('character_analysis', {}).get('character_continuity', False) else '❌ No'}</p>
                    <p><strong>Progression:</strong> {thread_analysis.get('character_analysis', {}).get('character_progression', 'Unknown')}</p>
                </div>
                <div>
                    <h4>Emotional Analysis</h4>
                    <p><strong>Flow:</strong> {thread_analysis.get('emotional_analysis', {}).get('emotional_flow', 'Unknown')}</p>
                    <p><strong>Score:</strong> {thread_analysis.get('emotional_analysis', {}).get('emotional_coherence_score', 0.0):.3f}</p>
                </div>
            </div>
        </div>
"""
        
        # Add recommendations
        recommendations = coherence_results.get("recommendations", [])
        if recommendations:
            html_content += """
        <div class="section">
            <h2>💡 Recommendations</h2>
"""
            for rec in recommendations:
                html_content += f'            <div class="recommendation">{rec}</div>\n'
            html_content += "        </div>\n"
        
        # Add sequence details
        html_content += """
        <div class="section">
            <h2>📊 Sequence Analysis</h2>
"""
        
        for seq in sequence_results[:10]:  # Limit to top 10
            seq_id = seq.get("sequence_id", "Unknown")
            score = seq.get("coherence_score", 0.0)
            assessment = seq.get("overall_assessment", "unknown")
            panel_range = seq.get("panel_range", "unknown")
            
            score_class = "score-excellent" if score >= 0.8 else "score-good" if score >= 0.6 else "score-poor"
            status_emoji = "🌟" if score >= 0.8 else "✅" if score >= 0.6 else "⚠️"
            
            html_content += f"""
            <div class="sequence-card">
                <h4>{status_emoji} Sequence {seq_id} (Panels {panel_range})</h4>
                <p><strong>Score:</strong> <span class="{score_class}">{score:.3f}</span></p>
                <p><strong>Assessment:</strong> {assessment.title()}</p>
"""
            
            # Add issues if any
            issues = seq.get("issues_detected", [])
            if issues:
                html_content += f"                <p><strong>Issues:</strong> {', '.join(issues)}</p>\n"
            
            html_content += "            </div>\n"
        
        html_content += """
        </div>
    </div>
</body>
</html>"""
        
        # Save HTML report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"🌐 HTML report saved: {output_path}")
    
    def generate_reports(self, manga_dir: str, output_dir: str = None) -> Dict[str, Any]:
        """Generate all coherence reports for a manga directory."""
        
        # Run coherence evaluation if results don't exist
        results_file = Path(manga_dir) / "coherence_results.json"
        
        if results_file.exists():
            print(f"📁 Loading existing coherence results...")
            with open(results_file, 'r', encoding='utf-8') as f:
                coherence_results = json.load(f)
        else:
            print(f"🔍 Running coherence analysis...")
            coherence_results = self.evaluator.evaluate_manga_coherence(manga_dir)
            
            # Save results
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(coherence_results, f, indent=2)
        
        # Determine output directory
        output_path = Path(output_dir) if output_dir else Path(manga_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate reports
        md_path = output_path / "coherence_report.md"
        html_path = output_path / "coherence_report.html"
        
        self.generate_markdown_report(coherence_results, str(md_path))
        self.generate_html_report(coherence_results, str(html_path))
        
        return {
            "coherence_results": coherence_results,
            "markdown_report": str(md_path),
            "html_report": str(html_path),
            "json_results": str(results_file)
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive narrative coherence reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python scripts/generate_coherence_report.py --input outputs/quality_manga_20250601_202543
    python scripts/generate_coherence_report.py --input outputs/final_manga_20250601_173550 --output coherence_reports/
        """
    )
    
    parser.add_argument(
        "--input",
        required=True,
        help="Path to manga output directory"
    )
    
    parser.add_argument(
        "--output",
        help="Output directory for reports (default: same as input)"
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize reporter
        reporter = CoherenceReporter()
        
        # Generate reports
        results = reporter.generate_reports(args.input, args.output)
        
        print(f"\n🎉 Coherence reports generated!")
        print(f"📊 Analysis results: {results['json_results']}")
        print(f"📄 Markdown report: {results['markdown_report']}")
        print(f"🌐 HTML report: {results['html_report']}")
        
        # Show summary
        coherence_results = results["coherence_results"]
        summary = coherence_results.get("summary", {})
        print(f"\n📈 Summary:")
        print(f"   {summary.get('grade_emoji', '❓')} Overall Grade: {summary.get('overall_grade', 'Unknown')}")
        print(f"   📊 Coherence Score: {summary.get('coherence_score', 0.0):.3f}")
        print(f"   🧵 Thread Score: {summary.get('thread_score', 0.0):.3f}")
        
        return 0
        
    except Exception as e:
        print(f"❌ Report generation failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
