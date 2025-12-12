import os
import sys
from typing import Optional

# Ensure project root is in sys.path for sibling imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from image_gen.comfy_client import ComfyUIClient, load_workflow_template

def generate_panel(
    output_path: str,
    scene_type: str,  # e.g. "basic", "closeup", "color", "sketch"
    emotion: str,     # e.g. "happy", "angry", "surprised"
    pose: str,        # e.g. "openpose", "arms_crossed", "sitting"
    style: str,       # "bw" or "color"
    seed: Optional[int] = None
) -> None:
    """
    Generates a single manga panel image at `output_path` using ComfyUI API.
    Chooses the correct ComfyUI workflow file from assets/workflows/ based on scene_type and style.
    Injects emotion and pose into the prompt. Always uses the new models/controllers.
    """
    # 1. Map scene_type and style to workflow JSON
    workflow_map = {
        ("basic", "bw"): "bw_manga_workflow.json",
        ("basic", "color"): "color_manga_workflow.json",
        ("closeup", "bw"): "adapter_workflow.json",
        ("closeup", "color"): "adapter_workflow.json",
        ("sketch", "bw"): "controlnet_workflow.json",
        ("sketch", "color"): "controlnet_workflow.json",
        ("scene_ref", "bw"): "scene_reference_workflow.json",
        ("scene_ref", "color"): "scene_reference_workflow.json",
    }
    workflow_file = workflow_map.get((scene_type, style))
    if not workflow_file:
        raise ValueError(f"Unsupported scene_type/style combination: {scene_type}/{style}")
    workflow_path = os.path.join("assets", "workflows", workflow_file)

    # 2. Build prompt
    base_prompt = f"manga panel of a character expressing {emotion} with {pose} pose"
    style_mod = "lineart style, black-and-white shading" if style == "bw" else "vibrant color shading"
    if scene_type == "closeup":
        base_prompt = f"tight closeup focusing on facial expression, {base_prompt}"
    if style == "color":
        style_mod += ", high-resolution color rendering, waifu-diffusion style"
    prompt = f"{base_prompt}, {style_mod}"

    # 3. Load workflow template and inject prompt/seed/placeholders
    workflow = load_workflow_template(workflow_path)
    # Replace placeholders in workflow
    for node in workflow.values():
        if node.get("class_type", "").lower().startswith("cliptextencode"):
            node["inputs"]["text"] = prompt
        if "seed" in node.get("inputs", {}):
            node["inputs"]["seed"] = seed if seed is not None else -1
        # Replace adapter/controlnet/reference placeholders
        if "adapter_name" in node.get("inputs", {}):
            node["inputs"]["adapter_name"] = "t2iadapter_sketch_sd15v2.pth"
        if "control_net_name" in node.get("inputs", {}):
            node["inputs"]["control_net_name"] = "control_sd15_openpose.pth"
        if "image" in node.get("inputs", {}):
            if node["inputs"]["image"] == "REFERENCE_IMAGE_PLACEHOLDER":
                # Use a valid test image path
                node["inputs"]["image"] = os.path.abspath(os.path.join("assets", "references", "test_reference.png"))

    # 4. Use ComfyUIClient to generate image
    client = ComfyUIClient()
    saved_paths = client.generate_images(workflow, output_dir=os.path.dirname(output_path))
    # Move/rename the first image to output_path if needed
    if saved_paths:
        os.replace(saved_paths[0], output_path)
    else:
        raise RuntimeError(f"No image was generated for {output_path}")
