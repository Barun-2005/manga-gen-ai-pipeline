# Phase 18 Migration Guide

## Overview

Phase 18 represents a major migration of the manga-gen-ai-pipeline to use:
- **New Models**: Anything v4.5, enhanced embeddings, and optimized workflows
- **Centralized Configuration**: YAML-based configuration system
- **Improved Architecture**: Better error handling, fallback mechanisms, and modularity

## What's New in Phase 18

### 🎨 New Models & Assets
- **Anything v4.5**: Superior anime/manga generation quality
- **Enhanced Embeddings**: EasyNegative, BadHandV4 for better results
- **Updated Workflows**: Optimized for new model architecture
- **LoRA Support**: Integrated LoRA loading in workflows

### ⚙️ Centralized Configuration
- **Single Config File**: `config/settings.yaml` for all settings
- **Environment Variables**: `.env` for sensitive/local settings
- **Type-Safe Access**: Configuration manager with validation
- **Hot Reloading**: Changes take effect without restart

### 🔧 Improved Architecture
- **Better Error Handling**: Comprehensive error reporting and recovery
- **Fallback Mechanisms**: Automatic fallback to working methods
- **Retry Logic**: Exponential backoff for network operations
- **Modular Design**: Easier to extend and maintain

## Quick Start

### 1. Setup Models
```bash
# Create model directories and download essential models
python scripts/setup_models.py

# Include optional models (ControlNet, LoRAs, etc.)
python scripts/setup_models.py --include-optional
```

### 2. Configure Environment
```bash
# Copy and edit environment variables
cp .env.example .env
# Edit .env with your ComfyUI path and preferences
```

### 3. Run Sanity Test
```bash
# Comprehensive test of Phase 18 setup
python scripts/sanity_test.py
```

### 4. Generate Test Panel
```bash
# Test basic generation
python scripts/generate_panel.py --test

# Generate a sample panel
python scripts/generate_panel.py "a manga character in action pose" -o test_panel.png
```

## Configuration System

### Main Configuration (`config/settings.yaml`)
```yaml
# ComfyUI Settings
comfyui:
  server:
    url: "http://127.0.0.1:8188"
    timeout: 300
    max_retries: 3
    retry_delay: 2
  installation:
    path: "./ComfyUI-master"

# Model Configuration
models:
  checkpoint:
    name: "anything-v4.5-pruned.safetensors"
    path: "models/checkpoints"
  
# Generation Settings
generation:
  default_method: "txt2img"
  dimensions:
    width: 512
    height: 768
  sampling:
    steps: 25
    cfg_scale: 7.5
    sampler_name: "dpmpp_2m"
    scheduler: "karras"

# Output Configuration
output:
  color_mode: "color"
  base_dir: "outputs"
  include_color_mode_in_filename: true
```

### Environment Variables (`.env`)
```bash
# ComfyUI Configuration
COMFYUI_URL=http://127.0.0.1:8188
COMFYUI_PATH=./ComfyUI-master

# Model Paths
MODELS_DIR=models
OUTPUTS_DIR=outputs

# Feature Flags
ENABLE_STORY_MEMORY=false
ENABLE_EMOTION_MATCHING=false
ENABLE_POSE_MATCHING=false
```

## Model Directory Structure

```
models/
├── checkpoints/
│   └── anything-v4.5-pruned.safetensors
├── embeddings/
│   ├── easynegative.safetensors
│   └── badhandv4.pt
├── loras/
│   └── manga_style.safetensors
├── controlnet/
│   ├── control_v11p_sd15_depth.pth
│   └── control_v11p_sd15_canny.pth
├── t2i_adapter/
├── ipadapter/
└── vae/
    └── vae-ft-mse-840000-ema-pruned.safetensors
```

## Usage Examples

### Basic Panel Generation
```bash
# Simple text-to-image
python scripts/generate_panel.py "a manga warrior in battle stance" -o warrior.png

# Specify generation method and color mode
python scripts/generate_panel.py "dramatic scene" -o drama.png -m txt2img -c black_and_white

# Batch generation from file
python scripts/generate_panel.py --batch prompts.txt -o outputs/batch/
```

### Advanced Generation
```python
from core.panel_generator import EnhancedPanelGenerator

# Initialize generator
generator = EnhancedPanelGenerator()

# Generate with story context
success = generator.generate_panel(
    prompt="character looking determined",
    output_path="outputs/panel_001.png",
    generation_method="txt2img",
    color_mode="color",
    story_context={"character": "protagonist", "scene": "climax"}
)
```

### Configuration Access
```python
from core.config_manager import get_config

config = get_config()

# Access configuration values
comfyui_url = config.get_comfyui_url()
gen_settings = config.get_generation_settings()
color_config = config.get_color_mode_config("black_and_white")

# Check feature flags
if config.is_feature_enabled("enable_story_memory"):
    # Use story memory features
    pass
```

