# Phase 1 Tasks

- [x] Task 1: Expose core API via __init__.py
  - What: Add public exports (extract, _fallback_extract) to extraction/__init__.py so the module is importable with a clean API
  - Files: extraction/__init__.py
  - Done when: `from extraction import extract` works and returns a dict with the expected schema keys (title, topic, format, description, components, steps, tips, metadata)

- [x] Task 2: Add CLI argument validation and error handling
  - What: Add input validation (empty text, missing file, invalid format) with clear error messages; ensure graceful exit codes
  - Files: extraction/cli.py
  - Done when: Running with invalid inputs produces stderr messages and non-zero exit codes; running with valid inputs exits 0

- [x] Task 3: Create unit tests for fallback extraction
  - What: Write tests that verify _fallback_extract produces correct output for various inputs (numbered lists, bulleted lists, plain sentences, empty input)
  - Files: tests/test_fallback.py (new)
  - Done when: All fallback tests pass with `python -m pytest tests/` and cover at least 4 input scenarios

- [x] Task 4: Create unit tests for CLI parsing
  - What: Write tests that verify CLI argument parsing works correctly (format choices, output file creation, stdin input simulation)
  - Files: tests/test_cli.py (new)
  - Done when: CLI tests pass with `python -m pytest tests/` and cover format choices, output file writing, and stdin simulation

- [x] Task 5: Create a setup.py or pyproject.toml for installability
  - What: Add a minimal package configuration so the module can be installed and imported
  - Files: pyproject.toml (new)
  - Done when: `pip install -e .` from the workspace root succeeds and `python -c "from extraction import extract"` works