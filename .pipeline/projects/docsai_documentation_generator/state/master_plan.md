# DocsAI Documentation Generator — Master Implementation Plan

> **Idea:** An AI-powered technical documentation assistant that structures API specs, generates READMEs, and maintains versioned changelogs.
> **Created:** 2026-05-05
> **Status:** Draft

---

## Core Deliverable

A CLI + library tool that ingests source code (or existing docs) and produces:
1. **Structured API specifications** (YAML/JSON) from code analysis.
2. **README.md** files auto-generated with project context, usage examples, and architecture diagrams.
3. **Versioned changelogs** that track and format code changes over time using git history.

All three outputs are produced by a single pipeline driven by an LLM, with a pluggable backend so users can swap in different model providers.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    DocsAI CLI                           │
│              (docsai generate / docsai diff)            │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   Pipeline Engine                       │
│  ┌──────────┐  ┌───────────┐  ┌─────────────────────┐  │
│  │  Source   │→ │  AST/Doc  │→ │   LLM Orchestrator  │  │
│  │  Parser   │  │  Analyzer │  │   (pluggable)       │  │
│  └──────────┘  └───────────┘  └─────────┬───────────┘  │
│                                         │               │
│                    ┌────────────────────┼───────────┐   │
│                    ▼                    ▼           ▼   │
│             ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│             │  API Spec│  │ README   │  │ Changelog│  │
│             │ Generator│  │ Generator│  │ Generator│  │
│             └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  Output Layer                           │
│  ┌──────────┐  ┌───────────┐  ┌─────────────────────┐  │
│  │  YAML/   │  │ Markdown  │  │  Git-backed version │  │
│  │  JSON    │  │           │  │  store              │  │
│  └──────────┘  └───────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Key Design Decisions
- **Language-agnostic core:** Uses AST parsing via `tree-sitter` for code analysis, supporting Python, TypeScript, Go, and Rust.
- **LLM-agnostic:** Abstracts the model provider behind a `ModelBackend` interface (OpenAI, Anthropic, Ollama, etc.).
- **Config-driven:** A `docsai.yaml` config file controls templates, output paths, model selection, and style guides.
- **Git-native:** Changelog generation reads directly from `git log` diffs; no separate database needed.

---

## Phase 1 — MVP: API Spec Generator

### Description
Build the core pipeline engine and the API specification generator. This is the smallest useful thing: a tool that parses source code, extracts function/class signatures, and produces a structured API spec in YAML/JSON.

### Deliverable
- A working CLI (`docsai spec`) that takes a source directory and outputs a structured API spec file.
- AST parser supporting Python and TypeScript.
- Configurable output format (YAML or JSON).
- Basic LLM integration: the spec includes auto-generated docstrings/comments extracted from code.

### Dependencies
- None (foundation phase).

### Success Criteria
- [ ] `docsai spec ./my_project` produces a valid YAML/JSON API spec with all public functions/classes.
- [ ] Supports Python and TypeScript source files.
- [ ] Output includes function signatures, parameter types, return types, and docstrings.
- [ ] Config file (`docsai.yaml`) controls output format and target language.
- [ ] End-to-end test passes on a sample project.

---

## Phase 2 — README Generator with Templates

### Description
Extend the pipeline to generate README.md files. This phase adds a template engine and an LLM-powered content generator that produces project overviews, installation instructions, usage examples, and architecture summaries.

### Deliverable
- A CLI subcommand `docsai readme` that generates a complete README.md.
- Template system supporting custom markdown templates.
- LLM-generated content: project description, usage examples, architecture notes.
- Integration with Phase 1: the README can reference the generated API spec.

### Dependencies
- Phase 1 (API spec generator must exist and produce parseable output).

### Success Criteria
- [ ] `docsai readme ./my_project` produces a complete, well-formatted README.md.
- [ ] README includes: project overview, install steps, usage examples, API reference link, architecture diagram (text-based).
- [ ] Custom templates can override default sections.
- [ ] Generated content is coherent and accurate for a sample project.
- [ ] README references the Phase 1 API spec output.

---

## Phase 3 — Versioned Changelog with Git Integration

