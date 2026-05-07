## Phase 2 — SOP Engine & Enhanced Triage

> **Goal:** Add configurable multi-step workflows, advanced triage, and LLM-assisted response generation.

### Description

Extend the pipeline with a full SOP execution engine that supports multi-step workflows with conditional branching, human-in-the-loop gates, and escalation rules. Add an advanced triage engine with sentiment analysis, priority scoring, and ML-assisted classification. Introduce LLM-assisted draft response generation for complex or novel ticket types that don't match existing templates.

### Deliverable

- **SOP DSL & Engine**: YAML-based workflow definitions with support for:
  - Multi-step sequences with conditional branches
  - Human-in-the-loop approval gates
  - Escalation rules (timeout-based, confidence-based, category-based)
  - Workflow versioning and rollback
- **Enhanced Triage**:
  - Sentiment analysis (positive / neutral / negative / angry)
  - Priority scoring (1–5 scale) based on urgency signals
  - ML classifier for auto-categorization (fine-tuned or zero-shot)
- **LLM Response Generator**:
  - Template fallback for known patterns
  - LLM generation for unknown patterns with confidence scoring
  - Tone/style customization per team or customer tier
- **Workflow Builder UI (minimal)**:
  - Visual SOP editor (drag-and-drop or form-based)
  - Import/export SOPs
  - Version history

### Dependencies

- Phase 1 (core ticket pipeline must be stable and tested)

### Success Criteria

- [ ] SOP engine executes ≥ 5 distinct multi-step workflows correctly
- [ ] Human-in-the-loop gates pause and resume workflows without data loss
- [ ] Escalation rules trigger correctly in ≥ 95% of test scenarios
- [ ] ML classifier accuracy ≥ 90% on held-out test set
- [ ] Sentiment analysis F1 ≥ 0.80
- [ ] LLM draft responses rated "acceptable" by ≥ 80% of human reviewers
- [ ] SOP versioning supports ≥ 3 versions per workflow with rollback
- [ ] Workflow Builder UI can create a new SOP in < 5 minutes
- [ ] Integration with at least 2 external systems (e.g., email + CRM)

---

