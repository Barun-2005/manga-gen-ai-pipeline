# 📊 Image Generation API Research Results

> Research conducted via Perplexity AI on 2025-12-13

## 🏆 Strategy Summary

**Hybrid Approach (Best of Both Worlds):**
1. **Character References** → High-quality API (Gemini Imagen / Leonardo.ai)
2. **Bulk Panel Generation** → Local SDXL on Colab with IP-Adapter

This leverages:
- API quality for critical character consistency (5-10 images per story)
- Colab's free GPU for bulk generation (unlimited with session management)

---

## 📋 API Comparison Table

| API | Free Tier | Cost/Image | Anime Models | Character Consistency | Speed |
|-----|-----------|------------|--------------|----------------------|-------|
| **Hugging Face** | 300 req/hr ✅ | Pro $10/mo | Flux/Anime SDXL | LoRA via endpoints | 10-40s |
| **Leonardo.ai** | 150 tokens/day ✅ | $10+/mo | Anime-specific | Character ref imgs ✅ | 10-30s |
| **Stability AI** | 25 credits (~125 imgs) | $0.002/img | SDXL anime | IP-Adapter via custom | 15-45s |
| **Replicate** | Pay-per-use | $0.01-0.05 | Animagine XL 3.1 ✅ | LoRA support | 10-30s |
| **Fal.ai** | Credits on signup | $0.01-0.03 | Kokoro (Japanese) | Photomaker for faces | 5-20s |
| **Novita.ai** | Trial credits | $0.01-0.05 | SDXL anime | LoRA | 20-40s |
| **Together.ai** | Min $5 prepay | $0.02-0.10 | Flux variants | Limited | 20-60s |
| **RunPod** | No free | $0.0002/hr | Any HF model | Full LoRA/IP-Adapter | Setup time |

---

## 🎯 Best Options for Our Project

### Tier 1: Character References (High Quality)
1. **Gemini Imagen** (user has access!) - Use for main character refs
2. **Leonardo.ai** - 150 tokens/day, strong character ref support
3. **Replicate Animagine XL 3.1** - Best anime quality

### Tier 2: Bulk Panel Generation (Free/Unlimited)
1. **Google Colab T4** - 30-90s/image, free, our primary approach
2. **Hugging Face Inference** - 300 req/hr backup

---

## 🧩 Character Consistency Methods

| Method | Where Available | Quality | Complexity |
|--------|-----------------|---------|------------|
| **IP-Adapter** | Colab (local), RunPod | ⭐⭐⭐⭐⭐ | Medium |
| **LoRA Training** | Replicate, HuggingFace | ⭐⭐⭐⭐⭐ | High |
| **Reference Images** | Leonardo.ai, Fal.ai | ⭐⭐⭐⭐ | Low |
| **Face Preservation** | Fal.ai Photomaker | ⭐⭐⭐⭐ | Low |

---

## 🔬 AniFusion/MAGI Insights

From research:
- Use **LoRA** for panel consistency
- **SDXL lineart models** for B/W manga
- **ComfyUI workflows** with IP-Adapter
- **ControlNet** for layouts

---

## 💡 Our Implementation Plan

### Phase 1: MVP on Colab (Now)
```
Story Prompt → Gemini → Scene JSON → SDXL on Colab → Manga Page
```

### Phase 2: Character Reference Enhancement
```
Character Description → Gemini Imagen OR Leonardo.ai → High-quality ref
→ IP-Adapter on Colab → Consistent panels
```

### Phase 3: Advanced (Optional)
```
Train custom LoRA for main characters
Use API for first panel, IP-Adapter for rest
Multi-style support (B/W lineart vs color anime)
```

---

## 📌 Action Items

- [x] Research APIs (Perplexity)
- [ ] Test Colab T4 with SDXL
- [ ] Test IP-Adapter for character consistency
- [ ] Explore Gemini Imagen for character refs
- [ ] Consider Leonardo.ai as backup
