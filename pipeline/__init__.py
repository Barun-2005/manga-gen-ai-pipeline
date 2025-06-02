"""
Pipeline Module

Main manga generation pipeline and utilities.
"""

from .generate_manga import MangaGenerator
from .utils import (
    setup_logging,
    set_seed,
    generate_hash,
    save_json,
    load_json,
    ensure_directory,
    clean_filename,
    timestamp_string,
    ProgressTracker,
    clean_visual_prompt,
    detect_faces,
    detect_blur,
    detect_pose_keypoints
)
# prompt_builder functionality moved to image_gen module

__all__ = [
    "MangaGenerator",
    "setup_logging",
    "set_seed",
    "generate_hash",
    "save_json",
    "load_json",
    "ensure_directory",
    "clean_filename",
    "timestamp_string",
    "ProgressTracker",
    "clean_visual_prompt",
    "detect_faces",
    "detect_blur",
    "detect_pose_keypoints"
]
