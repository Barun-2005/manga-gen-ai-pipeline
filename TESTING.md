# Testing Checklist for MangaGen

> Systematic testing before local model integration

## ✅ Unit Testing (Scripts)

### Story Director
- [ ] `test_story_director.py`
  - [ ] Plan chapter with different page counts (1, 3, 5 pages)
  - [ ] Validate JSON schema output
  - [ ] Test character DNA extraction
  - [ ] Verify cinematography parameters

### Image Generation
- [ ] `test_image_generation.py`
  - [ ] Pollinations API (no key)
  - [ ] NVIDIA FLUX (with key, if available)
  - [ ] Negative prompts applied
  - [ ] Character DNA injected correctly

### Dialogue System
- [ ] `test_dialogue.py`
  - [ ] Dialogue extracted to JSON
  - [ ] No dialogue baked into panels
  - [ ] JSON structure correct

### Panel Regeneration
- [ ] `test_regeneration.py`
  - [ ] Regenerate with same prompt
  - [ ] Regenerate with custom prompt
  - [ ] Character DNA preserved
  - [ ] Dialogue unchanged

---

## 🌐 Integration Testing (API)

### Generation Flow
- [ ] End-to-end generation (1 page, 2x2)
- [ ] Multi-page generation (3 pages, 2x3)
- [ ] Different styles (B/W vs color)
- [ ] Character consistency across panels
- [ ] PDF output quality (300 DPI check)

### Panel Regeneration Endpoint
- [ ] `/api/regenerate/{job_id}` - successful regen
- [ ] Invalid job ID returns 404
- [ ] Invalid panel index returns 400
- [ ] Prompt override works
- [ ] Image updated correctly

### Error Handling
- [ ] Missing API key (graceful fallback)
- [ ] Rate limit triggered (429 error)
- [ ] Invalid request (validation errors)
- [ ] Server errors logged properly

---

## 🎨 Frontend Testing

### Canvas Editor
- [ ] Add dialogue bubble
- [ ] Drag bubble
- [ ] Resize bubble (if implemented)
- [ ] Delete bubble
- [ ] Change bubble style
- [ ] Font size controls
- [ ] Text sync (sidebar ↔ canvas)

### Panel Regeneration UI
- [ ] Select panel
- [ ] Edit prompt
- [ ] Click regenerate
- [ ] New image loads
- [ ] Dialogue preserved

### Export
- [ ] Download PDF
- [ ] Download PNG
- [ ] Download ZIP (if implemented)

---

## 🔧 Performance Testing

### Load Testing
- [ ] 5 concurrent users
- [ ] 10 concurrent users
- [ ] Rate limiting activates correctly
- [ ] No memory leaks
- [ ] CPU usage acceptable

### Caching
- [ ] LLM responses cached
- [ ] Cache hit rate > 50% for repeated prompts
- [ ] Expired cache cleaned up

### Image Optimization
- [ ] PNG files optimized
- [ ] Thumbnails generated
- [ ] File sizes reasonable

---

## 🛡️ Security Testing

### API Security
- [ ] Rate limit enforced
- [ ] Request size limit enforced (10MB)
- [ ] Invalid inputs rejected
- [ ] No API key exposure in responses

### Environment
- [ ] `.env` not in Git
- [ ] Placeholder detection works
- [ ] Required vars validated

---

## 📊 Monitoring

### Health Endpoint
- [ ] `/health` returns status
- [ ] CPU/memory metrics accurate
- [ ] Uptime tracking works
- [ ] Request counters increment

### Logging
- [ ] Logs written to file
- [ ] Colored terminal output
- [ ] Error logs detailed
- [ ] Log rotation works (daily)

---

## 🐛 Bug Fixes Needed

_Document any bugs found during testing here_

| Bug ID | Description | Severity | Status |
|--------|-------------|----------|--------|
| | | | |

---

## ✅ Sign-Off

- [ ] All critical tests pass
- [ ] Performance acceptable
- [ ] Security validated
- [ ] Documentation complete
- [ ] **Ready for local model integration**

---

_Once all tests pass, proceed to local model integration phase_
