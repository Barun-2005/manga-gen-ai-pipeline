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
    image_provider: str = "pollinations"  # "pollinations" (cloud), "comfyui" (local Z-Image), or "auto"
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
    # For dynamic layouts (AI), estimate ~4 panels per page (updated after LLM decides)
    if request.layout in ["ai", "dynamic", "AI"]:
        panels_per_page = 4  # Estimate for progress bar
        is_dynamic = True
    else:
        panels_per_page = {"2x2": 4, "2x3": 6, "3x3": 9, "full": 1}.get(request.layout, 4)
        is_dynamic = False
    total_panels = panels_per_page * request.pages
    
    # Initialize job status with enhanced tracking
    # V4: Added "Generating cover" step, dynamic panel count updated after LLM planning
    job = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        current_step="Initializing...",
        steps=[
            StepStatus(name="Story planning", status="pending"),
            StepStatus(name="Generating panels", status="pending"),
            StepStatus(name="Composing pages", status="pending"),
            StepStatus(name="Generating cover", status="pending"),
            StepStatus(name="Finalizing", status="pending"),
        ],
        current_panel=0,
        total_panels=total_panels,  # Estimate for dynamic, updated after LLM planning
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
    """Get job status - checks memory first, then local saved files."""
    if job_id in jobs:
        return jobs[job_id]
    
    # Fallback: Try to load from local saved project files
    output_dir = Path("outputs") / job_id
    project_save = output_dir / "project_save.json"
    story_state = output_dir / "story_state.json"
    
    if project_save.exists() or story_state.exists():
        try:
            import json
            
            # Load saved project data
            if project_save.exists():
                with open(project_save, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            else:
                with open(story_state, 'r', encoding='utf-8') as f:
                    saved_data = json.load(f)
            
            # Defensive check: ensure saved_data is a dict
            if not isinstance(saved_data, dict):
                print(f"Warning: saved_data for {job_id} is not a dict, type={type(saved_data)}")
                saved_data = {}
            
            # Helper: safely get nested dict values
            def safe_get(d, key, default=None):
                if isinstance(d, dict):
                    return d.get(key, default)
                return default
            
            # Get metadata and generation_params safely
            metadata = safe_get(saved_data, "metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            gen_params = safe_get(saved_data, "generation_params", {})
            if not isinstance(gen_params, dict):
                gen_params = {}
            
            # Reconstruct result from saved data or find pages
            pages = saved_data.get("pages", [])
            if not isinstance(pages, list):
                pages = []
            result_pages = []
            
            # Find page images from the output directory
            page_images = sorted(output_dir.glob("manga_page_*.png"))
            
            # Build page data with panel geometry from story_state
            # Try 'chapters' first (newer format), then 'chapter_plan.pages' (generator format)
            chapters = saved_data.get("chapters", [])
            if not isinstance(chapters, list):
                chapters = []
            
            # Fallback: Try chapter_plan (generator saves here)
            if not chapters:
                chapter_plan = saved_data.get("chapter_plan", {})
                if isinstance(chapter_plan, dict):
                    plan_pages = chapter_plan.get("pages", [])
                    if plan_pages:
                        # Wrap in single chapter for consistent processing
                        chapters = [{"pages": plan_pages}]
            
            # Create a map of page_number -> panels for easy lookup
            page_panels_map = {}
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    continue
                chapter_pages = chapter.get("pages", [])
                if not isinstance(chapter_pages, list):
                    continue
                for page in chapter_pages:
                    if not isinstance(page, dict):
                        continue
                    page_num = page.get("page_number", 0)
                    panels = page.get("panels", [])
                    if panels and isinstance(panels, list):
                        page_panels_map[page_num] = panels
            
            # DEBUG: Log panel geometry loading
            print(f"📐 Loading panels from story_state for {job_id}:")
            print(f"   Chapters found: {len(chapters)}")
            print(f"   Pages with geometry: {list(page_panels_map.keys())}")
            if page_panels_map:
                first_page = list(page_panels_map.keys())[0]
                first_panels = page_panels_map[first_page]
                if first_panels:
                    first_panel = first_panels[0]
                    print(f"   Sample panel (page {first_page}): x={first_panel.get('x')}, y={first_panel.get('y')}, w={first_panel.get('w')}, h={first_panel.get('h')}")
            
            # FALLBACK: If page geometry is missing, try to reconstruct from layout_template
            # This fixes existing projects where chapters were overwritten
            from scripts.layout_templates import LAYOUT_TEMPLATES
            
            # Also build a map of page_number -> layout_template for fallback
            page_layout_map = {}
            for chapter in chapters:
                if isinstance(chapter, dict):
                    for page in chapter.get("pages", []):
                        if isinstance(page, dict):
                            page_num = page.get("page_number", 0)
                            layout_template = page.get("layout_template", "")
                            if layout_template:
                                page_layout_map[page_num] = layout_template
            
            for idx, page_img in enumerate(page_images):
                page_num = idx + 1
                page_data = {
                    "page_number": page_num,
                    "page_image": str(page_img)
                }
                
                # Add panels with x,y,w,h geometry if available
                if page_num in page_panels_map:
                    page_data["panels"] = page_panels_map[page_num]
                else:
                    # FALLBACK: Reconstruct from layout_template
                    layout_name = page_layout_map.get(page_num, "2x2_grid")
                    template = LAYOUT_TEMPLATES.get(layout_name, LAYOUT_TEMPLATES.get("2x2_grid", {}))
                    template_layout = template.get("layout", [])
                    
                    # Build panels with geometry from template
                    reconstructed_panels = []
                    for panel_idx, panel_geo in enumerate(template_layout):
                        reconstructed_panels.append({
                            "panel_number": panel_idx + 1,
                            "x": panel_geo.get("x", 0),
                            "y": panel_geo.get("y", 0),
                            "w": panel_geo.get("w", 50),
                            "h": panel_geo.get("h", 50),
                            "description": f"Panel {panel_idx + 1}"
                        })
                    
                    if reconstructed_panels:
                        page_data["panels"] = reconstructed_panels
                        print(f"   🔧 Reconstructed geometry for page {page_num} from {layout_name}")
                
                result_pages.append(page_data)
            
            # Find or create PDF path
            pdf_files = list(output_dir.glob("*.pdf"))
            pdf_path = str(pdf_files[0]) if pdf_files else ""
            
            # Extract dialogue data from story_state chapters/pages
            llm_dialogues = {}
            chapters = saved_data.get("chapters", [])
            if not isinstance(chapters, list):
                chapters = []
            for chapter in chapters:
                if not isinstance(chapter, dict):
                    continue
                chapter_pages = chapter.get("pages", [])
                if not isinstance(chapter_pages, list):
                    continue
                for page in chapter_pages:
                    if not isinstance(page, dict):
                        continue
                    page_num = page.get("page_number", 1)
                    panels = page.get("panels", [])
                    if not isinstance(panels, list):
                        continue
                    for panel_idx, panel in enumerate(panels):
                        if not isinstance(panel, dict):
                            continue
                        panel_dialogues = panel.get("dialogue", [])
                        if panel_dialogues and isinstance(panel_dialogues, list):
                            panel_key = f"page-{page_num}-panel-{panel_idx}"
                            llm_dialogues[panel_key] = [
                                {
                                    "id": f"llm-{page_num}-{panel_idx}-{i}",
                                    "text": d.get("text", "") if isinstance(d, dict) else str(d),
                                    "x": 10,  # Default position
                                    "y": 10 + i * 20,  # Stack vertically
                                    "style": d.get("style", "speech") if isinstance(d, dict) else "speech",
                                    "character": d.get("character", "") if isinstance(d, dict) else "",
                                    "fontSize": 11
                                }
                                for i, d in enumerate(panel_dialogues)
                            ]
            
            # Build result pages with dialogue data
            for idx, page_info in enumerate(result_pages):
                page_num = page_info.get("page_number", idx + 1)
                # Find dialogue data for this page's panels
                page_dialogue = []
                for panel_idx in range(4):  # Assume 4 panels per page
                    panel_key = f"page-{page_num}-panel-{panel_idx}"
                    if panel_key in llm_dialogues:
                        page_dialogue.append({
                            "panel_index": panel_idx,
                            "dialogues": [
                                {"text": d["text"], "character": d.get("character", ""), "style": d.get("style", "speech")}
                                for d in llm_dialogues[panel_key]
                            ]
                        })
                if page_dialogue:
                    page_info["dialogue"] = page_dialogue
            
            # Create a completed job status from saved data
            job = JobStatus(
                job_id=job_id,
                status="completed",
                progress=100,
                current_step="Loaded from saved project",
                steps=[
                    StepStatus(name="Story analyzed", status="completed"),
                    StepStatus(name="Generating panels", status="completed"),
                    StepStatus(name="Adding dialogue", status="completed"),
                    StepStatus(name="Composing pages", status="completed"),
                ],
                current_panel=0,
                total_panels=len(result_pages) * 4,
                panel_previews=[],
                log_messages=["Loaded from saved project"],
                layout=gen_params.get("layout_template", "2x2"),
                result={
                    "manga_title": metadata.get("manga_title", gen_params.get("title", "Saved Manga")),
                    "title": gen_params.get("title", saved_data.get("title", "Saved Manga")),
                    "cover_url": metadata.get("cover_url", f"/outputs/{job_id}/manga_page_01.png"),
                    "pages": result_pages,  # Now includes dialogue data!
                    "pdf": pdf_path,
                    "style": gen_params.get("style", "bw_manga"),
                    "layout": gen_params.get("layout_template", "2x2")
                }
            )
            
            # Cache it in memory for faster subsequent access
            jobs[job_id] = job
            return job
            
        except Exception as e:
            import traceback
            print(f"Error loading saved project {job_id}: {e}")
            traceback.print_exc()
    
    raise HTTPException(status_code=404, detail="Job not found")


# NOTE: regenerate_panel endpoint is defined later with full LLM intelligence (see line ~720)


# V4: Direct PDF file endpoint - serves pre-generated PDFs without requiring jobs dict
@app.get("/api/pdf/{job_id}")
async def get_pdf_direct(job_id: str):
    """Serve pre-generated PDF directly from filesystem."""
    from pathlib import Path
    
    output_dir = Path("outputs") / job_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find PDF file
    pdf_files = list(output_dir.glob("*.pdf"))
    if pdf_files:
        return FileResponse(
            str(pdf_files[0]),
            media_type="application/pdf",
            filename=pdf_files[0].name
        )
    
    raise HTTPException(status_code=404, detail="No PDF found for this project")

@app.get("/api/download/{job_id}/{file_type}")
async def download_file(job_id: str, file_type: str, dialogues: Optional[str] = None):
    """Download generated manga file with optional dialogue bubble rendering."""
    from pathlib import Path
    
    output_dir = Path("outputs") / job_id
    
    # V4: Fallback chain - check memory, then filesystem
    job = jobs.get(job_id)
    result = None
    
    if job and job.result:
        result = job.result
    elif output_dir.exists():
        # Fallback: load from filesystem if server reloaded
        page_files = sorted(output_dir.glob("manga_page_*.png"))
        if page_files:
            result = {
                "pages": [
                    {
                        "page_number": i + 1,
                        "page_image": str(pf),
                        "panels": []
                    }
                    for i, pf in enumerate(page_files)
                ]
            }
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or no output files")
    
    # For PDF with dialogues - render bubbles onto images
    if file_type == "pdf" and dialogues:
        try:
            import json
            from PIL import Image, ImageDraw, ImageFont
            import io
            import tempfile
            
            dialogue_data = json.loads(dialogues)
            pages = result.get("pages", [])
            
            if not pages:
                raise HTTPException(status_code=404, detail="No pages to export")
            
            # Process each page and render bubbles
            rendered_pages = []
            output_dir = Path("outputs") / job_id
            
            for page_info in pages:
                page_num = page_info.get("page_number", 1)
                page_path = page_info.get("page_image")
                
                if not page_path or not Path(page_path).exists():
                    continue
                
                # Load page image
                img = Image.open(page_path).convert("RGBA")
                draw = ImageDraw.Draw(img)
                
                # Parse layout to get grid (default 2x2)
                layout = result.get("layout", "2x2") or "2x2"
                parts = layout.split("x")
                cols = int(parts[0]) if len(parts) >= 1 else 2
                rows = int(parts[1]) if len(parts) >= 2 else 2
                
                # Calculate panel dimensions on the page
                # Typical manga page: has title area at top, margins around panels
                title_height = int(img.height * 0.05)  # Title takes ~5% of height
                margin = int(img.width * 0.02)  # Small margin
                gutter = int(img.width * 0.01)  # Gap between panels
                
                content_width = img.width - (2 * margin) - ((cols - 1) * gutter)
                content_height = img.height - title_height - (2 * margin) - ((rows - 1) * gutter)
                
                panel_width = content_width // cols
                panel_height = content_height // rows
                
                # Get dialogues for each panel on this page
                for panel_idx in range(cols * rows):
                    panel_key = f"page-{page_num}-panel-{panel_idx}"
                    panel_bubbles = dialogue_data.get(panel_key, [])
                    
                    if not panel_bubbles:
                        continue
                    
                    # Calculate panel position on page
                    panel_col = panel_idx % cols
                    panel_row = panel_idx // cols
                    
                    panel_x = margin + panel_col * (panel_width + gutter)
                    panel_y = title_height + margin + panel_row * (panel_height + gutter)
                    
                    for bubble in panel_bubbles:
                        # Calculate bubble position within panel (x/y are percentages within panel)
                        x_pct = bubble.get("x", 10) / 100
                        y_pct = bubble.get("y", 10) / 100
                        
                        # Position relative to panel, not whole page
                        bubble_x = int(panel_x + x_pct * panel_width)
                        bubble_y = int(panel_y + y_pct * panel_height)
                        
                        text = bubble.get("text", "")
                        style = bubble.get("style", "speech")
                        font_size = bubble.get("fontSize", 11)
                        
                        if not text:
                            continue
                        
                        # Try to load a font
                        try:
                            font = ImageFont.truetype("arial.ttf", font_size * 2)  # Scale up for image
                        except:
                            try:
                                font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", font_size * 2)
                            except:
                                font = ImageFont.load_default()
                        
                        # Word wrap text to fit in bubble (max ~20 chars per line for manga)
                        words = text.split()
                        lines = []
                        current_line = ""
                        for word in words:
                            test_line = f"{current_line} {word}".strip()
                            if len(test_line) > 25:
                                if current_line:
                                    lines.append(current_line)
                                current_line = word
                            else:
                                current_line = test_line
                        if current_line:
                            lines.append(current_line)
                        
                        wrapped_text = "\n".join(lines)
                        
                        # Calculate text bbox
                        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]
                        
                        # Bubble padding
                        padding = 10
                        bubble_width = text_width + padding * 2
                        bubble_height = text_height + padding * 2
                        
                        # Clamp bubble to stay within panel
                        bubble_x = max(panel_x, min(bubble_x, panel_x + panel_width - bubble_width))
                        bubble_y = max(panel_y, min(bubble_y, panel_y + panel_height - bubble_height))
                        
                        # Draw bubble background based on style (JJK-style matching canvas!)
                        if style == "thought":
                            # Cloud-like thought bubble - draw overlapping circles
                            cx = bubble_x + bubble_width // 2
                            cy = bubble_y + bubble_height // 2
                            # Main ellipse
                            draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                        fill="white", outline="gray", width=2)
                            # Cloud bumps around edges
                            bump_size = min(bubble_width, bubble_height) // 4
                            for angle in [0, 45, 90, 135, 180, 225, 270, 315]:
                                import math
                                bx = cx + int((bubble_width//2 - bump_size//2) * math.cos(math.radians(angle)))
                                by = cy + int((bubble_height//2 - bump_size//2) * math.sin(math.radians(angle)))
                                draw.ellipse([bx - bump_size//2, by - bump_size//2, 
                                            bx + bump_size//2, by + bump_size//2], 
                                            fill="white", outline="gray", width=1)
                            # Small thought bubbles below
                            draw.ellipse([bubble_x + 5, bubble_y + bubble_height + 3, 
                                         bubble_x + 12, bubble_y + bubble_height + 10], fill="white", outline="gray", width=1)
                            draw.ellipse([bubble_x, bubble_y + bubble_height + 12, 
                                         bubble_x + 6, bubble_y + bubble_height + 18], fill="white", outline="gray", width=1)
                            
                        elif style == "shout":
                            # JJK-style spiky/jagged polygon
                            # Create jagged edge points
                            points = []
                            spikes = 12  # Number of spikes
                            for i in range(spikes):
                                angle = (360 / spikes) * i
                                import math
                                # Alternate between outer and inner radius for spikes
                                if i % 2 == 0:
                                    r_x = bubble_width // 2 + 8  # Outer spike
                                    r_y = bubble_height // 2 + 8
                                else:
                                    r_x = bubble_width // 2 - 5  # Inner notch
                                    r_y = bubble_height // 2 - 5
                                cx = bubble_x + bubble_width // 2
                                cy = bubble_y + bubble_height // 2
                                px = cx + int(r_x * math.cos(math.radians(angle - 90)))
                                py = cy + int(r_y * math.sin(math.radians(angle - 90)))
                                points.append((px, py))
                            draw.polygon(points, fill="white", outline="black", width=3)
                            
                        elif style == "narrator":
                            # Caption box - dark gradient-like with left accent
                            draw.rectangle([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                          fill=(30, 30, 35), outline=None)
                            # Left accent bar
                            draw.rectangle([bubble_x, bubble_y, bubble_x + 4, bubble_y + bubble_height], 
                                          fill=(100, 100, 120))
                            
                        elif style == "whisper":
                            # Dashed outline ellipse (simulated with dots)
                            # First draw white background
                            draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                        fill="white", outline=None)
                            # Draw dashed border using line segments
                            cx = bubble_x + bubble_width // 2
                            cy = bubble_y + bubble_height // 2
                            import math
                            dash_count = 20
                            for i in range(dash_count):
                                if i % 2 == 0:  # Only draw every other segment (dash)
                                    angle1 = (360 / dash_count) * i
                                    angle2 = (360 / dash_count) * (i + 0.7)
                                    x1 = cx + int((bubble_width // 2) * math.cos(math.radians(angle1)))
                                    y1 = cy + int((bubble_height // 2) * math.sin(math.radians(angle1)))
                                    x2 = cx + int((bubble_width // 2) * math.cos(math.radians(angle2)))
                                    y2 = cy + int((bubble_height // 2) * math.sin(math.radians(angle2)))
                                    draw.line([(x1, y1), (x2, y2)], fill="gray", width=1)
                        else:
                            # Regular speech bubble - clean ellipse
                            draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                        fill="white", outline="black", width=2)
                        
                        # Draw text (with special handling for narrator)
                        text_x = bubble_x + padding
                        text_y = bubble_y + padding
                        if style == "narrator":
                            text_x += 6  # Account for left accent bar
                            draw.multiline_text((text_x, text_y), wrapped_text, fill="white", font=font)
                        else:
                            draw.multiline_text((text_x, text_y), wrapped_text, fill="black", font=font)
                
                # Convert to RGB for PDF
                rendered_pages.append(img.convert("RGB"))
            
            if not rendered_pages:
                raise HTTPException(status_code=500, detail="Could not render pages with dialogues")
            
            # Create PDF with rendered pages
            pdf_path = output_dir / f"manga_{job_id}_with_dialogues.pdf"
            rendered_pages[0].save(
                str(pdf_path),
                "PDF",
                resolution=150.0,
                save_all=True,
                append_images=rendered_pages[1:] if len(rendered_pages) > 1 else []
            )
            
            return FileResponse(
                str(pdf_path),
                media_type="application/pdf",
                filename=f"manga_{job_id}.pdf"
            )
            
        except json.JSONDecodeError:
            print("Warning: Could not parse dialogues JSON, returning raw PDF")
        except Exception as e:
            print(f"PDF rendering error: {e}")
            # Fall through to return raw PDF
    
    # Default: return original files
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


async def run_generation(job_id: str, request: GenerateRequest):
    """Run manga generation in background with detailed progress tracking."""
    
    # V4: Initialize sync MongoDB client BEFORE generation starts
    # This prevents silent auto-save failures that caused the user's data loss
    from src.database.mongodb import Database
    Database.init_sync_client()
    
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
    
    # Helper function for story continuation context
    def _get_last_page_context(result):
        """Extract last page/panel context for continuation."""
        pages = result.get("pages", [])
        if not pages:
            return ""
        
        last_page = pages[-1]
        panels = last_page.get("panels", [])
        
        context_parts = []
        context_parts.append(f"Last page summary: {last_page.get('page_summary', 'N/A')}")
        context_parts.append(f"Emotional beat: {last_page.get('emotional_beat', 'N/A')}")
        
        if panels:
            last_panel = panels[-1] if isinstance(panels[-1], dict) else {}
            context_parts.append(f"Final panel: {last_panel.get('description', 'N/A')[:200]}")
            context_parts.append(f"Characters in final panel: {last_panel.get('characters_present', [])}")
        
        return " | ".join(context_parts)
    
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
            
            # Handle plan completion - update total_panels with actual count
            elif data and data.get("event") == "plan_complete":
                actual_total = data.get("total_panels", 0)
                job.total_panels = actual_total
                # Pre-fill panel_previews for loading skeletons
                job.panel_previews = ["loading"] * actual_total
                log(f"Plan complete: {actual_total} panels planned")
            
            elif data and data.get("event") == "panel_complete":
                # Handle panel live preview
                if job.panel_previews is None:
                    job.panel_previews = []
                
                # Ensure list is large enough
                idx = data["panel_index"]
                while len(job.panel_previews) <= idx:
                    job.panel_previews.append("loading")
                
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
                # Handle pipeline step transitions for Timeline (V4: 5-step)
                step_type = data.get("step")
                if job.steps:
                    if step_type == "composition":
                        job.steps[1].status = "completed"  # Generating panels done
                        job.steps[2].status = "in_progress" # Composing pages
                    elif step_type == "cover":
                        job.steps[2].status = "completed"  # Composing pages done
                        job.steps[3].status = "in_progress" # Generating cover
                        job.progress = 92
                        job.current_step = "Generating cover..."
            
            elif data and data.get("event") == "cover_start":
                # V4: Cover generation started
                if job.steps:
                    job.steps[2].status = "completed"  # Composing pages done
                    job.steps[3].status = "in_progress" # Generating cover
                job.progress = 92
                job.current_step = "Generating cover..."

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
                
                # V4: Update total_panels with ACTUAL count from blueprint (not estimate!)
                if request.layout == "dynamic":
                    actual_panel_count = 0
                    for page in blueprint.get("pages", []):
                        panels = page.get("panels", [])
                        actual_panel_count += len(panels)
                    
                    if actual_panel_count > 0:
                        job.total_panels = actual_panel_count
                        log(f"📊 Dynamic layout: {actual_panel_count} panels total (not {request.pages * 4})")
                
            except Exception as e:
                log(f"⚠️ Blueprint generation failed (will use fallback): {e}")

        # This is where we hook into panel generation
        result = await generator.generate_chapter(
            story_prompt=request.story_prompt,
            groq_api_key=groq_key or "",
            characters=characters,
            progress_callback=progress_handler
        )
        
        # Verify result contains output (PDF path or pages)
        if not result.get("pages") and not result.get("pdf"):
             raise RuntimeError("Generator returned empty result - failures in image generation")

        # V4: Update total_panels with ACTUAL count from LLM result
        actual_panels = sum(len(p.get("panels", [])) for p in result.get("pages", []))
        if actual_panels > 0:
            job.total_panels = actual_panels
            log(f"📊 Actual panel count: {actual_panels} (updated from LLM)")

        step_duration = f"{time.time() - step_start:.1f}s"
        update_step(1, "completed", step_duration)  # Step 1: Generating panels
        log(f"Panel generation complete ({step_duration})")
        
        # Step 2: Composing pages (already done in generator)
        update_step(2, "completed", "auto")
        log("Page composition complete")
        
        # Step 3: Cover generation (handled by generator)
        update_step(3, "completed", "auto")
        log("Cover generation complete")
        
        # Step 4: Finalizing
        update_step(4, "completed", "auto")
        
        # Complete
        job.status = "completed"
        job.progress = 100
        job.current_step = "Done!"
        job.result = result
        log("✅ Generation complete!")
        
        # Save to MongoDB if available - FORCE SAVE full initial state
        try:
            from src.database.mongodb import Database
            import asyncio
            from datetime import datetime
            
            # V4 Force Save: Extract dialogues from result immediately after generation
            # This ensures all LLM-generated content is saved even if user doesn't edit
            initial_dialogues = {}
            
            # V4: Initialize face detector for smart bubble placement
            try:
                from scripts.face_detector import FaceDetector
                face_detector = FaceDetector()
            except Exception as fd_err:
                print(f"⚠️ Face detector not available: {fd_err}")
                face_detector = None
            
            pages = result.get("pages", [])
            for page in pages:
                if not isinstance(page, dict):
                    continue
                page_num = page.get("page_number", 1)
                page_dialogue = page.get("dialogue", [])
                
                # Get panel images for face detection
                page_panels = page.get("panels", [])
                
                # Convert page dialogue to panel-based format
                if isinstance(page_dialogue, list):
                    for panel_info in page_dialogue:
                        if isinstance(panel_info, dict):
                            panel_idx = panel_info.get("panel_index", 0)
                            dialogues = panel_info.get("dialogues", [])
                            if dialogues:
                                panel_key = f"page-{page_num}-panel-{panel_idx}"
                                
                                # V4: Smart Bubble Placement - Get safe positions avoiding faces
                                safe_positions = []
                                if face_detector and panel_idx < len(page_panels):
                                    panel_img = page_panels[panel_idx].get("panel_image", "") if isinstance(page_panels[panel_idx], dict) else ""
                                    if panel_img and Path(panel_img).exists():
                                        try:
                                            safe_positions = face_detector.find_safe_bubble_positions(
                                                str(panel_img), 
                                                num_positions=len(dialogues)
                                            )
                                            print(f"   🎯 Smart placement: {len(safe_positions)} safe positions for panel {panel_idx}")
                                        except Exception as fp_err:
                                            print(f"   ⚠️ Face detection failed: {fp_err}")
                                
                                # Build dialogues with smart positions
                                panel_dialogues = []
                                for i, d in enumerate(dialogues):
                                    # Use safe position if available, otherwise fall back to corners
                                    if i < len(safe_positions):
                                        pos_x = safe_positions[i].get("x", 10)
                                        pos_y = safe_positions[i].get("y", 10 + i * 20)
                                    else:
                                        # Fallback: alternate between top-left and top-right
                                        pos_x = 10 if i % 2 == 0 else 60
                                        pos_y = 5 + (i // 2) * 20
                                    
                                    panel_dialogues.append({
                                        "id": f"init-{page_num}-{panel_idx}-{i}",
                                        "text": d.get("text", "") if isinstance(d, dict) else str(d),
                                        "x": pos_x,
                                        "y": pos_y,
                                        "style": d.get("style", "speech") if isinstance(d, dict) else "speech",
                                        "character": d.get("character", "") if isinstance(d, dict) else "",
                                        "fontSize": 11
                                    })
                                
                                initial_dialogues[panel_key] = panel_dialogues
            
            project_data = {
                "job_id": job_id,
                "manga_title": result.get("manga_title", request.title),  # Series name
                "title": result.get("title", request.title),  # Chapter title
                "pages": request.pages,
                "style": request.style,
                "layout": request.layout,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                # Use generated cover if available, else first page
                "cover_url": result.get("cover_url") or f"/outputs/{job_id}/manga_page_01.png",
                "result": result,
                "blueprint": blueprint,  # SAVE BLUEPRINT TO DB!
                "dialogues": initial_dialogues,  # FORCE SAVE: LLM-generated dialogues
                "characters": result.get("characters", []),  # FORCE SAVE: Characters
                
                # V4 CONTINUATION SAFETY: Explicit story_state for "Continue Story"
                "story_state": {
                    "summary": result.get("summary", ""),
                    "cliffhanger": result.get("cliffhanger", ""),
                    "next_chapter_hook": result.get("next_chapter_hook", ""),
                    "chapter_count": len(set(p.get("chapter_number", 1) for p in result.get("pages", []))),
                    "total_pages_generated": len(result.get("pages", [])),
                    # Extract last panel context for visual continuity
                    "last_page_context": _get_last_page_context(result),
                    # Character states at story end
                    "character_states": [
                        {
                            "name": c.get("name", ""),
                            "arc_state": c.get("arc_state", ""),
                            "visual_prompt": c.get("visual_prompt", "")
                        }
                        for c in result.get("characters", [])
                    ]
                },
            }
            
            log(f"💾 Auto-saving project to MongoDB...")
            
            # Use sync save method - no async loop conflicts!
            if Database.save_job_sync(job_id, project_data):
                log("💾 ✅ Auto-saved to MongoDB with Blueprint + Dialogues")
            else:
                log("⚠️ MongoDB auto-save failed (sync_db not available)")
                
        except Exception as db_error:
            import traceback
            print(f"⚠️ MongoDB save failed (continuing): {db_error}")
            print(traceback.format_exc())
        
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
            projects = []
            
            # First, get from projects collection (user-saved projects)
            try:
                cursor = Database.db.projects.find({}).sort("created_at", -1).limit(50)
                async for doc in cursor:
                    doc.pop("_id", None)
                    # Ensure required fields exist
                    if "job_id" in doc:
                        projects.append({
                            "job_id": doc.get("job_id"),
                            "title": doc.get("title", "Untitled"),
                            "pages": doc.get("pages", 0),
                            "style": doc.get("style", "unknown"),
                            "created_at": doc.get("created_at", ""),
                            "updated_at": doc.get("updated_at", ""),
                            "cover_url": doc.get("cover_url", f"/outputs/{doc.get('job_id')}/manga_page_01.png")
                        })
            except Exception as e:
                print(f"Projects collection query error: {e}")
            
            # Also get from jobs collection (auto-saved during generation)
            try:
                cursor = Database.db.jobs.find({}).sort("created_at", -1).limit(50)
                existing_job_ids = {p["job_id"] for p in projects}
                async for doc in cursor:
                    doc.pop("_id", None)
                    job_id = doc.get("job_id")
                    if job_id and job_id not in existing_job_ids:
                        projects.append(doc)
            except Exception as e:
                print(f"Jobs collection query error: {e}")
            
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
                        "cover_url": f"/outputs/{job_id}/manga_page_01.png" if job.result.get("pages") else ""
                    })
            return {"projects": projects, "source": "memory"}
    except Exception as e:
        print(f"Projects API error: {e}")
        return {"projects": [], "error": str(e)}


# V4: Delete Project - Full cleanup from DB + filesystem
@app.delete("/api/projects/{job_id}")
async def delete_project(job_id: str):
    """
    Delete a project completely:
    1. Remove from MongoDB
    2. Delete all output files from filesystem
    """
    import shutil
    from pathlib import Path
    
    deleted_db = False
    deleted_files = False
    
    # 1. Delete from MongoDB
    try:
        from src.database.mongodb import Database
        deleted_db = Database.delete_project_sync(job_id)
        if deleted_db:
            print(f"🗑️ Deleted project {job_id} from MongoDB")
    except Exception as e:
        print(f"⚠️ Failed to delete from DB: {e}")
    
    # 2. Delete output files
    output_dir = Path("outputs") / job_id
    if output_dir.exists():
        try:
            shutil.rmtree(output_dir)
            deleted_files = True
            print(f"🗑️ Deleted output folder: {output_dir}")
        except Exception as e:
            print(f"⚠️ Failed to delete output folder: {e}")
    
    # 3. Remove from in-memory jobs if present
    if job_id in jobs:
        del jobs[job_id]
        print(f"🗑️ Removed {job_id} from in-memory jobs")
    
    if deleted_db or deleted_files:
        return {"status": "deleted", "job_id": job_id, "db": deleted_db, "files": deleted_files}
    else:
        # V4: Still return success to let frontend remove ghost entries
        # This handles cases where files were already deleted but DB entry remained
        print(f"⚠️ Project {job_id} not found in DB or filesystem, but allowing cleanup")
        return {"status": "not_found_but_cleaned", "job_id": job_id, "db": False, "files": False}


# Save Project (with auth check)
class SaveProjectRequest(BaseModel):
    job_id: str
    manga_title: Optional[str] = None  # Series name (LLM generated or user edited)
    title: str                          # Chapter title
    dialogues: Optional[dict] = None    # Panel dialogues from canvas
    
@app.post("/api/projects/save")
async def save_project(request: SaveProjectRequest, authorization: Optional[str] = Header(None)):
    """
    Save project to user's profile.
    Falls back to local JSON storage if MongoDB is unavailable.
    """
    import json
    from datetime import datetime
    from pathlib import Path
    
    output_dir = Path("outputs") / request.job_id
    
    # V4: Fallback chain - check memory, then filesystem
    job = jobs.get(request.job_id)
    result = None
    
    if job and job.result:
        result = job.result
    elif output_dir.exists():
        # Fallback: load from filesystem if server reloaded
        page_files = sorted(output_dir.glob("manga_page_*.png"))
        story_state_file = output_dir / "story_state.json"
        
        # Build page_panels_map from story_state.json first
        page_panels_map = {}
        story_data = {}
        
        if story_state_file.exists():
            try:
                with open(story_state_file, "r", encoding="utf-8") as f:
                    story_data = json.load(f)
                    
                    # Extract panels from chapters (same logic as /api/status)
                    chapters = story_data.get("chapters", [])
                    if not chapters:
                        # Fallback to chapter_plan
                        chapter_plan = story_data.get("chapter_plan", {})
                        if isinstance(chapter_plan, dict) and chapter_plan.get("pages"):
                            chapters = [{"pages": chapter_plan["pages"]}]
                    
                    for ch in chapters:
                        if isinstance(ch, dict):
                            for page in ch.get("pages", []):
                                if isinstance(page, dict):
                                    page_num = page.get("page_number", 0)
                                    panels = page.get("panels", [])
                                    if panels:
                                        page_panels_map[page_num] = panels
            except Exception as e:
                print(f"Warning: Could not load story_state for save: {e}")
        
        # Build pages with panels from story_state
        result = {
            "pages": [
                {
                    "page_number": i + 1,
                    "page_image": str(pf),
                    "panels": page_panels_map.get(i + 1, [])  # Include geometry!
                }
                for i, pf in enumerate(page_files)
            ]
        }
        
        # Add other story_state data
        result.update({k: v for k, v in story_data.items() if k not in ["pages", "chapters"]})
        
        # Check for cover
        cover_file = output_dir / "cover.png"
        if cover_file.exists():
            result["cover_url"] = f"/{request.job_id}/cover.png"
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or no output files")
    
    # Build project data
    project_data = {
        "job_id": request.job_id,
        "manga_title": request.manga_title or result.get("manga_title", request.title),  # Series name
        "title": request.title or result.get("title", "Untitled Manga"),  # Chapter title
        "cover_url": result.get("cover_url") or f"/outputs/{request.job_id}/manga_page_01.png",
        "story_prompt": result.get("prompt", ""),
        "characters": result.get("characters", []),
        "pages": result.get("pages", []),
        "dialogues": request.dialogues or {},
        "story_state": {
            "summary": result.get("summary", ""),
            "cliffhanger": result.get("cliffhanger", ""),
            "next_chapter_hook": result.get("next_chapter_hook", ""),
            "chapter_number": result.get("chapter_number", 1)
        },
        "style": result.get("style", "bw_manga"),
        "layout": result.get("layout", "2x2"),
        "page_count": len(result.get("pages", [])),
        "saved_at": datetime.now().isoformat()
    }
    
    # Try MongoDB first, fallback to local file
    try:
        from src.database.mongodb import Database
        if Database.db is None:
            await Database.connect_db()
        
        # Check if auth is provided
        user_id = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            user_id = f"user_{token[:8]}" if token else None
        
        if user_id and Database.db is not None:
            success = await Database.save_project(user_id, project_data)
            if success:
                return {"success": True, "message": "Project saved to your profile!", "job_id": request.job_id}
    except Exception as e:
        print(f"⚠️ MongoDB save failed: {e}")
    
    # Fallback: Save to local JSON file
    try:
        save_dir = OUTPUT_DIR / request.job_id
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / "project_save.json"
        
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2, default=str)
        
        print(f"💾 Project saved locally: {save_path}")
        return {
            "success": True, 
            "message": "Project saved locally! (MongoDB unavailable)", 
            "job_id": request.job_id,
            "local_path": str(save_path)
        }
    except Exception as e:
        print(f"❌ Local save also failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save project: {str(e)}")


@app.get("/api/projects/{job_id}/dialogues")
async def get_saved_dialogues(job_id: str):
    """Get saved dialogue positions from MongoDB or local project_save.json."""
    
    # First try MongoDB
    try:
        from src.database.mongodb import Database
        
        if Database.db is None:
            await Database.connect_db()
        
        if Database.db is not None:
            # Check projects collection
            project = await Database.db.projects.find_one({"job_id": job_id})
            if project and project.get("dialogues"):
                print(f"📝 Loaded dialogues from MongoDB for {job_id}")
                return {
                    "dialogues": project.get("dialogues", {}),
                    "source": "mongodb"
                }
    except Exception as e:
        print(f"MongoDB dialogue fetch error: {e}")
    
    # Fallback to local file
    output_dir = Path("outputs") / job_id
    project_save = output_dir / "project_save.json"
    
    if project_save.exists():
        try:
            with open(project_save, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            
            # dialogues is stored as a dict: {"page-1-panel-0": [{id, text, x, y, style}]}
            dialogues = saved_data.get("dialogues", {})
            
            if dialogues:
                print(f"📝 Loaded dialogues from local file for {job_id}")
                return {
                    "dialogues": dialogues,
                    "source": "project_save.json"
                }
        except Exception as e:
            print(f"Error loading local dialogues: {e}")
    
    return {"dialogues": {}, "source": "none"}


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


@app.get("/api/projects/{job_id}/story")
async def get_project_story(job_id: str):
    """
    Get story context for the Story Viewer tab.
    
    Returns the full story_state.json with:
    - Story context (prompt, LLM interpretation)
    - Characters with DNA for visual consistency
    - Chapters breakdown
    - Pages and panels with stable IDs
    - Continuation state for "continue" feature
    """
    # Try to load from output directory first
    output_dir = Path("outputs") / job_id
    story_state_path = output_dir / "story_state.json"
    legacy_path = output_dir / "story_blueprint.json"
    
    # Prefer story_state.json (new format)
    if story_state_path.exists():
        try:
            with open(story_state_path, 'r', encoding='utf-8') as f:
                story_state = json.load(f)
            return {"story": story_state, "format": "v1.0"}
        except Exception as e:
            print(f"Error loading story_state.json: {e}")
    
    # Fall back to legacy format
    if legacy_path.exists():
        try:
            with open(legacy_path, 'r', encoding='utf-8') as f:
                blueprint = json.load(f)
            # Convert legacy format to minimal story context
            return {
                "story": {
                    "story_context": {
                        "original_prompt": blueprint.get("original_prompt", ""),
                        "llm_interpretation": blueprint.get("chapter_plan", {}).get("summary", "")
                    },
                    "characters": blueprint.get("chapter_plan", {}).get("characters", []),
                    "pages": blueprint.get("chapter_plan", {}).get("pages", []),
                    "continuation_state": {
                        "cliffhanger": blueprint.get("chapter_plan", {}).get("cliffhanger", ""),
                        "next_chapter_hook": blueprint.get("chapter_plan", {}).get("next_chapter_hook", "")
                    },
                    "panel_prompts": blueprint.get("panel_prompts", [])
                },
                "format": "legacy"
            }
        except Exception as e:
            print(f"Error loading legacy blueprint: {e}")
    
    raise HTTPException(status_code=404, detail="Story data not found for this project")


@app.get("/api/panels/{job_id}/{page}/{panel}/faces")
async def get_panel_faces(job_id: str, page: int, panel: int):
    """
    Detect faces in a panel and return exclusion zones for smart bubble placement.
    
    Returns:
    - exclusion_zones: Areas to avoid (faces with 20% expansion)
    - safe_positions: Recommended bubble positions that don't overlap faces
    - face_count: Number of faces detected
    """
    # Check if output directory exists
    output_dir = Path("outputs") / job_id
    if not output_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Find the panel image - panels are stored separately or we extract from page
    # For now, we'll analyze the full page image and use panel bounds
    page_image = output_dir / f"manga_page_{page:02d}.png"
    if not page_image.exists():
        page_image = output_dir / f"manga_page_{page}.png"
    if not page_image.exists():
        raise HTTPException(status_code=404, detail="Page image not found")
    
    try:
        from scripts.face_detector import detect_faces_in_panel
        result = detect_faces_in_panel(str(page_image))
        return {
            "job_id": job_id,
            "page": page,
            "panel": panel,
            **result
        }
    except ImportError:
        # If OpenCV not installed, return empty zones
        return {
            "job_id": job_id,
            "page": page,
            "panel": panel,
            "exclusion_zones": [],
            "safe_positions": [
                {"x": 10, "y": 10, "anchor": "top-left"},
                {"x": 70, "y": 10, "anchor": "top-right"},
                {"x": 10, "y": 70, "anchor": "bottom-left"},
                {"x": 70, "y": 70, "anchor": "bottom-right"}
            ],
            "face_count": 0,
            "note": "OpenCV not available - using default positions"
        }
    except Exception as e:
        print(f"Face detection error: {e}")
        return {
            "job_id": job_id,
            "page": page,
            "panel": panel,
            "exclusion_zones": [],
            "safe_positions": [],
            "face_count": 0,
            "error": str(e)
        }


# ============================================
# Dialogue Regeneration (V3 Phase 4)
# ============================================

class RegenerateDialogueRequest(BaseModel):
    """Request to regenerate dialogue for a panel."""
    job_id: str
    page: int
    panel: int
    dialogue_index: Optional[int] = None  # If None, regenerate all dialogues
    style_hint: Optional[str] = None  # "more dramatic", "funnier", "shorter"
    character_focus: Optional[str] = None  # Focus on specific character

@app.post("/api/dialogues/regenerate")
async def regenerate_dialogue(request: RegenerateDialogueRequest):
    """
    Regenerate dialogue for a panel using Groq (fast LLM).
    
    Uses story context to maintain consistency.
    Returns new dialogue suggestions.
    """
    # Load story context
    output_dir = Path("outputs") / request.job_id
    story_state_path = output_dir / "story_state.json"
    legacy_path = output_dir / "story_blueprint.json"
    
    story_context = None
    panel_data = None
    characters = []
    
    # Try to load story context
    if story_state_path.exists():
        with open(story_state_path, 'r', encoding='utf-8') as f:
            story_state = json.load(f)
            story_context = story_state.get('story_context', {})
            characters = story_state.get('characters', [])
            pages = story_state.get('pages', [])
            for page in pages:
                if page.get('page_number') == request.page:
                    for panel in page.get('panels', []):
                        if panel.get('panel_number') == request.panel:
                            panel_data = panel
                            break
    elif legacy_path.exists():
        with open(legacy_path, 'r', encoding='utf-8') as f:
            blueprint = json.load(f)
            chapter_plan = blueprint.get('chapter_plan', {})
            story_context = {"original_prompt": blueprint.get("original_prompt", "")}
            characters = chapter_plan.get('characters', [])
            for page in chapter_plan.get('pages', []):
                if page.get('page_number') == request.page:
                    for panel in page.get('panels', []):
                        if panel.get('panel_number') == request.panel:
                            panel_data = panel
                            break
    
    if not panel_data:
        raise HTTPException(status_code=404, detail="Panel not found in story data")
    
    # Build prompt for Groq
    char_info = "\n".join([f"- {c.get('name')}: {c.get('personality', 'N/A')}" for c in characters])
    current_dialogues = panel_data.get('dialogue', [])
    current_dialogue_text = "\n".join([
        f"- [{d.get('type', 'speech')}] {d.get('character', 'Narrator')}: \"{d.get('text', '')}\""
        for d in current_dialogues
    ])
    
    style_instruction = ""
    if request.style_hint:
        style_instruction = f"\nStyle: Make it {request.style_hint}"
    if request.character_focus:
        style_instruction += f"\nFocus: Center dialogue around {request.character_focus}"
    
    prompt = f"""You are a manga dialogue writer. Regenerate the dialogue for this panel.

STORY CONTEXT:
{story_context.get('original_prompt', 'N/A')}

CHARACTERS IN STORY:
{char_info}

PANEL DESCRIPTION:
{panel_data.get('description', 'N/A')}

CHARACTERS IN THIS PANEL:
{', '.join(panel_data.get('characters_present', ['Unknown']))}

CURRENT DIALOGUE:
{current_dialogue_text}
{style_instruction}

Generate NEW dialogue that:
1. Fits the scene description
2. Matches each character's personality
3. Advances the story
4. Uses appropriate bubble types (speech/thought/narrator/shout/whisper)

Return ONLY a JSON array of dialogue objects:
[
  {{"character": "Name", "text": "What they say", "type": "speech"}},
  {{"type": "narrator", "text": "Caption text"}},
  {{"character": "Name", "text": "Inner thoughts", "type": "thought"}}
]

Return ONLY the JSON array, no other text."""

    try:
        # Use Groq for fast regeneration
        from src.ai.llm_factory import get_llm
        llm = get_llm()
        
        response = llm.generate(prompt, max_tokens=1000)
        
        # Parse JSON response
        if "```json" in response:
            response = response.split("```json")[1].split("```")[0]
        elif "```" in response:
            response = response.split("```")[1].split("```")[0]
        
        new_dialogues = json.loads(response.strip())
        
        # Add IDs to new dialogues
        import uuid
        for dlg in new_dialogues:
            dlg['dialogue_id'] = f"dlg_{uuid.uuid4().hex[:8]}"
        
        return {
            "success": True,
            "job_id": request.job_id,
            "page": request.page,
            "panel": request.panel,
            "original_dialogues": current_dialogues,
            "new_dialogues": new_dialogues,
            "llm_used": llm.name
        }
        
    except Exception as e:
        print(f"Dialogue regeneration error: {e}")
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


class ContinueChapterRequest(BaseModel):
    pages: int = 3
    chapter_title: Optional[str] = None
    user_direction: Optional[str] = None  # "I want the hero to meet a villain"
    api_keys: Optional[Dict[str, str]] = None # For BYOK support

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
    
    # PROJECT MERGING: Reuse original job_id (not create new one)
    # This appends pages to the same project instead of creating duplicates
    
    # Count existing pages for correct numbering (manga_page_04.png, etc.)
    existing_pages = project.get("pages", [])
    starting_page_number = len(existing_pages) + 1
    print(f"\n📚 Continuing project {job_id}: {len(existing_pages)} existing pages, starting at page {starting_page_number}")
    
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
    
    # PROJECT MERGING: Update existing job status (or create if not in memory)
    # This allows frontend to show progress on the SAME project
    if job_id in jobs:
        continuation_job = jobs[job_id]
        continuation_job.status = "processing"
        continuation_job.progress = 0
        continuation_job.current_step = "Planning continuation..."
        continuation_job.steps = [
            StepStatus(name="Story planning", status="pending"),
            StepStatus(name="Generating panels", status="pending"),
            StepStatus(name="Composing pages", status="pending"),
            StepStatus(name="Finalizing", status="pending"),
        ]
        continuation_job.current_panel = 0
        continuation_job.total_panels = None
        continuation_job.panel_previews = []
        continuation_job.log_messages = [
            f"> Continuing story: {job_id}",
            f"> Starting at page {starting_page_number}",
            f"> Target: {request.pages} new pages",
            "> Using DYNAMIC layout"
        ]
    else:
        continuation_job = JobStatus(
            job_id=job_id,
            status="processing",
            progress=0,
            current_step="Planning continuation...",
            steps=[
                StepStatus(name="Story planning", status="pending"),
                StepStatus(name="Generating panels", status="pending"),
                StepStatus(name="Composing pages", status="pending"),
                StepStatus(name="Finalizing", status="pending"),
            ],
            current_panel=0,
            total_panels=None,
            panel_previews=[],
            log_messages=[f"> Continuing story: {job_id}", f"> Starting at page {starting_page_number}", f"> Target: {request.pages} new pages"]
        )
        jobs[job_id] = continuation_job
    
    # Run continuation in background
    # Run continuation in background
    async def run_continuation():
        try:
            # Import generator (same as in run_generation)
            from scripts.generate_manga import MangaGenerator, MangaConfig
            
            # Helper function for story continuation context
            def _get_last_page_context(result):
                """Extract last page/panel context for continuation."""
                pages = result.get("pages", [])
                if not pages:
                    return ""
                
                last_page = pages[-1]
                panels = last_page.get("panels", [])
                
                context_parts = []
                context_parts.append(f"Last page summary: {last_page.get('page_summary', 'N/A')}")
                context_parts.append(f"Emotional beat: {last_page.get('emotional_beat', 'N/A')}")
                
                if panels:
                    last_panel = panels[-1] if isinstance(panels[-1], dict) else {}
                    context_parts.append(f"Final panel: {last_panel.get('description', 'N/A')[:200]}")
                    context_parts.append(f"Characters in final panel: {last_panel.get('characters_present', [])}")
                
                return " | ".join(context_parts)
            
            continuation_job.current_step = "Initializing MangaGenerator..."
            continuation_job.progress = 5
            
            # 1. Build Continuation Prompt
            continuation_prompt = f"""
            CONTINUE THE STORY from the previous summary:
            "{previous_summary}"
            
            Last scene context:
            "{last_panel}"
            
            Next Chapter Hook (from blueprint):
            "{blueprint.get('next_chapter_hook', '')}"
            
            USER DIRECTION for this continuation:
            "{request.user_direction or 'Continue the story naturally'}"
            """
            
            # 2. Inherit Config from Project
            # This ensures we use the exact same settings (Provider, Layout, Style)
            original_config = project.get("config", {})
            
            # Determine provider (Critical Fix #1)
            provider = original_config.get("image_provider") 
            if not provider:
                provider = project.get("image_provider", "comfyui") # Default fallback
            
            config = MangaConfig(
                title=f"{project.get('title')} (Continuation)",
                style=project.get("style", "bw_manga"),
                layout="dynamic", # Fix: Force dynamic layout as requested by user
                pages=request.pages,
                output_dir=str(OUTPUT_DIR / job_id),  # PROJECT MERGING: Use original folder
                image_provider=provider,
                is_complete_story=False,
                starting_page_number=starting_page_number  # Continue from page N+1
            )
            
            # Ensure output directory exists (already exists for continuations)
            Path(config.output_dir).mkdir(parents=True, exist_ok=True)
            
            # 3. initialize Generator
            generator = MangaGenerator(config)

            # Extract API keys (same logic as run_generation)
            api_keys = request.api_keys or {}
            groq_key = api_keys.get("GROQ_API_KEY") or os.environ.get("GROQ_API_KEY")
            
            # 4. Prepare Characters from Blueprint
            characters = []
            for c in blueprint.get("characters", []):
                characters.append({
                    "name": c.get("name"),
                    "appearance": c.get("appearance"),
                    "personality": c.get("personality", "")
                })
            
            continuation_job.current_step = "Generating continuation (AI Planning + Art)..."
            continuation_job.progress = 10
            
            # Define helpers (Local to this job)
            def log(msg: str):
                if continuation_job.log_messages is None:
                    continuation_job.log_messages = []
                continuation_job.log_messages.append(f"> {msg}")
            
            def update_step(idx: int, status: str):
                if continuation_job.steps and 0 <= idx < len(continuation_job.steps):
                    continuation_job.steps[idx].status = status

            # Define progress callback
            def progress_handler(msg: str, percent: int, data: Optional[Dict] = None):
                continuation_job.current_step = msg
                if percent >= 0:
                    continuation_job.progress = percent
                
                # Update Log
                log(msg)
                
                # Update Timeline (Basic Logic)
                msg_lower = msg.lower()
                if "planning" in msg_lower or "story director" in msg_lower:
                    update_step(0, "in_progress")
                elif "panel" in msg_lower or "comfyui" in msg_lower or "processing page" in msg_lower:
                    update_step(0, "completed")
                    update_step(1, "in_progress")
                elif "composing" in msg_lower:
                    update_step(1, "completed")
                    update_step(2, "in_progress")
                elif "finalizing" in msg_lower or "saving" in msg_lower:
                    update_step(2, "completed")
                    update_step(3, "in_progress")
                
                # Handle plan completion - update total_panels with actual count
                if data and data.get("event") == "plan_complete":
                    actual_total = data.get("total_panels", 0)
                    continuation_job.total_panels = actual_total
                    # Pre-fill panel_previews for loading skeletons
                    continuation_job.panel_previews = ["loading"] * actual_total
                    log(f"Plan complete: {actual_total} panels planned")
                
                # Handle live panel updates (reuse logic from run_generation)
                if data and data.get("event") == "panel_complete":
                    if continuation_job.panel_previews is None:
                        continuation_job.panel_previews = []
                    
                    idx = data["panel_index"]
                    while len(continuation_job.panel_previews) <= idx:
                        continuation_job.panel_previews.append("loading")
                    
                    filename = Path(data["image_path"]).name
                    relative_url = f"/outputs/{job_id}/{filename}"  # PROJECT MERGING: Use original job_id
                    continuation_job.panel_previews[idx] = relative_url
                    
                    continuation_job.current_panel = idx + 1
                    if continuation_job.total_panels and continuation_job.total_panels > 0:
                         # Map 20-90% progress
                        panel_prog = 20 + int(70 * (idx + 1) / continuation_job.total_panels)
                        continuation_job.progress = panel_prog
            
            # 5. EXECUTE GENERATION (The "One Call" Solution)
            # This runs StoryDirector -> ScriptDoctor -> Image Gen -> Layouts
            result = await generator.generate_chapter(
                story_prompt=continuation_prompt,
                groq_api_key=groq_key, # Pass API key!
                characters=characters,
                progress_callback=progress_handler
            )
            
            # 6. Post-Processing: Pages already have correct numbers from generator
            # (generator uses starting_page_number for continuation support)
            final_pages = result["pages"]  # No offset needed - generator handled it
                
            print(f"✅ Continuation complete: {len(final_pages)} pages generated (Pages {starting_page_number} to {starting_page_number + len(final_pages) - 1})")
            
            # 6.5 Extract dialogues from new pages (same as run_generation)
            # This ensures continuation dialogues are merged into saved dialogues
            new_dialogues = {}
            for page in final_pages:
                if not isinstance(page, dict):
                    continue
                page_num = page.get("page_number", 1)
                page_dialogue = page.get("dialogue", [])
                
                # Convert page dialogue to panel-based format
                if isinstance(page_dialogue, list):
                    for panel_info in page_dialogue:
                        if isinstance(panel_info, dict):
                            panel_idx = panel_info.get("panel_index", 0)
                            dialogues = panel_info.get("dialogues", [])
                            if dialogues:
                                panel_key = f"page-{page_num}-panel-{panel_idx}"
                                
                                # Build dialogues with default positions
                                panel_dialogues = []
                                for i, d in enumerate(dialogues):
                                    pos_x = 10 if i % 2 == 0 else 60
                                    pos_y = 5 + (i // 2) * 20
                                    
                                    panel_dialogues.append({
                                        "id": f"cont-{page_num}-{panel_idx}-{i}",
                                        "text": d.get("text", "") if isinstance(d, dict) else str(d),
                                        "x": pos_x,
                                        "y": pos_y,
                                        "style": d.get("style", "speech") if isinstance(d, dict) else "speech",
                                        "character": d.get("character", "") if isinstance(d, dict) else "",
                                        "fontSize": 11
                                    })
                                
                                new_dialogues[panel_key] = panel_dialogues
            
            print(f"💬 Extracted {len(new_dialogues)} panel dialogues from continuation")
            
            # 7. Update Project in DB (append pages AND merge dialogues)
            continuation_job.progress = 95
            continuation_job.current_step = "Saving continuation..."
            
            updated_state = {
                "summary": result.get("progress_summary", ""), # Auto-updated by generator
                "pages_generated": starting_page_number + len(final_pages) - 1,
                "last_page_summary": result.get("progress_summary", ""),
                "last_panel_description": _get_last_page_context(result) # Use helper
            }
            
            if Database.db is not None:
                # Get existing dialogues first
                existing_project = await Database.db.projects.find_one({"job_id": job_id})
                existing_dialogues = existing_project.get("dialogues", {}) if existing_project else {}
                
                # Merge new dialogues with existing ones
                merged_dialogues = {**existing_dialogues, **new_dialogues}
                
                await Database.db.projects.update_one(
                    {"job_id": job_id},
                    {
                        "$push": {"pages": {"$each": final_pages}},
                        "$set": {
                            "story_state": updated_state,
                            "updated_at": datetime.now().isoformat(),
                            "dialogues": merged_dialogues  # MERGE: Add new dialogues!
                        }
                    }
                )
            
            # Set job result - merge with existing pages for full view
            all_pages = existing_pages + final_pages
            continuation_job.result = {
                "title": project.get("title"),
                "pages": all_pages,  # All pages for canvas to display
                "characters": blueprint.get("characters"),
                "continuation_state": updated_state
            }
            continuation_job.status = "completed"
            continuation_job.progress = 100
            continuation_job.current_step = "Continuation complete!"
            
        except Exception as e:
            import traceback
            print(f"❌ Continuation failed: {traceback.format_exc()}")
            continuation_job.status = "failed"
            continuation_job.error = str(e)
    
    # Start background task
    background_tasks.add_task(run_continuation)
    
    # PROJECT MERGING: Return original job_id so frontend tracks the SAME project
    return {
        "job_id": job_id,  # Not new_job_id - same project!
        "pages_requested": request.pages,
        "starting_page": starting_page_number,
        "status": "processing",
        "message": f"Generating {request.pages} new pages (starting at page {starting_page_number})...",
        "check_status_at": f"/api/status/{job_id}"
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
    
    output_dir = Path("outputs") / job_id
    
    # V4: Fallback chain - check memory, then filesystem
    job = jobs.get(job_id)
    result = None
    
    if job and job.result:
        result = job.result
    elif output_dir.exists():
        # Fallback: load from filesystem if server reloaded
        # Reconstruct minimal result from files
        page_files = sorted(output_dir.glob("manga_page_*.png"))
        if page_files:
            result = {
                "pages": [
                    {
                        "page_number": i + 1,
                        "page_image": str(pf),
                        "panels": []  # Panel data not available without DB
                    }
                    for i, pf in enumerate(page_files)
                ]
            }
    
    if not result:
        raise HTTPException(status_code=404, detail="Job not found or no result available")
    
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
        pages = result.get("pages", [])
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
            
            pages = result.get("pages", [])
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
                            
                            # Draw bubble based on style - JJK-STYLE MATCHING CANVAS!
                            padding = 10
                            bubble_width = tw + padding * 2
                            bubble_height = th + padding * 2
                            bubble_x = bx - padding
                            bubble_y = by - padding
                            
                            if style == "narrator":
                                # Dark box with left accent (matches canvas)
                                draw.rectangle([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                              fill=(30, 30, 35))
                                draw.rectangle([bubble_x, bubble_y, bubble_x + 4, bubble_y + bubble_height], 
                                              fill=(100, 100, 120))
                                draw.text((bx + 4, by), text, fill="white", font=font)
                                
                            elif style == "thought":
                                # Cloud-like with bumps + thought trail
                                import math
                                # Main ellipse
                                draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                            fill="white", outline="gray", width=2)
                                # Cloud bumps
                                cx = bubble_x + bubble_width // 2
                                cy = bubble_y + bubble_height // 2
                                bump_size = min(bubble_width, bubble_height) // 4
                                for angle in [0, 60, 120, 180, 240, 300]:
                                    bpx = cx + int((bubble_width//2 - bump_size//3) * math.cos(math.radians(angle)))
                                    bpy = cy + int((bubble_height//2 - bump_size//3) * math.sin(math.radians(angle)))
                                    draw.ellipse([bpx - bump_size//2, bpy - bump_size//2, 
                                                bpx + bump_size//2, bpy + bump_size//2], 
                                                fill="white", outline="gray", width=1)
                                # Thought trail
                                draw.ellipse([bubble_x + 5, bubble_y + bubble_height + 2, 
                                             bubble_x + 12, bubble_y + bubble_height + 9], fill="white", outline="gray", width=1)
                                draw.ellipse([bubble_x, bubble_y + bubble_height + 10, 
                                             bubble_x + 6, bubble_y + bubble_height + 16], fill="white", outline="gray", width=1)
                                draw.text((bx, by), text, fill="gray", font=font)
                                
                            elif style == "shout":
                                # AGGRESSIVE JJK-style SPIKY polygon! (MAINSTREAM QUALITY)
                                import math
                                import random
                                points = []
                                spikes = 14  # More spikes for aggressive look
                                cx = bubble_x + bubble_width // 2
                                cy = bubble_y + bubble_height // 2
                                for i in range(spikes):
                                    angle = (360 / spikes) * i - 90
                                    if i % 2 == 0:
                                        # Outer spike - DEEP and RANDOMIZED
                                        r_x = bubble_width // 2 + 25 + random.randint(-5, 5)
                                        r_y = bubble_height // 2 + 25 + random.randint(-5, 5)
                                    else:
                                        # Inner notch - AGGRESSIVE inward dip
                                        r_x = bubble_width // 2 - 12
                                        r_y = bubble_height // 2 - 12
                                    px = cx + int(r_x * math.cos(math.radians(angle)))
                                    py = cy + int(r_y * math.sin(math.radians(angle)))
                                    points.append((px, py))
                                draw.polygon(points, fill="white", outline="black", width=4)  # Thicker outline
                                draw.text((bx, by), text, fill="black", font=font)
                                
                            elif style == "whisper":
                                # Dashed ellipse border
                                import math
                                # White fill first
                                draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                            fill="white", outline=None)
                                # Dashed border using line segments
                                cx = bubble_x + bubble_width // 2
                                cy = bubble_y + bubble_height // 2
                                dash_count = 24
                                for i in range(dash_count):
                                    if i % 2 == 0:  # Dash
                                        a1 = (360 / dash_count) * i
                                        a2 = (360 / dash_count) * (i + 0.6)
                                        x1 = cx + int((bubble_width // 2) * math.cos(math.radians(a1)))
                                        y1 = cy + int((bubble_height // 2) * math.sin(math.radians(a1)))
                                        x2 = cx + int((bubble_width // 2) * math.cos(math.radians(a2)))
                                        y2 = cy + int((bubble_height // 2) * math.sin(math.radians(a2)))
                                        draw.line([(x1, y1), (x2, y2)], fill="gray", width=1)
                                draw.text((bx, by), text, fill="gray", font=font)
                                
                            else:
                                # Regular speech bubble - clean ellipse
                                draw.ellipse([bubble_x, bubble_y, bubble_x + bubble_width, bubble_y + bubble_height], 
                                            fill="white", outline="black", width=2)
                                draw.text((bx, by), text, fill="black", font=font)
                                
                                # Directional tail based on speaker_position
                                speaker_pos = bubble.get("speakerPosition", bubble.get("speaker_position", "center"))
                                bubble_cx = bx + tw // 2
                                bubble_cy = by + th // 2
                                
                                if speaker_pos == "left":
                                    draw.polygon([
                                        (bubble_x, bubble_cy - 5),
                                        (bubble_x - 12, bubble_cy + 5),
                                        (bubble_x, bubble_cy + 5)
                                    ], fill="white", outline="black")
                                elif speaker_pos == "right":
                                    draw.polygon([
                                        (bubble_x + bubble_width, bubble_cy - 5),
                                        (bubble_x + bubble_width + 12, bubble_cy + 5),
                                        (bubble_x + bubble_width, bubble_cy + 5)
                                    ], fill="white", outline="black")
                                else:
                                    draw.polygon([
                                        (bubble_cx, bubble_y + bubble_height),
                                        (bubble_cx + 10, bubble_y + bubble_height + 15),
                                        (bubble_cx - 5, bubble_y + bubble_height)
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
