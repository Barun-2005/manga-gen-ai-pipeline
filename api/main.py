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

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
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
    user_direction: Optional[str] = None # For continuation
    api_keys: Optional[Dict[str, str]] = None # For BYOK (Bring Your Own Key)


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

# Include auth routes
from api.routes.auth import router as auth_router
app.include_router(auth_router)

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


# NOTE: regenerate_panel endpoint is defined later with full LLM intelligence (see line ~720)


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
        # Priority: Request Keys (BYOK) > Environment Variables
        api_keys = request.api_keys or {}
        
        groq_key = api_keys.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
        nvidia_key = api_keys.get("NVIDIA_API_KEY") or os.environ.get("NVIDIA_API_KEY")
        gemini_key = api_keys.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
        
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

        # Step 1: Story Planning
        # ------------------------
        # NEW: Generate Story Blueprint if using StoryDirector
        # This gives the project a "Soul" for future high-quality continuation
        
        from src.ai.story_director import StoryDirector
        story_director = None
        blueprint = {}
        
        # gemini_key is already defined above
        if gemini_key:
            try:
                log("🧠 Creating Story Blueprint (High-Quality Context)...")
                story_director = StoryDirector(gemini_key)
                
                # Generate full blueprint
                blueprint = story_director.generate_blueprint(
                    story_prompt=request.story_prompt,
                    characters=[c.model_dump() for c in (request.characters or [])],
                    style=request.style
                )
                
                # Update blueprint generation state
                blueprint["generation_state"] = {
                    "current_chapter": 1,
                    "pages_generated": request.pages,
                    "last_page_summary": "Chapter 1 completed",
                    "last_panel_description": "End of Chapter 1"
                }
                
                log(f"📘 Blueprint created: {blueprint.get('title')} ({len(blueprint.get('chapter_outlines', []))} chapters)")
                
            except Exception as e:
                log(f"⚠️ Blueprint generation failed (will use fallback): {e}")

        # This is where we hook into panel generation
        result = generator.generate_chapter(
            story_prompt=request.story_prompt,
            groq_api_key=groq_key or "",
            characters=characters,
            progress_callback=progress_handler
        )
        
        # Verify result contains output (PDF path or pages)
        if not result.get("pages") and not result.get("pdf"):
             raise RuntimeError("Generator returned empty result - failures in image generation")

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
        
        # Save to MongoDB if available
        try:
            from src.database.mongodb import Database
            import asyncio
            from datetime import datetime
            
            project_data = {
                "job_id": job_id,
                "title": result.get("title", request.title), # Use result title if generated
                "pages": request.pages,
                "style": request.style,
                "layout": request.layout,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "cover_url": result.get("pages", [{}])[0].get("page_image", "") if result.get("pages") else "",
                "result": result,
                "blueprint": blueprint  # SAVE BLUEPRINT TO DB!
            }
            
            # Run async save in event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(Database.save_job(job_id, project_data))
            loop.close()
            log("💾 Saved to MongoDB with Blueprint")
        except Exception as db_error:
            print(f"⚠️ MongoDB save failed (continuing): {db_error}")
        
    except Exception as e:
        import traceback
        print(f"Generation error: {traceback.format_exc()}")
        job.status = "failed"
        job.error = str(e)
        job.current_step = "Failed"
        log(f"❌ Error: {str(e)}")

# ============================================
# Panel Regeneration API
# ============================================

# RegenerateRequest model is defined at the top of the file (line ~65)

