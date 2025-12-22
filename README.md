# MangaGen - AI Coding Agent Powered Manga Studio

An automated manga generation engine that converts text stories into consistent, multi-page manga chapters. Built with ComfyUI, Python, and React.

**Status:** V4.5 Production Ready

---

## 🚀 Key Features

### V4 Dynamic Layout Engine
No fixed grids. The LLM Story Director chooses from 15+ layout templates based on narrative context - action scenes get dynamic diagonals, dialogue gets talk panels.

### Character Consistency (Z-Image Hybrid Workflow)
Uses a custom ComfyUI workflow with Z-Image for manga-style generation. Character DNA is extracted and maintained across panels for visual consistency.

### Smart Bubble Placement
Face detection system finds safe zones for dialogue bubbles, avoiding character faces. Bubbles auto-position based on panel composition.

### Project Merging (Infinite Story Continuation)
"Continue Story" appends new pages to existing projects. No duplicate entries - pages merge seamlessly with correct numbering.

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Backend** | Python 3.10, FastAPI |
| **Frontend** | React, Next.js 14, TypeScript |
| **Image Gen** | ComfyUI (Z-Image SDXL) |
| **LLM** | Groq (Llama-3.3-70b), Gemini, NVIDIA NIM |
| **Database** | MongoDB Atlas |
| **Styling** | Tailwind CSS |

---

## ⚡ Quick Setup

### Prerequisites
- Python 3.10+
- Node.js 18+
- ComfyUI with Z-Image models
- MongoDB Atlas account (or local MongoDB)

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_USERNAME/manga-gen-ai-pipeline.git
cd manga-gen-ai-pipeline

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys:
# - GROQ_API_KEY
# - MONGODB_URI
# - GOOGLE_API_KEY (optional)
```

### 3. Run

**Terminal 1 - ComfyUI:**
```bash
py -3.10 ComfyUI/main.py --listen --port 8188 --novram
```

**Terminal 2 - Backend:**
```bash
py -3.10 -m uvicorn api.main:app --reload --port 8000
```

**Terminal 3 - Frontend:**
```bash
cd frontend && npm run dev
```

Visit: `http://localhost:3000`

---

## 📁 Project Structure

```
manga-gen-ai-pipeline/
├── api/                  # FastAPI backend
│   └── main.py           # Main API endpoints
├── scripts/              # Core generation logic
│   ├── generate_manga.py # MangaGenerator class
│   ├── layout_templates.py
│   └── image_generator.py
├── src/                  # Utilities & database
│   └── database/
├── frontend/             # Next.js React app
│   └── src/app/
├── ComfyUI/              # Image generation (git-ignored)
└── outputs/              # Generated mangas (git-ignored)
```

---

## 🎨 Generated Samples

*Coming soon - Gallery of generated manga pages*

---

## 📈 Roadmap

- [x] V4 Dynamic Layouts
- [x] Character DNA Consistency
- [x] Project Merging
- [x] Smart Bubble Placement
- [ ] Color Manga Mode
- [ ] Panel Regeneration (Qwen-VL)
- [ ] Multi-chapter Export

---

## 🤝 Contributing

Built by a 3rd year CSE student who got tired of AI art generators making inconsistent characters. PRs welcome.

---

## 📜 License

MIT License - Use it, break it, make something cool.
