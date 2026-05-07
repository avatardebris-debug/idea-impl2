# Phase 1 Tasks

- [x] Task 1: Project scaffolding and configuration
  - What: Create the project directory structure, `pyproject.toml`, and `docsai.yaml` config parser.
  - Files: `docsai/pyproject.toml`, `docsai/docsai.yaml`, `docsai/core/config.py`, `docsai/core/__init__.py`, `docsai/parsers/__init__.py`, `docsai/generators/__init__.py`, `docsai/cli/__init__.py`
  - Done when: `pyproject.toml` lists dependencies (typer, tree-sitter, pyyaml); `core/config.py` can load `docsai.yaml` and return output_format (yaml/json), languages (list), and output_path; a minimal `docsai.yaml` with these keys parses without error.

- [x] Task 2: Python AST parser
  - What: Build the Python source parser using `tree-sitter` that extracts public functions, classes, methods, their signatures, parameter types, return types, and docstrings.
  - Files: `docsai/parsers/base.py`, `docsai/parsers/python_parser.py`
  - Done when: `python_parser.py` takes a `.py` file path, returns a structured dict with entries containing `name`, `kind` (function/class/method), `params` (list of `{name, type}`), `return_type`, `docstring`, and `line_number`; supports extracting both top-level and class-level public symbols (those not prefixed with `_`); unit test on a sample `.py` file produces correct output.

- [x] Task 3: TypeScript AST parser
  - What: Build the TypeScript source parser using `tree-sitter` with the same interface as the Python parser.
  - Files: `docsai/parsers/typescript_parser.py`
  - Done when: `typescript_parser.py` takes a `.ts`/`.tsx` file path, returns a structured dict with entries containing `name`, `kind` (function/interface/class/method/enum), `params`, `return_type`, `docstring`, and `line_number`; correctly extracts public symbols (exported or not prefixed with `_`); unit test on a sample `.ts` file produces correct output.

- [x] Task 4: API spec generator
  - What: Build the generator that takes parsed AST data from both parsers and produces a structured API spec in YAML or JSON format.
  - Files: `docsai/generators/base.py`, `docsai/generators/api_spec.py`
  - Done when: `api_spec.py` accepts a list of parsed symbol dicts and an output format (yaml/json), produces a spec document with `project_name`, `language`, `symbols` (array of all extracted symbols), and `metadata` (file count, total symbols); output is valid YAML or JSON; generator respects the `output_format` from config.

- [x] Task 5: CLI entry point and `docsai spec` command
  - What: Build the Typer CLI with the `spec` subcommand that ties config loading, file discovery, parsing, and spec generation together.
  - Files: `docsai/cli/__init__.py`, `docsai/cli/spec.py`
  - Done when: Running `docsai spec ./sample_project` discovers `.py` and `.ts` files recursively, parses them, and writes a valid API spec to the configured output path (default: `./docsai_output/api_spec.yaml`); CLI accepts `--format yaml|json`, `--output <path>`, and `--config <path>` flags; `docsai --help` shows usage.

- [x] Task 6: End-to-end test on a sample project
  - What: Create a sample project with Python and TypeScript files, and an end-to-end test that runs `docsai spec` against it and validates the output.
  - Files: `tests/sample_project/sample_python.py`, `tests/sample_project/sample_typescript.ts`, `tests/test_e2e.py`
  - Done when: `test_e2e.py` runs `docsai spec` on the sample project, loads the output YAML/JSON, and asserts: (1) at least 3 symbols are present, (2) each symbol has `name`, `kind`, `params`, `return_type`, and `docstring` fields, (3) both Python and TypeScript files are represented, (4) output format matches the requested format; test passes with `pytest`.