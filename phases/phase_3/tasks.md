# Phase 3 Tasks: Unified goal_trace outcomes + learning hygiene

- [ ] Task 1: Closed outcome enum + helpers on goal_trace
  - What: Add closed outcome set (`proven | failed | deeper | revoked | human_rejected` and any already-used statuses you must map into) plus `failure_class` and `train_weight` helpers. Prefer extending `pipeline/goal_trace.py` (`finalize_trace` / new `set_outcome`) without breaking existing callers. Default train_weight rules: high only for field/goal proven-like; low/zero for draft, external-untrusted, failed.
  - Files: `pipeline/goal_trace.py`, `test_goal_trace.py` (create if missing)
  - Done when: unit tests cover set_outcome / finalize with outcome + failure_class + train_weight; KEEP_GOAL_TRACES default-on still skips disk when off.

- [ ] Task 2: Wire goal_policy attempt finalize
  - What: On `execute_policy` / attempt finalize, set structured outcome fields from success/fail/yield/mcp_enqueued (map honestly — e.g. mcp_enqueued is not `proven`). Preserve existing event stream.
  - Files: `pipeline/goal_policy.py`, `test_goal_policy.py` or extend existing policy tests
  - Done when: at least one test asserts outcome/train_weight present on a reuse or yield path; no regression in existing policy tests.

- [ ] Task 3: Wire connector_smoke + block_registry promote traces
  - What: Ensure connector smoke case finalize and block_registry promote/sandbox traces call the same outcome helpers (≥3 writers total with policy). Use failure_class when checks fail (e.g. secret_fail, smoke_fail).
  - Files: `pipeline/connector_smoke.py`, `pipeline/block_registry.py`, related tests
  - Done when: tests or assertions show promote fail and connector fail carry outcome/failure_class; pass paths set appropriate train_weight.

- [ ] Task 4: Optional MCP factory smoke/invoke/revoke trace hook
  - What: Light goal_trace (or shared outcome dict on reports) for re-smoke / invoke oracle / revoke so Phase 1 MCP work feeds the same learning schema. Keep non-LLM; skip if already covered by smoke_report only — then document why in notes.
  - Files: `pipeline/mcp_factory.py`, `test_mcp_factory.py` (optional)
  - Done when: either MCP operations emit goal_trace with outcomes, or explicit documented decision that smoke_report is the durable oracle until Phase 5.

- [ ] Task 5: Docs — external low weight + COMMANDS
  - What: Document closed outcomes, train_weight rules, and **never high-weight train on untrusted external success** (prep for Phase 4–5). Update COMMANDS.md goal_traces section; note in `notes/agi-lmaooo2.md` Layer D / learning bullets.
  - Files: `COMMANDS.md`, `notes/agi-lmaooo2.md` or short notes under `notes/`
  - Done when: operator can find outcome enum + external train_weight rule without reading source.

- [ ] Task 6: Verification suite
  - What: Run focused tests and fix regressions.
  - Files: `test_goal_trace.py`, policy/connector/block tests as touched
  - Done when: `python -m pytest test_goal_trace.py test_goal_policy.py test_block_registry.py test_mcp_factory.py -q` (adjust list to existing test files) passes on Windows.

## Out of scope
- External GitHub ingest implementation (Phase 4)
- Deconstructor → graph bridge (Phase 3)
- Corpus/finetune export merge (note only unless trivial)
- Graph engineer
- Changing troubleshoot consumer action policy

## Notes
- Factory root paths (not nested product workspace/).
- Preserve KEEP_GOAL_TRACES default-on semantics.
- Map legacy status strings carefully so old traces still load.
