# MangaGen

Text-to-manga generator. Give it a story prompt, get back a multi-page manga with consistent characters.

Built because I got tired of AI art generators giving me different faces every panel.

## What it does

- **Dynamic layouts** - LLM picks layouts based on the scene (action = diagonal panels, dialogue = talking heads)
- **Character consistency** - Same character looks the same across panels using visual DNA extraction
- **Bubble placement** - Auto-places speech bubbles avoiding faces
- **Continue story** - Add more pages to existing manga without creating duplicate projects

## Tech

- Python/FastAPI backend
- Next.js frontend  
- ComfyUI for image gen (Z-Image SDXL)
- Groq/Llama-70b for story planning
- MongoDB for persistence

## Setup

```bash
# Clone
git clone https://github.com/Barun-2005/manga-gen-ai-pipeline.git
cd manga-gen-ai-pipeline

# Backend
pip install -r requirements.txt

# Frontend
cd frontend && npm install

# Copy env and add your keys
cp .env.example .env
```

## Run

```bash
# Terminal 1 - ComfyUI
py -3.10 ComfyUI/main.py --listen --port 8188 --novram

# Terminal 2 - Backend  
py -3.10 -m uvicorn api.main:app --reload --port 8000

# Terminal 3 - Frontend
cd frontend && npm run dev
```

Go to `localhost:3000`

## Structure

```
api/          - FastAPI endpoints
scripts/      - Core generation (MangaGenerator, layouts)
src/          - Database, utils
frontend/     - Next.js app
ComfyUI/      - Image gen (not in repo, download separately)
```

## Gallery

*will add sample outputs here*

---

3rd year CSE project. MIT license.
