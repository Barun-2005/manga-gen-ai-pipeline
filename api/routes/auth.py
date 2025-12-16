#!/usr/bin/env python3
"""
Authentication routes for MangaGen
Simple JWT-based auth with MongoDB user storage
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os
import hashlib
import secrets
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/auth", tags=["auth"])

# Secret key for JWT (use env var in production)
SECRET_KEY = os.getenv("JWT_SECRET", secrets.token_hex(32))

class UserRegister(BaseModel):
    email: str  # Changed from EmailStr to avoid email-validator dep
    password: str

class UserLogin(BaseModel):
    email: str  # Changed from EmailStr to avoid email-validator dep
    password: str

class AuthResponse(BaseModel):
    token: str
    user: dict

def hash_password(password: str) -> str:
    """Hash password with salt."""
    salt = SECRET_KEY[:16]
    return hashlib.sha256(f"{salt}{password}".encode()).hexdigest()

def create_token(user_id: str) -> str:
    """Create a simple session token."""
    # In production, use proper JWT with expiry
    return f"{user_id}:{secrets.token_hex(32)}"

@router.post("/register", response_model=AuthResponse)
async def register(user: UserRegister):
    """Register a new user."""
    try:
        from src.database.mongodb import Database
        
        # Connect if needed
        if Database.db is None:
            await Database.connect_db()
        
        if Database.db is None:
            # Demo mode - no database
            return AuthResponse(
                token=create_token("demo"),
                user={"email": user.email, "id": "demo", "plan": "free"}
            )
        
        # Check if user exists
        existing = await Database.db.users.find_one({"email": user.email})
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create user
        user_doc = {
            "email": user.email,
            "password_hash": hash_password(user.password),
            "created_at": datetime.now().isoformat(),
            "plan": "free"
        }
        result = await Database.db.users.insert_one(user_doc)
        user_id = str(result.inserted_id)
        
        return AuthResponse(
            token=create_token(user_id),
            user={"email": user.email, "id": user_id, "plan": "free"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {e}")
        # Fallback to demo mode
        return AuthResponse(
            token=create_token("demo"),
            user={"email": user.email, "id": "demo", "plan": "free"}
        )

@router.post("/login", response_model=AuthResponse)
async def login(user: UserLogin):
    """Login existing user."""
    try:
        from src.database.mongodb import Database
        
        # Connect if needed
        if Database.db is None:
            await Database.connect_db()
        
        if Database.db is None:
            # Demo mode - accept any login
            return AuthResponse(
                token=create_token("demo"),
                user={"email": user.email, "id": "demo", "plan": "free"}
            )
        
        # Find user
        user_doc = await Database.db.users.find_one({"email": user.email})
        if not user_doc:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Check password
        if user_doc["password_hash"] != hash_password(user.password):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user_id = str(user_doc["_id"])
        
        return AuthResponse(
            token=create_token(user_id),
            user={
                "email": user_doc["email"],
                "id": user_id,
                "plan": user_doc.get("plan", "free")
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {e}")
        # Fallback to demo mode
        return AuthResponse(
            token=create_token("demo"),
            user={"email": user.email, "id": "demo", "plan": "free"}
        )

@router.get("/me")
async def get_current_user(token: str = None):
    """Get current user info (placeholder)."""
    # In production, validate JWT and return user
    return {"message": "Auth endpoint ready", "demo_mode": True}
