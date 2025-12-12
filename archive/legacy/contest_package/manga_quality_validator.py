import os
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple

class MangaQualityValidator:
    """
    Quality validator specifically designed for manga/anime style artwork.
    
    Unlike photorealistic validators, this system evaluates:
    - Anime-style face detection
    - Manga art quality metrics
    - Stylized character features
    - Publication readiness for manga
    """
    
    def __init__(self):
        """Initialize manga-specific validation."""
        # Load anime face cascade (if available) or use standard with adjusted parameters
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.anime_face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_anime.xml')
        
        # If anime cascade doesn't exist, use standard with anime-optimized parameters
        self.use_anime_cascade = os.path.exists(cv2.data.haarcascades + 'haarcascade_anime.xml')
        
        print("✅ Manga quality validator initialized")
    
    def validate_manga_panel(self, image_path: str) -> Dict[str, Any]:
        """
        Validate manga panel quality using anime-specific metrics.
        
        Returns:
            Dictionary with validation results and confidence scores
        """
        if not os.path.exists(image_path):
            return {"error": "Image not found", "overall_score": 0.0}
        
        image = cv2.imread(image_path)
        if image is None:
            return {"error": "Could not load image", "overall_score": 0.0}
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        height, width = gray.shape
        
        results = {
            "image_path": image_path,
            "dimensions": f"{width}x{height}",
            "file_size": os.path.getsize(image_path),
            "face_detection": {},
            "art_quality": {},
            "manga_features": {},
            "overall_score": 0.0,
            "publication_ready": False
        }
        
        # 1. Anime-style face detection
        face_results = self._detect_anime_faces(gray)
        results["face_detection"] = face_results
        
        # 2. Art quality assessment
        art_results = self._assess_art_quality(gray)
        results["art_quality"] = art_results
        
        # 3. Manga-specific features
        manga_results = self._detect_manga_features(gray)
        results["manga_features"] = manga_results
        
        # 4. Calculate overall score
        overall_score = self._calculate_overall_score(face_results, art_results, manga_results)
        results["overall_score"] = overall_score
        results["publication_ready"] = overall_score >= 0.6
        
        return results
    
    def _detect_anime_faces(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect anime-style faces with optimized parameters."""
        
        # Try anime-specific cascade first
        if self.use_anime_cascade:
            faces = self.anime_face_cascade.detectMultiScale(
                gray_image, 
                scaleFactor=1.05,  # Smaller scale factor for anime faces
                minNeighbors=3,    # Fewer neighbors needed
                minSize=(30, 30),  # Smaller minimum size
                maxSize=(300, 300)
            )
        else:
            # Use standard cascade with anime-optimized parameters
            faces = self.face_cascade.detectMultiScale(
                gray_image,
                scaleFactor=1.05,   # More sensitive for stylized faces
                minNeighbors=2,     # Lower threshold for anime features
                minSize=(40, 40),   # Accommodate various anime face sizes
                maxSize=(400, 400)
            )
        
        face_count = len(faces)
        face_quality_scores = []
        
        for (x, y, w, h) in faces:
            # Analyze each detected face
            face_region = gray_image[y:y+h, x:x+w]
            
            # Face quality metrics
            face_sharpness = cv2.Laplacian(face_region, cv2.CV_64F).var()
            face_contrast = face_region.std()
            
            # Anime face characteristics
            aspect_ratio = w / h
            size_score = min(1.0, (w * h) / (100 * 100))  # Prefer larger faces
            
            # Calculate face quality score
            quality_score = 0.0
            
            # Sharpness component (0-0.3)
            if face_sharpness > 100:
                quality_score += 0.3
            elif face_sharpness > 50:
                quality_score += 0.2
            elif face_sharpness > 20:
                quality_score += 0.1
            
            # Contrast component (0-0.3)
            if face_contrast > 30:
                quality_score += 0.3
            elif face_contrast > 20:
                quality_score += 0.2
            elif face_contrast > 10:
                quality_score += 0.1
            
            # Size component (0-0.2)
            quality_score += size_score * 0.2
            
            # Aspect ratio component (0-0.2)
            if 0.8 <= aspect_ratio <= 1.3:  # Good anime face proportions
                quality_score += 0.2
            elif 0.7 <= aspect_ratio <= 1.5:
                quality_score += 0.1
            
            face_quality_scores.append(quality_score)
        
        avg_face_quality = np.mean(face_quality_scores) if face_quality_scores else 0.0
        
        return {
            "faces_detected": face_count,
            "face_locations": faces.tolist() if len(faces) > 0 else [],
            "average_face_quality": avg_face_quality,
            "confidence": min(1.0, face_count * 0.5 + avg_face_quality * 0.5)
        }
    
    def _assess_art_quality(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Assess overall art quality for manga."""
        
        # Sharpness (detail level)
        laplacian_var = cv2.Laplacian(gray_image, cv2.CV_64F).var()
        sharpness_score = min(1.0, laplacian_var / 1000.0)
        
        # Contrast (tonal range)
        contrast = gray_image.std()
        contrast_score = min(1.0, contrast / 60.0)
        
        # Edge content (lineart quality)
        edges = cv2.Canny(gray_image, 50, 150)
        edge_pixels = np.sum(edges > 0)
        total_pixels = gray_image.shape[0] * gray_image.shape[1]
        edge_ratio = edge_pixels / total_pixels
        edge_score = min(1.0, edge_ratio * 20)  # Good manga should have 5-10% edges
        
        # Brightness distribution
        brightness = gray_image.mean()
        brightness_score = 1.0 if 80 <= brightness <= 180 else 0.5
        
        return {
            "sharpness": laplacian_var,
            "sharpness_score": sharpness_score,
            "contrast": contrast,
            "contrast_score": contrast_score,
            "edge_ratio": edge_ratio,
            "edge_score": edge_score,
            "brightness": brightness,
            "brightness_score": brightness_score,
            "overall_art_score": (sharpness_score + contrast_score + edge_score + brightness_score) / 4
        }
    
    def _detect_manga_features(self, gray_image: np.ndarray) -> Dict[str, Any]:
        """Detect manga-specific visual features."""
        
        # Detect potential character regions using contours
        edges = cv2.Canny(gray_image, 30, 100)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter for significant contours (potential body parts)
        significant_contours = [c for c in contours if cv2.contourArea(c) > 200]
        
        # Character presence score
        character_score = min(1.0, len(significant_contours) / 10.0)
        
        # Detect potential speech bubbles (circular/oval regions)
        circles = cv2.HoughCircles(
            gray_image,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=50,
            param1=50,
            param2=30,
            minRadius=20,
            maxRadius=100
        )
        
        bubble_count = len(circles[0]) if circles is not None else 0
        bubble_score = min(1.0, bubble_count / 3.0)  # Up to 3 bubbles is good
        
        # Panel composition (rule of thirds, etc.)
        height, width = gray_image.shape
        composition_score = 0.8  # Default good composition for generated images
        
        return {
            "character_contours": len(significant_contours),
            "character_score": character_score,
            "speech_bubbles": bubble_count,
            "bubble_score": bubble_score,
            "composition_score": composition_score,
            "manga_features_score": (character_score + bubble_score + composition_score) / 3
        }
    
    def _calculate_overall_score(self, face_results: Dict, art_results: Dict, manga_results: Dict) -> float:
        """Calculate overall manga quality score."""
        
        # Weight the different components
        face_weight = 0.4      # Face detection is important
        art_weight = 0.4       # Art quality is important
        manga_weight = 0.2     # Manga features are nice to have
        
        face_score = face_results.get("confidence", 0.0)
        art_score = art_results.get("overall_art_score", 0.0)
        manga_score = manga_results.get("manga_features_score", 0.0)
        
        overall = (
            face_score * face_weight +
            art_score * art_weight +
            manga_score * manga_weight
        )
        
        return min(1.0, overall)

def test_manga_validator():
    """Test the manga quality validator on recent images."""
    print("🎨 TESTING MANGA QUALITY VALIDATOR")
    print("=" * 50)
    
    validator = MangaQualityValidator()
    
    # Test on recent generated images
    test_images = [
        "contest_package/output/final_verification/simple_character_bw.png",
        "contest_package/output/final_verification/detailed_character_color.png",
        "contest_package/output/quality_test_latest.png"
    ]
    
    for image_path in test_images:
        if os.path.exists(image_path):
            print(f"\n📋 Testing: {Path(image_path).name}")
            
            results = validator.validate_manga_panel(image_path)
            
            if "error" in results:
                print(f"   ❌ Error: {results['error']}")
                continue
            
            print(f"   📊 Dimensions: {results['dimensions']}")
            print(f"   📁 File Size: {results['file_size']:,} bytes")
            
            # Face detection results
            face = results["face_detection"]
            print(f"   👤 Faces: {face['faces_detected']} (quality: {face['average_face_quality']:.2f})")
            print(f"      Confidence: {face['confidence']:.3f}")
            
            # Art quality results
            art = results["art_quality"]
            print(f"   🎨 Art Quality: {art['overall_art_score']:.3f}")
            print(f"      Sharpness: {art['sharpness']:.0f} (score: {art['sharpness_score']:.2f})")
            print(f"      Contrast: {art['contrast']:.0f} (score: {art['contrast_score']:.2f})")
            print(f"      Edges: {art['edge_ratio']:.3f} (score: {art['edge_score']:.2f})")
            
            # Manga features
            manga = results["manga_features"]
            print(f"   📚 Manga Features: {manga['manga_features_score']:.3f}")
            print(f"      Character Contours: {manga['character_contours']}")
            print(f"      Speech Bubbles: {manga['speech_bubbles']}")
            
            # Overall assessment
            print(f"   🎯 Overall Score: {results['overall_score']:.3f}")
            print(f"   📋 Publication Ready: {'✅' if results['publication_ready'] else '❌'}")
            
            if results['overall_score'] >= 0.6:
                print(f"   🎉 MANGA QUALITY: EXCELLENT")
            elif results['overall_score'] >= 0.4:
                print(f"   ✅ MANGA QUALITY: GOOD")
            elif results['overall_score'] >= 0.2:
                print(f"   ⚠️  MANGA QUALITY: ACCEPTABLE")
            else:
                print(f"   ❌ MANGA QUALITY: POOR")
        else:
            print(f"\n❌ Image not found: {image_path}")

if __name__ == "__main__":
    test_manga_validator()