### Description
Add changelog generation powered by git history. This phase reads commit messages and diffs, uses the LLM to summarize changes into categories (Added, Changed, Deprecated, Removed, Fixed), and writes versioned changelog entries.

### Deliverable
- A CLI subcommand `docsai changelog` that generates a versioned changelog from git history.
- Semantic versioning support (semver bumping).
- Configurable changelog format (following Keep a Changelog conventions).
- Optional: auto-bump version and update CHANGELOG.md on `git tag`.

### Dependencies
- Phase 1 (for source code context).
- Phase 2 (for template consistency across outputs).
- Git must be installed and the project must be a git repo.

### Success Criteria
- [ ] `docsai changelog ./my_project` produces a properly formatted CHANGELOG.md from git history.
- [ ] Changes are categorized correctly (Added/Changed/Fixed/Removed/Deprecated).
- [ ] Supports semver version tags (e.g., `v1.0.0`, `v1.1.0`).
- [ ] Output follows Keep a Changelog format conventions.
- [ ] `docsai changelog --bump minor` bumps the version and updates the changelog.
- [ ] End-to-end test passes on a sample project with realistic git history.

---

## Architecture Notes

### Module Structure
```
docsai/
├── cli/
│   ├── __init__.py          # CLI entry point (click/typer)
│   ├── spec.py              # `docsai spec` command
│   ├── readme.py            # `docsai readme` command
│   └── changelog.py         # `docsai changelog` command
├── core/
│   ├── pipeline.py          # Pipeline orchestration
│   ├── config.py            # docsai.yaml parsing
│   └── model_backend.py     # LLM provider abstraction
├── parsers/
│   ├── base.py              # Abstract parser interface
│   ├── python_parser.py     # tree-sitter Python
│   └── typescript_parser.py # tree-sitter TypeScript
├── generators/
│   ├── api_spec.py          # API spec generation
│   ├── readme.py            # README generation
│   └── changelog.py         # Changelog generation
├── templates/
│   ├── readme_default.md    # Default README template
│   └── changelog_default.md # Default changelog template
└── utils/
    ├── git_helper.py        # Git log/diff utilities
    └── formatting.py        # Output formatting helpers
```

### Technology Stack
| Component | Technology |
|-----------|-----------|
| CLI framework | Typer or Click |
| AST parsing | tree-sitter (via `tree-sitter` Python bindings) |
| LLM backend | OpenAI API / Anthropic / Ollama (pluggable) |
| Config | PyYAML |
| Versioning | semver (Python library) |
| Output formats | YAML, JSON, Markdown |

### Data Flow
1. **Input:** Source directory + `docsai.yaml` config.
2. **Parse:** AST parser extracts symbols, types, docstrings.
3. **Analyze:** Pipeline engine builds an intermediate representation (IR).
4. **Generate:** LLM orchestrator fills templates with IR data.
5. **Output:** Formatted files written to disk.

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| LLM costs for large codebases | Medium | Add caching layer; batch requests; support local models via Ollama. |
| AST parser limitations for non-Python/TS | Medium | Start with Python + TypeScript; add languages iteratively; fall back to regex-based extraction. |
| LLM hallucination in generated docs | High | Add a validation step that cross-references generated content against the AST; allow user review before final output. |
| Git history complexity (squash merges, rebase) | Low | Document supported git workflows; provide `--ignore-merges` flag. |
| Template maintenance burden | Low | Ship sensible defaults; provide template override mechanism; collect community templates. |

---

## Future Extensions (Out of Scope for v1)

- **Multi-language support:** Add Go, Rust, Java parsers.
- **Web dashboard:** Interactive docs viewer with search.
- **CI/CD integration:** GitHub Action that auto-generates docs on PR.
- **API spec validation:** Compare generated spec against runtime behavior (OpenAPI generation).
- **Collaborative editing:** Multi-user docs with conflict resolution.
- **Plugin system:** Allow community-contributed generators and templates.

---

## Timeline Estimate

| Phase | Estimated Duration |
|-------|-------------------|
| Phase 1 — API Spec Generator | 2–3 weeks |
| Phase 2 — README Generator | 2 weeks |
| Phase 3 — Changelog Generator | 2 weeks |
| **Total** | **6–7 weeks** |

---

*Plan created by Idea Planner. Ready for review.*
