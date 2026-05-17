## Phase 2 — Persistence, Domains & Adaptive Weights

**Goal:** Add domain-aware taste modeling, persistent storage, adaptive weight decay, and a plugin interface for tool integration.

### Description

Build on Phase 1 with production-quality features:
- **Domain-aware profiles:** Taste profiles organized by domain/category with cross-domain weight transfer
- **Persistent storage:** SQLite-backed TasteProfileStore with migration support
- **Adaptive weights:** Exponential decay on older signals; configurable half-life per domain
- **Signal pruning:** Configurable retention (max signals per domain, time-based expiry)
- **Plugin interface:** `RankerPlugin` base class for tools to register themselves and emit signals
- **REST API:** FastAPI-based HTTP endpoint for remote signal submission and profile queries
- **Dashboard:** Simple web dashboard (HTML/JS) showing taste profile visualization and signal history

### Deliverable

Extensions to `ranker_core/`:
- `ranker_core/domains.py` — Domain management, cross-domain weight transfer
- `ranker_core/storage.py` — SQLite storage backend with migrations
- `ranker_core/decay.py` — Exponential decay and half-life configuration
- `ranker_core/pruning.py` — Signal pruning strategies
- `ranker_core/plugins.py` — RankerPlugin base class and registration
- `ranker_core/api/` — FastAPI application (signal submission, profile queries, ranking)
- `ranker_core/dashboard/` — Static dashboard with profile visualization
- `tests/` — Integration tests, storage tests, API tests
- `examples/domain_ranking.py` — Example: multi-domain taste modeling
- `examples/plugin_integration.py` — Example: custom tool plugin

### Dependencies

- Phase 1 (ranker_core core)
- SQLite (bundled with Python)
- FastAPI + uvicorn (for API)
- Minimal JS/CSS for dashboard (no framework)

### Success Criteria

- [ ] Taste profiles persist across restarts (SQLite)
- [ ] Domain-aware profiles produce distinct rankings per domain
- [ ] Signal decay works correctly (verify with time-travel tests)
- [ ] Signal pruning respects configured limits
- [ ] At least 2 example tools can register as plugins and emit signals
- [ ] API accepts signals and returns profiles/rankings
- [ ] Dashboard displays profile weights and signal history
- [ ] Integration tests pass (≥80% coverage)

---

