"""
Utility Functions

Common utilities for logging, seed setting, file operations, and other helper functions
used throughout the manga generation pipeline.
"""

import os
import json
import random
import logging
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from datetime import datetime


def setup_logging(level: str = "INFO", log_file: str = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("manga_generator")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def set_seed(seed: int) -> None:
    """
    Set random seed for reproducible generation.
    
    Args:
        seed: Random seed value
    """
    random.seed(seed)
    # Note: For full reproducibility, you might also want to set seeds for
    # numpy, torch, etc. depending on what libraries are used
    
    # If using numpy:
    # import numpy as np
    # np.random.seed(seed)
    
    # If using torch:
    # import torch
    # torch.manual_seed(seed)


def generate_hash(text: str) -> str:
    """
    Generate a hash for text content.
    
    Args:
        text: Input text
        
    Returns:
        SHA256 hash string
    """
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def save_json(data: Dict[str, Any], file_path: str, indent: int = 2) -> None:
    """
    Save data to JSON file.
    
    Args:
        data: Data to save
        file_path: Output file path
        indent: JSON indentation
    """
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def load_json(file_path: str) -> Dict[str, Any]:
    """
    Load data from JSON file.
    
    Args:
        file_path: Input file path
        
    Returns:
        Loaded data dictionary
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj


def get_file_size(file_path: str) -> int:
    """
    Get file size in bytes.
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes
    """
    return os.path.getsize(file_path)


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def clean_filename(filename: str) -> str:
    """
    Clean filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters for most filesystems
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename


def timestamp_string(format_str: str = "%Y%m%d_%H%M%S") -> str:
    """
    Generate timestamp string.
    
    Args:
        format_str: Timestamp format
        
    Returns:
        Formatted timestamp string
    """
    return datetime.now().strftime(format_str)


def split_text_into_chunks(
    text: str, 
    max_length: int = 1000, 
    overlap: int = 100
) -> List[str]:
    """
    Split text into overlapping chunks.
    
    Args:
        text: Input text
        max_length: Maximum chunk length
        overlap: Overlap between chunks
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_length
        
        # Try to break at sentence boundary
        if end < len(text):
            # Look for sentence endings
            for i in range(end, start + max_length // 2, -1):
                if text[i] in '.!?':
                    end = i + 1
                    break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks


def validate_config(config: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary
        required_keys: List of required keys
        
    Returns:
        True if valid, False otherwise
    """
    for key in required_keys:
        if key not in config:
            return False
    return True


def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge two configuration dictionaries.
    
    Args:
        base_config: Base configuration
        override_config: Override configuration
        
    Returns:
        Merged configuration
    """
    merged = base_config.copy()
    merged.update(override_config)
    return merged


def retry_on_failure(func, max_retries: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure.
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retries
        delay: Delay between retries in seconds
        
    Returns:
        Decorated function
    """
    import time
    
    def wrapper(*args, **kwargs):
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                if attempt < max_retries:
                    time.sleep(delay)
                    continue
                else:
                    raise last_exception
    
    return wrapper


def progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Generate a simple progress bar string.
    
    Args:
        current: Current progress
        total: Total items
        width: Progress bar width
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + "=" * width + "] 100%"
    
    progress = current / total
    filled = int(width * progress)
    bar = "=" * filled + "-" * (width - filled)
    percentage = int(progress * 100)
    
    return f"[{bar}] {percentage}% ({current}/{total})"


def estimate_processing_time(
    items_processed: int, 
    total_items: int, 
    elapsed_time: float
) -> str:
    """
    Estimate remaining processing time.
    
    Args:
        items_processed: Number of items processed
        total_items: Total number of items
        elapsed_time: Elapsed time in seconds
        
    Returns:
        Estimated time remaining as string
    """
    if items_processed == 0:
        return "Unknown"
    
    rate = items_processed / elapsed_time
    remaining_items = total_items - items_processed
    estimated_seconds = remaining_items / rate
    
    if estimated_seconds < 60:
        return f"{estimated_seconds:.0f} seconds"
    elif estimated_seconds < 3600:
        return f"{estimated_seconds/60:.1f} minutes"
    else:
        return f"{estimated_seconds/3600:.1f} hours"


class ProgressTracker:
    """Simple progress tracking utility."""
    
    def __init__(self, total_items: int, description: str = "Processing"):
        """
        Initialize progress tracker.
        
        Args:
            total_items: Total number of items to process
            description: Description of the process
        """
        self.total_items = total_items
        self.description = description
        self.current_item = 0
        self.start_time = datetime.now()
    
    def update(self, increment: int = 1) -> None:
        """
        Update progress.
        
        Args:
            increment: Number of items to increment
        """
        self.current_item += increment
        self._print_progress()
    
    def _print_progress(self) -> None:
        """Print current progress."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        progress_str = progress_bar(self.current_item, self.total_items)
        time_est = estimate_processing_time(self.current_item, self.total_items, elapsed)
        
        print(f"\r{self.description}: {progress_str} ETA: {time_est}", end="", flush=True)
        
        if self.current_item >= self.total_items:
            print()  # New line when complete


if __name__ == "__main__":
    # Example usage
    logger = setup_logging("INFO")
    logger.info("Utils module loaded successfully")
    
    # Test progress tracker
    import time
    tracker = ProgressTracker(10, "Testing")
    for i in range(10):
        time.sleep(0.1)
        tracker.update()
    
    print("Utils module test completed")
