# Phase 6 Tasks: Compose policy + smoke for external nodes

- [x] Task 1: Resolve promoted external assets for graph/policy
  - What: Add helpers (in `external_ingest.py` or thin facade) to load `external/promoted/{id}.json`, list promoted-only assets, and map kind → graph node kind (`external_mcp` / `skill` / `software` / `mcp`). Reject missing, non-promoted, or revoked records. Path-safe ids only (reuse ingest id rules).
  - Files: `pipeline/external_ingest.py`, optional `pipeline/goal_graph.py` helpers, `test_external_ingest.py` / `test_goal_graph.py`
  - Done when: unit tests load a fixture promoted JSON and fail closed on draft/quarantined-only assets.

- [x] Task 2: `smoke_node` honesty for external kinds
  - What: Extend `smoke_graph` / `smoke_node` so nodes with kind `external_mcp` (and skill/software that declare external provenance or slug matching `external_*` / promoted id) require a **promoted** record + pin hash + presence of quarantine/promoted payload as appropriate. **Draft, quarantined, scanned, approved-but-not-promoted, revoked → smoke fail.** Never git-clone. Prefer reading Phase 5 promoted draft over inventing paths.
  - Files: `pipeline/goal_graph.py`, `test_goal_graph.py`
  - Done when: tests show promoted external node can smoke_pass presence; unpinned/draft/revoked external fails with clear issue text; no network.

- [x] Task 3: Compile / hits path for external nodes (thin)
  - What: Allow graph compile or a small helper to attach external promoted assets as route hits / nodes (e.g. `compile` with hits-json entry kind=external_mcp status=verified only if promoted, or `goal_compose` subcommand / flag to include external list). Keep max node budget. Document that deconstruct→graph still does not auto-ingest.
  - Files: `pipeline/goal_graph.py`, `scripts/goal_compose.py` (optional subcommand or hits helper), tests
  - Done when: one test builds a graph including a promoted external fixture node without calling pin/scan live.

- [x] Task 4: Policy / attempt traces with trust=external
  - What: When attempt/reuse path touches an external-promoted capability (or policy reason marks external), finalize goal_trace with `trust=external` so train_weight stays ≤ EXTERNAL_MAX (Phase 3 clamp). Do not treat external presence smoke as field_proven. Map honest outcomes (reuse success still `proven` claim but low weight if external).
  - Files: `pipeline/goal_policy.py`, `pipeline/goal_trace.py` (call only), tests
  - Done when: test asserts external-touched attempt/trace has train_weight ≤ 0.2; internal reuse unchanged.

- [x] Task 5: Docs + operator path
  - What: COMMANDS.md: after external_ingest promote, how to smoke a graph that includes external nodes; what fails if not promoted. notes/agi-lmaooo2 or master_plan Phase 6 status when implemented. Explicit: compose never clones; field dual-gate still separate.
  - Files: `COMMANDS.md`, `state/master_plan.md`, notes as needed
  - Done when: operator can go pin→…→promote→compile/hits→smoke without reading source.

- [x] Task 6: Verification suite
  - What: Focused pytest for smoke reject/pass external + policy weight + no regressions on existing goal_graph/external_ingest.
  - Files: `test_goal_graph.py`, `test_external_ingest.py`, `test_goal_policy.py` as touched
  - Done when: `python -m pytest test_goal_graph.py test_external_ingest.py test_goal_policy.py -q` passes on Windows (adjust if new module).

## Out of scope
- Auto GitHub search/clone (still out)
- Attaching external skills to executor sockets via block_registry (optional later; not required for Phase 6)
- Field dual-gate changes
- Graph engineer (Phase 8)
- Ops matrix / GitHub L1–L2 publish (Phase 7)
- Full field_prove of external assets

## Notes
- Phase 5 already produces `external/promoted/{id}.json` with provenance + compose_hint.
- Prefer dual gate honesty: smoke_pass ≠ field_proven; external proven claims stay low weight.
- Factory root paths.