@app.post("/api/regenerate/{job_id}")
async def regenerate_panel(job_id: str, request: RegenerateRequest):
    """
    INTELLIGENT panel regeneration using LLM to understand user feedback.
    
    Process:
    1. Get full story context from original generation
    2. Get character DNA for visual consistency
    3. Send user feedback + context to LLM
    4. LLM generates refined prompt that maintains consistency
    5. Generate new panel with proper style tags
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Can only regenerate completed jobs")
    
    try:
        import httpx
        from pathlib import Path
        from src.ai.llm_factory import get_llm
        
        # ============================================
        # Step 1: Extract full context from job result
        # ============================================
        
        result = job.result or {}
        story_summary = result.get("summary", "")
        chapter_title = result.get("title", "Untitled")
        style = result.get("style", "bw_manga")
        
        # Get character info for consistency
        characters = result.get("characters", [])
        character_descriptions = []
        for char in characters:
            if isinstance(char, dict):
                name = char.get("name", "Unknown")
                appearance = char.get("appearance", "")
                character_descriptions.append(f"{name}: {appearance}")
        characters_context = "\n".join(character_descriptions) if character_descriptions else "No specific characters defined"
        
        # Get the specific page and panel context
        pages = result.get("pages", [])
        original_panel_prompt = ""
        page_summary = ""
        panel_description = ""
        
        if request.page <= len(pages):
            page_data = pages[request.page - 1]
            page_summary = page_data.get("summary", page_data.get("page_summary", ""))
            
            # Get panel info - panels might be stored as paths or descriptions
            panels = page_data.get("panels", [])
            if request.panel < len(panels):
                panel_info = panels[request.panel]
                if isinstance(panel_info, str):
                    # It's a file path, try to get description from elsewhere
                    original_panel_prompt = f"Panel {request.panel + 1} of page {request.page}"
                else:
                    original_panel_prompt = str(panel_info)
        
        # ============================================
        # Step 2: Use LLM to understand user feedback
        # ============================================
        
        user_feedback = request.prompt_override or "Make this panel better"
        
        llm_prompt = f"""You are a manga panel prompt engineer. A user wants to REGENERATE a panel from their manga.

## STORY CONTEXT
Title: {chapter_title}
Story Summary: {story_summary}
Page {request.page} Summary: {page_summary}
Panel Number: {request.panel + 1}

## CHARACTERS (use these for visual consistency)
{characters_context}

## ORIGINAL PANEL
{original_panel_prompt}

## USER FEEDBACK
The user said: "{user_feedback}"

## YOUR TASK
Based on the user's NATURAL LANGUAGE feedback, generate an IMPROVED image prompt for this panel.
The prompt should:
1. Maintain visual consistency with the characters described
2. Fit the story context and this page's mood
3. Address whatever the user is unhappy about
4. Be formatted as comma-separated visual tags (NOT prose)

## STYLE
{"Black and white manga style: use 'manga, monochrome, ink lineart, screentone, dramatic shadows'" if style == "bw_manga" else "Color anime style: use 'anime, vibrant colors, cel shading, detailed'"}

