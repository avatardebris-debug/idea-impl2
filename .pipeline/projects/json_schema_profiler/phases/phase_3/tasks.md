# Phase 3 Tasks

- [x] Task 1: Schema Drift Detection (`compare` command)
  - What: Add `json-schema-profiler compare <schema-a> <schema-b>` to detect drift.
  - Files:
    - `src/json_schema_profiler/drift.py` — Logic to diff two JSON schemas.
    - `src/json_schema_profiler/cli.py` — Add the `compare` command.
  
- [x] Task 2: Streaming Support
  - What: Add `--stream` flag using `ijson` or chunked reading.
  - Files:
    - `src/json_schema_profiler/inference.py` — Add stream-based processing.
    - `src/json_schema_profiler/cli.py` — Add `--stream` flag.

- [x] Task 3: Progress Indicators
  - What: Use `rich.progress` to display a progress bar during analysis.
  - Files:
    - `src/json_schema_profiler/cli.py` — Wrap heavy operations in `rich` contexts.

- [x] Task 4: Caching
  - What: Skip processing if files haven't changed using `xxhash` and mtime.
  - Files:
    - `src/json_schema_profiler/cache.py` — Implement file hashing and cache manifest.

- [x] Task 5: Packaging & Config
  - What: Finalize `pyproject.toml`, `.json-schema-profiler.yaml` loading, and documentation.
  - Files:
    - `pyproject.toml` — Ensure correct entry points and dependencies.
    - `src/json_schema_profiler/config.py` — Implement YAML config loading.
    - `README.md` — Write comprehensive documentation.
