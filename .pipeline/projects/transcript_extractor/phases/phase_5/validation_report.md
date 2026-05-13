# Validation Report — Phase 5
## Summary
- Tests: 254 passed, 54 failed, 4 errors
## Verdict: FAIL

## Details

### Test Results
- **Total tests run:** 312
- **Passed:** 254
- **Failed:** 54
- **Errors:** 4

### Failure Categories

1. **FileNotFoundError (missing test fixtures):** Multiple tests in `test_audio_extractor.py`, `test_pipeline.py` fail because they reference input files (e.g., `test.mp4`, `test.wav`) that do not exist in the workspace.

2. **TypeError (API mismatches):** Tests in `test_formatter.py` and `test_transcript_extractor.py` fail because:
   - `TranscriptFormatter.format_to_json()` does not accept an `indent` keyword argument
   - `TranscriptionSegment.__init__()` requires a `language` positional argument that callers don't provide

3. **AttributeError (missing attributes/methods):** Tests in `test_parser.py` and `test_transcript_extractor.py` fail because:
   - `'dict' object has no attribute 'start'` — parser returns dicts instead of objects with `start`/`end` attributes
   - `TranscriptionSegment` objects lack `duration`, `to_dict`, `to_json` attributes
   - `TranscriptionResultData` objects lack `to_dict`, `to_json` attributes
   - Video handler classes (AVIHandler, MKVHandler, MOVHandler, MP4Handler) lack `extract_audio` method

4. **AssertionError (incorrect output):** Tests in `test_parser.py`, `test_formatter.py`, `test_transcript_extractor.py` fail because:
   - TXT output format does not contain expected `'Test transcript'` text
   - VTT output format has wrong timestamp separator (`.000` vs `,000`)
   - Summary generation returns wrong keys (e.g., missing `'length'`)
   - Pipeline mock expectations not met (e.g., `format` called 0 times instead of 1)

5. **RuntimeError (ffmpeg failures):** Audio extraction tests fail due to ffmpeg conversion errors.

### Root Causes
- The core code has API incompatibilities between the implementation and what tests expect
- Missing test fixture files (test.mp4, test.wav)
- Incorrect output formatting in parser/formatter components
- Missing methods/attributes on model classes (TranscriptionSegment, TranscriptionResultData)
- Video handler classes missing required methods
