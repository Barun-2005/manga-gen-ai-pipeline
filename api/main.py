#!/usr/bin/env python3
"""
MangaGen - FastAPI Backend

REST API for the web frontend.
Handles manga generation requests.
"""

import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


# ============================================
# Pydantic Models
# ============================================

class CharacterInput(BaseModel):
    name: str
    appearance: str
    personality: Optional[str] = ""


class GenerateRequest(BaseModel):
    story_prompt: str
    title: str = "My Manga"
    style: str = "color_anime"  # "color_anime" or "bw_manga"
    layout: str = "2x2"  # "2x2", "2x3", "3x3"
    pages: int = 1
    characters: Optional[List[CharacterInput]] = None


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "generating", "completed", "failed"
    progress: int  # 0-100
    current_step: str
    result: Optional[dict] = None
    error: Optional[str] = None


# ============================================
# App Setup
# ============================================

app = FastAPI(
    title="MangaGen API",
    description="AI-powered manga generation",
    version="1.0.0"
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Job storage (in-memory for now, use Redis in production)
jobs: dict[str, JobStatus] = {}

# Output directory
OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================
# API Endpoints
# ============================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "MangaGen API",
        "version": "1.0.0"
    }


@app.post("/api/generate", response_model=JobStatus)
async def start_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """Start manga generation job."""
    
    # Create job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Initialize job status
    job = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        current_step="Initializing..."
    )
    jobs[job_id] = job
    
    # Start background generation
    background_tasks.add_task(
        run_generation,
        job_id,
        request
    )
    
    return job


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return jobs[job_id]


@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str):
    """Download generated manga file."""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    result = job.result
    if not result:
        raise HTTPException(status_code=404, detail="No result")
    
    if file_type == "pdf":
        file_path = result.get("pdf")
    elif file_type == "png":
        # Return first page PNG
        pages = result.get("pages", [])
        if pages:
            file_path = pages[0].get("page_image")
        else:
            file_path = None
    else:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    if not file_path or not Path(file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=Path(file_path).name
    )


@app.get("/api/preview/{job_id}/{page_num}")
async def get_page_preview(job_id: str, page_num: int):
    """Get preview image for a specific page."""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if not job.result:
        raise HTTPException(status_code=400, detail="No result yet")
    
    pages = job.result.get("pages", [])
    for page in pages:
        if page.get("page_number") == page_num:
            file_path = page.get("page_image")
            if file_path and Path(file_path).exists():
                return FileResponse(file_path)
    
    raise HTTPException(status_code=404, detail="Page not found")


# ============================================
# Background Generation
# ============================================

async def run_generation(job_id: str, request: GenerateRequest):
    """Run manga generation in background."""
    
    job = jobs[job_id]
    
    try:
        # Import here to avoid circular imports
        from scripts.generate_manga import MangaGenerator, MangaConfig
        
        # Update status
        job.status = "generating"
        job.current_step = "Setting up..."
        job.progress = 5
        
        # Get API key
        groq_key = os.environ.get("GROQ_API_KEY")
        if not groq_key:
            raise ValueError("GROQ_API_KEY not set")
        
        # Create config
        config = MangaConfig(
            title=request.title,
            style=request.style,
            layout=request.layout,
            pages=request.pages,
            output_dir=str(OUTPUT_DIR / job_id)
        )
        
        # Create output directory for this job
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        job.current_step = "Generating scenes..."
        job.progress = 10
        
        # Generate
        generator = MangaGenerator(config)
        
        # Update progress during generation
        job.current_step = "Generating panels..."
        job.progress = 30
        
        result = generator.generate_chapter(
            story_prompt=request.story_prompt,
            groq_api_key=groq_key
        )
        
        # Complete
        job.status = "completed"
        job.progress = 100
        job.current_step = "Done!"
        job.result = result
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.current_step = "Failed"


# ============================================
# Static Files (for serving generated images)
# ============================================

# Mount outputs directory for image serving
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs")


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Starting MangaGen API Server...")
    print("   http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
