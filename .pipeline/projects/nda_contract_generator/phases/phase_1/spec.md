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