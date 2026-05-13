# Phase 2 Tasks

- [ ] Task 1: Add error handling and input validation to core modules
  - What: Add proper exception types, input validation, and graceful error handling across ingestor, transcriber, translator, and summarizer modules.
  - Files: video_babbel/core.py (add custom exceptions), video_babbel/ingestor.py, video_babbel/transcriber.py, video_babbel/translator.py, video_babbel/summarizer.py
  - Done when: All modules raise descriptive exceptions (e.g., VideoBabbelError, IngestionError, TranscriptionError, TranslationError) on invalid input; empty/None inputs return sensible defaults or raise typed errors; existing code paths still work.

- [ ] Task 2: Write unit tests for core utilities and translator
  - What: Create tests for sanitize_text, get_logger, and the Translator class (mock translation, language lookup, unknown language fallback, backend dispatch).
  - Files: tests/test_core.py, tests/test_translator.py
  - Done when: All tests pass with `pytest tests/ -v`; coverage includes sanitize_text edge cases (None, empty, whitespace-only), get_logger returns configured logger, Translator.translate with known/unknown languages, Translator.translate with unsupported backend raises NotImplementedError.

- [ ] Task 3: Write unit tests for summarizer and QAEngine
  - What: Create tests for Summarizer.summarize (empty input, single sentence, multi-sentence, max_sentences limits) and QAEngine.answer (no transcript, no word overlap, high overlap).
  - Files: tests/test_summarizer.py
  - Done when: All tests pass with `pytest tests/ -v`; coverage includes edge cases (empty string, single sentence, max_sentences=1, max_sentences > sentence count), QAEngine with no overlap returns fallback, QAEngine with high overlap returns matching sentence.

- [ ] Task 4: Write integration tests for the VideoBabbel pipeline with mocked dependencies
  - What: Create tests that exercise VideoBabbel.process() end-to-end using mocked VideoIngestor, Transcriber, Translator, Summarizer, and QAEngine so tests run without real video files or Whisper.
  - Files: tests/test_pipeline.py
  - Done when: All tests pass with `pytest tests/ -v`; tests cover: happy-path full pipeline, FileNotFoundError on missing video, custom target_lang override, all return dict keys present (transcript, translated_transcript, summary, qa), cleanup is called.

- [ ] Task 5: Write README and add a CONTRIBUTING guide
  - What: Create a comprehensive README.md with project overview, installation instructions, usage examples (CLI and Python API), architecture diagram, and a CONTRIBUTING.md with development setup and test running instructions.
  - Files: README.md, CONTRIBUTING.md
  - Done when: README.md includes: project description, install steps (pip install -e .[dev]), quick-start example, full API reference for VideoBabbel, Translator, Summarizer, QAEngine, Transcriber, VideoIngestor, architecture overview, and license; CONTRIBUTING.md includes dev setup, how to run tests, how to add new modules.

- [ ] Task 6: Run full test suite and verify all tests pass
  - What: Execute the complete test suite with verbose output, fix any failures, and confirm the package is importable and all public APIs are documented.
  - Files: tests/ (all test files), pyproject.toml (ensure dev dependencies are correct)
  - Done when: `pytest tests/ -v` passes with zero failures and zero errors; `python -c "import video_babbel; print(video_babbel.__all__)"` prints all expected exports; `pip install -e .[dev]` succeeds.