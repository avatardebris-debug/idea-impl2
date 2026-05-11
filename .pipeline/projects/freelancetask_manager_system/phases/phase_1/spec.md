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