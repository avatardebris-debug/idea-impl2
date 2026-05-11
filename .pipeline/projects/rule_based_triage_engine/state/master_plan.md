# Master Plan: Rule-Based Triage Engine

## Goal
Extend the existing email tool with a visual rule builder that auto-filters, tags, and routes incoming messages to specific CRM pipelines based on content analysis — turning raw inbox into organized, actionable leads.

## Core Deliverable
A working triage engine where incoming emails are automatically analyzed against user-defined rules, tagged with categories, and routed to the correct CRM pipeline — all managed through a visual rule-building interface.

---

## Phase 1: Core Rule Engine — Parse, Match, Tag
- **Description**: Build the foundational rule engine that can parse incoming email messages, evaluate them against a set of rules, and apply tags and routing decisions. Rules are defined in a structured JSON format. This phase includes the rule parser, the evaluation engine, and the tagging/routing output layer.
- **Deliverable**: A standalone Python module `rule_engine/` with:
  - `Rule` dataclass (fields: `id`, `name`, `conditions`, `actions`, `priority`, `enabled`)
  - `Condition` dataclass (fields: `field`, `operator`, `value`) — supports fields: `subject`, `from`, `body`, `has_attachment`, `priority_header`
  - Operators: `contains`, `not_contains`, `equals`, `regex`, `is_empty`, `gt`, `lt`
  - `Action` dataclass (fields: `type`, `target` — type: `tag`, `route`, `archive`, `flag`)
  - `RuleEngine` class with method `evaluate(email: dict) -> list[Action]` that returns all matching actions sorted by priority
  - `RuleStore` class for loading/saving rules from JSON files
  - Unit tests for all condition operators and rule matching logic
- **Dependencies**: none
- **Success criteria**:
  - [ ] A rule defined in JSON (e.g., `{"conditions": [{"field": "subject", "operator": "contains", "value": "invoice"}], "actions": [{"type": "tag", "target": "billing"}]}`) correctly matches an email dict with "invoice" in the subject
  - [ ] Multiple rules with different priorities are evaluated in correct order; higher priority rules' actions are applied first
  - [ ] `RuleStore` can save and reload rules without data loss
  - [ ] All unit tests pass (minimum 15 test cases covering each operator and edge cases like empty bodies, unicode subjects)
  - [ ] No rules match → returns empty action list (graceful no-op)

## Phase 2: Visual Rule Builder — UI Layer
- **Description**: Build a visual interface for creating, editing, and managing triage rules without touching JSON files. Provides a form-based UI where users can select email fields, choose operators, enter values, and define actions. Rules are persisted to the same JSON store from Phase 1.
- **Deliverable**: A visual rule builder module `rule_builder_ui/` with:
  - `RuleBuilderPanel` — main UI component (Tkinter or web-based via Flask/FastAPI + HTMX) with:
    - Rule list sidebar showing all rules with name, priority, enabled toggle
    - Rule editor panel with:
      - Rule name input
      - Dynamic condition builder (add/remove conditions with dropdowns for field, operator, value)
      - Dynamic action builder (add/remove actions with type selector and target input)
      - Priority slider/input
      - Enable/disable toggle
    - Import/export rules as JSON
    - Duplicate rule shortcut
  - `RuleForm` — validation layer that validates user input before saving
  - API endpoints (if web-based): `GET /rules`, `POST /rules`, `PUT /rules/{id}`, `DELETE /rules/{id}`
  - Integration tests for the full CRUD lifecycle of rules through the UI
- **Dependencies**: Phase 1 (RuleEngine, RuleStore, Rule/Condition/Action dataclasses)
- **Success criteria**:
  - [ ] User can create a new rule via the UI and it is saved to the JSON store and loaded back correctly
  - [ ] User can edit an existing rule and changes are persisted
  - [ ] User can delete a rule and it is removed from the store
  - [ ] Rule validation catches invalid inputs (e.g., missing value for `contains` operator) and shows user-friendly errors
  - [ ] Import/export JSON round-trips correctly (export → import produces identical rule set)
  - [ ] All integration tests pass

## Phase 3: Content Analysis & CRM Pipeline Integration
- **Description**: Add intelligent content analysis capabilities and connect the triage engine to CRM pipelines. This includes keyword/theme detection, sender reputation scoring, and configurable CRM pipeline routing targets. The engine can now auto-suggest rules based on email patterns and route matched emails to specific CRM destinations.
- **Deliverable**: Extended triage engine with:
  - `ContentAnalyzer` module:
    - Keyword/theme extraction using lightweight NLP (TF-IDF or keyword frequency)
    - Sender reputation scoring (domain-based, whitelists/blacklists)
    - Auto-suggest rules: analyzes existing email corpus and suggests rules for recurring patterns (e.g., "You receive 15 emails from @supplier.com — create a rule?")
  - `CRMRouter` module:
    - Configurable pipeline destinations (webhook, API key, or local file export)
    - Pipeline config schema: `{name, type, config: {url, method, headers, auth_type}}`
    - Batch routing support (group emails by pipeline, send in batches)
    - Retry logic with exponential backoff for failed deliveries
  - `TriagePipeline` orchestrator that ties Phase 1-3 together:
    - `process_email(email: dict) -> {tags: list, route: str, actions: list}`
    - Hooks for pre-processing (normalize headers, strip HTML) and post-processing (log results, trigger webhooks)
  - End-to-end integration test simulating email ingestion → rule matching → CRM routing
