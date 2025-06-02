#!/usr/bin/env python3
"""
Output Manager

Manages clean, organized output structure for manga generation pipeline.
Handles versioning, naming conventions, and prevents overwrites.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

class OutputManager:
    """Manages organized output structure for manga generation."""
    
    def __init__(self, base_output_dir: str = "outputs/runs"):
        """Initialize output manager."""
        self.base_dir = Path(base_output_dir)
        self.current_run_dir = None
        self.run_metadata = {}
        
        # Standard directory structure
        self.structure = {
            "panels": {
                "base": "Base panels (standard prompts)",
                "enhanced": "Enhanced panels (layout-enhanced prompts)"
            },
            "scene": {
                "panels": "Scene-aware panels with visual coherence",
                "metadata": "Scene metadata and character descriptors",
                "references": "Reference images for visual consistency"
            },
            "validation": {
                "logs": "Validation execution logs",
                "scores": "Coherence and quality scores",
                "reports": "Human-readable validation reports",
                "scene_reports": "Scene-specific validation reports"
            },
            "emotions": "Emotion extraction results",
            "metadata": "Run metadata and prompt mappings"
        }
    
    def create_new_run(self, run_name: Optional[str] = None) -> Path:
        """Create a new run directory with versioning."""
        
        if run_name is None:
            # Auto-generate run name with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_name = f"run_{timestamp}"
        
        # Check for existing runs and auto-increment if needed
        run_counter = 1
        original_run_name = run_name
        while (self.base_dir / run_name).exists():
            run_name = f"{original_run_name}_{run_counter:02d}"
            run_counter += 1
        
        # Create run directory
        self.current_run_dir = self.base_dir / run_name
        self.current_run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectory structure
        self._create_directory_structure()
        
        # Initialize metadata
        self.run_metadata = {
            "run_name": run_name,
            "created_at": datetime.now().isoformat(),
            "color_mode": "unknown",  # Will be updated when generation starts
            "structure": self.structure,
            "panel_mappings": {
                "base": {},
                "enhanced": {}
            },
            "validation_results": {},
            "emotion_results": {}
        }
        
        self._save_metadata()

        print(f"Created new run directory: {self.current_run_dir}")
        return self.current_run_dir

    def set_color_mode(self, color_mode: str):
        """Set the color mode for the current run."""
        if self.run_metadata:
            self.run_metadata["color_mode"] = color_mode
            self._save_metadata()
            print(f"Color mode set to: {color_mode}")
    
    def _create_directory_structure(self):
        """Create the standard directory structure."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")
        
        # Create panel directories
        (self.current_run_dir / "panels" / "base").mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "panels" / "enhanced").mkdir(parents=True, exist_ok=True)
        
        # Create validation directories
        (self.current_run_dir / "validation" / "logs").mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "validation" / "scores").mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "validation" / "reports").mkdir(parents=True, exist_ok=True)
        
        # Create other directories
        (self.current_run_dir / "emotions").mkdir(parents=True, exist_ok=True)
        (self.current_run_dir / "metadata").mkdir(parents=True, exist_ok=True)
    
    def get_panel_path(self, panel_type: str, panel_index: int, prompt_summary: Optional[str] = None) -> Path:
        """Get the path for a panel with proper naming."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")
        
        if panel_type not in ["base", "enhanced"]:
            raise ValueError(f"Invalid panel type: {panel_type}. Must be 'base' or 'enhanced'")
        
        # Create meaningful filename
        if prompt_summary:
            # Clean prompt summary for filename
            clean_summary = "".join(c for c in prompt_summary if c.isalnum() or c in " -_").strip()
            clean_summary = clean_summary.replace(" ", "_")[:50]  # Limit length
            filename = f"panel_{panel_index:03d}_{clean_summary}.png"
        else:
            filename = f"panel_{panel_index:03d}.png"
        
        panel_path = self.current_run_dir / "panels" / panel_type / filename
        
        # Store mapping in metadata
        self.run_metadata["panel_mappings"][panel_type][panel_index] = {
            "filename": filename,
            "prompt_summary": prompt_summary,
            "created_at": datetime.now().isoformat()
        }
        
        return panel_path
    
    def save_validation_results(self, results: Dict, result_type: str = "scores"):
        """Save validation results to appropriate directory."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if result_type == "scores":
            output_path = self.current_run_dir / "validation" / "scores" / f"validation_scores_{timestamp}.json"
        elif result_type == "logs":
            output_path = self.current_run_dir / "validation" / "logs" / f"validation_log_{timestamp}.txt"
        elif result_type == "reports":
            output_path = self.current_run_dir / "validation" / "reports" / f"validation_report_{timestamp}.md"
        else:
            output_path = self.current_run_dir / "validation" / f"{result_type}_{timestamp}.json"
        
        # Save results
        if output_path.suffix == ".json":
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                if isinstance(results, dict):
                    f.write(json.dumps(results, indent=2, ensure_ascii=False))
                else:
                    f.write(str(results))
        
        # Update metadata
        self.run_metadata["validation_results"][result_type] = {
            "file": str(output_path.relative_to(self.current_run_dir)),
            "saved_at": datetime.now().isoformat()
        }
        
        self._save_metadata()
        print(f"Saved validation {result_type}: {output_path}")
        return output_path
    
    def save_emotion_results(self, results: Dict) -> Path:
        """Save emotion extraction results."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")
        
        output_path = self.current_run_dir / "emotions" / "emotion_labels.json"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        # Update metadata
        self.run_metadata["emotion_results"] = {
            "file": str(output_path.relative_to(self.current_run_dir)),
            "saved_at": datetime.now().isoformat(),
            "total_lines": results.get("total_lines", 0)
        }
        
        self._save_metadata()
        print(f"Saved emotion results: {output_path}")
        return output_path

    def get_scene_panel_path(self, panel_index: int, scene_name: str) -> Path:
        """Get path for a scene panel."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")

        scene_panels_dir = self.current_run_dir / "scene" / "panels"
        scene_panels_dir.mkdir(parents=True, exist_ok=True)

        # Create meaningful filename
        clean_scene_name = "".join(c for c in scene_name if c.isalnum() or c in " -_").strip()
        clean_scene_name = clean_scene_name.replace(" ", "_")

        filename = f"scene_panel_{panel_index+1:03d}_{clean_scene_name}.png"
        return scene_panels_dir / filename

    def save_scene_metadata(self, scene_data: Dict[str, Any]) -> Path:
        """Save scene metadata and character descriptors."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")

        scene_metadata_dir = self.current_run_dir / "scene" / "metadata"
        scene_metadata_dir.mkdir(parents=True, exist_ok=True)

        # Save scene info
        scene_info_file = scene_metadata_dir / "scene_info.json"
        with open(scene_info_file, 'w') as f:
            json.dump(scene_data, f, indent=2)

        # Update run metadata
        self.run_metadata["scene_data"] = scene_data
        self._save_metadata()

        print(f"Saved scene metadata: {scene_info_file}")
        return scene_info_file

    def save_scene_validation_report(self, report_data: Dict[str, Any], report_name: str = "scene_validation_report") -> Path:
        """Save scene-specific validation report."""
        if not self.current_run_dir:
            raise ValueError("No current run directory set")

        scene_reports_dir = self.current_run_dir / "validation" / "scene_reports"
        scene_reports_dir.mkdir(parents=True, exist_ok=True)

        # Save as both JSON and markdown
        json_file = scene_reports_dir / f"{report_name}.json"
        md_file = scene_reports_dir / f"{report_name}.md"

        # Save JSON
        with open(json_file, 'w') as f:
            json.dump(report_data, f, indent=2)

        # Generate markdown report
        self._generate_scene_validation_markdown(report_data, md_file)

        print(f"Saved scene validation report: {md_file}")
        return md_file

    def _generate_scene_validation_markdown(self, report_data: Dict[str, Any], output_path: Path):
        """Generate markdown scene validation report."""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Scene Validation Report\n\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Scene overview
            scene_info = report_data.get("scene_info", {})
            f.write("## Scene Overview\n\n")
            f.write(f"- **Scene Name**: {scene_info.get('scene_name', 'Unknown')}\n")
            f.write(f"- **Panel Count**: {scene_info.get('panel_count', 0)}\n")
            f.write(f"- **Characters**: {len(scene_info.get('characters', []))}\n")
            f.write(f"- **Location**: {scene_info.get('settings', {}).get('location', 'Unknown')}\n")
            f.write(f"- **Color Mode**: {scene_info.get('color_mode', 'Unknown')}\n\n")

            # Visual consistency results
            consistency = report_data.get("visual_consistency", {})
            f.write("## Visual Consistency Analysis\n\n")
            f.write(f"- **Character Appearance**: {'✅ Consistent' if consistency.get('character_consistent', False) else '❌ Inconsistent'}\n")
            f.write(f"- **Background Continuity**: {'✅ Consistent' if consistency.get('background_consistent', False) else '❌ Inconsistent'}\n")
            f.write(f"- **Lighting Consistency**: {'✅ Consistent' if consistency.get('lighting_consistent', False) else '❌ Inconsistent'}\n")
            f.write(f"- **Art Style**: {'✅ Consistent' if consistency.get('style_consistent', False) else '❌ Inconsistent'}\n\n")

            # Coherence score
            coherence_score = report_data.get("coherence_score", 0.0)
            f.write("## Overall Coherence\n\n")
            f.write(f"**Score**: {coherence_score:.3f} / 1.000\n\n")

            if coherence_score >= 0.8:
                f.write("🎉 **Excellent coherence** - Scene flows naturally with strong visual consistency\n\n")
            elif coherence_score >= 0.6:
                f.write("✅ **Good coherence** - Scene has acceptable visual flow with minor inconsistencies\n\n")
            elif coherence_score >= 0.4:
                f.write("⚠️ **Fair coherence** - Scene has noticeable inconsistencies that may affect flow\n\n")
            else:
                f.write("❌ **Poor coherence** - Scene has significant visual inconsistencies\n\n")

            # Panel details
            panels = report_data.get("panels", [])
            if panels:
                f.write("## Panel Analysis\n\n")
                for i, panel in enumerate(panels):
                    f.write(f"### Panel {i+1}\n")
                    f.write(f"- **Prompt**: {panel.get('prompt', 'N/A')[:100]}...\n")
                    f.write(f"- **Character Focus**: {panel.get('character_focus', 'None')}\n")
                    f.write(f"- **Emotion**: {panel.get('emotion', 'neutral')}\n")
                    if panel.get('reference_image_path'):
                        f.write(f"- **Reference Used**: Yes\n")
                    f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")
            if coherence_score < 0.6:
                f.write("- Consider using stronger reference image influence\n")
                f.write("- Review character descriptor consistency\n")
                f.write("- Check lighting and setting prompts\n")
            else:
                f.write("- Scene coherence is acceptable\n")
                f.write("- Continue with current generation settings\n")
    
    def _save_metadata(self):
        """Save run metadata."""
        if not self.current_run_dir:
            return
        
        metadata_path = self.current_run_dir / "metadata" / "run_info.json"
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.run_metadata, f, indent=2, ensure_ascii=False)
    
    def get_run_summary(self) -> Dict:
        """Get summary of current run."""
        if not self.current_run_dir:
            return {"error": "No current run"}
        
        summary = {
            "run_directory": str(self.current_run_dir),
            "run_name": self.run_metadata.get("run_name", "unknown"),
            "created_at": self.run_metadata.get("created_at", "unknown"),
            "panels": {
                "base": len(self.run_metadata.get("panel_mappings", {}).get("base", {})),
                "enhanced": len(self.run_metadata.get("panel_mappings", {}).get("enhanced", {}))
            },
            "validation_files": len(self.run_metadata.get("validation_results", {})),
            "emotion_files": 1 if self.run_metadata.get("emotion_results") else 0
        }
        
        return summary
    
    def list_recent_runs(self, limit: int = 10) -> List[Dict]:
        """List recent runs with summaries."""
        runs = []
        
        if not self.base_dir.exists():
            return runs
        
        # Find all run directories
        run_dirs = [d for d in self.base_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        run_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        for run_dir in run_dirs[:limit]:
            metadata_file = run_dir / "metadata" / "run_info.json"
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    runs.append({
                        "run_name": metadata.get("run_name", run_dir.name),
                        "path": str(run_dir),
                        "created_at": metadata.get("created_at", "unknown"),
                        "panels_base": len(metadata.get("panel_mappings", {}).get("base", {})),
                        "panels_enhanced": len(metadata.get("panel_mappings", {}).get("enhanced", {}))
                    })
                except:
                    # Fallback for runs without metadata
                    runs.append({
                        "run_name": run_dir.name,
                        "path": str(run_dir),
                        "created_at": "unknown",
                        "panels_base": len(list((run_dir / "panels" / "base").glob("*.png"))) if (run_dir / "panels" / "base").exists() else 0,
                        "panels_enhanced": len(list((run_dir / "panels" / "enhanced").glob("*.png"))) if (run_dir / "panels" / "enhanced").exists() else 0
                    })
        
        return runs
    
    def cleanup_old_runs(self, keep_recent: int = 5):
        """Clean up old runs, keeping only the most recent ones."""
        runs = self.list_recent_runs(limit=100)  # Get all runs
        
        if len(runs) <= keep_recent:
            print(f"Only {len(runs)} runs found, no cleanup needed")
            return
        
        runs_to_delete = runs[keep_recent:]
        deleted_count = 0
        
        for run in runs_to_delete:
            run_path = Path(run["path"])
            if run_path.exists():
                try:
                    shutil.rmtree(run_path)
                    deleted_count += 1
                    print(f"Deleted old run: {run['run_name']}")
                except Exception as e:
                    print(f"Failed to delete {run['run_name']}: {e}")
        
        print(f"Cleanup complete: deleted {deleted_count} old runs, kept {keep_recent} recent runs")

def main():
    """Test the output manager."""
    manager = OutputManager()
    
    # Create a test run
    run_dir = manager.create_new_run("test_output_system")
    
    # Test panel paths
    base_path = manager.get_panel_path("base", 1, "ninja discovers temple")
    enhanced_path = manager.get_panel_path("enhanced", 1, "ninja discovers temple enhanced")
    
    print(f"Base panel path: {base_path}")
    print(f"Enhanced panel path: {enhanced_path}")
    
    # Test validation results
    test_results = {"coherence_score": 0.85, "test": True}
    manager.save_validation_results(test_results, "scores")
    
    # Test emotion results
    emotion_results = {"total_lines": 6, "emotions": ["happy", "sad"]}
    manager.save_emotion_results(emotion_results)
    
    # Get summary
    summary = manager.get_run_summary()
    print(f"Run summary: {summary}")

if __name__ == "__main__":
    main()
