import os
import sys
import cv2
import json
from typing import Dict, Any, List, Tuple
from pathlib import Path
from datetime import datetime

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from story_generator import StoryGenerator
from enhanced_panel_generator import EnhancedPanelGenerator

class MultiPanelGenerator:
    """
    Multi-panel manga generator with character consistency and story structure.
    
    Features:
    - Story-driven panel generation
    - Character consistency across panels
    - Enhanced prompt engineering
    - Quality validation per panel
    - Narrative flow optimization
    """
    
    def __init__(self):
        """Initialize the multi-panel generator."""
        self.story_generator = StoryGenerator()
        print("✅ Multi-panel generator initialized")
    
    def generate_complete_manga(
        self,
        user_prompt: str,
        style: str = "bw",
        panels: int = 4,
        output_dir: str = None
    ) -> Dict[str, Any]:
        """
        Generate a complete multi-panel manga from user prompt.
        
        Args:
            user_prompt: User's story idea
            style: "bw" or "color"
            panels: Number of panels (3-5)
            output_dir: Output directory path
            
        Returns:
            Complete manga generation results
        """
        print(f"\n🎨 GENERATING COMPLETE {panels}-PANEL MANGA")
        print(f"📝 Prompt: '{user_prompt}'")
        print(f"🎨 Style: {style}")
        print("=" * 60)
        
        # Create output directory
        if not output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = f"contest_package/output/manga_{timestamp}"
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize results tracking
        manga_results = {
            "user_prompt": user_prompt,
            "style": style,
            "target_panels": panels,
            "output_directory": str(output_path),
            "generation_timestamp": datetime.now().isoformat(),
            "story_data": None,
            "panels": [],
            "quality_metrics": {
                "successful_panels": 0,
                "quality_passed": 0,
                "dialogue_integrated": 0,
                "character_consistency_score": 0.0
            },
            "success": False
        }
        
        try:
            # Step 1: Generate story structure
            print("\n📖 Step 1: Generating story structure...")
            story_data = self.story_generator.generate_manga_story(user_prompt, panels)
            manga_results["story_data"] = story_data
            
            # Save story data
            story_path = output_path / "story_structure.json"
            with open(story_path, 'w', encoding='utf-8') as f:
                json.dump(story_data, f, indent=2)
            print(f"   📁 Story saved: {story_path}")
            
            # Step 2: Generate panels with enhanced prompts
            print(f"\n🎨 Step 2: Generating {panels} manga panels...")
            panel_generator = EnhancedPanelGenerator(style)
            
            for i, panel_data in enumerate(story_data["panels"]):
                panel_num = i + 1
                print(f"\n   📋 Panel {panel_num}/{panels}: {panel_data['narrative_purpose']}")
                
                # Create enhanced prompt with character consistency
                enhanced_prompt = self._build_character_consistent_prompt(
                    story_data["character"], panel_data, style
                )
                
                # Generate panel
                panel_output = output_path / f"panel_{panel_num:02d}.png"
                
                result = panel_generator.generate_quality_panel(
                    output_image=str(panel_output),
                    style=style,
                    emotion=panel_data["character_emotion"],
                    pose=panel_data["character_pose"],
                    dialogue_lines=panel_data["dialogue"],
                    scene_description=enhanced_prompt
                )
                
                # Track results
                panel_result = {
                    "panel_number": panel_num,
                    "panel_data": panel_data,
                    "enhanced_prompt": enhanced_prompt,
                    "generation_result": result,
                    "output_path": str(panel_output),
                    "file_exists": os.path.exists(panel_output),
                    "file_size": os.path.getsize(panel_output) if os.path.exists(panel_output) else 0
                }
                
                manga_results["panels"].append(panel_result)
                
                # Update quality metrics
                if result.get("success"):
                    manga_results["quality_metrics"]["successful_panels"] += 1
                    
                    validation = result.get("validation", {})
                    if validation.get("quality_passed"):
                        manga_results["quality_metrics"]["quality_passed"] += 1
                    
                    dialogue = result.get("dialogue", {})
                    if dialogue.get("dialogue_added"):
                        manga_results["quality_metrics"]["dialogue_integrated"] += 1
                
                # Print panel results
                if result.get("success"):
                    validation = result.get("validation", {})
                    dialogue = result.get("dialogue", {})
                    print(f"      ✅ Generated successfully")
                    print(f"      🔍 Quality: {'✅' if validation.get('quality_passed') else '⚠️'}")
                    print(f"      💬 Dialogue: {'✅' if dialogue.get('dialogue_added') else '⚠️'}")
                    if os.path.exists(panel_output):
                        size_mb = os.path.getsize(panel_output) / 1024 / 1024
                        print(f"      📁 File: {size_mb:.1f}MB")
                else:
                    print(f"      ❌ Generation failed: {result.get('error', 'Unknown error')}")
            
            # Step 3: Calculate character consistency
            print(f"\n🎭 Step 3: Analyzing character consistency...")
            consistency_score = self._analyze_character_consistency(manga_results["panels"])
            manga_results["quality_metrics"]["character_consistency_score"] = consistency_score
            print(f"   📊 Character consistency: {consistency_score:.2f}")
            
            # Step 4: Determine overall success
            metrics = manga_results["quality_metrics"]
            success_rate = metrics["successful_panels"] / panels
            quality_rate = metrics["quality_passed"] / panels
            dialogue_rate = metrics["dialogue_integrated"] / panels
            
            # Success criteria: ≥75% panels successful, ≥50% quality passed, ≥50% dialogue integrated
            manga_results["success"] = (
                success_rate >= 0.75 and
                quality_rate >= 0.5 and
                dialogue_rate >= 0.5 and
                consistency_score >= 0.6
            )
            
            # Save results
            results_path = output_path / "manga_results.json"
            with open(results_path, 'w', encoding='utf-8') as f:
                json.dump(manga_results, f, indent=2)
            
            # Print summary
            print(f"\n🎯 MANGA GENERATION SUMMARY")
            print("=" * 40)
            print(f"📊 Successful Panels: {metrics['successful_panels']}/{panels} ({success_rate:.1%})")
            print(f"🔍 Quality Passed: {metrics['quality_passed']}/{panels} ({quality_rate:.1%})")
            print(f"💬 Dialogue Integrated: {metrics['dialogue_integrated']}/{panels} ({dialogue_rate:.1%})")
            print(f"🎭 Character Consistency: {consistency_score:.2f}")
            print(f"📁 Output Directory: {output_path}")
            
            if manga_results["success"]:
                print(f"🎉 MANGA GENERATION: SUCCESS")
            else:
                print(f"⚠️ MANGA GENERATION: NEEDS IMPROVEMENT")
            
            return manga_results
            
        except Exception as e:
            print(f"❌ Manga generation failed: {e}")
            manga_results["error"] = str(e)
            return manga_results
    
    def _build_character_consistent_prompt(
        self, 
        character: Dict[str, Any], 
        panel_data: Dict[str, Any], 
        style: str
    ) -> str:
        """Build enhanced prompt with character consistency."""
        
        # Base character description
        char_desc = character["appearance"]
        char_name = character["name"]
        
        # Panel-specific details
        emotion = panel_data["character_emotion"]
        pose = panel_data["character_pose"]
        scene = panel_data["scene_description"]
        visual_prompt = panel_data["visual_prompt"]
        
        # Build comprehensive prompt
        enhanced_prompt = f"manga panel featuring {char_name}: {char_desc}"
        enhanced_prompt += f", showing {emotion} facial expression with {pose} body pose"
        enhanced_prompt += f", in scene: {scene}"
        enhanced_prompt += f", {visual_prompt}"
        
        # Add style-specific enhancements
        if style == "bw":
            enhanced_prompt += ", black and white manga style, detailed lineart, screentones"
            enhanced_prompt += ", high contrast shading, traditional manga artwork"
        else:
            enhanced_prompt += ", full color manga style, vibrant colors, detailed shading"
            enhanced_prompt += ", professional anime artwork, rich color palette"
        
        # Add quality modifiers
        enhanced_prompt += ", high quality character art, consistent character design"
        enhanced_prompt += ", clear facial features, proper anatomy, detailed background"
        enhanced_prompt += ", professional manga illustration, publication quality"
        
        return enhanced_prompt
    
    def _analyze_character_consistency(self, panels: List[Dict[str, Any]]) -> float:
        """Analyze character consistency across panels using basic metrics."""
        
        if len(panels) < 2:
            return 1.0
        
        # Simple consistency analysis based on file sizes and generation success
        successful_panels = [p for p in panels if p["generation_result"].get("success")]
        
        if len(successful_panels) < 2:
            return 0.5
        
        # Check file size consistency (similar sizes suggest similar content complexity)
        file_sizes = [p["file_size"] for p in successful_panels if p["file_size"] > 0]
        
        if not file_sizes:
            return 0.3
        
        # Calculate coefficient of variation for file sizes
        import statistics
        mean_size = statistics.mean(file_sizes)
        std_size = statistics.stdev(file_sizes) if len(file_sizes) > 1 else 0
        
        cv = std_size / mean_size if mean_size > 0 else 1.0
        
        # Lower coefficient of variation suggests more consistency
        consistency_score = max(0.0, 1.0 - cv)
        
        # Bonus for all panels being successful
        success_rate = len(successful_panels) / len(panels)
        consistency_score = (consistency_score + success_rate) / 2
        
        return min(1.0, consistency_score)
