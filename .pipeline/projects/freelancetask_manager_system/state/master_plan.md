# FreelanceTask Manager System — Master Plan

## Core Deliverable
A unified system that merges a drop-servicing SOP engine with a job automation tool to streamline the freelance workflow: proposal generation, client matching, and contract signing. The system takes a service offering as input and automates the full pipeline from identifying matching opportunities through to signed contracts and SOP handoff.

---

## Architecture Notes

```
freelancetask_manager/
├── core/                          # Shared domain models
│   ├── service_offering.py        # Service definition (SOP, pricing, scope)
│   ├── client_profile.py          # Client data, preferences, history
│   ├── opportunity.py             # Job/opportunity representation
│   ├── contract.py                # Contract model (terms, e-sign fields)
│   └── state.py                   # Pipeline state serialization
│
├── sop_engine/                    # Drop-servicing SOP engine
│   ├── template_manager.py        # SOP template CRUD and versioning
│   ├── scope_extractor.py         # Extract deliverables/scope from SOP
│   ├── pricing_calculator.py      # Compute pricing tiers from SOP
│   └── quality_checklist.py       # SOP quality assurance checklist
│
├── proposal_engine/               # Proposal generation
│   ├── proposal_builder.py        # Assemble proposal from SOP + client data
│   ├── template_renderer.py       # Render proposals (Markdown/HTML/PDF)
│   ├── customization.py           # Client-specific proposal customization
│   └── version_control.py         # Track proposal revisions
│
├── client_matcher/                # Client-opportunity matching
│   ├── matcher.py                 # Core matching algorithm
│   ├── scoring.py                 # Match scoring (skills, budget, timeline)
│   ├── filters.py                 # Hard filters (availability, rate, etc.)
│   └── feed_parser.py             # Parse job feeds (Upwork, Fiverr, etc.)
│
├── contract_engine/               # Contract signing
│   ├── contract_generator.py      # Generate contract from matched proposal
│   ├── esign_integration.py       # E-signature API integration (DocuSign/HelloSign)
│   ├── clause_library.py          # Reusable contract clause library
│   └── signer_workflow.py         # Multi-party signing workflow
│
├── automation/                    # Job automation tool
│   ├── job_scraper.py             # Scrape/listings from freelance platforms
│   ├── auto_bidder.py             # Automated bidding/proposal submission
│   ├── notification.py            # Alerts for new matches
│   └── scheduler.py               # Cron-like scheduling for recurring tasks
│
├── cli/                           # Command-line interface
│   └── main.py                    # CLI entry point
│
├── tests/
│   ├── test_sop_engine.py
│   ├── test_proposal_engine.py
│   ├── test_client_matcher.py
│   ├── test_contract_engine.py
│   └── test_integration.py
│
├── benchmarks/                    # Reference data for validation
│   ├── sample_sops.json
│   ├── sample_clients.json
│   └── sample_opportunities.json
│
├── pyproject.toml
└── requirements.txt
```

**Key design decisions:**
- Python-first, CLI-driven tool with optional web dashboard in Phase 3.
- All engines are modular and independently testable; they communicate via domain models (no tight coupling).
- E-signature integration uses a pluggable adapter pattern (DocuSign, HelloSign, or manual fallback).
- Job feed parsing uses a feed adapter pattern so new platforms can be added without core changes.
- State is serialized as JSON for portability and version control.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Freelance platform API rate limits / ToS restrictions | High | Use headless browser fallbacks with polite delays; respect robots.txt; add configurable rate limiting |
| SOP quality varies widely across inputs | Medium | Build a SOP quality checker in Phase 1; require minimum fields for valid SOPs |
| E-signature API costs and compliance | Medium | Start with PDF generation + manual signing; add e-sign integration in Phase 3 |
| Client matching accuracy | High | Start rule-based scoring in Phase 2; add ML-based scoring as an optional Phase 3 enhancement |
| Scope creep across three subsystems | High | Strict phase boundaries; each phase ships a complete, testable subsystem |

---

## Phase 1: SOP Engine + Proposal Generator (MVP)

**Description:** Build the foundational SOP engine that manages drop-servicing service offerings and the proposal generator that produces client-ready proposals from SOPs. This is the smallest useful deliverable — a user can define a service SOP and generate a customized proposal for a given client profile.

**Deliverable:**
- `core/service_offering.py`, `core/client_profile.py`, `core/state.py` — domain models
- `sop_engine/template_manager.py` — SOP CRUD, versioning, validation
- `sop_engine/scope_extractor.py` — Extract deliverables, timelines, and scope from SOP
- `sop_engine/pricing_calculator.py` — Compute pricing tiers from SOP inputs
- `proposal_engine/proposal_builder.py` — Assemble proposal from SOP + client data
- `proposal_engine/template_renderer.py` — Render proposals as Markdown/HTML
- `cli/main.py` — CLI commands: `sop create/list/edit`, `proposal generate`
- Full test suite for Phase 1
- `benchmarks/sample_sops.json`, `benchmarks/sample_clients.json`

**Dependencies:** None (foundation phase)

