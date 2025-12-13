# 🎨 MangaGen

> AI-powered manga generation pipeline. Transform text prompts into complete manga pages.

![Status](https://img.shields.io/badge/status-working-brightgreen)
![Python](https://img.shields.io/badge/python-3.10+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Features

- **Story to Scene** - AI converts your story into structured panel descriptions
- **Panel Generation** - High-quality anime/manga images via Pollinations.ai
- **Smart Layout** - Automatic 2x2 manga page composition
- **Multiple Styles** - Black & white manga or color anime

## 🚀 Quick Start

1. **Clone the repo**
   ```bash
   git clone https://github.com/Barun-2005/manga-gen-ai-pipeline.git
   cd manga-gen-ai-pipeline
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Generate your first manga**
   ```bash
   python scripts/generate_panels_api.py
   python scripts/simple_compose.py
   ```

4. **Check output**
   ```
   outputs/manga_page.png
   outputs/manga_page.pdf
   ```

## 📸 Example Output

Your manga will be composed as a 2x2 panel layout:

```
┌─────────┬─────────┐
│ Panel 1 │ Panel 2 │
├─────────┼─────────┤
│ Panel 3 │ Panel 4 │
└─────────┴─────────┘
```

## 🛠️ Pipeline

```
Text Prompt → Scene Plan → Panel Images → Composed Page
              (Groq/Gemini)  (Pollinations.ai)
```

## 📁 Project Structure

```
manga-gen/
├── scripts/
│   ├── generate_scene_json.py  # Story → Scene plan
│   ├── generate_panels_api.py  # Panel image generation
│   ├── place_bubbles.py        # Dialogue placement
│   └── compose_page.py         # Final page composition
├── src/
│   └── schemas.py              # Data models
├── outputs/                    # Generated manga
└── examples/                   # Sample outputs
```

## 🔑 API Keys

| Service | Purpose | Required |
|---------|---------|----------|
| Pollinations.ai | Image generation | **No key needed** |
| Groq/Gemini | Scene generation | Optional |

## 🎯 Roadmap

- [x] Image generation with Pollinations.ai
- [x] 4-panel manga page composition
- [ ] Smart dialogue bubble placement
- [ ] Character consistency across panels
- [ ] Web UI (Next.js)

## 📄 License

MIT License - feel free to use for your projects!

---

Made with ❤️ by Barun
