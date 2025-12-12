# MangaGen Repository Audit

**Date**: 2025-12-12  
**Auditor**: AI Assistant  
**Purpose**: Salvage useful components and prepare for MVP branch `mvp/kaggle-flux`

---

## Executive Summary

This repository contains a sophisticated but incomplete AI manga generation system. The codebase shows evidence of ~18 development phases targeting a contest deadline. Key findings:

- **LLM Integration**: Uses OpenRouter/DeepSeek (needs rewrite for Gemini)
- **Image Generation**: ComfyUI-based with SD1.5 models (can adapt for Flux/Kaggle)
- **Dialogue System**: Mature bubble placement with face detection (highly reusable)
- **PDF Compilation**: Working ReportLab-based compiler (reusable)
- **Testing**: Scattered test files, no structured test suite

---

## Directory Structure Analysis

### Root Level Files

| File | Size | Decision | Reason |
|------|------|----------|--------|
| `README.md` | 11KB | REWRITE | Outdated structure, needs MVP-specific docs |
| `README_PHASE18.md` | 9KB | ARCHIVE | Historical phase documentation |
| `PHASE18_SUMMARY.md` | 8KB | ARCHIVE | Phase-specific status |
| `SYSTEM_STATUS.md` | 6KB | ARCHIVE | Development status tracking |
| `requirements.txt` | 1.4KB | REWRITE | Bloated, needs minimal Kaggle deps |
| `.env.example` | 2KB | REWRITE | Add GEMINI_API_KEY, remove OpenRouter |
| `.gitignore` | 1KB | REUSE | Standard Python/model ignores |
| `phase17b_hotfix_report.md` | 522B | DISCARD | Obsolete hotfix notes |

### Root Level Scripts (Test/Debug)

| File | Size | Decision | Reason |
|------|------|----------|--------|
| `direct_test.py` | 5KB | DISCARD | One-off test |
| `execute_phase18_test.py` | 7KB | ARCHIVE | Phase-specific |
| `execute_test.py` | 5KB | ARCHIVE | Generic test runner |
| `final_test.py` | 5KB | ARCHIVE | Phase test |
| `inline_test.py` | 4KB | DISCARD | Debug script |
| `phase18_status.py` | 6KB | ARCHIVE | Status checker |
| `quick_test.py` | 3KB | DISCARD | Quick debug |
| `run_phase18_test.py` | 8KB | ARCHIVE | Phase test |
| `run_setup.py` | 4KB | ARCHIVE | Setup helper |
| `run_test.py` | 688B | DISCARD | Minimal test |
| `setup_dirs.py` | 1KB | REUSE | Directory setup utility |
| `simple_config_test.py` | 2KB | DISCARD | Config debug |
| `step_by_step_test.py` | 5KB | ARCHIVE | Debug walkthrough |
| `test_*.py` (6 files) | Various | DISCARD | Scattered tests |
| `verify_*.py` (2 files) | Various | ARCHIVE | Verification scripts |
| `yaml_test_inline.py` | 3KB | DISCARD | YAML debug |

---

## Core Modules (`core/`)

| File | Lines | Decision | Reason |
|------|-------|----------|--------|
| `__init__.py` | 202 | REUSE | Module exports |
| `dialogue_placer.py` | 1,244 | **REUSE** | Excellent bubble placement with face detection, tone analysis, overlap prevention |
| `config_manager.py` | 400+ | REUSE | YAML config loading |
| `panel_generator.py` | 414 | REWRITE | ComfyUI-specific, needs Flux/Diffusers adaptation |
| `scene_generator.py` | 400+ | REWRITE | Needs Gemini integration |
| `scene_validator.py` | 500+ | REWRITE | Replace with Pydantic schema |
| `emotion_extractor.py` | 400+ | ARCHIVE | Over-engineered for MVP |
| `emotion_matcher.py` | 500+ | ARCHIVE | Over-engineered for MVP |
| `pose_matcher.py` | 600+ | ARCHIVE | Over-engineered for MVP |
| `story_memory.py` | 500+ | ARCHIVE | Complex state management |
| `coherence_analyzer.py` | 800+ | ARCHIVE | Advanced validation |
| `local_flow_checker.py` | 500+ | ARCHIVE | Flow validation |
| `output_manager.py` | 600+ | REUSE | File organization logic |

### Salvage Highlights from `core/`
1. **`dialogue_placer.py`** - Production-ready bubble placement:
   - Face detection using OpenCV Haar cascades
   - Tone detection for bubble shape selection
   - Force-directed layout optimization
   - Reading order arrangement
   - PIL text rendering with wrapping

---

## LLM Module (`llm/`)

| File | Lines | Decision | Reason |
|------|-------|----------|--------|
| `__init__.py` | 20 | REUSE | Exports |
| `story_generator.py` | 216 | **REWRITE** | Uses OpenRouter API, need Gemini version |
| `prompt_templates.py` | 270 | **REUSE** | Excellent act/scene/dialogue templates |

