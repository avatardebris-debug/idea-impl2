# Validation Report — Phase 2
## Summary
- Tests: 62 passed, 22 failed
## Verdict: FAIL

### Detailed Findings

**Test Results by File:**
- `tests/test_core.py`: All tests PASSED (18/18) — sanitize_text, get_logger, exception hierarchy all working correctly.
- `tests/test_translator.py`: FAILED (0/0 shown) — AttributeError on `video_babbel.translator` module for `deepl` and `google` attributes. Mock patching targets are incorrect.
- `tests/test_transcriber.py`: FAILED (0/0 shown) — AttributeError on `video_babbel.transcriber` module for `whisper` attribute. Mock patching targets are incorrect.
- `tests/test_summarizer.py`: FAILED (1/1 shown) — `test_summarize_exception_wrapped` did not raise `SummarizationError` as expected.
- `tests/test_qa.py`: FAILED (5/5 shown) — Keyword matching issues (case sensitivity), empty string returns, and NoneType errors in QAEngine.
- `tests/test_pipeline.py`: FAILED (6/6 shown) — FileNotFoundError on `/fake/video.mp4` instead of mocked VideoIngestor; mock patching targets are incorrect.

**Missing Files:**
- `CONTRIBUTING.md` — Task 5 not completed.

### Root Causes
1. **Mock patching targets are wrong** in `test_pipeline.py`, `test_transcriber.py`, and `test_translator.py` — tests patch `video_babbel.translator.deepl` and `video_babbel.transcriber.whisper` but these modules don't expose those as module-level attributes.
2. **QAEngine keyword matching** is case-sensitive — tests expect 'AI' to match 'ai' in transcripts.
3. **QAEngine edge cases** — empty transcript returns empty string instead of fallback; None transcript causes TypeError.
4. **Summarizer** — `test_summarize_exception_wrapped` expects `SummarizationError` to be raised but the code doesn't raise it.
5. **CONTRIBUTING.md** is missing entirely.
