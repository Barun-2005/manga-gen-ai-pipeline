"""
Image Generator Module

Handles image generation using ComfyUI API for manga panel creation.
Sends prompts to ComfyUI and manages image saving and file organization.
"""

import os
import time
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Import our ComfyUI client
from .comfy_client import ComfyUIClient

load_dotenv()


def generate_image(prompt: str, index: int) -> str:
    """
    Sends prompt to ComfyUI API and saves the image to output/ folder with name panel_{index}.png.
    
    Args:
        prompt: The image generation prompt (may include negative prompt after |)
        index: Panel index for filename (1-6)
        
    Returns:
        Path to the saved image file
    """
    try:
        # Parse prompt and negative prompt
        positive_prompt, negative_prompt = _parse_prompt(prompt)
        
        # Initialize ComfyUI client
        client = ComfyUIClient()
        
        # Check if ComfyUI server is available
        if not client.is_server_ready():
            print(f"ComfyUI server not available, using placeholder for panel {index}")
            return _create_placeholder_image(index)
        
        # Create workflow for image generation
        workflow = _load_and_customize_workflow(
            positive_prompt=positive_prompt,
            negative_prompt=negative_prompt,
            seed=_generate_seed(index)
        )
        
        # Generate image
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        image_paths = client.generate_images(workflow, str(output_dir))
        
        if image_paths:
            # Rename the generated image to our naming convention
            generated_path = Path(image_paths[0])
            target_path = output_dir / f"panel_{index:02d}.png"
            
            if generated_path.exists():
                generated_path.rename(target_path)
                print(f"Generated panel {index}: {target_path}")
                return str(target_path)
        
        # Fallback to placeholder if generation failed
        print(f"Image generation failed for panel {index}, using placeholder")
        return _create_placeholder_image(index)
        
    except Exception as e:
        print(f"Error generating image for panel {index}: {e}")
        return _create_placeholder_image(index)


def _parse_prompt(prompt: str) -> tuple[str, str]:
    """
    Parse prompt to separate positive and negative prompts.
    
    Args:
        prompt: Full prompt string (may contain | NEGATIVE: section)
        
    Returns:
        Tuple of (positive_prompt, negative_prompt)
    """
    if "| NEGATIVE:" in prompt:
        parts = prompt.split("| NEGATIVE:")
        positive = parts[0].strip()
        negative = parts[1].strip() if len(parts) > 1 else ""
    else:
        positive = prompt.strip()
        negative = "blurry, low quality, distorted, ugly, bad anatomy"
    
    return positive, negative


def _generate_seed(index: int) -> int:
    """
    Generate a consistent seed based on panel index.
    
    Args:
        index: Panel index
        
    Returns:
        Seed value for reproducible generation
    """
    # Use a base seed that can be modified for variation
    base_seed = int(os.getenv("RANDOM_SEED", "42"))
    if base_seed == -1:
        return int(time.time()) + index
    return base_seed + index * 1000


def _load_and_customize_workflow(
    positive_prompt: str,
    negative_prompt: str,
    seed: int = None
) -> Dict[str, Any]:
    """
    Load and customize the working manga workflow template.

    Args:
        positive_prompt: Positive prompt text
        negative_prompt: Negative prompt text
        seed: Random seed

    Returns:
        Customized ComfyUI workflow dictionary
    """
    import json

    if seed is None:
        seed = int(time.time()) % 1000000

    # Load the working workflow template
    workflow_path = Path("workflows/manga/working_manga_workflow.json")

    try:
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)

        # Customize the workflow with our parameters
        # Replace prompt placeholder
        if "2" in workflow and "inputs" in workflow["2"]:
            template_text = workflow["2"]["inputs"]["text"]
            workflow["2"]["inputs"]["text"] = template_text.replace("{prompt}", positive_prompt)

        # Update negative prompt if provided
        if negative_prompt and "3" in workflow and "inputs" in workflow["3"]:
            workflow["3"]["inputs"]["text"] = negative_prompt

        # Set seed
        if "5" in workflow and "inputs" in workflow["5"]:
            workflow["5"]["inputs"]["seed"] = seed

        # Update filename with timestamp
        if "7" in workflow and "inputs" in workflow["7"]:
            timestamp = int(time.time())
            workflow["7"]["inputs"]["filename_prefix"] = f"manga_panel_{timestamp}"

        return workflow

    except Exception as e:
        print(f"Error loading workflow template: {e}")
        # Fallback to basic workflow
        return _create_basic_workflow(positive_prompt, negative_prompt, seed)


def _create_basic_workflow(
    positive_prompt: str,
    negative_prompt: str,
    seed: int
) -> Dict[str, Any]:
    """
    Create a basic fallback workflow when template loading fails.

    Args:
        positive_prompt: Positive prompt text
        negative_prompt: Negative prompt text
        seed: Random seed

    Returns:
        Basic ComfyUI workflow dictionary
    """
    return {
        "1": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "v1-5-pruned-emaonly.safetensors"
            }
        },
        "2": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": f"{positive_prompt}, masterpiece, best quality, manga style, black and white",
                "clip": ["1", 1]
            }
        },
        "3": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": negative_prompt or "blurry, low quality, bad anatomy",
                "clip": ["1", 1]
            }
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 768,
                "batch_size": 1
            }
        },
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "seed": seed,
                "steps": 25,
                "cfg": 7.5,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["1", 0],
                "positive": ["2", 0],
                "negative": ["3", 0],
                "latent_image": ["4", 0]
            }
        },
        "6": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["5", 0],
                "vae": ["1", 2]
            }
        },
        "7": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["6", 0],
                "filename_prefix": f"manga_panel_{seed}"
            }
        }
    }



