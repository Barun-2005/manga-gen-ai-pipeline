# Add this after line 220 (after get_status endpoint)

class RegenerateRequest(BaseModel):
    page: int
    panel: int
    prompt_override: Optional[str] = None


@app.post("/api/regenerate/{job_id}")
async def regenerate_panel(
    job_id: str,
    request: RegenerateRequest,
    background_tasks: BackgroundTasks
):
    """Regenerate a specific panel with optional prompt override."""
    
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job.status != "completed":
        raise HTTPException(status_code=400, detail="Job must be completed first")
    
    if not job.result:
        raise HTTPException(status_code=404, detail="No job result found")
    
    try:
        # Get the original generation data
        pages = job.result.get("pages", [])
        if request.page < 1 or request.page > len(pages):
            raise HTTPException(status_code=400, detail=f"Invalid page number")
        
        page_data = pages[request.page - 1]
        panels = page_data.get("panels", [])
        
        if request.panel < 0 or request.panel >= len(panels):
            raise HTTPException(status_code=400, detail=f"Invalid panel number")
        
        panel_data = panels[request.panel]
        
        # Get the original prompt or use override
        original_prompt = panel_data.get("prompt", panel_data.get("description", ""))
        prompt_to_use = request.prompt_override if request.prompt_override else original_prompt
        
        # Import needed modules
        from scripts.generate_manga import MangaConfig
        from scripts.generate_panels_api import PollinationsGenerator, NVIDIAImageGenerator
        from src.ai.character_dna import CharacterDNAManager
        import os
        
        # Get image provider from original job
        # Assume Pollinations for now, can be enhanced later
        output_dir = OUTPUT_DIR / job_id
        output_dir.mkdir(exist_ok=True, parents=True)
        
        # Initialize image generator (same as original job would have used)
        image_generator = PollinationsGenerator(str(output_dir))
        
        # Get style from original job
        style = job.result.get("style", "bw_manga")
        
        # Get character data if available
        characters_data = job.result.get("characters", [])
        characters_dict = {c.get("name", ""): c for c in characters_data}
        
        # Initialize Character DNA manager
        character_dna = CharacterDNAManager(style=style)
        for char in characters_data:
            character_dna.register_character(
                name=char.get("name", "Unknown"),
                appearance=char.get("appearance", ""),
                personality=char.get("personality", ""),
                role=char.get("role", "")
            )
        
        # Get panel parameters
        shot_type = panel_data.get("shot_type", "medium shot")
        camera_angle = panel_data.get("camera_angle", "straight-on")
        composition = panel_data.get("composition", "rule of thirds")
        lighting_mood = panel_data.get("lighting_mood", "soft lighting")
        characters_present = panel_data.get("characters_present", [])
        
        # Construct enhanced prompt with cinematography
        cinematography = f"{shot_type}, {camera_angle}, {composition}, {lighting_mood}"
        enhanced_prompt = character_dna.enhance_panel_prompt(
            base_prompt=f"{cinematography}, {prompt_to_use}",
            characters_present=characters_present
        )
        
        # Generate new panel image
        panel_filename = f"p{request.page:02d}_panel_{request.panel:02d}_regen.png"
        new_panel_path = image_generator.generate_image(
            prompt=enhanced_prompt,
            filename=panel_filename,
            style=style
        )
        
        if new_panel_path:
            # Update panel data with new image
            panel_data["imageUrl"] = f"/outputs/{job_id}/{panel_filename}"
            panel_data["image_path"] = new_panel_path
            
            # If prompt was overridden, store it
            if request.prompt_override:
                panel_data["prompt"] = request.prompt_override
                panel_data["user_edited"] = True
            
            # Save updated job
            jobs[job_id] = job
            
            return {
                "success": True,
                "panel_url": panel_data["imageUrl"],
                "message": f"Panel {request.panel} on page {request.page} regenerated successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Panel regeneration failed")
            
    except Exception as e:
        print(f"Regeneration error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
