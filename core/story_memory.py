"""
Story Memory System for Persistent Character and Plot Continuity

Manages story arcs, character development, and plot consistency across
multiple scenes and chapters in manga generation.
"""

import json
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict


@dataclass
class CharacterArc:
    """Character development arc across story."""
    character_name: str
    initial_state: str          # Starting character state/personality
    current_state: str          # Current character state
    development_goals: List[str] # Character growth objectives
    key_relationships: Dict[str, str] # Relationships with other characters
    emotional_journey: List[str] # Emotional progression through story
    appearance_changes: List[str] # Physical changes over time
    last_scene_appearance: Optional[str] = None


@dataclass
class PlotThread:
    """Individual plot thread or story arc."""
    thread_id: str
    thread_name: str
    description: str
    status: str                 # "active", "resolved", "paused"
    importance: str             # "main", "subplot", "background"
    introduced_scene: str       # Scene where thread was introduced
    key_events: List[str]       # Major events in this thread
    resolution_target: Optional[str] = None # Expected resolution scene


@dataclass
class StoryState:
    """Current state of the overall story."""
    story_id: str
    story_title: str
    current_chapter: int
    current_scene: int
    world_state: Dict[str, Any] # Current state of the story world
    active_conflicts: List[str] # Current unresolved conflicts
    established_facts: List[str] # Facts established in the story
    foreshadowing_elements: List[str] # Elements set up for future payoff