### `prompt_templates.py` Salvage Details
- `ACT_TEMPLATES`: 3-act story structure prompts
- `SCENE_TEMPLATES`: Action, dialogue, establishing scene templates
- `DIALOGUE_TEMPLATES`: Character-type emotional dialogue patterns
- `GENRE_MODIFIERS`: Shonen, seinen, slice-of-life, fantasy style guides

---

## Image Generation (`image_gen/`)

| File | Lines | Decision | Reason |
|------|-------|----------|--------|
| `__init__.py` | 100+ | REUSE | Exports |
| `comfy_client.py` | 500+ | ARCHIVE | ComfyUI HTTP client, Kaggle won't use this |
| `image_generator.py` | 540 | REWRITE | Has good validation logic, needs Diffusers/Flux |
| `prompt_builder.py` | 600+ | **REUSE** | Prompt enhancement with quality tags |

### `prompt_builder.py` Salvage Details
- Character-focused prompt construction
- Style tag injection (manga, anime, B&W)
- Quality enhancer prefixes
- Negative prompt combination

---

## Scripts (`scripts/`)

| File | Lines | Decision | Reason |
|------|-------|----------|--------|
| `compile_pdf.py` | 416 | **REUSE** | ReportLab PDF with 2×2 grid layout |
| `generate_scene.py` | 350+ | REWRITE | Scene JSON generation |
| `generate_panel.py` | 300+ | REWRITE | Panel image generation |
| `run_full_pipeline.py` | 800+ | REFERENCE | Pipeline orchestration patterns |
| `run_dialogue_pipeline.py` | 600+ | REFERENCE | Dialogue integration patterns |
| `demo_phase15.py` | 400+ | ARCHIVE | Phase demo |
| `demo_dialogue_system.py` | 400+ | ARCHIVE | Dialogue demo |
| `test_*.py` (8 files) | Various | ARCHIVE | Phase-specific tests |
| `setup_models.py` | 400+ | ARCHIVE | Model download helper |
| `sanity_test.py` | 600+ | ARCHIVE | Validation tests |

### `compile_pdf.py` Salvage Details
- `collect_panel_images()` - Gathers panels from directories
- `create_manga_page()` - 2×2 grid composition with PIL
- `compile_manga_pdf_reportlab()` - PDF generation with title pages
- `compile_panels_to_pdf()` - Direct panel list → PDF

---

## Pipeline Modules (`pipeline/`, `pipeline_v2/`)

### `pipeline/`
| File | Decision | Reason |
|------|----------|--------|
| `__init__.py` | ARCHIVE | Old exports |
| `generate_manga.py` | REFERENCE | Orchestration patterns |
| `manga_automation.py` | ARCHIVE | ComfyUI automation |
| `utils.py` | **REUSE** | Face detection, blur detection, pose keypoints |
| `automation_stubs.py` | ARCHIVE | Stub implementations |

### `pipeline_v2/`
| File | Decision | Reason |
|------|----------|--------|
| All files | ARCHIVE | Experimental v2 pipeline |

### `pipeline/utils.py` Salvage Details
- `detect_faces()` - OpenCV Haar cascade face detection
- `detect_blur()` - Laplacian variance blur detection
- `detect_pose_keypoints()` - MediaPipe pose detection
- `clean_visual_prompt()` - Prompt sanitization

---

## Asset Files

### `assets/prompts/`
| File | Size | Decision |
|------|------|----------|
| `base_prompts.txt` | 2KB | **REUSE** - Quality manga prompt examples |
| `enhanced_prompts.txt` | 4KB | **REUSE** - Enhanced prompt patterns |
| `scene_prompts.txt` | 368B | **REUSE** - Scene-specific prompts |

### `assets/negatives/`
| File | Size | Decision |
|------|------|----------|
| `bad_hand_v4.txt` | 219B | **REUSE** - Bad hands negative prompt |
| `easy_negative.txt` | 221B | **REUSE** - General negative prompt |

### `assets/workflows/`
| File | Decision | Reason |
|------|----------|--------|
| `manga_graph.json` | ARCHIVE | ComfyUI txt2img workflow |
| `bw_manga_workflow.json` | ARCHIVE | B&W ComfyUI workflow |
| `color_manga_workflow.json` | ARCHIVE | Color ComfyUI workflow |
| `controlnet_workflow.json` | REFERENCE | ControlNet node structure |
| `adapter_workflow.json` | REFERENCE | T2I adapter structure |
| `improved_manga_workflow.json` | ARCHIVE | Enhanced workflow |
| `scene_reference_workflow.json` | ARCHIVE | Reference-based workflow |

---

## Configuration Files (`config/`)

