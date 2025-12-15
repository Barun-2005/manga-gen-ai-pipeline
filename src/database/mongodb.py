#!/usr/bin/env python3
"""
Database Configuration and Setup
MongoDB connection for MangaGen persistence
"""

from typing import Optional
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
import os

class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db = None
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB."""
        try:
            # Get MongoDB URL from environment or use default
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            
            cls.client = AsyncIOMotorClient(mongodb_url)
            cls.db = cls.client.mangagen
            
            # Test connection
            await cls.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {mongodb_url}")
            
        except Exception as e:
            print(f"⚠️ MongoDB connection failed: {e}")
            print(f"   App will work in-memory mode (no persistence)")
            cls.client = None
            cls.db = None
    
    @classmethod
    async def close_db(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            print("📴 MongoDB connection closed")
    
    @classmethod
    def get_db(cls):
        """Get database instance."""
        return cls.db
    
    @classmethod
    async def save_job(cls, job_id: str, job_data: dict):
        """Save job to database."""
        if cls.db is not None:
            try:
                await cls.db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": job_data},
                    upsert=True
                )
            except Exception as e:
                print(f"⚠️ Failed to save job to DB: {e}")
    
    @classmethod
    async def get_job(cls, job_id: str) -> Optional[dict]:
        """Get job from database."""
        if cls.db is not None:
            try:
                return await cls.db.jobs.find_one({"job_id": job_id})
            except Exception as e:
                print(f"⚠️ Failed to get job from DB: {e}")
        return None
    
    @classmethod
    async def list_user_jobs(cls, user_id: str, limit: int = 10) -> list:
        """List jobs for a user."""
        if cls.db is not None:
            try:
                cursor = cls.db.jobs.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
                return await cursor.to_list(length=limit)
            except Exception as e:
                print(f"⚠️ Failed to list jobs: {e}")
        return []