class StoryMemoryManager:
    """Manages persistent story memory across scenes and chapters."""
    
    def __init__(self, story_id: str = None, memory_dir: str = "outputs/story_memory"):
        """Initialize story memory manager."""
        self.memory_dir = Path(memory_dir)
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        self.story_id = story_id or str(uuid.uuid4())[:8]
        self.memory_file = self.memory_dir / f"story_{self.story_id}.json"
        
        # Initialize story components
        self.story_state = None
        self.character_arcs = {}
        self.plot_threads = {}
        self.scene_history = []
        self.continuity_rules = {}
        
        # Load existing memory if available
        self._load_memory()
    
    def initialize_story(
        self,
        story_title: str,
        main_characters: List[str],
        main_plot: str,
        setting: Dict[str, Any]
    ) -> str:
        """
        Initialize a new story with basic setup.
        
        Args:
            story_title: Title of the story
            main_characters: List of main character names
            main_plot: Main plot description
            setting: Story setting information
            
        Returns:
            Story ID for tracking
        """
        print(f"📚 Initializing story: {story_title}")
        
        # Create story state
        self.story_state = StoryState(
            story_id=self.story_id,
            story_title=story_title,
            current_chapter=1,
            current_scene=1,
            world_state=setting,
            active_conflicts=[main_plot],
            established_facts=[],
            foreshadowing_elements=[]
        )
        
        # Initialize character arcs
        for char_name in main_characters:
            self.character_arcs[char_name] = CharacterArc(
                character_name=char_name,
                initial_state="introduced",
                current_state="introduced",
                development_goals=[],
                key_relationships={},
                emotional_journey=["introduction"],
                appearance_changes=[]
            )
        
        # Create main plot thread
        main_thread = PlotThread(
            thread_id="main_plot",
            thread_name="Main Story",
            description=main_plot,
            status="active",
            importance="main",
            introduced_scene="scene_1_1",
            key_events=[]
        )
        self.plot_threads["main_plot"] = main_thread
        
        # Save initial state
        self._save_memory()
        
        print(f"   ✅ Story initialized with {len(main_characters)} characters")
        return self.story_id
    
    def add_scene_memory(
        self,
        scene_name: str,
        scene_summary: str,
        characters_present: List[str],
        plot_developments: List[str],
        new_facts: List[str] = None,
        character_changes: Dict[str, str] = None
    ):
        """
        Add memory from a completed scene.
        
        Args:
            scene_name: Name/ID of the scene
            scene_summary: Brief summary of what happened
            characters_present: Characters who appeared in scene
            plot_developments: Plot points that advanced
            new_facts: New facts established in this scene
            character_changes: Character state changes
        """
        print(f"   📝 Recording scene memory: {scene_name}")
        
        scene_memory = {
            "scene_name": scene_name,
            "scene_summary": scene_summary,
            "characters_present": characters_present,
            "plot_developments": plot_developments,
            "new_facts": new_facts or [],
            "character_changes": character_changes or {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to scene history
        self.scene_history.append(scene_memory)
        
        # Update story state
        if self.story_state:
            self.story_state.current_scene += 1
            if new_facts:
                self.story_state.established_facts.extend(new_facts)
        
        # Update character arcs
        if character_changes:
            for char_name, change in character_changes.items():
                if char_name in self.character_arcs:
                    self.character_arcs[char_name].current_state = change
                    self.character_arcs[char_name].last_scene_appearance = scene_name
        
        # Update plot threads
        for development in plot_developments:
            for thread_id, thread in self.plot_threads.items():
                if thread.status == "active":
                    thread.key_events.append(f"{scene_name}: {development}")
        
        self._save_memory()
    
    def get_character_context(self, character_name: str) -> Dict[str, Any]:
        """Get current context for a character."""
        if character_name not in self.character_arcs:
            return {"error": f"Character {character_name} not found in story memory"}
        
        arc = self.character_arcs[character_name]
        
        # Get recent appearances
        recent_scenes = [
            scene for scene in self.scene_history[-5:]  # Last 5 scenes
            if character_name in scene["characters_present"]
        ]
        
        return {
            "character_name": character_name,
            "current_state": arc.current_state,
            "emotional_journey": arc.emotional_journey,
            "key_relationships": arc.key_relationships,
            "recent_appearances": recent_scenes,
            "development_goals": arc.development_goals,
            "last_appearance": arc.last_scene_appearance
        }
    
    def get_story_context(self) -> Dict[str, Any]:
        """Get current story context for scene generation."""
        if not self.story_state:
            return {"error": "No story initialized"}
        
        # Get active plot threads
        active_threads = {
            thread_id: thread for thread_id, thread in self.plot_threads.items()
            if thread.status == "active"
        }
        
        # Get recent story developments
        recent_developments = []
        for scene in self.scene_history[-3:]:  # Last 3 scenes
            recent_developments.extend(scene["plot_developments"])
        
        return {
            "story_title": self.story_state.story_title,
            "current_chapter": self.story_state.current_chapter,
            "current_scene": self.story_state.current_scene,
            "world_state": self.story_state.world_state,
            "active_conflicts": self.story_state.active_conflicts,
            "established_facts": self.story_state.established_facts[-10:],  # Last 10 facts
            "active_plot_threads": list(active_threads.keys()),
            "recent_developments": recent_developments,
            "total_scenes": len(self.scene_history)
        }
    
    def generate_continuity_prompt(self, new_scene_description: str) -> str:
        """Generate continuity-aware prompt for new scene."""
        story_context = self.get_story_context()

        if "error" in story_context:
            print("   📝 No story context available - using base prompt")
            return new_scene_description

        print(f"   📚 Generating continuity prompt using story memory")
        
        # Build continuity elements
        continuity_parts = []
        used_elements = []

        # Add established facts
        if story_context["established_facts"]:
            facts_text = ", ".join(story_context["established_facts"][-3:])
            continuity_parts.append(f"maintaining story continuity: {facts_text}")
            used_elements.append(f"facts: {story_context['established_facts'][-3:]}")

        # Add world state
        if story_context["world_state"]:
            world_elements = []
            for key, value in story_context["world_state"].items():
                if isinstance(value, str):
                    world_elements.append(f"{key}: {value}")
            if world_elements:
                continuity_parts.append(f"world state: {', '.join(world_elements[:2])}")
                used_elements.append(f"world_state: {world_elements[:2]}")

        # Add recent developments context
        if story_context["recent_developments"]:
            recent_text = story_context["recent_developments"][-1]
            continuity_parts.append(f"following previous events: {recent_text}")
            used_elements.append(f"recent_events: {recent_text}")

        # Log what memory elements were used
        if used_elements:
            print(f"   🧠 Memory elements used: {', '.join(used_elements)}")
        else:
            print("   ⚠️  No memory elements available for continuity")
        
        # Combine with new scene
        if continuity_parts:
            continuity_text = ", ".join(continuity_parts)
            enhanced_prompt = f"{new_scene_description}, {continuity_text}, consistent story progression"
        else:
            enhanced_prompt = new_scene_description
        
        return enhanced_prompt
    
    def _load_memory(self):
        """Load existing story memory from file."""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    data = json.load(f)
                
                # Restore story state
                if "story_state" in data:
                    state_data = data["story_state"]
                    self.story_state = StoryState(**state_data)
                
                # Restore character arcs
                if "character_arcs" in data:
                    for char_name, arc_data in data["character_arcs"].items():
                        self.character_arcs[char_name] = CharacterArc(**arc_data)
                
                # Restore plot threads
                if "plot_threads" in data:
                    for thread_id, thread_data in data["plot_threads"].items():
                        self.plot_threads[thread_id] = PlotThread(**thread_data)
                
                # Restore scene history
                self.scene_history = data.get("scene_history", [])
                self.continuity_rules = data.get("continuity_rules", {})
                
                print(f"   📚 Loaded story memory: {len(self.scene_history)} scenes")
                
            except Exception as e:
                print(f"   ⚠️ Could not load story memory: {e}")
    
    def _save_memory(self):
        """Save current story memory to file."""
        data = {
            "story_id": self.story_id,
            "story_state": asdict(self.story_state) if self.story_state else None,
            "character_arcs": {name: asdict(arc) for name, arc in self.character_arcs.items()},
            "plot_threads": {id: asdict(thread) for id, thread in self.plot_threads.items()},
            "scene_history": self.scene_history,
            "continuity_rules": self.continuity_rules,
            "last_updated": datetime.now().isoformat()
        }
        
        with open(self.memory_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """Get summary of current story memory."""
        return {
            "story_id": self.story_id,
            "story_title": self.story_state.story_title if self.story_state else "Unknown",
            "total_scenes": len(self.scene_history),
            "character_count": len(self.character_arcs),
            "active_plot_threads": len([t for t in self.plot_threads.values() if t.status == "active"]),
            "memory_file": str(self.memory_file)
        }


def create_sample_story() -> Tuple[str, List[str], str, Dict[str, Any]]:
    """Create sample story data for testing."""
    return (
        "Temple of Shadows",
        ["ninja", "guardian", "master"],
        "Young ninja must prove worthy to ancient temple guardian",
        {
            "location": "ancient temple complex",
            "time_period": "feudal era",
            "magical_elements": "ancient spirits",
            "danger_level": "moderate"
        }
    )


if __name__ == "__main__":
    # Test story memory system
    memory_manager = StoryMemoryManager()
    
    # Initialize sample story
    title, characters, plot, setting = create_sample_story()
    story_id = memory_manager.initialize_story(title, characters, plot, setting)
    
    # Add sample scene
    memory_manager.add_scene_memory(
        scene_name="temple_entrance",
        scene_summary="Ninja approaches the ancient temple",
        characters_present=["ninja"],
        plot_developments=["ninja begins quest"],
        new_facts=["temple is heavily guarded", "entrance has mystical symbols"],
        character_changes={"ninja": "determined"}
    )
    
    # Test context retrieval
    story_context = memory_manager.get_story_context()
    char_context = memory_manager.get_character_context("ninja")
    
    print(f"Story context: {story_context['story_title']}")
    print(f"Character state: {char_context['current_state']}")
    print(f"Memory summary: {memory_manager.get_memory_summary()}")