| File | Decision | Reason |
|------|----------|--------|
| `settings.yaml` | **REUSE** | Comprehensive config structure |
| `llm_provider_config.json` | REWRITE | Add Gemini provider |
| `output_config.json` | REUSE | Output directory settings |
| `pipeline_config.json` | REUSE | Pipeline parameters |

### `settings.yaml` Salvage Details
- ComfyUI server configuration
- Model paths (checkpoints, VAE, ControlNet, LoRA, IP-Adapter)
- Workflow templates mapping
- Generation settings (dimensions, sampling, quality)
- Prompt configuration (styles, quality enhancers)
- Color mode configuration
- Output directory structure
- Validation settings
- Performance tuning

---

## Production Module (`production/`)

| File | Decision | Reason |
|------|----------|--------|
| `complete_manga_generator.py` | REFERENCE | Full pipeline integration |
| `web_interface.py` | ARCHIVE | Flask web UI |
| `templates/` | ARCHIVE | Web UI templates |
| `test_*.py` (5 files) | ARCHIVE | Production tests |
| `*.png` (8 files) | ARCHIVE | Test outputs |

---

## Tests (`tests/`)

| File | Decision | Reason |
|------|----------|--------|
| `README.md` | REUSE | Test documentation |
| `sample_prompts.txt` | **REUSE** | Example prompts for testing |
| `test_pipeline.py` | ARCHIVE | Pipeline integration tests |
| `test_phase17_integration.py` | ARCHIVE | Phase-specific tests |
| `test_emotion_matching.py` | ARCHIVE | Emotion validation tests |
| `test_pose_matching.py` | ARCHIVE | Pose validation tests |
| `gold_panels/`, `gold_panels_v2/` | REFERENCE | Golden test images |
| `test_outputs/` | DISCARD | Generated test outputs |

---

## External Dependencies (`ComfyUI-master/`)

| Decision | Reason |
|----------|--------|
| ARCHIVE | Full ComfyUI installation (393 files). Kaggle will use Diffusers/Flux directly. Keep as reference but not in MVP branch. |

---

## Salvage Actions

### Immediate Actions (Before MVP Branch)
1. ✅ Create this `archive/repo_audit.md`
2. [ ] Move legacy files to `archive/legacy/`:
   - All `phase*.py` files from root
   - All `test_*.py` from root (except those in `tests/`)
   - `contest_package/` entire directory
   - `PHASE18_SUMMARY.md`, `README_PHASE18.md`, `SYSTEM_STATUS.md`
   - `debug/` directory contents
   - `pipeline_v2/` directory

3. [ ] Create `archive/prompt_templates.txt` with consolidated prompts from:
   - `assets/prompts/base_prompts.txt`
   - `assets/prompts/enhanced_prompts.txt`
   - `llm/prompt_templates.py` (as Python reference)

4. [ ] Commit archive state and tag `archive/pre-mvp-YYYYMMDD`

### Files to Copy to MVP
1. **Core Reusables**:
   - `core/dialogue_placer.py` (bubble placement)
   - `scripts/compile_pdf.py` (PDF generation)
   - `pipeline/utils.py` (face/blur detection)
   - `llm/prompt_templates.py` (story templates)
   - `image_gen/prompt_builder.py` (prompt enhancement)

2. **Asset Files**:
   - `assets/prompts/` (all .txt files)
   - `assets/negatives/` (negative prompts)
   - `config/settings.yaml` (config structure)

3. **Test Resources**:
   - `tests/sample_prompts.txt`
   - `tests/README.md`

---

## CHECKPOINTS (Agent Must Fill)

- [ ] `archive/repo_audit.md` created and committed at `<commit-sha>`
- [ ] List of files moved to `/archive/legacy/`:
  - (to be filled after move)
- [ ] List of files reused in new pipeline:
  - (to be filled during MVP implementation)
- [ ] Any pre-existing prompts saved to `/archive/prompt_templates.txt`
- [ ] Tag created: `archive/pre-mvp-YYYYMMDD`

---

## Technical Debt Notes

1. **No Structured Testing**: Tests are scattered as individual scripts, not pytest suite
2. **OpenRouter Lock-in**: Story generation tightly coupled to OpenRouter API
3. **ComfyUI Dependency**: Image generation requires local ComfyUI server
4. **Over-engineered Validation**: Emotion/pose matching adds complexity without clear value for MVP
5. **Missing JSON Schema**: Scene plan output has no formal validation

## Recommendations for MVP

1. **Simplify LLM**: Direct Gemini API call with strict JSON output
2. **Simplify Image Gen**: Use Diffusers directly with Flux-dev or SD1.5
3. **Keep Bubble Placement**: `dialogue_placer.py` is production-ready
4. **Keep PDF Compilation**: `compile_pdf.py` works well
5. **Add Pydantic Validation**: Replace ad-hoc scene validation with schema
6. **Kaggle-First Design**: All heavy compute in notebook, local is thin wrapper
