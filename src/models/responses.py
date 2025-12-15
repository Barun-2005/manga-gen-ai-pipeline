#!/usr/bin/env python3
"""
Standardized API response models
Consistent error/success responses across all endpoints
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel

class APIResponse(BaseModel):
    """Standard API response wrapper."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class ErrorResponse(BaseModel):
    """Standard error response."""
    success: bool = False
    message: str
    error_code: str
    details: Optional[Dict[str, Any]] = None

class SuccessResponse(BaseModel):
    """Standard success response."""
    success: bool = True
    message: str
    data: Any

# Error code constants
class ErrorCodes:
    """Standard error codes."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    RATE_LIMIT = "RATE_LIMIT_EXCEEDED"
    SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    GENERATION_FAILED = "GENERATION_FAILED"
    INVALID_INPUT = "INVALID_INPUT"
    DATABASE_ERROR = "DATABASE_ERROR"
