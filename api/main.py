#!/usr/bin/env python3
"""
MangaGen - FastAPI Backend

REST API for the web frontend.
Handles manga generation requests.
"""

import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = PROJECT_ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded environment from {env_path}")
    else:
        print("⚠️ No .env file found - using system environment variables")
        print(f"   Create one by copying .env.example to .env")
except ImportError:
    print("⚠️ python-dotenv not installed. Run: pip install python-dotenv")
    print("   Using system environment variables only")

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
    image_provider: str = "pollinations"  # "pollinations" or "nvidia"
    characters: Optional[List[CharacterInput]] = None


class RegenerateRequest(BaseModel):
    page: int
    panel: int
    prompt_override: Optional[str] = None


class StepStatus(BaseModel):
    """Status of a generation step."""
    name: str
    status: str  # "pending", "in_progress", "completed"
    duration: Optional[str] = None


class JobStatus(BaseModel):
    job_id: str
    status: str  # "pending", "generating", "completed", "failed"
    progress: int  # 0-100
    current_step: str
    
    # Enhanced tracking for live preview
    steps: Optional[List[StepStatus]] = None
    current_panel: Optional[int] = None
    total_panels: Optional[int] = None
    panel_previews: Optional[List[str]] = None  # URLs of generated panels
    log_messages: Optional[List[str]] = None  # Terminal-style log
    layout: Optional[str] = None
    
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


class EnhanceRequest(BaseModel):
    prompt: str


class EnhanceResponse(BaseModel):
    original: str
    enhanced: str


@app.post("/api/enhance-prompt", response_model=EnhanceResponse)
async def enhance_prompt(request: EnhanceRequest):
    """Use AI to improve a story prompt."""
    
    try:
        from src.ai.story_director import StoryDirector
        director = StoryDirector()  # Uses FallbackLLM automatically!
        enhanced = director.enhance_prompt(request.prompt)
        return EnhanceResponse(original=request.prompt, enhanced=enhanced)
    except Exception as e:
        print(f"Enhance prompt error: {e}")
        # Fallback: just add some details without AI
        enhanced = f"{request.prompt}. A dramatic tale with intense action, emotional depth, and stunning visuals."
        return EnhanceResponse(original=request.prompt, enhanced=enhanced)


@app.get("/api/gallery")
async def get_gallery_prompts():
    """Get AI-generated gallery image prompts."""
    
    # Static gallery - no need to call LLM for this
    return {
        "images": [
            {"title": "Samurai at Sunset", "genre": "action", "prompt": "samurai warrior silhouette against orange sunset, katana drawn, cherry blossoms falling"},
            {"title": "Neon City", "genre": "sci-fi", "prompt": "cyberpunk street scene, neon signs, rain reflections, anime girl with umbrella"},
            {"title": "Dragon's Roar", "genre": "fantasy", "prompt": "dragon breathing fire, medieval castle, brave knight with shield, epic battle"},
            {"title": "School Days", "genre": "slice-of-life", "prompt": "anime schoolgirls walking home, cherry blossom trees, peaceful afternoon"},
            {"title": "Dark Forest", "genre": "horror", "prompt": "mysterious figure in dark forest, glowing eyes, full moon, mist"},
            {"title": "First Love", "genre": "romance", "prompt": "anime couple under umbrella, rain, city lights, romantic atmosphere"}
        ]
    }


