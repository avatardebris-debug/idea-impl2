# Phase 2 — README Generator with Templates

## Tasks

- [ ] Task 1: Scaffold docsai_documentation_generator project structure — create the package layout under `pipeline/projects/docsai_documentation_generator/` with submodules for `cli/`, `templates/`, `generators/`, `engine/`, and `tests/`. Define the CLI entry point and subcommand registration for `docsai readme`.

- [ ] Task 2: Implement the template engine — build a template loading and rendering system that supports custom markdown templates. Include a default template set (overview, installation, usage, API reference, architecture) and allow users to override sections via a `--template` flag or config file.

- [ ] Task 3: Build the LLM-powered content generator — create a generator module that produces project descriptions, usage examples, architecture notes, and installation instructions using LLM calls. Include prompt templates, input extraction from project files, and output formatting.

- [ ] Task 4: Implement the `docsai readme` CLI subcommand — wire together the template engine and content generator into a cohesive CLI command. Accept a project path argument, scan the project for metadata (e.g., `pyproject.toml`, `package.json`, `README.md` fragments), and produce a complete README.md output file.

- [ ] Task 5: Integrate with Phase 1 API spec output — add logic to detect and reference the Phase 1 API spec file (e.g., `api_spec.json` or `api_spec.md`) in the generated README. Include an "API Reference" section with a link to the spec and a summary of endpoints/types.

- [ ] Task 6: Write tests and validate with a sample project — create a sample test project (with a `pyproject.toml` and source files) and write integration tests that verify the generated README contains all required sections: project overview, install steps, usage examples, API reference link, and a text-based architecture diagram.