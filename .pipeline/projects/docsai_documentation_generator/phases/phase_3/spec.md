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

## Risks & Mitig