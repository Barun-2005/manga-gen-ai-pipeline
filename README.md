# 🎨 MangaGen - AI Manga Generation Pipeline

Generate complete manga pages from text prompts using AI.

## 🚀 Quick Start (Kaggle)

1. Open `notebooks/kaggle_run.ipynb` on Kaggle
2. Add your `GEMINI_API_KEY` in Kaggle Secrets
3. Run all cells
4. Download `outputs/manga_page.pdf`

## 📁 Project Structure

```
MangaGen/
├── notebooks/
│   └── kaggle_run.ipynb    # End-to-end Kaggle notebook
├── scripts/
│   ├── generate_scene_json.py   # Gemini → JSON scene plan
│   ├── generate_panels.py       # Image generation
│   ├── place_bubbles.py         # Dialogue bubble placement
│   └── compose_page.py          # PDF assembly
├── archive/
│   ├── salvaged/           # Useful code from original project
│   └── repo_audit.md       # Original project audit
├── examples/               # Sample prompts and outputs
├── tests/                  # Unit tests
├── requirements-mvp.txt    # Minimal dependencies
└── .env.example            # Environment template
```

## 🔧 Environment Variables

Copy `.env.example` to `.env` and fill in:

```bash
GEMINI_API_KEY=your_api_key_here   # Required - Google Gemini
HF_TOKEN=your_hf_token             # Optional - HuggingFace
KAGGLE_USERNAME=your_username      # Optional - Kaggle CLI
KAGGLE_KEY=your_key                # Optional - Kaggle CLI
```

## 💻 Local Development

```bash
# Install dependencies
pip install -r requirements-mvp.txt

# Generate scene plan
python scripts/generate_scene_json.py "A ninja discovers a temple"

# Generate panels (requires GPU or mock mode)
python scripts/generate_panels.py --scene scene_plan.json --mock

# Place dialogue bubbles
python scripts/place_bubbles.py --panels outputs/ --scene scene_plan.json

# Create PDF
python scripts/compose_page.py --panels outputs/ --bubbles bubbles.json
```

## 🎯 MVP Scope

- **Input**: Short text prompt
- **Output**: 1 manga page (3 panels) with dialogue bubbles as PDF
- **LLM**: Google Gemini for story → scene JSON
- **Image Gen**: Stable Diffusion via Kaggle GPU
- **Character Consistency**: IP-Adapter / LoRA

## 📋 Requirements

- Python 3.10+
- Kaggle account (free tier GPU)
- Gemini API key

## 🔗 Links

- [Kaggle Notebook](https://kaggle.com) - Run end-to-end pipeline
- [Gemini API](https://makersuite.google.com/app/apikey) - Get API key

---

**Branch**: `mvp/kaggle-flux`
