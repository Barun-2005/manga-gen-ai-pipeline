#!/usr/bin/env python3
"""
Request validation and rate limiting middleware
Professional API protection
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
import time

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting (use Redis in production)."""
    
    def __init__(self, app, calls: int = 10, period: int = 60):
        super().__init__(app)
        self.calls = calls  # Max calls per period
        self.period = period  # Period in seconds
        self.clients = defaultdict(list)  # IP -> list of timestamps
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Clean old timestamps
        now = time.time()
        self.clients[client_ip] = [
            ts for ts in self.clients[client_ip]
            if now - ts < self.period
        ]
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {self.calls} requests per {self.period}s"
            )
        
        # Add current timestamp
        self.clients[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        return response


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Validate request sizes and content types."""
    
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        # Check content length
        if request.headers.get("content-length"):
            content_length = int(request.headers["content-length"])
            if content_length > self.MAX_CONTENT_LENGTH:
                raise HTTPException(
                    status_code=413,
                    detail=f"Request too large. Max {self.MAX_CONTENT_LENGTH / 1024 / 1024}MB"
                )
        
        response = await call_next(request)
        return response
