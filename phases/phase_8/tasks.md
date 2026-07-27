# Phase 8 Tasks: Graph engineer thin + success-model import

- [x] Task 1: Thin graph engineer API (no invent outside pipeline)
  - What: Add a pure/CLI path that authors or revises a **draft** graph.v1 only through existing gates: load/save graph, critique_graph, optional compile_graph_from_deconstruct or compile_goal_graph with hits. Must **not** set smoke_pass or field_proven. Engineer output status stays draft/critiqued/blocked until separate smoke. Prefer `pipeline/goal_graph.py` helpers + `scripts/goal_compose.py engineer` or `scripts/graph_engineer.py`.
  - Files: `pipeline/goal_graph.py` and/or new thin module, scripts, tests
  - Done when: unit test creates/revises a graph via engineer helper; assert smoke_pass is never true from engineer alone; critique runs.
  - Met: `pipeline/graph_engineer.py` `engineer_author` / `engineer_revise`; CLI `scripts/graph_engineer.py` + `goal_compose engineer`; tests in `test_graph_engineer.py`.

- [x] Task 2: Enforce smoke before claim of executable/smoke_pass
  - What: Any engineer “finalize” or CLI that would set status executable/smoke_pass must call `smoke_graph` (or refuse). Document fail-closed if smoke fails.
  - Files: engineer CLI/module, `test_goal_graph.py`
  - Done when: test shows engineer cannot mark smoke_pass without going through smoke_graph; failed smoke leaves smoke_failed/blocked.
  - Met: `engineer_finalize` always calls `smoke_graph`; refuse field_proven; fail-closed tests.

- [x] Task 3: Success-model / fixture import
  - What: Import one small fixture graph (e.g. JSON under tests/fixtures or generate from deconstruct fixture) representing a success-model inventory; load, critique, smoke (with mocked/temp verified stubs as needed), write goal_trace or document attempt optional. Keep knowledge vs workflow separate.
  - Files: fixture file, import helper, tests
  - Done when: one imported fixture re-smokes under temp PIPELINE_DIR and produces durable graph + optional trace.
  - Met: `tests/fixtures/success_model_inventory.json` + `import_success_model` + stubs + optional trace.

- [x] Task 4: Explicit non-goals + docs
  - What: COMMANDS + master_plan Phase 8: engineer authors into critique→resolve→smoke→attempt only. Non-goals: trust/funds/captcha, RSI primary, nest-system-as-only-tool, unattended external pull.
  - Files: `COMMANDS.md`, `state/master_plan.md`, skill note if useful
  - Done when: operator path is clear; non-goals listed.
  - Met: COMMANDS Phase 8 section; master_plan Phase 8 DONE + non-goals; current_idea ladder_complete.

- [x] Task 5: Verification
  - What: pytest focused suite + optional matrix soft check if cheap.
  - Files: tests
  - Done when: relevant pytest passes; `python scripts/factory_feature_matrix.py` still exit 0 (no regression).
  - Met: `test_graph_engineer.py` + matrix run at close-out.

## Out of scope
- Full KG OS / multi-agent graph product
- Auto external GitHub discovery
- Changing field dual-gate or troubleshoot consumer policy
- High train_weight on untrusted external

## Notes
- Prefer reusing compile_graph_from_deconstruct + smoke_graph rather than a new LLM-heavy agent unless thin `call_llm_direct` plan is optional and tested with inject.
- Factory root paths.
