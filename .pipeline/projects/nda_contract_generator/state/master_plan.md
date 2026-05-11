# NDA Contract Generator — Master Plan

## Core Deliverable
A Python CLI tool that drafts jurisdiction-specific non-disclosure agreements using customizable clauses and AI-assisted legal phrasing. Users provide party details, jurisdiction, and clause preferences; the tool generates a complete, professionally-worded NDA in plain text, PDF, or DOCX format.

## Architecture Notes

```
nda_contract_generator/
├── core/
│   ├── template_engine.py     # Template rendering (Jinja2 or string-based)
│   ├── clause_library.py      # Structured clause definitions (name, default, options)
│   ├── jurisdiction_db.py     # Jurisdiction-specific rules and defaults
│   └── validator.py           # NDA completeness and consistency checks
├── cli/
│   ├── main.py                # CLI entry point (argparse)
│   ├── commands/
│   │   ├── draft.py           # Draft subcommand
│   │   ├── customize.py       # Customize subcommand
│   │   └── validate.py        # Validate subcommand
│   └── prompts.py             # Interactive prompt helpers
├── ai/
│   ├── phrasing_engine.py     # AI-assisted clause generation/refinement
│   ├── prompts/
│   │   ├── clause_generation.md  # System prompt for clause drafting
│   │   └── refinement.md         # System prompt for clause refinement
│   └── providers/
│       ├── base.py            # Abstract LLM provider interface
│       ├── openai.py          # OpenAI API provider
│       └── ollama.py          # Ollama (local) provider
├── exporters/
│   ├── base.py                # Abstract exporter interface
│   ├── text_exporter.py       # Plain text (.txt)
│   ├── pdf_exporter.py        # PDF via reportlab or weasyprint
│   └── docx_exporter.py       # DOCX via python-docx
├── jurisdictions/
│   ├── base.py                # Base jurisdiction config
│   ├── us/
│   │   ├── california.py      # CA-specific (CCPA, trade secrets)
│   │   ├── new_york.py        # NY-specific (governing law)
│   │   └── delaware.py        # DE-specific (corporate law)
│   ├── uk/
│   │   └── england_wales.py   # England & Wales (GDPR, common law)
│   ├── eu/
│   │   └── gdpr_compliant.py  # EU GDPR-aware template
│   └── index.py               # Jurisdiction registry
├── tests/
│   ├── test_template_engine.py
│   ├── test_clause_library.py
│   ├── test_jurisdictions.py
│   ├── test_exporters.py
│   └── test_integration.py
├── templates/
│   ├── mutual_nda.txt         # Mutual NDA template
│   ├── unilateral_nda.txt     # Unilateral NDA template
│   └── employment_nda.txt     # Employment NDA template
├── config/
│   └── defaults.json          # Default settings
├── pyproject.toml
└── requirements.txt
```

**Key design decisions:**
- CLI-first design with `argparse` subcommands; interactive mode available via `--interactive`.
- Template engine uses Jinja2 for flexible, composable templates with variable substitution.
- Clause library is a JSON/YAML-backed registry; each clause has a name, default text, allowed values, and jurisdiction overrides.
- AI phrasing is an optional layer — users can generate clauses via LLM or use built-in templates. Supports OpenAI and Ollama backends.
- Exporters are pluggable; each implements a `render(nda_data) -> bytes` interface.
- Jurisdiction configs define governing law defaults, required clauses, and prohibited clauses per region.
- No heavy dependencies for core; PDF export uses `reportlab` (optional install), DOCX uses `python-docx` (optional install).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Legal liability — incorrect or misleading clauses | High | Include prominent disclaimer; make AI phrasing clearly optional; allow human review; document that output is not legal advice |
| AI provider dependency / cost | Medium | Support multiple providers (OpenAI, Ollama, local models); make AI optional; cache generated clauses |
| Jurisdiction coverage gaps | Medium | Start with 3-5 key jurisdictions; design jurisdiction registry to be extensible; community-contributed configs encouraged |
| Template complexity explosion | Medium | Use clause composition (atomic clauses → composite); avoid monolithic templates; test each clause independently |
| PDF/DOCX export reliability | Low | Use well-maintained libraries; test on multiple OSes; fall back to plain text if export fails |

---

## Phase 1: Core CLI + Template Engine + 3 Jurisdictions

**Description:** Build the foundational CLI with a Jinja2-based template engine, a structured clause library, and support for 3 jurisdictions (US/California, UK/England & Wales, EU/GDPR). Users can select a template type (mutual, unilateral, employment), choose a jurisdiction, customize key clauses, and output a plain-text NDA. This is the smallest useful deliverable — a user can generate a complete, jurisdiction-aware NDA in text format.

**Deliverable:**
- `core/template_engine.py` — Jinja2 template engine with variable substitution and clause composition
- `core/clause_library.py` — JSON-backed clause registry (20+ clauses: definition of confidential info, exclusions, term, remedies, governing law, etc.)
- `core/jurisdiction_db.py` — registry for 3 jurisdictions with defaults and overrides
- `templates/mutual_nda.txt`, `templates/unilateral_nda.txt`, `templates/employment_nda.txt` — base templates
- `cli/main.py` — CLI with subcommands: `draft`, `customize`, `validate`
- `cli/prompts.py` — interactive prompt helpers for party details and clause selection
- `jurisdictions/us/california.py`, `jurisdictions/uk/england_wales.py`, `jurisdictions/eu/gdpr_compliant.py`
- `tests/` — unit tests for template engine, clause library, jurisdiction configs
- Sample fixture files for testing

**Dependencies:** None (foundation phase)

