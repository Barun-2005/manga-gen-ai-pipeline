#!/usr/bin/env python3
"""
Intelligent caching system
Cache expensive operations (LLM responses, image metadata)
"""

from typing import Optional, Any, Dict
import json
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
import pickle

class Cache:
    """Simple file-based cache with TTL."""
    
    def __init__(self, cache_dir: str = ".cache", default_ttl_hours: int = 24):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = timedelta(hours=default_ttl_hours)
    
    def _get_key_path(self, key: str) -> Path:
        """Get cache file path for key."""
        # Hash key for filesystem safety
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        cache_file = self._get_key_path(key)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
            
            # Check TTL
            if datetime.now() > data['expires_at']:
                cache_file.unlink()  # Delete expired
                return None
            
            return data['value']
            
        except Exception as e:
            print(f"Cache read error: {e}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl_hours: Optional[int] = None
    ):
        """Set value in cache."""
        ttl = timedelta(hours=ttl_hours) if ttl_hours else self.default_ttl
        expires_at = datetime.now() + ttl
        
        cache_file = self._get_key_path(key)
        
        try:
            data = {
                'value': value,
                'expires_at': expires_at,
                'created_at': datetime.now()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(data, f)
                
        except Exception as e:
            print(f"Cache write error: {e}")
    
    def delete(self, key: str):
        """Delete key from cache."""
        cache_file = self._get_key_path(key)
        if cache_file.exists():
            cache_file.unlink()
    
    def clear(self):
        """Clear all cache."""
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
    
    def cleanup_expired(self) -> int:
        """Remove expired cache entries."""
        removed = 0
        now = datetime.now()
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                
                if now > data['expires_at']:
                    cache_file.unlink()
                    removed += 1
                    
            except:
                # Corrupted cache file
                cache_file.unlink()
                removed += 1
        
        return removed


# Global cache instances
story_cache = Cache(".cache/stories", default_ttl_hours=48)
prompt_cache = Cache(".cache/prompts", default_ttl_hours=24)
