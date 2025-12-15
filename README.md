# MangaGen - AI Manga Generation Pipeline

> 🎨 Professional-grade manga creation powered by AI | [Pollinations](https://pollinations.ai/) + Local Models

[![Status](https://img.shields.io/badge/Status-Beta-yellow)]()
[![Progress](https://img.shields.io/badge/Progress-60%25-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

## 🚀 Features

### ✅ **Intelligent Story Generation**
- **Story Director AI** with sliding context window
- Proper pacing based on page count
- Character expansion and meaningful dialogue
- TAG-based visual descriptions for better image quality

### ✅ **Professional Image Generation**
- **Pollinations.ai** (FREE, no API key needed)
- **NVIDIA FLUX.1-dev** (optional, high quality)
- Character DNA system for visual consistency
- Advanced prompt engineering (60+ negative prompts)
- Weighted quality boosters: `(masterpiece:1.3), (best quality:1.3)`

### ✅ **Mind-Blowing Canvas Editor**
- **Panel Regeneration** with custom prompts
- Drag-and-drop bubble editing
- Multiple bubble styles (speech, thought, shout, narrator)
- Font size controls
- True iterative editing (Canva-like experience!)

### ✅ **Production-Ready Backend**
- MongoDB integration (optional, graceful fallback)
- Rate limiting (10 req/60s)
- Professional logging with colors
- Health monitoring (CPU, memory, disk)
- Image optimization and thumbnails
- Environment validation

### ✅ **High-Quality Output**
- 300 DPI PDFs with metadata
- Optimized PNGs for web
- Multiple export formats (PDF, PNG, ZIP)

---

## 📦 Quick Start

### 1. Clone & Install
```bash
git clone https://github.com/YOUR_USERNAME/MangaGen.git
cd MangaGen

# Backend
pip install -r requirements.txt

# Frontend  
cd frontend
npm install
```

### 2. Configure Environment
```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your GROQ API key (REQUIRED)
# Get free key from: https://console.groq.com
GROQ_API_KEY=your_key_here
```

### 3. Run
```bash
# Terminal 1: Backend
python api/main.py

# Terminal 2: Frontend
cd frontend
npm run dev
```

Open http://localhost:3000 🎉

---

## 🎯 Usage

1. **Create Story** - Enter your manga idea
2. **Choose Style** - B/W manga or color anime
3. **Set Layout** - 2x2, 2x3, or 3x3 panels per page
4. **Generate** - AI creates your manga!
5. **Edit** - Use canvas to refine dialogue and regenerate panels
6. **Export** - Download as PDF or individual PNGs

---

## 🔧 Configuration

### API Keys (Optional)
- **NVIDIA_IMAGE_API_KEY** - FLUX.1-dev for highest quality
- **GEMINI_API_KEY** - Enhanced story direction
- **MONGODB_URL** - Database persistence

### Feature Flags
- `ENABLE_DATABASE` - MongoDB persistence (default: false)
- `ENABLE_RATE_LIMIT` - API rate limiting (default: true)
- `LOG_LEVEL` - Logging verbosity (default: INFO)

---

## 🏗️ Architecture

```
MangaGen/
├── api/              # FastAPI backend
├── frontend/         # Next.js React frontend
├── scripts/          # Core generation logic
├── src/
│   ├── ai/          # Story Director, Character DNA
│   ├── dialogue/    # Bubble placement
│   ├── database/    # MongoDB integration
│   └── utils/       # Logging, optimization, validation
└── outputs/         # Generated manga
```

---

## 🎨 Prompt Engineering

MangaGen uses advanced prompt engineering for maximum quality:

**Positive Prompts** (weighted):
- `(masterpiece:1.3), (best quality:1.3), (ultra detailed:1.2)`
- Camera parameters: shot type, angle, composition, lighting
- Character DNA tags for consistency

**Negative Prompts** (35+ optimized):
- Avoids: text, watermarks, 3D, blur, bad anatomy, artifacts
- Style-specific (B/W avoids color, color avoids grayscale)

---

## 📊 Progress

- [x] Story Director with TAG prompts
- [x] Character DNA system
- [x] Panel regeneration
- [x] Advanced prompt engineering
- [x] MongoDB + security
- [x] Professional logging
- [x] Image optimization
- [x] Health monitoring
- [ ] Testing phase (next)
- [ ] Local model integration (Z-Image Turbo on RTX 4060)

---

## 🤝 Contributing

Contributions welcome! This is a portfolio project showcasing AI integration, full-stack development, and prompt engineering.

---

## 📝 License

MIT License - feel free to use for learning and portfolio projects!

---

## 🙏 Credits

- **Image Generation**: [Pollinations.ai](https://pollinations.ai), NVIDIA FLUX.1-dev
- **LLM**: Groq (LLaMA 3.3), Google Gemini
- **Dialogue System**: Custom PIL-based bubble placement

---

**Built with ❤️ for the manga community**
