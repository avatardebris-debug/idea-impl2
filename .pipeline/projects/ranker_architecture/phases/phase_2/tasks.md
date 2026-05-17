# Phase 2 Tasks

- [ ] Task 1: Domain-aware taste modeling
  - What: Implement domain management with cross-domain weight transfer. Create `DomainManager` class that organizes taste profiles by domain/category, supports domain registration, domain-to-domain weight transfer ratios, and per-domain taste vectors. Extend `TasteProfile` to carry per-domain taste vectors.
  - Files: `ranker_core/domains.py` (new), `ranker_core/profile.py` (modify to support per-domain taste vectors)
  - Done when: `DomainManager` can register domains, create per-domain taste vectors, and transfer weights between domains using configurable transfer ratios; `TasteProfile` stores and serializes per-domain vectors; unit tests verify domain isolation and cross-domain transfer

- [ ] Task 2: Persistent storage backend
  - What: Build SQLite-backed `TasteProfileStore` with migration support. Handles persistence of signals, taste profiles, and domain metadata across restarts. Includes schema versioning and migration helpers.
  - Files: `ranker_core/storage.py` (new), `ranker_core/__init__.py` (update exports)
  - Done when: `TasteProfileStore` can create/connect to a SQLite DB, persist and reload signals and profiles, run schema migrations on version bumps; integration tests verify data survives store restart and migration paths work

- [ ] Task 3: Adaptive weight decay and signal pruning
  - What: Implement exponential decay on older signals with configurable half-life per domain. Add signal pruning strategies (max signals per domain, time-based expiry). Wire decay into the aggregator so scored weights reflect signal age.
  - Files: `ranker_core/decay.py` (new), `ranker_core/pruning.py` (new), `ranker_core/aggregator.py` (modify to accept decay weights)
  - Done when: Signals decay correctly with configurable half-life (verified with time-travel tests); pruning respects configured limits (max count and time expiry); aggregator applies decay weights during scoring; unit + integration tests pass

- [ ] Task 4: Plugin interface for tool integration
  - What: Create `RankerPlugin` base class that tools can subclass to register themselves, define their domain, and emit signals. Include a plugin registry for discovery and lifecycle management. Provide two example tools as plugins.
  - Files: `ranker_core/plugins.py` (new), `examples/domain_ranking.py` (new), `examples/plugin_integration.py` (new)
  - Done when: `RankerPlugin` base class supports registration, domain binding, and signal emission; plugin registry discovers and manages plugins; at least 2 example tools register and emit signals; integration tests verify plugin lifecycle

- [ ] Task 5: REST API and web dashboard
  - What: Build FastAPI application with endpoints for signal submission, profile queries, and ranking. Create a static HTML/JS dashboard that visualizes taste profile weights and signal history.
  - Files: `ranker_core/api/__init__.py` (new), `ranker_core/api/main.py` (new), `ranker_core/api/schemas.py` (new), `ranker_core/api/routes.py` (new), `ranker_core/dashboard/index.html` (new), `ranker_core/dashboard/style.css` (new), `ranker_core/dashboard/app.js` (new)
  - Done when: API accepts signals via POST and returns profiles/rankings via GET; dashboard loads and displays profile weights and signal history; API tests verify all endpoints; dashboard renders correctly in a browser

- [ ] Task 6: Integration tests and examples
  - What: Write comprehensive integration tests covering storage persistence, domain-aware ranking, decay with time-travel, pruning limits, plugin registration, and API endpoints. Ensure ≥80% coverage. Update `__init__.py` exports.
  - Files: `tests/test_domains.py` (new), `tests/test_storage.py` (new), `tests/test_decay.py` (new), `tests/test_pruning.py` (new), `tests/test_plugins.py` (new), `tests/test_api.py` (new), `tests/test_integration.py` (new), `ranker_core/__init__.py` (update exports)
  - Done when: All integration tests pass; coverage ≥80%; examples run without errors; all Phase 2 success criteria met