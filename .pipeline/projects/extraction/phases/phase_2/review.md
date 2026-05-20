# Code Review — Phase 2

## Verdict
PASS

## Blocking Bugs
None

## Non-Blocking Notes
- `test_cli.py` uses `subprocess` to invoke the CLI — consider adding a direct `argparse` parsing test for faster feedback.
- `test_extract.py` mocks `_call_ollama` — ensure the mock covers timeout and connection-refused scenarios in a future iteration.
- `test_fallback.py` tests rule-based extraction well but could add coverage for edge cases like single-line input and very long inputs.
- `README.md` is comprehensive but could include a quick-start section for first-time users.

## Summary
- Tests: 74 passed, 0 failed
- README.md: PRESENT — covers Overview, Installation, CLI Usage, Python API Usage, Output Schema, Development/Testing
- test_json_parsing.py: PRESENT — covers valid JSON object, valid JSON array, no braces, partial/malformed JSON, extra text before/after, nested JSON
- test_extract.py: PRESENT — covers successful LLM response, empty LLM response (triggers fallback), malformed JSON (triggers fallback), missing 'steps' key (triggers fallback), empty input (triggers fallback), schema normalisation, format hints, model parameter passthrough
- test_fallback.py: PRESENT — covers numbered lists, bulleted lists, plain sentences, empty input
- test_cli.py: PRESENT — covers format choices, output file writing, stdin input, error handling, pretty print
- All Phase 1 tests still pass — no regressions
