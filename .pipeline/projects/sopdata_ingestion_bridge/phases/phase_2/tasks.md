# Phase 2 Tasks

- [ ] Task 1: Create test suite structure and CSV ingestion tests
  - What: Create a `tests/` directory with `__init__.py` and `test_ingest.py`. Write tests for the `read_csv` and `read_csv_from_string` functions in `ingest.py`. Cover happy path (valid CSV), empty file, missing file, no headers, and custom encoding.
  - Files: tests/__init__.py, tests/test_ingest.py
  - Done when: All ingest tests pass with `pytest tests/test_ingest.py`. Tests cover: valid CSV returns correct rows, FileNotFoundError raised for missing files, ValueError raised for empty CSV, ValueError raised for CSV with no headers, read_csv_from_string works with raw CSV text.

- [ ] Task 2: Create transformation and model tests
  - What: Create `tests/test_transform.py` and `tests/test_models.py`. Write tests for `SOPInputRow.from_dict()`, `SOPInputRow.to_dict()`, and the `transform()` function. Cover default mapping, custom mapping, missing columns, and empty input.
  - Files: tests/test_transform.py, tests/test_models.py
  - Done when: All model and transform tests pass with `pytest tests/test_transform.py tests/test_models.py`. Tests cover: default mapping correctly maps aliases, custom mapping overrides defaults, missing CSV columns produce empty strings, transform returns list of SOPInputRow instances, to_dict round-trips correctly.

- [ ] Task 3: Create bridge API integration tests
  - What: Create `tests/test_bridge.py`. Write integration tests for the `SOPBridge.ingest()` method and the convenience `ingest()` function. Test end-to-end flow with `sample_data.csv`, custom mappings, and error propagation.
  - Files: tests/test_bridge.py
  - Done when: All bridge tests pass with `pytest tests/test_bridge.py`. Tests cover: SOPBridge.ingest returns SOPInputRow list for valid CSV, custom mapping is respected end-to-end, FileNotFoundError and ValueError propagate correctly, convenience ingest() function works identically to SOPBridge().ingest().

- [ ] Task 4: Add error handling and edge case coverage
  - What: Add tests for edge cases across all modules: CSV with blank rows, CSV with extra columns, CSV with fewer columns than headers, CSV with special characters, and empty mapping dict. Also add tests for `core.py` utilities (`get_default_mapping`, `merge_mappings`).
  - Files: tests/test_edge_cases.py, tests/test_core.py
  - Done when: All edge case and core utility tests pass. Tests cover: blank rows are skipped, extra columns are ignored, fewer columns produce empty strings for missing values, special characters preserved, get_default_mapping returns a copy (not shared reference), merge_mappings correctly merges custom over default.

- [ ] Task 5: Write README and verify full test suite
  - What: Create a comprehensive `README.md` in the workspace root with project overview, installation instructions, usage examples (code snippets), API reference summary, and development setup notes. Then run the full test suite to confirm everything passes.
  - Files: README.md
  - Done when: README.md exists with sections for overview, installation, quick start, API reference, and development. Running `pytest` from the workspace root passes all tests with no errors or warnings.