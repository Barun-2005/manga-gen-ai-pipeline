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
    sync_client: Optional[MongoClient] = None  # For thread-safe sync operations
    db = None
    sync_db = None  # Sync database for background saves
    
    @classmethod
    async def connect_db(cls):
        """Connect to MongoDB Atlas with proper SSL/TLS settings."""
        try:
            import ssl
            import certifi
            
            # Get MongoDB URL from environment or use default
            mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
            
            # Check if it's Atlas (needs SSL)
            is_atlas = "mongodb.net" in mongodb_url or "mongodb+srv" in mongodb_url
            
            if is_atlas:
                # Use certifi for proper SSL certificates on Windows
                try:
                    cls.client = AsyncIOMotorClient(
                        mongodb_url,
                        tls=True,
                        tlsCAFile=certifi.where(),
                        serverSelectionTimeoutMS=10000,
                        connectTimeoutMS=10000
                    )
                except Exception as ssl_err:
                    print(f"⚠️ SSL with certifi failed: {ssl_err}")
                    # Fallback 1: tlsAllowInvalidCertificates
                    try:
                        cls.client = AsyncIOMotorClient(
                            mongodb_url,
                            tls=True,
                            tlsAllowInvalidCertificates=True,
                            serverSelectionTimeoutMS=10000
                        )
                    except Exception as ssl_err2:
                        print(f"⚠️ SSL fallback 1 failed: {ssl_err2}")
                        # Fallback 2: Custom SSL context with no verification
                        ssl_context = ssl.create_default_context()
                        ssl_context.check_hostname = False
                        ssl_context.verify_mode = ssl.CERT_NONE
                        cls.client = AsyncIOMotorClient(
                            mongodb_url,
                            tls=True,
                            tlsAllowInvalidCertificates=True,
                            serverSelectionTimeoutMS=15000,
                            socketTimeoutMS=20000
                        )
            else:
                # Local MongoDB
                cls.client = AsyncIOMotorClient(mongodb_url)
            
            cls.db = cls.client.mangagen
            
            # Test connection
            await cls.client.admin.command('ping')
            print(f"✅ Connected to MongoDB: {mongodb_url[:50]}...")
            
            # Also create synchronous client for thread-safe background saves
            try:
                import certifi
                if is_atlas:
                    cls.sync_client = MongoClient(
                        mongodb_url,
                        tls=True,
                        tlsCAFile=certifi.where(),
                        serverSelectionTimeoutMS=10000
                    )
                else:
                    cls.sync_client = MongoClient(mongodb_url)
                cls.sync_db = cls.sync_client.mangagen
                print(f"✅ Sync MongoDB client ready for background saves")
            except Exception as sync_err:
                print(f"⚠️ Sync client failed (auto-save disabled): {sync_err}")
                cls.sync_client = None
                cls.sync_db = None
            
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
    
    @classmethod
    def init_sync_client(cls) -> bool:
        """
        Initialize sync MongoDB client for background saves.
        MUST be called BEFORE starting generation to prevent silent save failures.
        """
        if cls.sync_db is not None:
            return True  # Already initialized
            
        try:
            from pymongo import MongoClient
            import certifi
            
            mongo_url = os.getenv("MONGODB_URL")
            if not mongo_url:
                print("⚠️ No MONGODB_URL set, sync client not initialized")
                return False
            
            is_atlas = "mongodb.net" in mongo_url or "mongodb+srv" in mongo_url
            
            if is_atlas:
                cls.sync_client = MongoClient(
                    mongo_url,
                    tls=True,
                    tlsCAFile=certifi.where(),
                    serverSelectionTimeoutMS=10000
                )
            else:
                cls.sync_client = MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
            
            # Use hardcoded 'mangagen' database (same as connect_db)
            cls.sync_db = cls.sync_client.mangagen
            print(f"✅ Sync MongoDB client ready for background saves")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to init sync MongoDB: {e}")
            return False
    
    @classmethod
    def delete_project_sync(cls, job_id: str) -> bool:
        """
        Delete project from MongoDB (synchronous).
        Deletes from BOTH 'jobs' and 'projects' collections.
        Returns True if deleted from at least one collection.
        """
        if cls.sync_db is None:
            cls.init_sync_client()
        
        if cls.sync_db is not None:
            deleted_any = False
            try:
                # Delete from jobs collection
                result1 = cls.sync_db.jobs.delete_one({"job_id": job_id})
                if result1.deleted_count > 0:
                    print(f"🗑️ Deleted from jobs collection: {job_id}")
                    deleted_any = True
                
                # Also delete from projects collection (user-saved projects)
                result2 = cls.sync_db.projects.delete_one({"job_id": job_id})
                if result2.deleted_count > 0:
                    print(f"🗑️ Deleted from projects collection: {job_id}")
                    deleted_any = True
                
                return deleted_any
            except Exception as e:
                print(f"⚠️ Failed to delete project from DB: {e}")
                return False
        return False
    
    # ============================================
    # Job Methods (for active generation)
    # ============================================
    
    @classmethod
    async def save_job(cls, job_id: str, job_data: dict):
        """Save job to database (async)."""
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
    def save_job_sync(cls, job_id: str, job_data: dict) -> bool:
        """
        Save job to database (synchronous).
        
        This method uses PyMongo directly for thread-safe operations
        from background threads (like the generation thread).
        """
        if cls.sync_db is not None:
            try:
                cls.sync_db.jobs.update_one(
                    {"job_id": job_id},
                    {"$set": job_data},
                    upsert=True
                )
                return True
            except Exception as e:
                print(f"⚠️ Failed to save job to DB (sync): {e}")
                return False
        return False
    
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