**Success Criteria:**
- [ ] CLI accepts: `python -m nda_contract_generator draft --template mutual --jurisdiction california --output output.txt`
- [ ] All 3 template types (mutual, unilateral, employment) render correctly with variable substitution
- [ ] All 3 jurisdictions apply correct governing law, required clauses, and default term lengths
- [ ] Clause library supports at least 20 clauses with configurable values (e.g., term: 1/2/3/5 years, indefinite)
- [ ] Custom clause override works: `--clause term=3_years --clause remedies=injunctive`
- [ ] Plain text output is well-formatted and legally coherent
- [ ] All unit tests pass (≥ 30 test cases)
- [ ] Interactive mode (`--interactive`) guides user through party details and clause selection
- [ ] `validate` subcommand checks for missing required fields and flags inconsistencies

---

## Phase 2: AI-Assisted Legal Phrasing + Expanded Jurisdictions

**Description:** Add an optional AI-assisted phrasing layer that generates and refines clause text using LLM APIs. Support multiple LLM backends (OpenAI, Ollama). Expand jurisdiction coverage to 8+ regions. Add a clause marketplace concept — users can save, share, and load custom clause sets. This phase significantly improves the quality and flexibility of generated clauses.

**Deliverable:**
- `ai/phrasing_engine.py` — AI clause generation and refinement engine
- `ai/prompt_templates/` — system prompts for clause generation, refinement, and tone adjustment
- `ai/providers/openai.py`, `ai/providers/ollama.py` — LLM provider implementations
- `ai/providers/base.py` — abstract provider interface
- Jurisdiction expansion to 8+ regions (US: NY, DE, TX; UK; EU; Canada; Australia; Singapore)
- `core/clause_library.py` extended with save/load custom clause sets
- `cli/commands/customize.py` extended with AI-assisted clause generation
- `tests/test_ai_phrasing.py` — integration tests for AI provider interface (mocked)
- Updated documentation with AI usage examples

**Dependencies:** Phase 1 (template engine, clause library, jurisdiction registry)

**Success Criteria:**
- [ ] AI phrasing generates coherent, legally-appropriate clause text for all 20+ clause types
- [ ] OpenAI and Ollama providers both work (configurable via `--ai-provider openai|ollama`)
- [ ] AI refinement mode (`--ai-refine`) rewrites existing clauses with adjusted tone (formal, plain-language, aggressive, balanced)
- [ ] 8+ jurisdictions produce correct governing law and required clause sets
- [ ] Custom clause sets can be saved to JSON and loaded: `--load-clauses my_clauses.json`
- [ ] AI calls are cached to avoid redundant API calls
- [ ] Graceful fallback when AI provider is unavailable (uses built-in templates)
- [ ] CLI: `python -m nda_contract_generator draft --template mutual --jurisdiction california --ai-provider ollama --ai-refine --output output.txt`

---

## Phase 3: Multi-Format Export + Validation + Polish

**Description:** Add PDF and DOCX export, comprehensive NDA validation (completeness checks, clause conflict detection, jurisdiction compliance), a `compare` subcommand for side-by-side NDA comparison, and polish the CLI with help text, examples, and documentation. This phase makes the tool production-ready for real-world use.

**Deliverable:**
- `exporters/pdf_exporter.py` — PDF export via reportlab (styled, with header/footer, page numbers)
- `exporters/docx_exporter.py` — DOCX export via python-docx (proper heading styles, paragraph formatting)
- `core/validator.py` extended with clause conflict detection and jurisdiction compliance checks
- `cli/commands/validate.py` — validation subcommand with detailed error/warning output
- `cli/commands/compare.py` — compare two NDA outputs side-by-side (diff-style)
- `config/defaults.json` — user-configurable defaults (default jurisdiction, template, AI provider)
- `README.md` — full documentation with examples, CLI reference, AI setup guide
- `tests/test_exporters.py`, `tests/test_integration.py` — end-to-end tests
- `pyproject.toml` with optional dependency groups (`[pdf]`, `[docx]`, `[ai]`)

**Dependencies:** Phases 1-2 (all core functionality must be complete)

**Success Criteria:**
- [ ] PDF output renders correctly on all platforms with proper formatting
- [ ] DOCX output opens in Microsoft Word with correct styles and formatting
- [ ] Validator catches: missing party info, inconsistent terms, prohibited clauses for jurisdiction
- [ ] `compare` subcommand shows unified diff of two NDA files
- [ ] `--defaults` config file works for setting persistent preferences
- [ ] All optional dependencies are installable via `pip install nda_contract_generator[all]`
- [ ] Full documentation with CLI reference, examples, and AI setup instructions
- [ ] End-to-end test: `draft → export to PDF/DOCX → validate → compare` all work without errors
- [ ] CLI help text includes examples for common use cases
- [ ] Prominent legal disclaimer included in all outputs and CLI help

---

## Summary

| Phase | Focus | Est. Complexity | Key Output |
|-------|-------|-----------------|------------|
| 1 | Core CLI + Template Engine + 3 Jurisdictions | Low | Working CLI that generates jurisdiction-aware NDAs in plain text |
| 2 | AI-Assisted Phrasing + 8+ Jurisdictions | Medium | AI clause generation, multiple LLM backends, expanded jurisdiction coverage |
| 3 | Multi-Format Export + Validation + Polish | Medium | PDF/DOCX export, validation, comparison, production-ready polish |

**Recommended execution order:** 1 → 2 → 3
(Rationale: Phase 1 delivers a usable MVP. Phase 2 adds the differentiating AI capability. Phase 3 rounds out with export formats and validation for real-world deployment.)