**Success Criteria:**
- [ ] User can create, list, and edit SOPs via CLI
- [ ] SOP validation enforces minimum fields (title, description, deliverables, timeline, pricing)
- [ ] Scope extractor correctly identifies all deliverables and milestones from SOP
- [ ] Pricing calculator produces correct tiered pricing from SOP inputs
- [ ] Proposal generator produces a well-formatted proposal from SOP + client data
- [ ] Proposal renders to both Markdown and HTML formats
- [ ] All unit tests pass; CLI integration tests pass
- [ ] CLI: `ftm sop create --file service.json` and `ftm proposal generate --sop my-sop --client john --format html`

---

## Phase 2: Client Matcher + Job Automation

**Description:** Implement the client-opportunity matching engine and the job automation tool. The matcher evaluates freelance job listings against available service SOPs and client profiles, scoring and ranking matches. The automation tool scrapes job feeds from freelance platforms, applies the matcher, and notifies the user of high-confidence matches.

**Deliverable:**
- `core/opportunity.py` — Opportunity/job model
- `client_matcher/matcher.py` — Core matching algorithm (rule-based scoring)
- `client_matcher/scoring.py` — Weighted scoring (skills match, budget fit, timeline alignment)
- `client_matcher/filters.py` — Hard filters (rate, availability, location)
- `client_matcher/feed_parser.py` — Parse job feeds from platforms
- `automation/job_scraper.py` — Scrape/listings from freelance platforms
- `automation/auto_bidder.py` — Automated proposal submission for high-confidence matches
- `automation/notification.py` — Alert system (CLI output, email, webhook)
- `automation/scheduler.py` — Schedule periodic job scanning
- Updated CLI with `match scan`, `match list`, `automation start/stop` commands
- Integration tests for matcher + scraper pipeline
- `benchmarks/sample_opportunities.json`

**Dependencies:** Phase 1 (SOP engine, proposal generator, domain models)

**Success Criteria:**
- [ ] Matcher correctly scores and ranks at least 90% of test opportunities against SOPs
- [ ] Scoring is configurable (user-defined weight adjustments)
- [ ] Feed parser handles at least 2 platform formats (e.g., Upwork RSS, Fiverr Gigs API)
- [ ] Job scraper can poll 50+ listings per minute with configurable rate limits
- [ ] Auto-bidder submits proposals for matches above a configurable confidence threshold
- [ ] Notification system delivers alerts within 5 minutes of a new high-confidence match
- [ ] CLI: `ftm match scan --platform upwork --threshold 0.75` and `ftm automation start --interval 300`

---

## Phase 3: Contract Engine + Unified Dashboard

**Description:** Implement the contract signing engine and a unified dashboard that ties all three subsystems together. The contract engine generates contracts from matched proposals and supports e-signature workflows. The dashboard provides a unified view of the entire pipeline — SOPs, proposals, matches, and contracts — with export capabilities.

**Deliverable:**
- `core/contract.py` — Contract domain model
- `contract_engine/contract_generator.py` — Generate contracts from matched proposal data
- `contract_engine/esign_integration.py` — E-signature API integration (pluggable: DocuSign, HelloSign, or PDF fallback)
- `contract_engine/clause_library.py` — Reusable contract clause library
- `contract_engine/signer_workflow.py` — Multi-party signing workflow management
- `cli/dashboard.py` — Unified dashboard (CLI-first, with optional web UI scaffold)
- Pipeline orchestration: end-to-end flow from SOP → proposal → match → contract
- Export to CSV/HTML/PDF for all pipeline stages
- Complete documentation, examples, and setup guide
- Full integration test suite

**Dependencies:** Phases 1-2 (SOP engine, proposal generator, matcher, automation)

**Success Criteria:**
- [ ] Contract generator produces legally-structured contracts from proposal data
- [ ] Clause library supports at least 10 common freelance contract clauses
- [ ] E-signature integration (or PDF fallback) completes a signing workflow end-to-end
- [ ] Dashboard displays real-time pipeline status for all active SOPs and matches
- [ ] End-to-end flow works: SOP → proposal → match → contract → signed
- [ ] Export generates complete pipeline reports in CSV, HTML, and PDF
- [ ] CLI: `ftm contract generate --match 123 --format pdf` and `ftm dashboard --live`
- [ ] All integration tests pass; documentation is complete

---

## Summary

| Phase | Focus | Est. Complexity | Key Output |
|-------|-------|----------------|------------|
| 1 | SOP Engine + Proposal Generator | Medium | Define SOPs, generate client proposals |
| 2 | Client Matcher + Job Automation | High | Match jobs to SOPs, auto-bid, notify |
| 3 | Contract Engine + Unified Dashboard | High | Contract generation, e-sign, end-to-end pipeline |

**Recommended execution order:** 1 → 2 → 3

---

## Success Metrics

- **Phase 1:** SOP creation and proposal generation work for 100% of test SOPs; proposal quality score > 0.8 on expert review
- **Phase 2:** Matcher achieves > 85% precision on known good matches; scraper handles 2+ platform formats reliably
- **Phase 3:** End-to-end pipeline completes SOP-to-signed-contract flow for 90% of test cases; dashboard is fully functional

---

*Plan Version: 1.0*
*Last Updated: 2025*
