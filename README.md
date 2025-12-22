# MangaGen Pipeline

End-to-end text-to-manga generation. Not just image generation - a full pipeline that handles story planning, character consistency, panel layouts, dialogue placement, and multi-page exports.

Built because I got tired of AI art generators giving me different faces every panel and having to manually stitch everything together.

## Why "Pipeline"?

Most AI manga tools stop at image generation. This one chains together:

1. **Story Director** - LLM plans the full chapter with proper pacing, not just random panels
2. **Character DNA** - Extracts visual traits and maintains them across all panels
3. **Dynamic Layouts** - LLM picks layouts based on scene type (action = diagonal panels, dialogue = talking heads, reveals = full page)
4. **Smart Bubbles** - Face detection to place speech bubbles without covering characters
5. **Project Merging** - Continue generating pages without breaking the project
6. **PDF Export** - Browser-ready PDF with all dialogue rendered

It's the difference between "generate 4 random images" and "here's your 12-page chapter as a PDF".

## The Cool Stuff

- **15+ layout templates** - The LLM picks from hero spreads, action grids, conversation layouts based on narrative context
- **Character consistency** - Same character actually looks the same across panels (this was surprisingly hard)
- **Infinite continuation** - Add 3 more pages to your 9-page manga, get a 12-page story, not two separate projects
- **ComfyUI backend** - Local SDXL generation, no API costs for images
- **Multi-LLM fallback** - Groq → Gemini → NVIDIA NIM, always has a working brain

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python, FastAPI |
| Frontend | Next.js 14, TypeScript |
| Image Gen | ComfyUI (Z-Image SDXL) |
| LLM | Groq/Llama-70b, Gemini, NVIDIA NIM |
| Database | MongoDB Atlas |

## Quick Start

```bash
git clone https://github.com/Barun-2005/manga-gen-ai-pipeline.git
cd manga-gen-ai-pipeline

pip install -r requirements.txt
cd frontend && npm install
cp .env.example .env  # add your API keys
```

Run three terminals:
```bash
# ComfyUI
py -3.10 ComfyUI/main.py --listen --port 8188 --novram

# Backend
py -3.10 -m uvicorn api.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

## Project Structure

```
api/          - FastAPI (generation endpoints, project management)
scripts/      - Core engine (MangaGenerator, layout templates, image gen)
src/          - Database, utilities
frontend/     - Next.js canvas editor and dashboard
```

## Gallery

*adding sample outputs soon*

---

3rd year CSE project. MIT license.