def _create_placeholder_image(index: int) -> str:
    """
    Create a placeholder image when ComfyUI is not available.
    
    Args:
        index: Panel index
        
    Returns:
        Path to placeholder image
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a simple placeholder image
        width, height = 512, 768
        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)
        
        # Draw a border
        draw.rectangle([10, 10, width-10, height-10], outline='black', width=3)
        
        # Add text
        try:
            # Try to use a default font
            font = ImageFont.truetype("arial.ttf", 36)
        except:
            # Fallback to default font
            font = ImageFont.load_default()
        
        text = f"Panel {index}\nPlaceholder"
        
        # Calculate text position (center)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.text((x, y), text, fill='black', font=font)
        
        # Save the image
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        image_path = output_dir / f"panel_{index:02d}.png"
        image.save(image_path)
        
        print(f"Created placeholder image: {image_path}")
        return str(image_path)
        
    except Exception as e:
        print(f"Error creating placeholder image: {e}")
        # Return a simple text file as last resort
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        placeholder_path = output_dir / f"panel_{index:02d}.txt"
        with open(placeholder_path, 'w') as f:
            f.write(f"Placeholder for Panel {index}\nImage generation not available")
        
        return str(placeholder_path)


def generate_manga_sequence(prompts: list[str]) -> list[str]:
    """
    Generate a complete sequence of manga panels.
    
    Args:
        prompts: List of image prompts for each panel
        
    Returns:
        List of paths to generated images
    """
    image_paths = []
    
    print(f"Generating {len(prompts)} manga panels...")
    
    for i, prompt in enumerate(prompts, 1):
        print(f"Generating panel {i}/{len(prompts)}...")
        image_path = generate_image(prompt, i)
        image_paths.append(image_path)
        
        # Small delay between generations to avoid overwhelming the API
        time.sleep(1)
    
    print(f"Generated {len(image_paths)} panels successfully!")
    return image_paths


def batch_generate_with_retry(prompts: list[str], max_retries: int = 3) -> list[str]:
    """
    Generate images with retry logic for failed generations.
    
    Args:
        prompts: List of image prompts
        max_retries: Maximum retry attempts per image
        
    Returns:
        List of paths to generated images
    """
    image_paths = []
    
    for i, prompt in enumerate(prompts, 1):
        success = False
        retry_count = 0
        
        while not success and retry_count < max_retries:
            try:
                image_path = generate_image(prompt, i)
                
                # Check if the generated file exists and is valid
                if Path(image_path).exists():
                    image_paths.append(image_path)
                    success = True
                    print(f"Panel {i} generated successfully")
                else:
                    raise Exception("Generated file not found")
                    
            except Exception as e:
                retry_count += 1
                print(f"Retry {retry_count}/{max_retries} for panel {i}: {e}")
                
                if retry_count >= max_retries:
                    # Use placeholder as final fallback
                    placeholder_path = _create_placeholder_image(i)
                    image_paths.append(placeholder_path)
                    print(f"Using placeholder for panel {i} after {max_retries} retries")
                else:
                    time.sleep(2)  # Wait before retry
    
    return image_paths


def cleanup_temp_files(keep_panels: bool = True) -> None:
    """
    Clean up temporary files from image generation.
    
    Args:
        keep_panels: Whether to keep the final panel images
    """
    output_dir = Path("outputs")
    
    if not output_dir.exists():
        return
    
    # Remove temporary files but keep panels if requested
    for file_path in output_dir.iterdir():
        if file_path.is_file():
            if keep_panels and file_path.name.startswith("panel_"):
                continue
            
            # Remove temporary ComfyUI files
            if any(temp_pattern in file_path.name for temp_pattern in ["temp_", "tmp_", "ComfyUI_"]):
                try:
                    file_path.unlink()
                    print(f"Removed temporary file: {file_path}")
                except Exception as e:
                    print(f"Error removing {file_path}: {e}")


if __name__ == "__main__":
    # Example usage
    test_prompts = [
        "manga style, young ninja on rooftop, city background, determined expression | NEGATIVE: blurry, low quality",
        "manga style, magical energy glowing, surprised character, dramatic lighting | NEGATIVE: blurry, low quality",
        "manga style, mysterious figure in shadows, dark atmosphere | NEGATIVE: blurry, low quality"
    ]
    
    print("Testing image generation...")
    
    # Test single image generation
    test_path = generate_image(test_prompts[0], 1)
    print(f"Test image generated: {test_path}")
    
    # Test sequence generation
    print("\nTesting sequence generation...")
    sequence_paths = generate_manga_sequence(test_prompts)
    print(f"Generated sequence: {sequence_paths}")
    
    # Cleanup
    print("\nCleaning up temporary files...")
    cleanup_temp_files(keep_panels=True)
