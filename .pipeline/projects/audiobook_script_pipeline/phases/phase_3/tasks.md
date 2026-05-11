# Phase 3 Tasks

- [x] Task 1: Add Python packaging configuration (pyproject.toml)
  - What: Create a pyproject.toml with build system (setuptools), project metadata (name, version, description, license), and console_scripts entry point so the package can be installed via pip. Also create a requirements.txt (empty or with any dependencies) and MANIFEST.in for package data.
  - Files: workspace/pyproject.toml, workspace/requirements.txt, workspace/MANIFEST.in
  - Done when: pyproject.toml defines [build-system], [project] (name, version, description, license, authors), and [project.scripts] with an entry point (e.g., `audiobook-pipeline = audiobook_script_pipeline.cli:main`). Running `pip install -e .` from the workspace directory succeeds without errors.

- [x] Task 2: Expose public API surface in package __init__.py
  - What: Update the top-level `__init__.py` to import and expose the main public classes (ManuscriptParser, AudioScriptFormatter, ScriptPipeline) so users can do `from audiobook_script_pipeline import ScriptPipeline`. Also add a `__all__` list to define the public API contract.
  - Files: workspace/audiobook_script_pipeline/__init__.py
  - Done when: `from audiobook_script_pipeline import ScriptPipeline, ManuscriptParser, AudioScriptFormatter` works without errors, and `__all__` lists exactly those three classes.

- [x] Task 3: Enhance CLI with --version, --format, and --config options
  - What: Extend the CLI to support: (a) `--version` flag that prints the package version, (b) `--format json|text` option to choose output format (default: text), (c) `--config` option to load pause/emphasis settings from a JSON config file. Update the help text accordingly.
  - Files: workspace/audiobook_script_pipeline/cli.py
  - Done when: `python -m audiobook_script_pipeline.cli --version` prints the version string. `--format json` outputs valid JSON to stdout. `--format text` (default) outputs the current formatted text. `--config config.json` loads and applies pause/emphasis settings. All options appear in `--help` output.

- [x] Task 4: Create deployment documentation and Docker support
  - What: Create a DEPLOYMENT.md file covering: (a) pip install instructions (from PyPI once published, from source), (b) Dockerfile for containerized usage, (c) Docker Compose example, (d) environment variable configuration, (e) troubleshooting common issues. Also create a .dockerignore file.
  - Files: workspace/DEPLOYMENT.md, workspace/Dockerfile, workspace/.dockerignore
  - Done when: DEPLOYMENT.md has clear sections for pip install, Docker build/run, config via env vars, and troubleshooting. Dockerfile builds successfully (docker build passes). .dockerignore excludes common non-essential files (.git, __pycache__, tests, .pytest_cache, etc.).

- [x] Task 5: Run full integration validation
  - What: Execute the full test suite to confirm nothing is broken by Phase 3 changes. Verify the CLI works end-to-end with all new options. Verify pip install works. Verify the package is importable from the installed location.
  - Files: (verification only — no new files)
  - Done when: All existing tests pass (`pytest` returns 0). CLI with --version, --format json, --format text, and --output all work correctly. `pip install -e .` succeeds and the console_scripts entry point is callable. `python -c "from audiobook_script_pipeline import ScriptPipeline"` succeeds.