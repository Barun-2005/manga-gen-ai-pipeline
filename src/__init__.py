"""
MangaGen - AI Manga Generation Pipeline

This package provides tools for generating complete manga pages from text prompts.
"""

__version__ = "2.0.0"
__author__ = "Barun"

from pathlib import Path

# Package root directory
PACKAGE_ROOT = Path(__file__).parent.parent
ARCHIVE_DIR = PACKAGE_ROOT / "archive" / "salvaged"
SCRIPTS_DIR = PACKAGE_ROOT / "scripts"
OUTPUTS_DIR = PACKAGE_ROOT / "outputs"
