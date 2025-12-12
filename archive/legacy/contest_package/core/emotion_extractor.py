#!/usr/bin/env python3
"""
Phase 7: Emotion Extraction Module
Lightweight emotion extraction using sentiment analysis and facial keyword detection.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

class EmotionExtractor:
    """Extracts emotions from manga-style dialogue using sentiment and keyword analysis."""
    
    def __init__(self):
        """Initialize the emotion extractor."""
        self.emotion_keywords = {
            "angry": [
                "damn", "hell", "stupid", "idiot", "hate", "furious", "mad", "rage", "pissed",
                "annoying", "irritating", "grr", "argh", "bastard", "shut up", "get lost"
            ],
            "sad": [
                "cry", "tears", "sob", "weep", "depressed", "miserable", "heartbroken",
                "lonely", "sorry", "regret", "miss", "lost", "hurt", "pain", "sigh"
            ],
            "happy": [
                "smile", "laugh", "joy", "excited", "wonderful", "amazing", "great",
                "awesome", "love", "perfect", "fantastic", "brilliant", "yay", "hooray"
            ],
            "surprised": [
                "what", "huh", "wow", "oh", "really", "seriously", "no way", "incredible",
                "unbelievable", "shocking", "gasp", "whoa", "omg", "amazing"
            ],
            "scared": [
                "afraid", "fear", "terrified", "scared", "frightened", "nervous", "worried",
                "panic", "help", "run", "hide", "monster", "ghost", "danger", "eek"
            ],
            "confused": [
                "confused", "don't understand", "what do you mean", "huh", "puzzled",
                "lost", "unclear", "explain", "how", "why", "strange", "weird"
            ],
            "determined": [
                "will", "must", "have to", "determined", "fight", "never give up",
                "strong", "power", "victory", "win", "overcome", "challenge"
            ],
            "neutral": [
                "okay", "yes", "no", "maybe", "perhaps", "think", "know", "see",
                "understand", "right", "well", "so", "then", "now"
            ]
        }
        
        # Punctuation-based emotion indicators
        self.punctuation_emotions = {
            "!": "excited",
            "?!": "surprised", 
            "...": "sad",
            "!!": "angry",
            "???": "confused"
        }
        
    def analyze_sentiment_basic(self, text: str) -> str:
        """Basic sentiment analysis using keyword matching."""
        text_lower = text.lower()
        
        # Count emotion keywords
        emotion_scores = {}
        for emotion, keywords in self.emotion_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                emotion_scores[emotion] = score
        
        # Check punctuation patterns
        for punct, emotion in self.punctuation_emotions.items():
            if punct in text:
                emotion_scores[emotion] = emotion_scores.get(emotion, 0) + 1
        
        # Return highest scoring emotion or neutral
        if emotion_scores:
            return max(emotion_scores.items(), key=lambda x: x[1])[0]
        else:
            return "neutral"
    
    def extract_dialogue_emotion(self, dialogue_line: str) -> Dict[str, Any]:
        """Extract emotion from a single dialogue line."""
        
        # Clean the dialogue
        cleaned_dialogue = dialogue_line.strip()
        if not cleaned_dialogue:
            return {
                "line": dialogue_line,
                "emotion": "neutral",
                "confidence": 0.0,
                "keywords_found": [],
                "method": "empty_line"
            }
        
        # Extract emotion
        emotion = self.analyze_sentiment_basic(cleaned_dialogue)
        
        # Find matching keywords
        keywords_found = []
        text_lower = cleaned_dialogue.lower()
        if emotion in self.emotion_keywords:
            keywords_found = [kw for kw in self.emotion_keywords[emotion] if kw in text_lower]
        
        # Calculate confidence based on keyword matches and punctuation
        confidence = 0.5  # Base confidence
        if keywords_found:
            confidence += 0.3 * len(keywords_found)
        
        # Boost confidence for punctuation matches
        for punct in self.punctuation_emotions:
            if punct in cleaned_dialogue:
                confidence += 0.2
        
        confidence = min(1.0, confidence)  # Cap at 1.0
        
        return {
            "line": dialogue_line,
            "emotion": emotion,
            "confidence": round(confidence, 2),
            "keywords_found": keywords_found,
            "method": "keyword_sentiment"
        }
    
    def extract_from_dialogue_list(self, dialogue_lines: List[str]) -> List[Dict[str, Any]]:
        """Extract emotions from a list of dialogue lines."""
        
        results = []
        for i, line in enumerate(dialogue_lines):
            emotion_data = self.extract_dialogue_emotion(line)
            emotion_data["line_index"] = i
            results.append(emotion_data)
        
        return results
    
    def extract_from_manga_data(self, manga_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract emotions from manga generation data."""
        
        print("🎭 Extracting emotions from manga data...")
        
        # Extract dialogue from various possible formats
        dialogue_lines = []
        
        # Check for story structure
        if "story_structure" in manga_data:
            story = manga_data["story_structure"]
            if isinstance(story, dict) and "scenes" in story:
                for scene in story["scenes"]:
                    if "dialogue" in scene:
                        dialogue_lines.append(scene["dialogue"])
        
        # Check for direct dialogue list
        if "dialogue" in manga_data:
            if isinstance(manga_data["dialogue"], list):
                dialogue_lines.extend(manga_data["dialogue"])
            else:
                dialogue_lines.append(str(manga_data["dialogue"]))
        
        # Check for scenes with dialogue
        if "scenes" in manga_data:
            for scene in manga_data["scenes"]:
                if isinstance(scene, dict) and "dialogue" in scene:
                    dialogue_lines.append(scene["dialogue"])
        
        # Extract emotions
        emotion_results = self.extract_from_dialogue_list(dialogue_lines)
        
        # Calculate summary statistics
        emotions_found = [r["emotion"] for r in emotion_results]
        emotion_counts = {}
        for emotion in emotions_found:
            emotion_counts[emotion] = emotion_counts.get(emotion, 0) + 1
        
        avg_confidence = sum(r["confidence"] for r in emotion_results) / len(emotion_results) if emotion_results else 0.0
        
        return {
            "extraction_timestamp": datetime.now().isoformat(),
            "total_lines": len(dialogue_lines),
            "emotions_extracted": len(emotion_results),
            "emotion_distribution": emotion_counts,
            "average_confidence": round(avg_confidence, 2),
            "dialogue_emotions": emotion_results,
            "method": "keyword_sentiment_analysis"
        }
    
    def save_emotion_results(self, emotion_data: Dict[str, Any], output_file: str):
        """Save emotion extraction results to JSON file."""
        
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(emotion_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Emotion results saved to: {output_path}")
    
    def process_manga_directory(self, manga_dir: str) -> Optional[Dict[str, Any]]:
        """Process a manga directory and extract emotions."""
        
        manga_path = Path(manga_dir)
        if not manga_path.exists():
            print(f"❌ Manga directory not found: {manga_dir}")
            return None
        
        # Look for manga results file
        results_file = manga_path / "manga_results.json"
        story_file = manga_path / "story_structure.json"
        
        manga_data = {}
        
        # Load manga results
        if results_file.exists():
            try:
                with open(results_file, 'r', encoding='utf-8') as f:
                    manga_data.update(json.load(f))
            except Exception as e:
                print(f"⚠️  Error loading manga results: {e}")
        
        # Load story structure
        if story_file.exists():
            try:
                with open(story_file, 'r', encoding='utf-8') as f:
                    story_data = json.load(f)
                    manga_data["story_structure"] = story_data
            except Exception as e:
                print(f"⚠️  Error loading story structure: {e}")
        
        if not manga_data:
            print(f"⚠️  No manga data found in {manga_dir}")
            return None
        
        # Extract emotions
        emotion_results = self.extract_from_manga_data(manga_data)
        
        # Save results
        output_file = manga_path / "emotion_analysis.json"
        self.save_emotion_results(emotion_results, str(output_file))
        
        return emotion_results

def main():
    """Main emotion extraction function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 7: Emotion Extraction")
    parser.add_argument("--manga-dir", type=str, help="Manga directory to process")
    parser.add_argument("--dialogue-file", type=str, help="Text file with dialogue lines")
    parser.add_argument("--output", type=str, default="outputs/emotion_outputs/emotion_labels.json",
                       help="Output file for emotion results")
    parser.add_argument("--test", action="store_true", help="Run test with sample dialogue")
    
    args = parser.parse_args()
    
    extractor = EmotionExtractor()
    
    if args.test:
        # Test with sample dialogue
        test_dialogue = [
            "I can't believe you did that!",
            "I'm so happy to see you again...",
            "What?! That's impossible!",
            "I don't understand what you mean.",
            "We must fight to protect everyone!",
            "This is really confusing...",
            "Okay, let's go then."
        ]
        
        print("🧪 Testing emotion extraction with sample dialogue:")
        results = extractor.extract_from_dialogue_list(test_dialogue)
        
        for result in results:
            print(f"   '{result['line']}' → {result['emotion']} ({result['confidence']})")
        
        # Save test results
        test_data = {
            "test_timestamp": datetime.now().isoformat(),
            "test_dialogue": test_dialogue,
            "emotion_results": results
        }
        extractor.save_emotion_results(test_data, args.output)
        
    elif args.manga_dir:
        # Process manga directory
        print(f"📂 Processing manga directory: {args.manga_dir}")
        results = extractor.process_manga_directory(args.manga_dir)
        
        if results:
            print(f"✅ Processed {results['total_lines']} dialogue lines")
            print(f"📊 Emotion distribution: {results['emotion_distribution']}")
        
    elif args.dialogue_file:
        # Process dialogue file
        dialogue_path = Path(args.dialogue_file)
        if not dialogue_path.exists():
            print(f"❌ Dialogue file not found: {args.dialogue_file}")
            return 1
        
        with open(dialogue_path, 'r', encoding='utf-8') as f:
            dialogue_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"📂 Processing {len(dialogue_lines)} dialogue lines from file")
        results = extractor.extract_from_dialogue_list(dialogue_lines)
        
        emotion_data = {
            "extraction_timestamp": datetime.now().isoformat(),
            "source_file": str(dialogue_path),
            "total_lines": len(dialogue_lines),
            "dialogue_emotions": results
        }
        
        extractor.save_emotion_results(emotion_data, args.output)
        
    else:
        print("❌ Please specify --manga-dir, --dialogue-file, or --test")
        return 1
    
    print("✅ Phase 7: Emotion Extraction Complete")
    return 0

if __name__ == "__main__":
    exit(main())
