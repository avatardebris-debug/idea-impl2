# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and package structure
  - What: Create the Python package layout with pyproject.toml, package directory, CLI entry point, and core module stubs. The package is named `json_schema_profiler` with a top-level `cli.py` (typer app) and `inference.py` (schema inference engine).
  - Files: `pyproject.toml`, `src/json_schema_profiler/__init__.py`, `src/json_schema_profiler/cli.py`, `src/json_schema_profiler/inference.py`, `tests/__init__.py`
  - Done when: `pip install -e .` succeeds, `json-schema-profiler --help` prints usage with an `infer` subcommand, and the package imports cleanly with no runtime errors.

- [ ] Task 2: Core schema inference engine
  - What: Implement `infer_schema(data)` in `inference.py` that accepts a Python object (dict or list of dicts) and returns a JSON Schema draft-07 dict. Must handle: (a) type detection per field — string, integer, number, boolean, null; (b) recursive inference for nested dicts; (c) array-of-objects infers `items` schema; (d) per-field metadata — `required` fields (present in all objects), `min`/`max` for numeric types, `minLength`/`maxLength` for strings, `enum` candidates for low-cardinality strings (≤10 unique values); (e) handles mixed types by reporting `["string", "number"]` etc.
  - Files: `src/json_schema_profiler/inference.py`
  - Done when: Unit tests pass for simple objects, nested objects, arrays of objects, mixed types, and empty arrays (see Task 4). The function returns a dict conforming to JSON Schema draft-07 structure with `type: "object"`, `properties`, `required`, and per-field constraints.

- [ ] Task 3: CLI implementation with output options
  - What: Wire the typer CLI in `cli.py` so `json-schema-profiler infer <input.json>` loads a JSON file (single object or array of objects), calls the inference engine, and writes the resulting JSON Schema to stdout. Add `--output <file>` flag to write to a file instead of stdout. Add `--format jsonschema` (current and only format for Phase 1). Exit code 0 on success, non-zero on error (file not found, invalid JSON, etc.).
  - Files: `src/json_schema_profiler/cli.py`
  - Done when: `json-schema-profiler infer tests/fixtures/simple.json` prints a valid JSON Schema to stdout; `json-schema-profiler infer tests/fixtures/simple.json --output /tmp/schema.json` writes the schema to the file; `--help` shows the infer subcommand with description and options; non-existent file returns exit code 1 with a helpful error message.

- [ ] Task 4: Test fixtures — sample JSON datasets
  - What: Create JSON fixture files covering all success criteria scenarios: (a) `simple.json` — flat object with string, int, float, bool fields; (b) `nested.json` — object with a nested dict field; (c) `array_of_objects.json` — array of 5+ objects with shared fields; (d) `mixed_types.json` — objects where a field has mixed types (e.g., string and int); (e) `empty_array.json` — empty array `[]`; (f) `low_cardinality.json` — object with a string field having ≤10 unique values (should be flagged as enum candidate); (g) `large_sample.json` — 100 objects with 5 fields (string, int, float, bool, nested) for the success criterion test.
  - Files: `tests/fixtures/simple.json`, `tests/fixtures/nested.json`, `tests/fixtures/array_of_objects.json`, `tests/fixtures/mixed_types.json`, `tests/fixtures/empty_array.json`, `tests/fixtures/low_cardinality.json`, `tests/fixtures/large_sample.json`
  - Done when: All fixture files are valid JSON, parseable by Python's `json.loads()`, and cover every scenario listed above.

- [ ] Task 5: Unit tests (≥15 test cases)
  - What: Write comprehensive unit tests in `tests/test_inference.py` and `tests/test_cli.py` covering: (1) simple object type detection; (2) nested object recursive inference; (3) array-of-objects item schema inference; (4) mixed-type field handling; (5) empty array returns empty properties; (6) required field detection (field present in all objects); (7) optional field detection (field missing in some objects); (8) numeric min/max metadata; (9) string minLength/maxLength metadata; (10) low-cardinality enum candidate detection; (11) large sample (100 objects, 5 fields) produces correct schema; (12) CLI exits 0 on valid input; (13) CLI exits non-zero on invalid input; (14) CLI --output writes to file; (15) CLI --help displays usage.
  - Files: `tests/test_inference.py`, `tests/test_cli.py`
  - Done when: `pytest tests/` runs ≥15 tests and all pass. Each test is focused, deterministic, and covers one specific inference or CLI behavior.

- [ ] Task 6: End-to-end validation and sign-off
  - What: Run the full tool against all test fixtures and validate that the output is a valid JSON Schema draft-07 document (use `jsonschema` library to validate the inferred schema itself, or at minimum verify it is well-formed JSON with correct structure). Confirm all success criteria from the Phase 1 spec are met.
  - Files: `tests/test_e2e.py` (optional integration tests), plus verification against the Phase 1 success criteria checklist.
  - Done when: All Phase 1 success criteria are checked off: (a) 100-object, 5-field input produces valid schema with correct types; (b) nested objects recursively inferred; (c) arrays of objects infer item schema; (d) low-cardinality strings flagged as enum candidates; (e) CLI exit codes correct; (f) --help works; (g) all ≥15 unit tests pass.