import os
import sys
from typing import Optional

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from image_gen.comfy_client import ComfyUIClient, load_workflow_template

def generate_panel(
    output_image: str,
    style: str,    # "bw" or "color"
    emotion: str,  # e.g. "happy", "angry"
    pose: str      # e.g. "openpose", "arms_crossed"
) -> None:
    """
    1) Choose workflow:
       - bw → bw_manga_workflow.json + anything-v4.5
       - color → color_manga_workflow.json + anything-v4.5
    2) Build prompt:
       "manga panel of a character in {pose} pose expressing {emotion}, {style}-style shading"
    3) Call ComfyUI client to generate and save `output_image`
    """
    # Use the original working approach with minimal changes
    # Map to the original function parameters
    scene_type = "basic"  # Always use basic for simplicity
    seed = None

    # 1. Map scene_type and style to workflow JSON (original logic)
    workflow_map = {
        ("basic", "bw"): "bw_manga_workflow.json",
        ("basic", "color"): "color_manga_workflow.json",
    }
    workflow_file = workflow_map.get((scene_type, style))
    if not workflow_file:
        raise ValueError(f"Unsupported scene_type/style combination: {scene_type}/{style}")
    workflow_path = os.path.join("assets", "workflows", workflow_file)

    # 2. Build prompt (original logic)
    base_prompt = f"manga panel of a character expressing {emotion} with {pose} pose"
    style_mod = "lineart style, black-and-white shading" if style == "bw" else "vibrant color shading"
    if style == "color":
        style_mod += ", high-resolution color rendering, waifu-diffusion style"
    prompt = f"{base_prompt}, {style_mod}"

    # 3. Load workflow template and inject prompt (original working logic)
    workflow = load_workflow_template(workflow_path)
    # Replace placeholders in workflow
    for node in workflow.values():
        if node.get("class_type", "").lower().startswith("cliptextencode"):
            node["inputs"]["text"] = prompt
        if "seed" in node.get("inputs", {}):
            # Fix: Use 0 instead of -1 for random seed (ComfyUI validation requires >= 0)
            node["inputs"]["seed"] = seed if seed is not None else 0

    # 4. Use ComfyUIClient to generate image (original logic)
    client = ComfyUIClient()
    saved_paths = client.generate_images(workflow, output_dir=os.path.dirname(output_image))
    # Move/rename the first image to output_image if needed
    if saved_paths:
        os.replace(saved_paths[0], output_image)
        print(f"Generated panel: {output_image}")
    else:
        raise RuntimeError(f"No image was generated for {output_image}")
