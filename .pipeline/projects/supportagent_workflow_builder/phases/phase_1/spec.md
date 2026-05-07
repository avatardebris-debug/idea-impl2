## Phase 1 — Core Ticket Pipeline (MVP)

> **Goal:** A working system that ingests a ticket, classifies it, routes it, and produces a draft response — end to end.

### Description

Build the foundational ticket processing pipeline. This includes a unified ticket model, a rule-based classifier, a simple SOP router, and a template-driven response generator. The system processes tickets through a linear pipeline: ingest → classify → route → draft → output. No multi-step workflows or agent orchestration yet — just a single, reliable path that handles the most common support scenarios.

### Deliverable

A runnable service (CLI + REST API) that:
- Accepts a ticket via API or file input
- Classifies it into one of ~10 predefined categories (billing, technical, account, etc.)
- Routes it to the correct team based on category + keyword rules
- Generates a draft response using a template engine with variable substitution
- Outputs the draft response as JSON + sends a notification (console log or email stub)

### Dependencies

- None (foundation phase — builds nothing on top of other project phases)

### Success Criteria

- [ ] Ticket ingestion accepts ≥3 input formats (JSON, email MIME, web form payload)
- [ ] Classification accuracy ≥ 85% on a test set of 500 labeled tickets
- [ ] Routing correctly assigns tickets to teams in ≥ 90% of test cases
- [ ] Draft response generation completes in < 2 seconds per ticket
- [ ] End-to-end pipeline latency p95 < 3 seconds
- [ ] Template system supports ≥ 5 distinct response templates
- [ ] API returns structured output with ticket ID, category, team, and draft body
- [ ] Unit test coverage ≥ 70% on core pipeline logic

---