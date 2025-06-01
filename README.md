# MangaGen – AI-Powered Manga Generation Framework

**MangaGen** is an experimental pipeline for turning plain text prompts into manga-style stories with visuals. It combines large language models (LLMs) for structured storytelling and Stable Diffusion (via ComfyUI) for generating stylized manga panels.

This project is still under active development, and many features are subject to change as we refine the workflow.

---

## Features

- **Story Generation**
  Generates multi-act story structures using OpenRouter-powered LLMs.

- **Visual Generation**
  Uses ComfyUI to generate high-resolution manga-style images from scene descriptions.

- **Modular Pipeline**
  Clean separation of logic between story, image, and orchestration components.

- **Multi-Genre Support**
  Works across genres like shonen, seinen, slice-of-life, and fantasy.

- **Customizable Output**
  Set your own dimensions, genre, seeds, and scene structure via config or CLI.

---

## Project Layout

```
manga-gen-ai-pipeline/
├── workflows/
│   └── manga/              # ComfyUI workflow templates
├── assets/
│   └── styles/             # Style presets and configurations
├── scripts/                # Utility and generation scripts
│   ├── generate_sample_panels.py
│   └── self_test.py
├── examples/               # Example configurations and prompts
├── outputs/                # Generated images and manga
│   └── 2025-06-01/        # Date-organized outputs
├── manga_archive/          # Completed manga storage
├── llm/                    # Language model story generation
│   ├── story_generator.py
│   └── prompt_templates.py
├── image_gen/              # ComfyUI-based image generation
│   ├── comfy_client.py
│   ├── prompt_builder.py
│   └── image_generator.py
├── pipeline/               # Main orchestration logic
│   ├── generate_manga.py
│   ├── automation_stubs.py
│   └── utils.py
├── .env                    # Environment configuration
├── requirements.txt
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- [ComfyUI](https://github.com/comfyanonymous/ComfyUI) installed and running
- OpenRouter API key for LLM-based story generation

### Setup

```bash
git clone <your-repo-url>
cd MangaGen
pip install -r requirements.txt
cp .env.example .env  # Then edit it with your API keys and config
```

### ComfyUI Setup

Follow ComfyUI's setup instructions and make sure it runs on `http://127.0.0.1:8188`. Update your `.env` file accordingly.

---

## Usage

### Basic Example

```bash
python pipeline/generate_manga.py "A young ninja discovers magical powers in a modern city"
```

### Advanced Usage

```bash
python pipeline/generate_manga.py \
  "A detective investigates supernatural crimes" \
  --genre seinen \
  --output detective_manga \
  --seed 42
```

### Python API

```python
from pipeline.generate_manga import MangaGenerator

generator = MangaGenerator()
result = generator.generate_complete_manga(
    prompt="A robot learns about human emotions",
    genre="slice_of_life"
)
```

### Working With Components

#### Story Only

```python
from llm.story_generator import generate_manga_story

story = generate_manga_story(
    "A chef discovers their recipes have magical properties",
    acts=3,
    scenes_per_act=4
)
print(story["story_text"])
```

#### Image Prompt Builder

```python
from image_gen.prompt_builder import PromptBuilder, Scene, Character

protagonist = Character(
    name="Akira",
    appearance="spiky black hair, determined eyes",
    clothing="chef uniform, magical amulet",
    personality_traits="passionate, creative"
)

scene = Scene(
    description="The chef discovers glowing ingredients",
    location="magical kitchen",
    time_of_day="midnight",
    mood="mysterious",
    characters=["Akira"],
    action="mixing glowing ingredients"
)

builder = PromptBuilder()
builder.add_character(protagonist)
prompt = builder.build_scene_prompt(scene, "dramatic")
```

---

## Configuration Overview

Edit your `.env` to tweak the following:

```env
OPENROUTER_API_KEY=your_key_here
LLM_MODEL=deepseek/deepseek-r1-distill-llama-70b
COMFYUI_URL=http://127.0.0.1:8188

IMAGE_WIDTH=512
IMAGE_HEIGHT=768
DEFAULT_GENRE=shonen
RANDOM_SEED=-1

OUTPUT_DIR=./outputs
LOG_LEVEL=INFO
```

### Story Generation Model

Uses **DeepSeek R1** (free via OpenRouter) for high-quality story generation:
- **Free to use** - No cost for story generation
- **High quality** - Excellent creative writing capabilities
- **Fast response** - Quick story generation
- **No quotas** - Generate as many stories as needed

### Genres Supported

**Shonen** – Action-packed, youth-focused stories

**Seinen** – More mature, dark, or psychological narratives

**Slice of Life** – Realistic, everyday settings

**Fantasy** – Magic, otherworldly settings, and epic themes

---

## Dev Notes

### Add New Templates
Modify `llm/prompt_templates.py`.

### Custom Prompts for Images
Extend logic in `image_gen/prompt_builder.py`.

### Run Tests

Comprehensive self-test:
```bash
python scripts/self_test.py
```

Generate sample panels:
```bash
python scripts/generate_sample_panels.py
```

Generate single panel from text:
```bash
python scripts/generate_from_prompt.py "ninja dodging kunai"
python scripts/generate_from_prompt.py "girl reading book" --style shoujo
```

Generate complete manga from vague prompt:
```bash
python scripts/generate_full_manga.py "ninja discovers magic"
python scripts/generate_full_manga.py "robot learns emotions" --chapters 5
```

Or run components manually:
```bash
python llm/story_generator.py
python image_gen/prompt_builder.py
```

### Format & Lint
```bash
black .
flake8 .
```

---

## Troubleshooting

**ComfyUI not connecting?**
- Make sure it's running at the URL specified in `.env`
- Check firewall or port issues

**API key errors?**
- Double-check your `.env`
- Make sure your key is active and has enough quota

**Image generation failed?**
- Check that the right models are loaded in ComfyUI
- Look at the log output for detailed error messages

---

## Future Plans

Some things on the roadmap:

- Web interface for easy prompt entry and preview
- Better panel layouting
- Character tracking and consistency across scenes
- Support for dialogue/voice synthesis
- Potential for multi-language support
- Shared editing tools for collaborative storybuilding
