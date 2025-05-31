# ComfyUI Workflows for Manga Generation

This directory contains ComfyUI workflow JSON files for automated manga panel generation using ControlNet and T2I Adapters.

## Workflow Files

### Main Workflows

#### `manga/manga_controlnet_adapter_workflow.json`
Complete workflow combining ControlNet (OpenPose) and T2I Adapter (Style) for manga generation.

**Features:**
- SD 1.5 base model
- OpenPose ControlNet for character pose guidance
- T2I Adapter for manga style conditioning
- 512x768 output resolution
- Optimized for black and white manga style

**Inputs:**
- Text prompt
- Pose reference image
- Style reference image

**Output:**
- High-quality manga panel

### Modular Components

#### `manga/text_to_pose_image.json`
Generates pose reference images from text descriptions.

**Usage:**
- Input: "boy punching in air"
- Output: OpenPose-compatible pose image

#### `manga/style_image_selector.json`
Processes style reference images for T2I Adapter conditioning.

**Usage:**
- Input: Style name (e.g., "naruto", "bleach")
- Output: Processed line art for style conditioning

#### `manga/generate_manga_panel.json`
Main panel generation workflow with placeholder substitution.

**Features:**
- Template-based workflow
- Dynamic placeholder replacement
- Configurable parameters

## Required Models

### Base Models
- `v1-5-pruned-emaonly.ckpt` - Stable Diffusion 1.5

### ControlNet Models
- `control_sd15_openpose.pth` - OpenPose ControlNet for SD 1.5

### T2I Adapter Models
- `t2iadapter_style_sd15.pth` - Style T2I Adapter for SD 1.5

### Preprocessors
- OpenPose Preprocessor
- Canny Edge Preprocessor

## Installation

1. **Install ComfyUI**
   ```bash
   git clone https://github.com/comfyanonymous/ComfyUI.git
   cd ComfyUI
   pip install -r requirements.txt
   ```

2. **Download Required Models**
   
   Place models in the appropriate ComfyUI directories:
   ```
   ComfyUI/models/checkpoints/v1-5-pruned-emaonly.ckpt
   ComfyUI/models/controlnet/control_sd15_openpose.pth
   ComfyUI/models/t2i_adapter/t2iadapter_style_sd15.pth
   ```

3. **Install Custom Nodes**
   
   Required custom nodes:
   - ComfyUI-ControlNet-Aux (for preprocessors)
   - ComfyUI-T2I-Adapter

4. **Start ComfyUI**
   ```bash
   python main.py
   ```

## Usage

### Manual Workflow Loading

1. Open ComfyUI web interface
2. Load workflow JSON file
3. Replace placeholder values
4. Queue prompt

### Automated Script Usage

Use the automation script for streamlined generation:

```bash
# Basic usage
python scripts/generate_panel.py --prompt "ninja jumping" --pose "generate:jumping pose" --style "process:naruto"

# Using configuration file
python scripts/generate_panel.py --input examples/ninja_panel_config.json
```

## Workflow Parameters

### Placeholder Variables

The workflows use placeholder variables that get replaced during automation:

- `{prompt}` - Main text prompt
- `{pose_image_path}` - Path to pose reference image
- `{style_image_path}` - Path to style reference image
- `{seed}` - Random seed for generation
- `{timestamp}` - Timestamp for unique filenames
- `{style_name}` - Style name for processing

### Generation Settings

**Quality Settings:**
- Steps: 20-25 (balance of quality and speed)
- CFG Scale: 7.0-7.5 (good prompt adherence)
- Sampler: euler_ancestral (good for manga style)

**ControlNet Settings:**
- OpenPose Strength: 1.0 (strong pose guidance)
- Style Adapter Strength: 0.8 (balanced style influence)

**Image Settings:**
- Resolution: 512x768 (manga panel aspect ratio)
- Format: PNG (lossless quality)

## Asset Organization

### Directory Structure
```
assets/
├── poses/          # Pose reference images
│   ├── jump.png
│   ├── stand.png
│   └── crouch.png
├── styles/         # Style reference images
│   ├── naruto.png
│   ├── bleach.png
│   └── one_piece.png
└── processed/      # Auto-generated processed assets
```

### Style References

Create style reference images by:
1. Finding high-quality manga panels in desired style
2. Ensuring clear line art and composition
3. Saving as PNG in `assets/styles/`
4. Using descriptive filenames (e.g., `naruto.png`, `seinen_style.png`)

### Pose References

Pose references can be:
- Hand-drawn pose sketches
- 3D model renders
- Photo references
- Auto-generated using the text-to-pose workflow

## Troubleshooting

### Common Issues

**Model Loading Errors:**
- Verify model files are in correct ComfyUI directories
- Check model file names match workflow specifications
- Ensure sufficient VRAM for model loading

**Workflow Execution Errors:**
- Check ComfyUI console for detailed error messages
- Verify all required custom nodes are installed
- Ensure input images exist and are accessible

**Quality Issues:**
- Adjust ControlNet and Adapter strength values
- Experiment with different samplers and CFG scales
- Improve quality of reference images

### Performance Optimization

**Speed Improvements:**
- Reduce step count for faster generation
- Use smaller image dimensions for testing
- Enable model offloading if VRAM limited

**Quality Improvements:**
- Increase step count (25-30 steps)
- Use higher resolution reference images
- Fine-tune strength parameters

## Advanced Usage

### Custom Workflows

Create custom workflows by:
1. Copying existing workflow JSON
2. Modifying node parameters
3. Adding new nodes for additional processing
4. Testing with ComfyUI interface

### Batch Processing

For batch generation:
1. Create multiple configuration JSON files
2. Use shell scripts to iterate through configs
3. Monitor ComfyUI queue status
4. Organize outputs by timestamp or prompt

### Integration

The workflows integrate with:
- Python automation scripts
- Web interfaces
- Batch processing systems
- Custom applications via ComfyUI API