- **Dependencies**: Phase 1 (core engine), Phase 2 (rule management)
- **Success criteria**:
  - [ ] Content analyzer correctly identifies top keywords in a sample email body with >80% accuracy on test corpus
  - [ ] Sender reputation scoring correctly classifies known domains (whitelisted = trusted, blacklisted = spam)
  - [ ] Auto-suggest feature generates at least one actionable rule suggestion from a corpus of 50+ emails with recurring patterns
  - [ ] CRM router successfully delivers routed emails to a mock webhook endpoint (e.g., httpbin.org/post) with correct payload
  - [ ] Batch routing groups emails by pipeline and sends them in configurable batch sizes
  - [ ] Retry logic retries failed deliveries up to 3 times with exponential backoff before marking as failed
  - [ ] End-to-end test passes: email → rule match → tag → route to CRM pipeline

---

## Architecture Notes

### Design Decisions
1. **Rule format**: JSON-based rule definitions enable version control, import/export, and programmatic rule generation. The `Rule`, `Condition`, `Action` dataclasses provide type safety on top of the JSON format.
2. **Evaluation strategy**: All rules are evaluated against each email (no short-circuit on first match) to ensure all applicable tags/actions are applied. Priority ordering determines action precedence.
3. **Pluggable CRM backends**: The `CRMRouter` uses a strategy pattern — each pipeline type (webhook, REST API, file export) is a separate implementation of a `PipelineBackend` interface. New backends can be added without modifying core logic.
4. **Content analysis**: Phase 3 uses lightweight, dependency-minimal NLP (no heavy ML models) to keep the engine fast and deployable. Keyword frequency and domain reputation are sufficient for most triage scenarios.
5. **UI framework**: Recommend FastAPI + HTMX for the rule builder UI — minimal JavaScript, server-rendered forms, easy to integrate with Python backend. Alternative: Tkinter for desktop-first users.

### Module Structure
```
rule_based_triage_engine/
├── rule_engine/
│   ├── __init__.py
│   ├── models.py          # Rule, Condition, Action dataclasses
│   ├── engine.py          # RuleEngine evaluation logic
│   ├── store.py           # RuleStore JSON persistence
│   └── operators.py       # Condition operator implementations
├── rule_builder_ui/
│   ├── __init__.py
│   ├── builder.py         # RuleBuilderPanel / RuleForm
│   ├── api.py             # REST endpoints (if web-based)
│   └── templates/         # HTML templates (if web-based)
├── content_analysis/
│   ├── __init__.py
│   ├── analyzer.py        # ContentAnalyzer
│   ├── reputation.py      # Sender reputation scoring
│   └── suggester.py       # Auto-rule suggestion
├── crm_router/
│   ├── __init__.py
│   ├── router.py          # CRMRouter
│   ├── backends/          # PipelineBackend implementations
│   │   ├── webhook.py
│   │   ├── rest_api.py
│   │   └── file_export.py
│   └── config.py          # Pipeline configuration schema
├── triage_pipeline/
│   ├── __init__.py
│   ├── pipeline.py        # TriagePipeline orchestrator
│   └── hooks.py           # Pre/post processing hooks
├── tests/
│   ├── test_engine.py
│   ├── test_store.py
│   ├── test_operators.py
│   ├── test_builder.py
│   ├── test_content_analyzer.py
│   ├── test_crm_router.py
│   └── test_e2e.py
└── config/
    └── default_rules.json # Starter rule templates
```

### Key Interfaces
```python
# Core evaluation
class RuleEngine:
    def evaluate(self, email: dict) -> list[Action]: ...
    def evaluate_batch(self, emails: list[dict]) -> dict[str, list[Action]]: ...

# Persistence
class RuleStore:
    def load(self) -> list[Rule]: ...
    def save(self, rules: list[Rule]) -> None: ...

# CRM routing
class CRMRouter:
    def route(self, email: dict, actions: list[Action]) -> RoutingResult: ...
    def route_batch(self, batches: dict[str, list[tuple[dict, list[Action]]]]) -> list[RoutingResult]: ...

# Content analysis
class ContentAnalyzer:
    def extract_keywords(self, text: str, top_n: int = 10) -> list[tuple[str, float]]: ...
    def score_sender(self, sender: str) -> float: ...
    def suggest_rules(self, email_corpus: list[dict]) -> list[Rule]: ...
```

---

## Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Rule evaluation performance** degrades with 100+ rules | Medium | Implement rule indexing (e.g., index rules by field/operator so only relevant rules are evaluated per email). Add caching for repeated evaluations. |
| **Content analysis accuracy** may be poor for domain-specific emails | Medium | Start with keyword frequency + regex patterns. Allow users to manually refine suggested rules. Phase 3 auto-suggest is advisory, not automatic. |
| **CRM API compatibility** varies widely across providers | Medium | Use the strategy pattern for backends. Provide a generic HTTP webhook backend that works with any REST API. Include mock backend for testing. |
| **UI complexity** — rule builder could become unwieldy | Low | Keep the UI focused on CRUD for rules. Defer advanced features (rule chaining, conditional logic) to later iterations. |
| **False positives** in auto-tagging could disrupt workflows | High | All auto-tags are logged and reviewable. Include a "undo" mechanism. Default to conservative matching (require explicit rule activation). |
| **Email parsing edge cases** (HTML emails, encoded subjects, multipart bodies) | Medium | Use a robust email parsing library (e.g., `email` stdlib + `beautifulsoup4` for HTML). Normalize all text to UTF-8 before analysis. |
