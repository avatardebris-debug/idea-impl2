## Phase 3 — Preset Library & Settings Selection UI

**Goal:** A full preset management system with a browsable library, settings selector, and polished UX.

**Description:**
- Build a **preset library/database** (SQLite-backed) with:
  - CRUD operations for presets
  - Tagging and categorization (e.g., "training", "inference", "rendering")
  - Search and filtering
  - Import/export (YAML, JSON, template sharing)
- Add a **settings selector interface**:
  - Browse presets by category/tag
  - Override individual settings per launch (e.g., change GPU type or count on the fly)
  - Preview what the launch will do before executing
- Add **template system**:
  - Base templates for common use cases (PyTorch training, Stable Diffusion, etc.)
  - Template inheritance (override specific fields)
- Add **scheduling** (optional):
  - Schedule batch launches at specific times
  - Recurring schedules
- **Polish the UX:**
  - Rich CLI tables, color-coded status
  - Optional web dashboard (FastAPI + simple frontend) for remote management
  - History of past launches with one-click re-launch

**Deliverable:**
- Full preset library with CRUD, search, tags, and templates.
- Settings selector interface (CLI or web).
- Optional scheduling and web dashboard.
- Polished, production-ready CLI/UX.

**Dependencies:**
- Phase 2 (batch orchestrator, preset format)
- VAST.ai API for any scheduling-related features

**Success Criteria:**
- [ ] Can create, edit, delete, tag, search, and export presets
- [ ] Can browse presets and select settings via a clean interface
- [ ] Can override preset settings per-launch without modifying the stored preset
- [ ] Templates work with inheritance and override
- [ ] Launch history is queryable and supports re-launch
- [ ] UX is polished (tables, colors, progress indicators)
- [ ] Web dashboard (if included) is functional and accessible

**Estimated Effort:** 4–6 weeks

---

## 4. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| VAST.ai API changes or instability | High | Abstract the API adapter behind an interface; write integration tests; cache responses where possible |
| API rate limits during batch launches | Medium | Implement exponential backoff; respect documented rate limits; add configurable concurrency |
| GPU availability on VAST.ai fluctuates | Medium | Add retry logic with configurable backoff; report specific availability errors; allow price-based filtering |
| Preset validation complexity | Medium | Start with a strict schema (Pydantic or jsonschema); expand validation rules incrementally |
| Authentication credential management | High | Use OS keyring or encrypted config file; never log credentials; support API key rotation |
| CLI UX becomes unwieldy with many commands | Low | Use subcommand structure (`vastai-init preset list`, `vastai-init batch launch`); keep help text concise |
| Web dashboard scope creep | Low | Defer web UI to a separate project or optional module; keep CLI as the 