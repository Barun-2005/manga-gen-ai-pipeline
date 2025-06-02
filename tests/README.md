# MangaGen Tests

This folder contains test cases and sample data for the MangaGen pipeline.

## Test Files

- `test_pipeline.py` - Core pipeline functionality tests
- `sample_prompts.txt` - Sample prompts for testing generation
- `test_outputs/` - Test output directory (auto-created)

## Running Tests

```bash
# Run all tests
python tests/test_pipeline.py

# Test individual components
python -c "from tests.test_pipeline import test_emotion_extraction; test_emotion_extraction()"
```

## Test Coverage

- ✅ Emotion extraction functionality
- ✅ Output manager operations
- ✅ Prompt processing and naming
- ✅ Configuration loading
- ⚠️  Panel generation (requires ComfyUI)
- ⚠️  Full pipeline integration (requires ComfyUI)

## Notes

- Tests that require ComfyUI will be skipped if ComfyUI is not running
- Test outputs are saved to `tests/test_outputs/` and can be safely deleted
- These tests are designed to be lightweight and fast
- **DO NOT DELETE THIS FOLDER** - It's protected from cleanup operations

## Adding New Tests

When adding new functionality, please add corresponding tests:

1. Add test function to `test_pipeline.py`
2. Update the `run_all_tests()` function
3. Add any required sample data files
4. Update this README with test coverage information
