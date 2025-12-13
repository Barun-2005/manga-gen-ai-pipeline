# 🔍 Image Generation API Research Prompt

Use this prompt with **Perplexity AI** or **Comet** to research the best options for our project.

---

## The Prompt (Copy This):

```
I'm building an AI manga/comic generation pipeline and need to research image generation APIs. Please help me find and compare options with the following requirements:

**Core Requirements:**
1. Must support anime/manga art style (NOT photorealistic)
2. Need both black & white manga style AND color anime style
3. Must have a free tier or credits for development/testing
4. Ideally supports character consistency (reference images, similar to IP-Adapter)

**Research Questions:**

**1. API Comparison Table**
Create a comparison table of these APIs (and any others you find relevant):
- Replicate (has anime models like Animagine)
- Together.ai
- Stability AI API
- Fal.ai
- Novita.ai
- Leonardo.ai
- RunPod
- Hugging Face Inference API

For each, tell me:
- Free tier limits (images per month, credits)
- Cost per image after free tier
- Available anime/manga models
- Image resolution supported
- Character reference / consistency features
- API latency (average time per image)

**2. Anime-Specific Models**
Which of these APIs offer these specific models or similar:
- Animagine XL 3.1
- Anything V5
- Blue Pencil XL
- Holodayo XL
- NovelAI (if available via API)
- AnimeFull / AnimeLineart models

**3. Character Consistency**
Which APIs support maintaining character consistency across multiple images?
- IP-Adapter style reference images
- Face swapping/preservation
- LoRA/character embeddings
- Any other methods

**4. Best Free Options**
Rank the top 3 APIs for my use case considering:
- I need to generate ~100-500 images for development/testing
- I need anime style output
- I want character consistency if possible
- I prefer pay-as-you-go over subscriptions

**5. Local vs API Trade-offs**
Compare running SDXL locally on Google Colab (free T4 GPU) vs using an API:
- Speed comparison
- Quality comparison
- Character consistency comparison
- Hassle/complexity comparison

**6. AniFusion Research**
Research how similar manga generation projects (like AniFusion, MAGI by Microsoft, etc.) handle:
- Character consistency across panels
- Different art styles (B/W manga vs color)
- Panel layout and composition
- Any public information about their tech stack
```

---

## What to Look For in the Response:

### Best API for Our Needs:
- [ ] Has anime models (not just SDXL base)
- [ ] Free tier: At least 50-100 images free
- [ ] Supports image-to-image or reference images
- [ ] Reasonable speed (<30 sec per image)

### Red Flags:
- ❌ Only photorealistic models
- ❌ Very low resolution (< 512px)
- ❌ No anime-specific models
- ❌ Expensive (> $0.05 per image)

---

## Quick Summary of What I Know:

| API | Free Tier | Anime Models | Notes |
|-----|-----------|--------------|-------|
| Replicate | $5 credit (~50-100 images) | Yes (Animagine, etc.) | Good option |
| Together.ai | $5 credit | Limited anime | More for LLMs |
| Fal.ai | Some free | Yes | Fast, good for anime |
| HuggingFace | Limited free | Yes | Can run custom models |
| Stability | $25 for 1000 | Limited | Official SDXL API |

---

## After Research, We'll Decide:

1. **Primary approach**: Local SDXL on Colab (free, full control)
2. **Backup API**: [TBD based on research] for when Colab is slow/limited
3. **Character consistency**: IP-Adapter locally or API equivalent