Return ONLY the improved prompt (comma-separated tags), no explanation.
Example format: character action, expression, camera angle, lighting, environment, style tags"""

        print(f"\n🧠 Regeneration: Using LLM to understand feedback...")
        print(f"   User said: \"{user_feedback[:50]}...\"")
        
        # Get LLM to process the feedback
        llm = get_llm()
        refined_prompt = llm.generate(llm_prompt, max_tokens=500)
        refined_prompt = refined_prompt.strip()
        
        # Remove quotes if LLM added them
        if refined_prompt.startswith('"') and refined_prompt.endswith('"'):
            refined_prompt = refined_prompt[1:-1]
        
        print(f"   ✨ Refined prompt: {refined_prompt[:80]}...")
        
        # ============================================
        # Step 3: Generate new panel with Pollinations
        # ============================================
        
        # Properly encode prompt
        import urllib.parse
        encoded_prompt = urllib.parse.quote(refined_prompt)
        
        # Use a different seed for variation
        import random
        new_seed = random.randint(1000, 9999)
        
        img_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=768&nologo=true&seed={new_seed}"
        
        print(f"   🎨 Generating new panel...")
        
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.get(img_url)
            
            if response.status_code == 200:
                # Save new panel (with timestamp to avoid overwrite)
                import time
                output_dir = Path("outputs") / job_id
                timestamp = int(time.time())
                panel_filename = f"p{request.page:02d}_panel_{request.panel + 1:02d}_regen_{timestamp}.png"
                panel_path = output_dir / panel_filename
                
                with open(panel_path, "wb") as f:
                    f.write(response.content)
                
                print(f"   ✅ Saved: {panel_path}")
                
                return {
                    "success": True,
                    "panel_path": str(panel_path),
                    "refined_prompt": refined_prompt,
                    "message": f"Panel {request.panel + 1} regenerated with context-aware prompt"
                }
            else:
                raise HTTPException(status_code=500, detail=f"Image generation failed: {response.status_code}")
                
    except Exception as e:
        import traceback
        print(f"Regeneration error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Projects API (Dashboard)
# ============================================

@app.get("/api/projects")
async def get_projects():
    """Get all completed projects for dashboard."""
    try:
        from src.database.mongodb import Database
        
        # Connect if not connected
        if Database.db is None:
            await Database.connect_db()
        
        if Database.db is not None:
            # Get from MongoDB
            cursor = Database.db.jobs.find({}).sort("created_at", -1).limit(50)
            projects = []
            async for doc in cursor:
                # Remove MongoDB _id for JSON serialization
                doc.pop("_id", None)
                projects.append(doc)
            return {"projects": projects, "source": "mongodb"}
        else:
            # Fallback: return from in-memory jobs
            projects = []
            for job_id, job in jobs.items():
                if job.status == "completed" and job.result:
                    projects.append({
                        "job_id": job_id,
                        "title": job.result.get("title", "Untitled"),
                        "pages": len(job.result.get("pages", [])),
                        "style": job.result.get("style", "unknown"),
                        "created_at": job.result.get("created_at", ""),
                        "updated_at": job.result.get("created_at", ""),
                        "cover_url": job.result.get("pages", [{}])[0].get("page_image", "") if job.result.get("pages") else ""
                    })
            return {"projects": projects, "source": "memory"}
    except Exception as e:
        print(f"Projects API error: {e}")
        return {"projects": [], "error": str(e)}


# Save Project (with auth check)
class SaveProjectRequest(BaseModel):
    job_id: str
    title: str
    dialogues: Optional[dict] = None  # Panel dialogues from canvas
    
@app.post("/api/projects/save")
async def save_project(request: SaveProjectRequest, authorization: Optional[str] = Header(None)):
    """
    Save project to user's profile.
    Requires authentication - returns 401 if not logged in.
    """
    from src.database.mongodb import Database
    
    # Check authentication
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        # In production, decode JWT here
        # For now, use token as user_id indicator
        user_id = f"user_{token[:8]}" if token else None
    
    if not user_id:
        raise HTTPException(
            status_code=401, 
            detail="Please login to save your project"
        )
    
    # Get job data
    if request.job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[request.job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Can only save completed projects")
    
    # Build project data
    result = job.result or {}
    project_data = {
        "job_id": request.job_id,
        "title": request.title or result.get("title", "Untitled Manga"),
        "story_prompt": result.get("prompt", ""),
        "characters": result.get("characters", []),  # Character DNA
        "pages": result.get("pages", []),
        "dialogues": request.dialogues or {},  # Bubble positions/text from canvas
        "story_state": {
            "summary": result.get("summary", ""),
            "cliffhanger": result.get("cliffhanger", ""),
            "next_chapter_hook": result.get("next_chapter_hook", ""),
            "chapter_number": result.get("chapter_number", 1)
        },
        "style": result.get("style", "bw_manga"),
        "layout": result.get("layout", "2x2"),
        "page_count": len(result.get("pages", []))
    }
    
    # Connect and save
    if Database.db is None:
        await Database.connect_db()
    
    success = await Database.save_project(user_id, project_data)
    
    if success:
        return {"success": True, "message": "Project saved to your profile!", "job_id": request.job_id}
    else:
        raise HTTPException(status_code=500, detail="Failed to save project. Database may be unavailable.")


@app.get("/api/projects/{job_id}")
async def get_project(job_id: str):
    """Get full project data for loading in canvas."""
    from src.database.mongodb import Database
    
    # Try database first
    if Database.db is None:
        await Database.connect_db()
    
    if Database.db is not None:
        project = await Database.get_project(job_id)
        if project:
            project.pop("_id", None)
            return {"project": project, "source": "database"}
    
    # Fallback to in-memory jobs
    if job_id in jobs:
        job = jobs[job_id]
        if job.status == "completed":
            return {
                "project": {
                    "job_id": job_id,
                    "title": job.result.get("title", "Untitled") if job.result else "Untitled",
                    "characters": job.result.get("characters", []) if job.result else [],
                    "pages": job.result.get("pages", []) if job.result else [],
                    "dialogues": {},
                    "style": job.result.get("style", "bw_manga") if job.result else "bw_manga"
                },
                "source": "memory"
            }
    
    raise HTTPException(status_code=404, detail="Project not found")


# Continue Chapter (Smart continuation with same characters)
class ContinueChapterRequest(BaseModel):
    pages: int = 3
    chapter_title: Optional[str] = None
    user_direction: Optional[str] = None  # "I want the hero to meet a villain"

@app.post("/api/projects/{job_id}/continue")
async def continue_chapter(job_id: str, request: ContinueChapterRequest, background_tasks: BackgroundTasks):
    """
    Generate next chapter/pages continuing the story.
    Uses StoryDirector.plan_continuation() with blueprint for consistency.
    """
    from src.database.mongodb import Database
    from src.ai.story_director import StoryDirector
    
    # Get existing project from DB
    if Database.db is None:
        await Database.connect_db()
    
    project = None
    if Database.db is not None:
        project = await Database.get_project(job_id)
    
    # Fallback to in-memory jobs
    if not project and job_id in jobs:
        job = jobs[job_id]
        if job.result:
            project = {
                "job_id": job_id,
                "characters": job.result.get("characters", []),
                "blueprint": job.result.get("blueprint", {}),
                "story_state": {
                    "summary": job.result.get("summary", ""),
                    "pages_generated": len(job.result.get("pages", [])),
                    "last_page_summary": "",
                    "last_panel_description": ""
                },
                "style": job.result.get("style", "bw_manga"),
                "story_prompt": job.result.get("prompt", "")
            }
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Create new job for continuation
    new_job_id = f"continue_{job_id}_{int(datetime.now().timestamp())}"
    
    # Extract blueprint or build one from existing data
    blueprint = project.get("blueprint", {})
    if not blueprint or not blueprint.get("characters"):
        # Build minimal blueprint from existing project data
        blueprint = {
            "title": project.get("title", "Continued Manga"),
            "overall_arc": project.get("story_prompt", ""),
            "characters": project.get("characters", []),
            "world_details": {"visual_style": project.get("style", "bw_manga")},
            "chapter_outlines": []
        }
    
    # Get continuation context
    story_state = project.get("story_state", {})
    previous_summary = story_state.get("summary", "") or story_state.get("pages_summary", "")
    last_panel = story_state.get("last_panel_description", "")
    
    # If no previous summary, try to build one from pages
    if not previous_summary and project.get("pages"):
        pages = project.get("pages", [])
        summaries = [p.get("page_summary", p.get("summary", "")) for p in pages if p]
        previous_summary = " ".join(summaries[-3:]) if summaries else "Story just began"
    
    # Create job for tracking
    new_job = Job(
        job_id=new_job_id,
        status="processing",
        progress=0,
        current_step="Planning continuation...",
        total_panels=request.pages * 4
    )
    jobs[new_job_id] = new_job
    
    # Run continuation in background
    async def run_continuation():
        try:
            # Initialize StoryDirector
            director = StoryDirector()
            
            new_job.current_step = "Generating next pages with StoryDirector..."
            new_job.progress = 10
            
            # Use plan_continuation for story
            continuation = director.plan_continuation(
                blueprint=blueprint,
                previous_pages_summary=previous_summary,
                last_panel_description=last_panel,
                new_page_count=request.pages,
                user_direction=request.user_direction
            )
            
            if not continuation.get("pages"):
                new_job.status = "failed"
                new_job.error = "Failed to generate continuation pages"
                return
            
            new_job.current_step = "Generating panel images..."
            new_job.progress = 30
            
            # Generate images for each panel
            # CLEAN IMPLEMENTATION: Use ImageProvider Abstraction
            from src.ai.image_factory import get_image_provider
            
            # Using automatic provider selection (defaults to Pollinations, falls back to others)
            image_provider = get_image_provider(provider="auto")
            
            import random
            from pathlib import Path
            
            output_dir = Path("outputs") / new_job_id
            output_dir.mkdir(parents=True, exist_ok=True)
            
            style_tags = "manga style, monochrome, ink lineart, screentone, high contrast" if project.get("style") == "bw_manga" else "anime style, vibrant colors, cel shading"
            
            pages_result = []
            total_panels = sum(len(p.get("panels", [])) for p in continuation["pages"])
            panels_done = 0
            
            # Build character DNA lookup from blueprint
            char_dna = {}
            for char in blueprint.get("characters", []):
                name = char.get("name", "")
                appearance = char.get("appearance", "")
                if name and appearance:
                    char_dna[name.lower()] = appearance
            
            # Helper to generate in loop (no async context manager needed for provider)
            for page in continuation["pages"]:
                page_num = page.get("page_number", len(pages_result) + 1)
                panels = page.get("panels", [])
                panel_images_data = [] # Stores full metadata
                
                for panel in panels:
                    panel_num = panel.get("panel_number", len(panel_images_data) + 1)
                    visual_prompt = panel.get("visual_prompt", "manga scene")
                    
                    # Inject character DNA for consistency
                    characters_in_panel = panel.get("characters_present", [])
                    char_tags = []
                    for char_name in characters_in_panel:
                        dna = char_dna.get(char_name.lower(), "")
                        if dna and dna.lower() not in visual_prompt.lower():
                            char_tags.append(f"{char_name} ({dna})")
                    
                    if char_tags:
                        visual_prompt = f"{', '.join(char_tags)}, {visual_prompt}"
                    
                    # Add camera/composition from panel if available
                    shot_type = panel.get("shot_type", "")
                    camera_angle = panel.get("camera_angle", "")
                    lighting = panel.get("lighting_mood", "")
                    
                    if shot_type and shot_type not in visual_prompt:
                        visual_prompt = f"{shot_type}, {visual_prompt}"
                    if camera_angle and camera_angle not in visual_prompt:
                        visual_prompt = f"{camera_angle}, {visual_prompt}"
                    if lighting and lighting not in visual_prompt:
                        visual_prompt = f"{visual_prompt}, {lighting}"
                    
                    # Add style tags if not present
                    if "manga style" not in visual_prompt.lower():
                        visual_prompt = f"{visual_prompt}, {style_tags}"
                    
                    # Generate image
                    seed = random.randint(1000, 9999)
                    
                    try:
                        # Use abstract provider!
                        image_bytes = await image_provider.generate(
                            prompt=visual_prompt,
                            width=768,
                            height=768,
                            seed=seed
                        )
                        
                        panel_path = output_dir / f"cont_{new_job_id}_p{page_num}_panel{panel_num}.png"
                        with open(panel_path, "wb") as f:
                            f.write(image_bytes)
                            
                        # Append full metadata structure required by frontend
                        panel_images_data.append({
                            "panel_number": panel_num,
                            "image_path": str(panel_path),
                            "prompt": visual_prompt,
                            "dialogue": panel.get("dialogue", [])
                        })
                        
                    except Exception as e:
                        print(f"⚠️ Panel generation failed: {e}")
                    
                    panels_done += 1
                    new_job.progress = 30 + int(60 * panels_done / max(total_panels, 1))
                    new_job.current_step = f"Generated panel {panels_done}/{total_panels}"
                
                pages_result.append({
                    "page_number": page_num,
                    "page_summary": page.get("page_summary", ""),
                    "panels": panel_images_data,
                    "dialogue": []
                })
            
            # Update project state for next continuation
            new_job.progress = 95
            new_job.current_step = "Saving continuation state..."
            
            updated_state = {
                "summary": continuation.get("progress_summary", previous_summary),
                "pages_generated": (story_state.get("pages_generated", 0) or 0) + request.pages,
                "last_page_summary": continuation.get("progress_summary", ""),
                "last_panel_description": continuation.get("last_panel_description", "")
            }
            
            # Update project in DB
            if Database.db is not None:
                await Database.db.projects.update_one(
                    {"job_id": job_id},
                    {
                        "$push": {"pages": {"$each": pages_result}},
                        "$set": {"story_state": updated_state}
                    }
                )
            
            # Set job result
            new_job.result = {
                "title": blueprint.get("title", "Continued Chapter"),
                "pages": pages_result,
                "characters": blueprint.get("characters", []),
                "continuation_state": updated_state,
                "parent_job_id": job_id
            }
            new_job.status = "completed"
            new_job.progress = 100
            new_job.current_step = "Continuation complete!"
            print(f"✅ Continuation complete: {len(pages_result)} new pages")
            
        except Exception as e:
            import traceback
            print(f"❌ Continuation failed: {traceback.format_exc()}")
            new_job.status = "failed"
            new_job.error = str(e)
    
    # Start background task
    background_tasks.add_task(run_continuation)
    
    return {
        "job_id": new_job_id,
        "parent_job_id": job_id,
        "pages_requested": request.pages,
        "status": "processing",
        "message": f"Generating {request.pages} new pages...",
        "check_status_at": f"/api/status/{new_job_id}"
    }


# ============================================
# Download API (with dialogue rendering on images)
# ============================================

@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str, dialogues: Optional[str] = None):
    """
    Download manga as PNG, PDF, or ZIP.
    If dialogues JSON is provided, renders them onto the images.
    """
    from pathlib import Path
    from io import BytesIO
    import json
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed" or not job.result:
        raise HTTPException(status_code=400, detail="Job not complete")
    
    output_dir = Path("outputs") / job_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Output directory not found")
    
    # Parse dialogues if provided
    bubble_data = {}
    if dialogues:
        try:
            bubble_data = json.loads(dialogues)
        except:
            pass
    
    if file_type == "png":
        # Return first page as PNG
        pages = job.result.get("pages", [])
        if pages:
            first_page = pages[0]
            page_image = first_page.get("page_image", "")
            if page_image and Path(page_image).exists():
                return FileResponse(page_image, media_type="image/png", filename=f"{job_id}_page1.png")
        raise HTTPException(status_code=404, detail="No page image found")
    
    elif file_type == "pdf":
        # Generate PDF with dialogues rendered on images
        try:
            from PIL import Image, ImageDraw, ImageFont
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            
            pages = job.result.get("pages", [])
            if not pages:
                raise HTTPException(status_code=404, detail="No pages to export")
            
            # Create PDF in memory
            pdf_buffer = BytesIO()
            pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
            page_width, page_height = A4
            
            for page_idx, page in enumerate(pages):
                page_image_path = page.get("page_image", "")
                if not page_image_path or not Path(page_image_path).exists():
                    continue
                
                # Load and optionally render dialogues
                img = Image.open(page_image_path)
                
                # Get dialogues for this page's panels
                page_num = page.get("page_number", page_idx + 1)
                panels = page.get("panels", [])
                
                for panel_idx in range(len(panels)):
                    panel_id = f"page-{page_num}-panel-{panel_idx}"
                    panel_dialogues = bubble_data.get(panel_id, [])
                    
                    if panel_dialogues:
                        # Render dialogues on image
                        draw = ImageDraw.Draw(img)
                        
                        # Get panel region (approximate based on grid)
                        grid_cols = 2
                        grid_rows = 2
                        panel_w = img.width // grid_cols
                        panel_h = img.height // grid_rows
                        panel_x = (panel_idx % grid_cols) * panel_w
                        panel_y = (panel_idx // grid_cols) * panel_h
                        
                        for bubble in panel_dialogues:
                            # Calculate bubble position
                            bx = panel_x + int((bubble.get("x", 50) / 100) * panel_w)
                            by = panel_y + int((bubble.get("y", 50) / 100) * panel_h)
                            text = bubble.get("text", "")
                            style = bubble.get("style", "speech")
                            
                            if not text:
                                continue
                            
                            # Try to load a font, fallback to default
                            try:
                                font = ImageFont.truetype("arial.ttf", 14)
                            except:
                                font = ImageFont.load_default()
                            
                            # Get text size
                            text_bbox = draw.textbbox((0, 0), text, font=font)
                            tw = text_bbox[2] - text_bbox[0]
                            th = text_bbox[3] - text_bbox[1]
                            
                            # Draw bubble based on style
                            padding = 10
                            if style == "narrator":
                                # Dark box
                                draw.rectangle([bx - padding, by - padding, bx + tw + padding, by + th + padding], fill="black")
                                draw.text((bx, by), text, fill="white", font=font)
                            elif style == "thought":
                                # Cloud-like ellipse
                                draw.ellipse([bx - padding - 5, by - padding - 5, bx + tw + padding + 5, by + th + padding + 5], fill="white", outline="black", width=2)
                                draw.text((bx, by), text, fill="gray", font=font)
                            else:
                                # Speech bubble
                                draw.ellipse([bx - padding, by - padding, bx + tw + padding, by + th + padding], fill="white", outline="black", width=2)
                                draw.text((bx, by), text, fill="black", font=font)
                                # Draw tail
                                draw.polygon([
                                    (bx + tw // 2, by + th + padding),
                                    (bx + tw // 2 + 10, by + th + padding + 15),
                                    (bx + tw // 2 - 5, by + th + padding)
                                ], fill="white", outline="black")
                
                # Save to temp and add to PDF
                img_buffer = BytesIO()
                img.save(img_buffer, format="PNG")
                img_buffer.seek(0)
                
                # Draw on PDF page
                pdf.drawImage(ImageReader(img_buffer), 0, 0, width=page_width, height=page_height)
                pdf.showPage()
            
            pdf.save()
            pdf_buffer.seek(0)
            
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename={job_id}_manga.pdf"}
            )
        except ImportError as e:
            # Fallback if reportlab not available
            raise HTTPException(status_code=500, detail=f"PDF generation requires reportlab: {e}")
    
    elif file_type == "zip":
        # Create ZIP with all images
        import zipfile
        from fastapi.responses import StreamingResponse
        
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            for f in output_dir.glob("*.png"):
                zf.write(f, f.name)
            for f in output_dir.glob("*.jpg"):
                zf.write(f, f.name)
        
        zip_buffer.seek(0)
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={"Content-Disposition": f"attachment; filename={job_id}_assets.zip"}
        )
    
    raise HTTPException(status_code=400, detail="Invalid file type. Use: png, pdf, or zip")


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
