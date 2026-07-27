# Phase 4 Tasks: Deconstructor → draft graph bridge

- [ ] Task 1: deconstruct.v0 → draft graph.v1 converter
  - What: Implement a pure function that maps a deconstruct document’s candidates (and optional departments) into a **draft** graph.v1: closed NODE_KINDS via CLASS_TO_GRAPH_KIND / replacement_class, oracle stubs from oracle_hint, edges from parent_id hierarchy (or sequential control). Never set smoke_pass or status smoke_pass/executable from this path alone—status stays `draft` or `critiqued` after critique_graph.
  - Files: `pipeline/deconstructor.py` and/or `pipeline/goal_graph.py`, `test_deconstructor.py` or `test_goal_graph.py`
  - Done when: unit tests convert a fixture deconstruct with 2+ levels into nodes/edges; critique can run; graph["smoke_pass"] is false/absent; production_graph never true.

- [ ] Task 2: CLI entrypoint
  - What: Add CLI: e.g. `python scripts/deconstructor.py to-graph --id <deconstruct_id>` and/or `python scripts/goal_compose.py from-deconstruct --id ... --goal-id ...`. Save under `PIPELINE_DIR/graphs/{goal_id}.json`. Support optional --goal-id / --goal-text.
  - Files: `scripts/deconstructor.py`, `scripts/goal_compose.py` (one or both), tests
  - Done when: CLI round-trip with temp PIPELINE_DIR writes graph file; exit 0 when critique ok or soft-ok draft; documents that smoke is a separate step.

- [ ] Task 3: Domain difference fixture
  - What: Two deconstruct fixtures (e.g. hospital vs law-firm structured or inject LLM JSON) produce draft graphs with **different** node name sets—no shared fake studio template leakage.
  - Files: tests, optional fixtures under tests or temp in-test
  - Done when: assert name sets differ; both are draft only.

- [ ] Task 4: Optional plan-fill → factory hints
  - What: Lightly attach plan_fill_actions summary or enqueue notes on the graph (metadata / notes field)—do **not** auto-wrap MCP or seed software. Optional only if cheap.
  - Files: converter module, docs
  - Done when: either metadata present in tests or explicitly documented as deferred in Out of scope with reason.

- [ ] Task 5: Docs + skill
  - What: Update `.grok/skills/deconstructor/SKILL.md` and COMMANDS.md: after deconstruct, `to-graph` → then `goal_compose smoke` separately. Master plan Phase 4 status when done.
  - Files: `.grok/skills/deconstructor/SKILL.md`, `COMMANDS.md`, `state/master_plan.md`
  - Done when: operator path is clear; skill says draft graph ≠ smoke_pass.

- [ ] Task 6: Verification
  - What: Run focused tests.
  - Files: touched tests
  - Done when: `python -m pytest test_deconstructor.py test_goal_graph.py -q` passes (adjust if new test module).

## Out of scope
- Auto smoke_pass on convert
- External GitHub ingest (Phase 5)
- Graph engineer product (Phase 8)
- Merging knowledge graph with workflow graph
- Auto MCP wrap from deconstruct leaves

## Notes
- Keep knowledge inventory vs production workflow separate: this phase emits **candidate map**, not proven runtime.
- Factory root paths.
- Prefer reuse of CLASS_TO_GRAPH_KIND already in deconstructor.py.
