#!/usr/bin/env python3
"""
Image optimization utilities
Compress and optimize generated images for web delivery
"""

from PIL import Image
from pathlib import Path
from typing import Optional
import os

class ImageOptimizer:
    """Optimize images for web delivery without quality loss."""
    
    @staticmethod
    def optimize_png(
        input_path: str,
        output_path: Optional[str] = None,
        max_size: int = 1920,
        quality: int = 90
    ) -> str:
        """
        Optimize PNG image for web.
        
        Args:
            input_path: Input image path
            output_path: Output path (overwrites input if None)
            max_size: Max dimension (width or height)
            quality: JPEG quality if converting to JPG (0-100)
        
        Returns:
            Path to optimized image
        """
        if output_path is None:
            output_path = input_path
        
        try:
            img = Image.open(input_path)
            
            # Resize if too large
            if max(img.size) > max_size:
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert RGBA to RGB if saving as JPEG
            if output_path.lower().endswith('.jpg') or output_path.lower().endswith('.jpeg'):
                if img.mode == 'RGBA':
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
            else:
                # Save as PNG with optimization
                img.save(output_path, 'PNG', optimize=True, compress_level=9)
            
            return output_path
            
        except Exception as e:
            print(f"Image optimization error: {e}")
            return input_path
    
    @staticmethod
    def create_thumbnail(
        input_path: str,
        output_path: str,
        size: tuple = (400, 400)
    ) -> str:
        """
        Create thumbnail for preview.
        
        Args:
            input_path: Input image
            output_path: Thumbnail output path
            size: Thumbnail size (width, height)
        
        Returns:
            Path to thumbnail
        """
        try:
            img = Image.open(input_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save as JPEG for smaller size
            if img.mode == 'RGBA':
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            
            img.save(output_path, 'JPEG', quality=85, optimize=True)
            return output_path
            
        except Exception as e:
            print(f"Thumbnail creation error: {e}")
            return input_path
    
    @staticmethod
    def get_image_size(image_path: str) -> int:
        """Get image file size in bytes."""
        try:
            return os.path.getsize(image_path)
        except:
            return 0
    
    @staticmethod
    def optimize_directory(
        directory: str,
        max_size: int = 1920,
        create_thumbnails: bool = True
    ) -> dict:
        """
        Optimize all images in a directory.
        
        Args:
            directory: Directory path
            max_size: Max dimension
            create_thumbnails: Create thumbnails
        
        Returns:
            Stats dict with counts and sizes
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            return {"error": "Directory not found"}
        
        stats = {
            "total_files": 0,
            "optimized": 0,
            "thumbnails": 0,
            "original_size": 0,
            "final_size": 0
        }
        
        for img_path in dir_path.glob("*.png"):
            stats["total_files"] += 1
            stats["original_size"] += ImageOptimizer.get_image_size(str(img_path))
            
            # Optimize
            ImageOptimizer.optimize_png(str(img_path), max_size=max_size)
            stats["optimized"] += 1
            stats["final_size"] += ImageOptimizer.get_image_size(str(img_path))
            
            # Create thumbnail
            if create_thumbnails:
                thumb_path = img_path.parent / f"{img_path.stem}_thumb.jpg"
                ImageOptimizer.create_thumbnail(str(img_path), str(thumb_path))
                stats["thumbnails"] += 1
        
        stats["saved_bytes"] = stats["original_size"] - stats["final_size"]
        stats["saved_percent"] = (stats["saved_bytes"] / stats["original_size"] * 100) if stats["original_size"] > 0 else 0
        
        return stats
