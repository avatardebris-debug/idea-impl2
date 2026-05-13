# Phase 2 Tasks

- [x] Task 1: Template engine for README generation
  - What: Build a Jinja2-based template engine that loads markdown templates from a configurable directory, supports variable substitution (project name, description, symbols, metadata), and allows custom template overrides via `docsai.yaml`.
  - Files: Create `docsai/generators/readme_templates.py` (template engine class), add `docsai/generators/readme_templates/default/` directory with `readme.md.j2` default template, update `docsai/core/config.py` to add `readme_template_dir` and `readme_template_file` config keys
  - Done when: Template engine loads the default `readme.md.j2` template, substitutes variables like `{{ project_name }}`, `{{ project_description }}`, `{{ symbols }}`, `{{ metadata }}` correctly, and renders valid markdown; custom templates in a user-specified directory override the defaults; unit test verifies rendering with mock data produces expected markdown output.

- [x] Task 2: README content generator (LLM-powered)
  - What: Build a `ReadmeContentGenerator` class that uses the existing `llm_interface.py` to produce project overview, usage examples, and architecture notes from parsed symbol data and source file content.
  - Files: Create `docsai/generators/readme_content.py` (ReadmeContentGenerator class with methods: `generate_project_description`, `generate_usage_examples`, `generate_architecture_notes`), update `docsai/generators/__init__.py` to export the new class
  - Done when: `ReadmeContentGenerator` accepts parsed symbols and source file contents, calls the LLM with a structured prompt, and returns coherent markdown sections; supports pluggable model backend via `llm_interface.get_llm()`; unit test with a mock LLM verifies it produces non-empty, well-structured markdown sections for the sample project.

- [x] Task 3: README generator orchestrator
  - What: Build the `ReadmeGenerator` class that ties the template engine and content generator together — it produces a complete README.md by combining LLM-generated sections with the template, and optionally references the Phase 1 API spec.
  - Files: Create `docsai/generators/readme_generator.py` (ReadmeGenerator class), update `docsai/generators/__init__.py` to export it
  - Done when: `ReadmeGenerator.generate()` accepts source directory path, optional API spec path, and output path; produces a README.md containing: project overview, install steps, usage examples, API reference link (pointing to the Phase 1 spec output), and a text-based architecture diagram; output is valid markdown; generator respects template overrides from config.

- [x] Task 4: CLI `docsai readme` subcommand
  - What: Add the `readme` subcommand to the Typer CLI that wires together config loading, source discovery, content generation, template rendering, and output writing.
  - Files: Create `docsai/cli/readme.py` (readme_app Typer app with `readme` command), update `docsai/cli/__init__.py` to register the `readme` subcommand
  - Done when: Running `docsai readme ./sample_project` discovers source files, generates content, renders the template, and writes `README.md` to the configured output path; CLI accepts `--output <path>`, `--template <path>`, `--api-spec <path>`, and `--config <path>` flags; `docsai --help` shows the new `readme` subcommand; running on the sample project produces a complete README.md.

- [x] Task 5: End-to-end test for README generation
  - What: Create an end-to-end test that runs `docsai readme` against the sample project and validates the output README.md contains all required sections and is coherent.
  - Files: Create `tests/test_readme_e2e.py`
  - Done when: `test_readme_e2e.py` runs `docsai readme` on the sample project, loads the output README.md, and asserts: (1) file exists and is non-empty, (2) contains a project overview section, (3) contains installation instructions, (4) contains usage examples, (5) contains an API reference link pointing to the Phase 1 spec output, (6) contains a text-based architecture diagram, (7) references symbols from the sample project (e.g., `Calculator`, `greet`); test passes with `pytest`.