## Migration from Previous Phases

### Configuration Migration
1. **Old JSON configs** → **New YAML config**
2. **Scattered settings** → **Centralized configuration**
3. **Hard-coded values** → **Configurable parameters**

### Code Changes
1. **Import updates**: Use `from core.config_manager import get_config`
2. **Initialization**: `EnhancedPanelGenerator()` (no config files needed)
3. **Method calls**: Same API, but with centralized config support

### Model Updates
1. **Download new models**: Use `scripts/setup_models.py`
2. **Update workflows**: New workflows use Anything v4.5
3. **Enhanced prompts**: Better negative prompts with embeddings

## Troubleshooting

### Common Issues

#### ComfyUI Connection Failed
```bash
# Check if ComfyUI is running
curl http://127.0.0.1:8188/system_stats

# Verify configuration
python scripts/sanity_test.py
```

#### Models Not Found
```bash
# Download missing models
python scripts/setup_models.py --categories checkpoints embeddings

# Verify model paths
ls -la models/checkpoints/
```

#### Generation Fails
```bash
# Run comprehensive test
python scripts/sanity_test.py

# Check logs for specific errors
python scripts/generate_panel.py "test prompt" -o test.png --verbose
```

### Configuration Issues

#### Invalid YAML Syntax
- Use a YAML validator to check `config/settings.yaml`
- Ensure proper indentation (spaces, not tabs)
- Quote string values with special characters

#### Missing Environment Variables
- Copy `.env.example` to `.env`
- Set required variables like `COMFYUI_URL`
- Restart application after changes

## Performance Optimization

### Generation Speed
- Use appropriate image dimensions (512x768 for manga)
- Optimize sampling steps (20-30 for quality/speed balance)
- Enable GPU acceleration in ComfyUI

### Memory Usage
- Monitor ComfyUI memory usage
- Use model offloading if needed
- Clear cache between large batches

### Network Optimization
- Increase timeout for slow connections
- Adjust retry settings for unstable networks
- Use local ComfyUI instance when possible

## Development

### Adding New Models
1. Update `scripts/setup_models.py` with model definitions
2. Add model paths to `config/settings.yaml`
3. Update workflows to use new models
4. Test with sanity test suite

### Extending Configuration
1. Add new settings to `config/settings.yaml`
2. Update `core/config_manager.py` with accessor methods
3. Add validation and default values
4. Update documentation

### Custom Workflows
1. Create workflow JSON in `assets/workflows/`
2. Add workflow path to configuration
3. Update panel generator to support new workflow
4. Test with various prompts and settings

## API Reference

### ConfigManager
```python
config = get_config()

# Core methods
config.get(key, default=None)
config.get_comfyui_url()
config.get_comfyui_installation_path()
config.get_generation_settings()
config.get_color_mode_config(mode)
config.is_feature_enabled(feature)
```

### EnhancedPanelGenerator
```python
generator = EnhancedPanelGenerator()

# Main generation method
generator.generate_panel(
    prompt: str,
    output_path: str,
    generation_method: str = None,
    control_type: str = None,
    reference_image: str = None,
    color_mode: str = None,
    story_context: Dict[str, Any] = None
) -> bool

# Batch generation
generator.generate_batch_panels(
    panel_configs: list,
    output_dir: str = "outputs/panels"
) -> Dict[str, bool]
```

### ComfyUIClient
```python
client = ComfyUIClient()

# Server status
client.is_server_ready() -> bool

# Image generation
client.generate_images(
    workflow: Dict[str, Any],
    output_dir: str
) -> List[str]

# Workflow creation
workflow = create_basic_txt2img_workflow(
    prompt: str,
    negative_prompt: str = "",
    width: int = 512,
    height: int = 768,
    steps: int = 25,
    cfg_scale: float = 7.5,
    seed: int = -1,
    use_config: bool = True
) -> Dict[str, Any]
```

## Support

### Getting Help
1. **Run sanity test**: `python scripts/sanity_test.py`
2. **Check logs**: Enable verbose mode with `--verbose`
3. **Verify setup**: Ensure all models and dependencies are installed
4. **Review configuration**: Check `config/settings.yaml` and `.env`

### Reporting Issues
Include the following information:
- Output of sanity test
- Configuration files (sanitized)
- Error messages and stack traces
- ComfyUI version and setup
- System specifications

### Contributing
1. Follow existing code style and patterns
2. Add tests for new features
3. Update documentation
4. Run sanity test before submitting changes

---

**Phase 18** brings significant improvements to the manga generation pipeline. The centralized configuration, new models, and enhanced architecture provide a solid foundation for future development while maintaining backward compatibility where possible.