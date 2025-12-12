# 🎨 MangaGen - AI Manga Generation Pipeline

Generate complete manga pages with consistent characters from simple text prompts!

![Status](https://img.shields.io/badge/status-MVP%20Development-yellow)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **📝 Story → Scene JSON**: Uses Gemini 2.0 to convert story prompts into structured scene plans
- **🎨 Consistent Characters**: IP-Adapter FaceID ensures the same character face across all panels
- **💬 Smart Bubble Placement**: Face-aware dialogue bubble positioning with tone detection
- **📐 Flexible Layouts**: 2×2 grid, vertical webtoon, 3-panel, and more
- **🎯 Style Options**: Black & white manga or colorful anime style
- **📦 Easy Export**: Zip file with PDF, PNG, and all assets

## 🚀 Quick Start (Kaggle)

1. **Open the notebook on Kaggle**: [notebooks/kaggle_run.ipynb](notebooks/kaggle_run.ipynb)
2. **Add your API key**: Settings → Add-ons → Secrets → `GEMINI_API_KEY`
3. **Run all cells** (GPU required)
4. **Download** `manga_output.zip`

> **Get your free Gemini API key**: https://aistudio.google.com/app/apikey

## 📁 Project Structure

```
MangaGen/
├── 📓 notebooks/
│   └── kaggle_run.ipynb          # Complete Kaggle pipeline notebook
├── 📜 scripts/
│   ├── generate_scene_json.py    # Gemini → JSON scene plan
│   ├── generate_panels.py        # SDXL + IP-Adapter image generation
│   ├── place_bubbles.py          # Dialogue bubble placement
│   └── compose_page.py           # PDF assembly + zip export
├── 🔧 src/
│   ├── __init__.py               # Package initialization
│   └── schemas.py                # Pydantic data models
├── 📦 archive/
│   ├── salvaged/                 # Reusable code from original project
│   │   ├── dialogue_placer.py    # Production-ready bubble engine
│   │   ├── compile_pdf.py        # PDF generation utilities
│   │   └── prompt_templates.py   # Story structure templates
│   └── repo_audit.md             # Original project audit
├── 🧪 examples/                   # Sample prompts and outputs
├── 🧪 tests/                      # Unit tests
├── requirements.txt              # Full dependencies (version-locked)
├── requirements-mvp.txt          # Minimal dependencies
├── install_kaggle_deps.sh        # Kaggle-specific installer
└── .env.example                  # Environment template
```

## 🔧 Local Development

### Prerequisites
- Python 3.10+
- CUDA GPU (for real generation) or use `--mock` mode

### Installation

```bash
# Clone the repository
git clone https://github.com/Barun-2005/manga-gen-ai-pipeline.git
cd manga-gen-ai-pipeline

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Set up environment
copy .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Usage

```bash
# 1. Generate scene plan from story prompt
python scripts/generate_scene_json.py "Astra discovers an ancient artifact" --style bw_manga --layout 2x2

# 2. Generate panel images (use --mock for testing without GPU)
python scripts/generate_panels.py --scene scene_plan.json --output outputs/ --mock

# 3. Place dialogue bubbles
python scripts/place_bubbles.py --panels outputs/ --scene scene_plan.json

# 4. Compose final page and PDF
python scripts/compose_page.py --panels outputs/ --bubbles bubbles.json --scene scene_plan.json
```

### Output
- `outputs/manga_page.pdf` - Final manga page
- `outputs/manga_page.png` - Full resolution page image
- `manga_output.zip` - All files zipped for easy sharing

## 🎯 Configuration Options

### Visual Style (`--style`)
| Style | Description |
|-------|-------------|
| `bw_manga` | Black & white traditional manga |
| `color_anime` | Colorful anime illustration |

### Panel Layout (`--layout`)
| Layout | Panels | Best For |
|--------|--------|----------|
| `2x2` | 4 | Traditional manga pages |
| `vertical_webtoon` | 3 | Mobile/scrolling format |
| `3_panel` | 3 | Story highlights |
| `single` | 1 | Splash pages |

## 🔑 Environment Variables

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key_here

# Optional
HF_TOKEN=your_huggingface_token  # For model downloads
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Story Prompt                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Gemini 2.0 Flash (FREE)                        │
│         Story → Structured JSON Scene Plan                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    Kaggle GPU (FREE)                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ 1. Generate Character Reference (SDXL)                  │ │
│  │ 2. Generate Panels (SDXL + IP-Adapter for consistency)  │ │
│  │ 3. Place Dialogue Bubbles (OpenCV + Face Detection)     │ │
│  │ 4. Compose Page Layout (PIL + ReportLab)                │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   manga_output.zip                           │
│              (PDF + Images + References)                     │
└─────────────────────────────────────────────────────────────┘
```

## 💰 Cost

| Resource | Free Tier | Usage per Manga | Cost |
|----------|-----------|-----------------|------|
| Gemini API | 1500 req/day | ~5-10 requests | **$0** |
| Kaggle GPU | 30h/week | ~5-10 min | **$0** |
| HuggingFace Models | Unlimited | Download once | **$0** |
| **Total** | - | - | **$0** |

## 🔗 Links

- [Kaggle Notebook](https://kaggle.com) - Run the pipeline
- [Gemini API](https://aistudio.google.com/app/apikey) - Get API key
- [IP-Adapter](https://huggingface.co/h94/IP-Adapter) - Character consistency
- [SDXL](https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0) - Base model

## 📋 Roadmap

- [x] Core MVP pipeline
- [x] Gemini scene generation
- [x] SDXL image generation
- [x] IP-Adapter character consistency
- [x] Bubble placement engine
- [x] PDF composition
- [x] Kaggle notebook
- [ ] ControlNet pose consistency
- [ ] Multi-page story support
- [ ] Web UI (Gradio/Streamlit)

## 🤝 Contributing

Contributions are welcome! Please read the [Contributing Guide](CONTRIBUTING.md) first.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

Made with ❤️ by Barun
