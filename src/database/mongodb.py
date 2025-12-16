#!/usr/bin/env python3
"""
Database Configuration and Setup
MongoDB connection for MangaGen persistence

Collections:
- jobs: Active generation jobs
- projects: Saved user projects (full data for editing)
- users: User accounts
"""

from typing import Optional, Dict, List
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from datetime import datetime
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
            
            # Create indexes for performance
            await cls.db.projects.create_index("user_id")
            await cls.db.projects.create_index("job_id")
            
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
    
    # ============================================
    # Job Methods (for active generation)
    # ============================================
    
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
    
    # ============================================
    # Project Methods (for saved user projects)
    # ============================================
    
    @classmethod
    async def save_project(cls, user_id: str, project_data: dict) -> bool:
        """
        Save a complete project to database.
        
        project_data should include:
        - job_id: Original job ID
        - title: Project title
        - story_prompt: Original prompt
        - characters: Character DNA list
        - pages: Page data with panel images
        - dialogues: Dialogue positions and text per panel
        - story_state: Where story ended (cliffhanger, summary)
        - style: Visual style
        - created_at, updated_at
        """
        if cls.db is None:
            return False
        
        try:
            project_data["user_id"] = user_id
            project_data["updated_at"] = datetime.now().isoformat()
            
            if "created_at" not in project_data:
                project_data["created_at"] = datetime.now().isoformat()
            
            await cls.db.projects.update_one(
                {"job_id": project_data.get("job_id")},
                {"$set": project_data},
                upsert=True
            )
            print(f"💾 Saved project: {project_data.get('title', 'Untitled')}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to save project: {e}")
            return False
    
    @classmethod
    async def update_project_dialogues(cls, job_id: str, dialogues: dict) -> bool:
        """Update just the dialogues (for canvas edits)."""
        if cls.db is None:
            return False
        
        try:
            await cls.db.projects.update_one(
                {"job_id": job_id},
                {
                    "$set": {
                        "dialogues": dialogues,
                        "updated_at": datetime.now().isoformat()
                    }
                }
            )
            return True
        except Exception as e:
            print(f"⚠️ Failed to update dialogues: {e}")
            return False
    
    @classmethod
    async def get_project(cls, job_id: str) -> Optional[dict]:
        """Get full project data for loading in canvas."""
        if cls.db is None:
            return None
        
        try:
            project = await cls.db.projects.find_one({"job_id": job_id})
            return project
        except Exception as e:
            print(f"⚠️ Failed to get project: {e}")
            return None
    
    @classmethod
    async def get_projects_for_user(cls, user_id: str, limit: int = 20) -> List[dict]:
        """Get all projects for a user (for dashboard)."""
        if cls.db is None:
            return []
        
        try:
            cursor = cls.db.projects.find(
                {"user_id": user_id},
                # Only return fields needed for dashboard listing
                {
                    "job_id": 1, 
                    "title": 1, 
                    "style": 1,
                    "pages": {"$slice": 1},  # Just first page for cover
                    "created_at": 1, 
                    "updated_at": 1
                }
            ).sort("updated_at", -1).limit(limit)
            
            return await cursor.to_list(length=limit)
        except Exception as e:
            print(f"⚠️ Failed to get user projects: {e}")
            return []
    
    @classmethod
    async def list_user_jobs(cls, user_id: str, limit: int = 10) -> list:
        """List jobs for a user (legacy)."""
        if cls.db is not None:
            try:
                cursor = cls.db.jobs.find({"user_id": user_id}).sort("created_at", -1).limit(limit)
                return await cursor.to_list(length=limit)
            except Exception as e:
                print(f"⚠️ Failed to list jobs: {e}")
        return []
