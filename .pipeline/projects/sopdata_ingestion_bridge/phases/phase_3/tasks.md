# Phase 3 Tasks

- [ ] Task 1: Consolidate duplicate DEFAULT_MAPPING and fix type annotations
  - What: Move DEFAULT_MAPPING to core.py as the single source of truth. Import it in transform.py and models.py instead of duplicating. Fix SOPInputRow.raw type annotation from `dict` to `dict[str, str]`. Fix pyproject.toml build-backend to use standard `setuptools.build_meta`.
  - Files: sopdata_ingestion_bridge/core.py, sopdata_ingestion_bridge/transform.py, sopdata_ingestion_bridge/models.py, pyproject.toml
  - Done when: DEFAULT_MAPPING exists only in core.py; transform.py and models.py import it from core.py; pyproject.toml build-backend is `setuptools.build_meta`; all existing tests still pass with no regressions.

- [ ] Task 2: Add CLI entry point
  - What: Create `sopdata_ingestion_bridge/__main__.py` that provides a CLI using `argparse`. The CLI should accept `--csv` (path to CSV file), `--mapping` (optional JSON file path for custom mapping), and `--format` (output format: `json` or `table`, default `json`). It should call `SOPBridge.ingest()` and print the results. Register the CLI in pyproject.toml under `[project.scripts]`.
  - Files: sopdata_ingestion_bridge/__main__.py, pyproject.toml
  - Done when: `python -m sopdata_ingestion_bridge --csv sample_data.csv` prints valid JSON output; `--format table` prints a human-readable table; `--mapping custom.json` loads and applies a custom mapping; CLI is registered as `sopdata-ingestion-bridge` console script in pyproject.toml.

- [ ] Task 3: Add deployment documentation
  - What: Create a `DEPLOYMENT.md` file in the workspace root with sections for: package installation (pip, editable install), CLI usage examples, Docker deployment (Dockerfile), environment variables (if any), and a checklist for releasing to PyPI (version bump, changelog, tag).
  - Files: DEPLOYMENT.md
  - Done when: DEPLOYMENT.md exists with sections for installation, CLI examples, Docker deployment (with a working Dockerfile), and PyPI release checklist. All examples in the doc are accurate and runnable.

- [ ] Task 4: Add type hints and mypy configuration
  - What: Add precise type hints to all public functions and methods across the package (bridge.py, ingest.py, transform.py, core.py). Add a `mypy.ini` or `pyproject.toml [tool.mypy]` section with sensible defaults. Ensure the codebase passes `mypy` with no errors.
  - Files: sopdata_ingestion_bridge/bridge.py, sopdata_ingestion_bridge/ingest.py, sopdata_ingestion_bridge/transform.py, sopdata_ingestion_bridge/core.py, pyproject.toml
  - Done when: All public functions have explicit return types and parameter types; `mypy sopdata_ingestion_bridge/` runs with zero errors; no new type-related regressions in existing tests.

- [ ] Task 5: Final integration verification
  - What: Run the full test suite (`pytest -v`), verify the package installs cleanly (`pip install -e .`), test the CLI end-to-end with sample_data.csv, and confirm the README is up to date with the new CLI and deployment sections.
  - Files: README.md (update if needed), all existing test files
  - Done when: All tests pass with `pytest -v`; `pip install -e .` succeeds; `sopdata-ingestion-bridge --csv sample_data.csv` works; README includes CLI usage and deployment links; no warnings or errors in the full build.