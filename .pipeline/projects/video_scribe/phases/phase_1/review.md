# Code Review — Phase 1

## Blocking Bugs
None

## Non-Blocking Notes
- `config.py` defines `get_base_url` and `get_model` functions that are not imported or used by any other module. These could be cleaned up or used by `vlm_analyzer.py` for future extensibility.
- `vlm_analyzer.py` does not use `get_base_url` or `get_model` from config — it hardcodes the model name `"gpt-4o"` and `"claude-sonnet-4-20250514"` instead of calling `config.get_model()`. This is not a bug but a missed opportunity for consistency.
- `test_cli_with_mock_vlm` does not actually invoke the CLI subprocess — it manually calls `extract_key_frame` and `format_as_markdown` and writes the file directly. This means the CLI integration is not fully tested end-to-end. Consider adding a test that invokes `video_scribe.py` as a subprocess with a mock VLM.

## Verdict
PASS — All Phase 1 tasks are complete. The code is functional, well-structured, and all 4 smoke tests pass.
