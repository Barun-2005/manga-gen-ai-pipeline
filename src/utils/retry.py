#!/usr/bin/env python3
"""
Retry utilities with exponential backoff
Robust API call handling
"""

import time
import random
from typing import Callable, Any, Optional, Type
from functools import wraps

class RetryError(Exception):
    """Raised when all retry attempts fail."""
    pass

def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        max_retries: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Multiplier for exponential backoff
        jitter: Add random jitter to delays
        exceptions: Tuple of exceptions to catch
    
    Example:
        @retry_with_backoff(max_retries=3)
        async def call_api():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        # Last attempt failed
                        break
                    
                    # Calculate delay
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # Add jitter
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    print(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {str(e)[:100]}")
                    time.sleep(delay)
            
            # All retries failed
            raise RetryError(
                f"Failed after {max_retries} attempts: {last_exception}"
            ) from last_exception
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries - 1:
                        break
                    
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    print(f"Retry {attempt + 1}/{max_retries} after {delay:.1f}s: {str(e)[:100]}")
                    time.sleep(delay)
            
            raise RetryError(
                f"Failed after {max_retries} attempts: {last_exception}"
            ) from last_exception
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def safe_execute(func: Callable, default: Any = None, silent: bool = False) -> Any:
    """
    Safely execute function with fallback.
    
    Args:
        func: Function to execute
        default: Default value if function fails
        silent: Suppress error messages
    
    Returns:
        Function result or default value
    """
    try:
        return func()
    except Exception as e:
        if not silent:
            print(f"Safe execute error: {e}")
        return default