@app.post("/api/generate", response_model=JobStatus)
async def start_generation(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """Start manga generation job."""
    
    # Create job ID
    job_id = str(uuid.uuid4())[:8]
    
    # Calculate total panels based on layout
    panels_per_page = {"2x2": 4, "2x3": 6, "3x3": 9, "full": 1}.get(request.layout, 4)
    total_panels = panels_per_page * request.pages
    
    # Initialize job status with enhanced tracking
    job = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        current_step="Initializing...",
        steps=[
            StepStatus(name="Story analyzed", status="pending"),
            StepStatus(name="Generating panels", status="pending"),
            StepStatus(name="Adding dialogue", status="pending"),
            StepStatus(name="Composing pages", status="pending"),
        ],
        current_panel=0,
        total_panels=total_panels,
        panel_previews=[],
        log_messages=[f"> Job {job_id} created", f"> Style: {request.style}", f"> Layout: {request.layout}"],
        layout=request.layout
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


class RegenerateRequest(BaseModel):
    page: int  # Page number (1-indexed)
    panel: int  # Panel index (0-indexed)
    prompt_override: Optional[str] = None  # Custom prompt or feedback


@app.post("/api/regenerate/{job_id}")
async def regenerate_panel(job_id: str, request: RegenerateRequest, background_tasks: BackgroundTasks):
    """Regenerate a single panel with optional custom prompt."""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Generation must be complete first")
    
    # Queue regeneration in background
    background_tasks.add_task(
        run_panel_regeneration,
        job_id,
        request.page,
        request.panel,
        request.prompt_override
    )
    
    return {
        "success": True,
        "message": f"Panel {request.panel + 1} on page {request.page} queued for regeneration",
        "job_id": job_id
    }


# ============================================
# Background Generation
# ============================================

def run_panel_regeneration(job_id: str, page: int, panel: int, prompt_override: Optional[str] = None):
    """Regenerate a single panel in background."""
    from scripts.generate_panels_api import PollinationsGenerator
    import time
    
    job = jobs[job_id]
    output_dir = Path("outputs") / job_id
    
    try:
        # Get the original prompt if available, or use override
        prompt = prompt_override or f"manga panel, anime style, high quality, detailed"
        
        # Generate new image
        generator = PollinationsGenerator(output_dir=str(output_dir))
        filename = f"regen_p{page}_panel{panel}_{int(time.time())}.png"
        
        result_path = generator.generate_image(
            prompt=prompt,
            filename=filename,
            width=1024,
            height=1024,
            style="anime"
        )
        
        if result_path:
            # Update job result with new panel
            if job.log_messages:
                job.log_messages.append(f"> ✅ Regenerated panel {panel + 1} on page {page}")
            
            # Update panel_previews if it exists
            if job.panel_previews:
                global_idx = (page - 1) * 4 + panel  # TODO: Use actual layout
                if global_idx < len(job.panel_previews):
                    job.panel_previews[global_idx] = f"/outputs/{job_id}/{filename}"
    except Exception as e:
        if job.log_messages:
            job.log_messages.append(f"> ❌ Regeneration failed: {str(e)}")


def run_generation(job_id: str, request: GenerateRequest):
    """Run manga generation in background with detailed progress tracking."""
    
    job = jobs[job_id]
    
    def log(msg: str):
        """Add a log message."""
        if job.log_messages is not None:
            job.log_messages.append(f"> {msg}")
    
    def update_step(idx: int, status: str, duration: str = None):
        """Update a step's status."""
        if job.steps and 0 <= idx < len(job.steps):
            job.steps[idx].status = status
            if duration:
                job.steps[idx].duration = duration
    
    try:
        # Import here to avoid circular imports
        from scripts.generate_manga import MangaGenerator, MangaConfig
        import time
        
        step_start = time.time()
        
        # Update status
        job.status = "generating"
        job.current_step = "Setting up..."
        job.progress = 5
        log("Initializing generation pipeline...")
        
        # Get API keys - FallbackLLM handles provider selection automatically
        groq_key = os.environ.get("GROQ_API_KEY")
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        
        if not groq_key and not nvidia_key:
            raise ValueError("Need GROQ_API_KEY or NVIDIA_API_KEY")
        
        log(f"API keys found: Groq={'yes' if groq_key else 'no'}, NVIDIA={'yes' if nvidia_key else 'no'}")
        
        # Create config
        config = MangaConfig(
            title=request.title,
            style=request.style,
            layout=request.layout,
            pages=request.pages,
            output_dir=str(OUTPUT_DIR / job_id),
            image_provider=request.image_provider,
            is_complete_story=False  # Default to chapter mode
        )
        
        # Create output directory for this job
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)
        
        # Step 1: Story Planning
        update_step(0, "in_progress")
        job.current_step = "Planning story with AI..."
        job.progress = 10
        log("Analyzing story prompt...")
        
        # Generate
        generator = MangaGenerator(config)
        
        # Prepare characters from request
        characters = None
        if request.characters:
            characters = [
                {
                    "name": c.name,
                    "appearance": c.appearance,
                    "personality": c.personality or ""
                }
                for c in request.characters
            ]
            log(f"Characters loaded: {', '.join(c.name for c in request.characters)}")
        
        step_duration = f"{time.time() - step_start:.1f}s"
        update_step(0, "completed", step_duration)
        log(f"Story planning complete ({step_duration})")
        
        # Step 2: Generate Panels
        step_start = time.time()
        update_step(1, "in_progress")
        job.current_step = "Generating panels..."
        job.progress = 20
        log(f"Starting parallel panel generation ({job.total_panels} panels)...")
        
        # Define callback for real-time progress updates
        def progress_handler(msg: str, percent: int, data: Optional[Dict] = None):
            job.current_step = msg
            if percent >= 0:
                job.progress = percent
            log(msg)
            
            # Handle live preview updates
            if data and data.get("event") == "page_complete":
                if job.result is None:
                    job.result = {"pages": [], "title": request.title}
                
                # Check if page already exists to avoid duplicates
                page_exists = False
                if "pages" in job.result:
                    for p in job.result["pages"]:
                        if p.get("page_number") == data["page_num"]:
                            page_exists = True
                            break
                
                if not page_exists:
                    # Store absolute path for API FileResponse serving
                    job.result["pages"].append({
                        "page_number": data["page_num"],
                        "page_image": data["image_path"],
                        "panels": [] # Panels added here if needed
                    })
                    log(f"📸 Live preview ready for Page {data['page_num']}")
            
            elif data and data.get("event") == "panel_complete":
                # Handle panel live preview
                if job.panel_previews is None:
                    job.panel_previews = []
                
                # Ensure list is large enough
                idx = data["panel_index"]
                while len(job.panel_previews) <= idx:
                    job.panel_previews.append("")
                
                # Store RELATIVE URL for direct frontend loading
                filename = Path(data["image_path"]).name
                relative_url = f"/outputs/{job_id}/{filename}"
                
                job.panel_previews[idx] = relative_url
                
                # Update counters and progress
                job.current_panel = idx + 1
                if job.total_panels and job.total_panels > 0:
                    # Progress logic: 20% (start) -> 90% (panels done)
                    # We map panel completion to the 20-90% range
                    panel_prog = 20 + int(70 * (idx + 1) / job.total_panels)
                    job.progress = panel_prog
                    
                log(f"🖼️ Generated panel {idx + 1} ({job.progress}%)")
            
            elif data and data.get("event") == "step_started":
                # Handle pipeline step transitions for Timeline
                step_type = data.get("step")
                if job.steps:
                    if step_type == "dialogue":
                        job.steps[1].status = "completed"  # Generating panels
                        job.steps[2].status = "in_progress" # Adding dialogue
                    elif step_type == "composition":
                        job.steps[2].status = "completed"  # Adding dialogue
                        job.steps[3].status = "in_progress" # Composing pages

            # Detect Story Analysis completion via log message
            if "Story planning complete" in msg and job.steps:
                job.steps[0].status = "completed"
                job.steps[1].status = "in_progress" # Start generating panels

        # This is where we hook into panel generation
        result = generator.generate_chapter(
            story_prompt=request.story_prompt,
            groq_api_key=groq_key or "",
            characters=characters,
            progress_callback=progress_handler
        )
        
        step_duration = f"{time.time() - step_start:.1f}s"
        update_step(1, "completed", step_duration)
        log(f"Panel generation complete ({step_duration})")
        
        # Step 3: Dialogue (happens inside generate_chapter)
        update_step(2, "completed", "auto")
        
        # Step 4: Composing
        update_step(3, "completed", "auto")
        log("Page composition complete")
        
        # Complete
        job.status = "completed"
        job.progress = 100
        job.current_step = "Done!"
        job.result = result
        log("✅ Generation complete!")
        
    except Exception as e:
        import traceback
        print(f"Generation error: {traceback.format_exc()}")
        job.status = "failed"
        job.error = str(e)
        job.current_step = "Failed"
        log(f"❌ Error: {str(e)}")


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
