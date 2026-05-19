# Phase 2 Tasks

- [x] Task 1: Create README.md with installation, usage, and API documentation
  - What: Write a comprehensive README.md in the workspace root covering project overview, installation, CLI usage examples, Python API usage, output schema, and development notes
  - Files: Create `workspace/README.md`
  - Done when: README.md exists with sections for Overview, Installation, CLI Usage (with examples for all three formats), Python API Usage, Output Schema, and Development/Testing; includes a note about Ollama dependency

- [x] Task 2: Add tests for `_parse_json_from_response` edge cases
  - What: Create `tests/test_json_parsing.py` with unit tests for the JSON extraction helper covering: valid JSON object, valid JSON array, no braces (returns empty dict), partial/malformed JSON, JSON with extra text before/after, nested JSON
  - Files: Create `workspace/tests/test_json_parsing.py`
  - Done when: All edge-case scenarios pass — valid JSON parsed correctly, invalid/missing JSON returns `{}`, partial JSON handled gracefully, nested structures preserved

- [ ] Task 3: Add tests for `extract()` with mocked Ollama responses
  - What: Create `tests/test_extract.py` with tests for the LLM extraction path using `unittest.mock.patch` to mock `_call_ollama`. Cover: successful LLM response with valid JSON, LLM returning empty string (triggers fallback), LLM returning malformed JSON (triggers fallback), topic passthrough, format passthrough, step number normalization, default value filling
  - Files: Create `workspace/tests/test_extract.py`
  - Done when: All 6+ test cases pass — valid LLM response produces correct schema, empty/malformed LLM response triggers fallback, all required keys present in output, step numbers start at 1, defaults applied correctly

- [ ] Task 4: Add error handling for edge cases and integration tests
  - What: Add error handling improvements and integration tests: (a) In `extractor.py`, add handling for when `_call_ollama` raises specific exceptions (timeout, connection refused); (b) In `tests/test_integration.py`, add end-to-end tests that verify CLI + extraction pipeline works together with mocked LLM, and test the `--no-llm` full pipeline path
  - Files: Modify `workspace/extraction/extractor.py` (add try/except around `_call_ollama` calls), Create `workspace/tests/test_integration.py`
  - Done when: `extractor.py` gracefully falls back when Ollama raises exceptions; integration tests verify end-to-end flow with mocked LLM and with `--no-llm` flag; all tests pass

- [ ] Task 5: Run full test suite and verify all tests pass
  - What: Install dev dependencies, run `pytest` on the full test suite, fix any failures, and verify test coverage is adequate (core functions tested, edge cases covered)
  - Files: Run `pytest` from workspace root; update any failing tests or code as needed
  - Done when: `pytest` runs with 0 failures, all Phase 2 tests execute, existing Phase 1 tests still pass, no regressions introduced