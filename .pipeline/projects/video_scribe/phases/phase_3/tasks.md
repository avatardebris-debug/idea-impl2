# Phase 3 Tasks

- [x] Task 1: Caching Engine
  - What: Build `cache.py` to hash PIL images and store/retrieve VLM JSON responses via SQLite.
  - Files:
    - `video_scribe/cache.py`
    - `video_scribe/vlm_analyzer.py` (integrate cache)

- [x] Task 2: Advanced Export Formats (Fountain & HTML)
  - What: Extend `output_formatter.py` to support Fountain screenplay syntax and basic HTML rendering.
  - Files:
    - `video_scribe/output_formatter.py`
    - `video_scribe/cli.py` (add `--format fountain/html`)

- [x] Task 3: Local Model Fallback Architecture
  - What: Refactor `vlm_analyzer.py` to use a `VLMProvider` base class. Implement `OpenAIProvider` and `OllamaProvider`.
  - Files:
    - `video_scribe/vlm_analyzer.py`
    - `video_scribe/cli.py` (add `--provider` flag)

- [x] Task 4: Tests & Polish
  - What: Add tests for the caching layer and new export formats.
  - Files:
    - `tests/test_cache.py`
    - `tests/test_pipeline.py`
