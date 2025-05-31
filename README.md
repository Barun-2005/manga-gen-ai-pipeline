# MangaGen - AI-Powered Manga Generation Pipeline

A full-stack manga generation pipeline that transforms text prompts into complete manga stories using AI. The system combines Large Language Models (LLMs) for story generation with Stable Diffusion via ComfyUI for visual creation.

## 🚀 Features

- **Story Generation**: Uses OpenRouter API to generate structured manga stories from simple prompts
- **Visual Creation**: Integrates with ComfyUI for high-quality manga-style image generation
- **Modular Design**: Clean, extensible architecture with separate modules for each pipeline stage
- **Multiple Genres**: Support for different manga genres (shonen, seinen, slice-of-life, fantasy)
- **Customizable**: Configurable story structure, image dimensions, and generation parameters
- **Progress Tracking**: Real-time progress monitoring and logging

## 📁 Project Structure

```
MangaGen/
│
├── llm/                           # LLM story generation
│   ├── story_generator.py         # OpenRouter LLM integration
│   └── prompt_templates.py        # Story prompt templates
│
├── image_gen/                     # Image generation
│   ├── comfy_client.py            # ComfyUI API client
│   └── prompt_builder.py          # SD prompt generation
│
├── pipeline/                      # Main pipeline
│   ├── generate_manga.py          # Main orchestration script
│   └── utils.py                   # Utilities and helpers
│
├── output/                        # Generated content
│   ├── images/                    # Generated images
│   └── manga/                     # Final compiled manga
│
├── .env                           # Environment variables
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## 🛠️ Installation

### Prerequisites

- Python 3.10 or higher
- ComfyUI installed and running (for image generation)
- OpenRouter API key (for story generation)

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd MangaGen
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and settings
   ```

4. **Set up ComfyUI**
   - Install ComfyUI following their official documentation
   - Ensure ComfyUI is running on `http://127.0.0.1:8188` (or update COMFYUI_URL in .env)
   - Load appropriate models for manga-style generation

## 🚀 Quick Start

### Basic Usage

Generate a manga from a simple prompt:

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

### Programmatic Usage

```python
from pipeline.generate_manga import MangaGenerator

# Initialize generator
generator = MangaGenerator()

# Generate complete manga
results = generator.generate_complete_manga(
    prompt="A robot learns about human emotions",
    genre="slice_of_life"
)

if results["success"]:
    print(f"Generated manga saved to: {results['manga_path']}")
```

## 📖 Usage Examples

### Story Generation Only

```python
from llm.story_generator import generate_manga_story

story = generate_manga_story(
    "A chef discovers their recipes have magical properties",
    acts=3,
    scenes_per_act=4
)
print(story["story_text"])
```

### Image Prompt Building

```python
from image_gen.prompt_builder import PromptBuilder, Scene, Character

# Create character
protagonist = Character(
    name="Akira",
    appearance="spiky black hair, determined eyes",
    clothing="chef uniform, magical amulet",
    personality_traits="passionate, creative"
)

# Create scene
scene = Scene(
    description="The chef discovers glowing ingredients",
    location="magical kitchen",
    time_of_day="midnight",
    mood="mysterious",
    characters=["Akira"],
    action="mixing glowing ingredients"
)

# Build prompt
builder = PromptBuilder()
builder.add_character(protagonist)
prompt = builder.build_scene_prompt(scene, "dramatic")
```

## ⚙️ Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# API Keys
OPENROUTER_API_KEY=your_key_here
COMFYUI_URL=http://127.0.0.1:8188

# Generation Settings
IMAGE_WIDTH=512
IMAGE_HEIGHT=768
DEFAULT_GENRE=shonen
RANDOM_SEED=-1

# Output Settings
OUTPUT_DIR=./output
LOG_LEVEL=INFO
```

### Story Structure

Configure story generation:

- **Acts**: Number of story acts (default: 3)
- **Scenes per Act**: Scenes in each act (default: 3)
- **Genre**: Story genre affecting tone and themes
- **Model**: LLM model for story generation

### Image Generation

Configure image output:

- **Dimensions**: Image width and height
- **Style**: Manga style presets
- **Quality**: Generation quality settings
- **Batch Size**: Number of concurrent generations

## 🎨 Supported Genres

- **Shonen**: Action-oriented, friendship themes
- **Seinen**: Mature, complex narratives
- **Slice of Life**: Everyday moments, character-driven
- **Fantasy**: Magic systems, epic quests

## 🔧 Development

### Adding New Features

1. **New Story Templates**: Add to `llm/prompt_templates.py`
2. **Custom Prompts**: Extend `image_gen/prompt_builder.py`
3. **Pipeline Steps**: Modify `pipeline/generate_manga.py`

### Testing

```bash
# Run basic tests
python -m pytest tests/

# Test individual components
python llm/story_generator.py
python image_gen/prompt_builder.py
```

### Code Style

```bash
# Format code
black .

# Check style
flake8 .
```

## 🐛 Troubleshooting

### Common Issues

1. **ComfyUI Connection Failed**
   - Ensure ComfyUI is running
   - Check COMFYUI_URL in .env
   - Verify firewall settings

2. **API Key Errors**
   - Verify OPENROUTER_API_KEY is set
   - Check API key permissions
   - Ensure sufficient API credits

3. **Generation Failures**
   - Check log files for detailed errors
   - Verify model availability in ComfyUI
   - Ensure sufficient disk space

### Debug Mode

Enable detailed logging:

```bash
export LOG_LEVEL=DEBUG
python pipeline/generate_manga.py "your prompt"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- OpenRouter for LLM API access
- ComfyUI for Stable Diffusion integration
- The open-source AI community

## 🔮 Future Features

- [ ] Web interface for easy manga generation
- [ ] Character consistency across panels
- [ ] Advanced panel layout algorithms
- [ ] Voice synthesis for dialogue
- [ ] Animation support
- [ ] Multi-language story generation
- [ ] Custom model training integration
- [ ] Collaborative story editing

## 📞 Support

For questions and support:

- Create an issue on GitHub
- Check the documentation
- Review existing issues for solutions

---

**Note**: This is a development framework. Actual manga generation quality depends on the underlying models (LLM and Stable Diffusion) and their configuration.
