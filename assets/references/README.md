# Reference Images for ControlNet and T2I Adapter

This directory contains reference images used for ControlNet and T2I Adapter generation.

## Directory Structure

```
references/
├── controlnet/
│   ├── scene_canny.png      # Canny edge detection reference
│   ├── scene_depth.png      # Depth map reference
│   └── scene_pose.png       # OpenPose reference
└── adapter/
    ├── scene_canny.png      # Canny edge reference for T2I Adapter
    ├── scene_depth.png      # Depth reference for T2I Adapter
    └── scene_sketch.png     # Sketch reference for T2I Adapter
```

## Usage

These reference images are automatically loaded when using ControlNet or T2I Adapter generation methods:

```bash
# Use ControlNet with depth control
python scripts/run_full_pipeline.py --generation-method controlnet --control-type depth

# Use T2I Adapter with sketch control
python scripts/run_full_pipeline.py --generation-method adapter --control-type sketch
```

## Creating Reference Images

To create your own reference images:

1. **For ControlNet**:
   - Canny: Edge-detected version of your desired composition
   - Depth: Depth map (grayscale, closer = brighter)
   - OpenPose: Pose keypoints overlay

2. **For T2I Adapter**:
   - Canny: Similar to ControlNet canny
   - Depth: Similar to ControlNet depth
   - Sketch: Hand-drawn or processed sketch

## Image Requirements

- **Format**: PNG recommended
- **Size**: 768x1024 (manga panel aspect ratio)
- **Quality**: High contrast for better control
- **Content**: Should match your desired panel composition

## Notes

- If reference images are missing, the system will fallback to txt2img generation
- Reference images should be placed in the correct subdirectory (controlnet/ or adapter/)
- File names must match the expected pattern: scene_{type}.png
