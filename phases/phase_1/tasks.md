# Phase 1 Tasks: MCP factory v1 — real block discipline

- [x] Task 1: MCP re-smoke and revoke API
  - What: Add durable re-smoke (re-run smoke checks, update smoke_report + last_smoke_at) and revoke (status revoked, detach from any registry/queue use as appropriate). CLI: `re-smoke` and `revoke` subcommands on `scripts/mcp_factory.py` (or equivalent). Follow existing wrap/smoke layout under `PIPELINE_DIR/mcps/`.
  - Files: `pipeline/mcp_factory.py`, `scripts/mcp_factory.py`, `test_mcp_factory.py`
  - Done when: pytest covers re-smoke pass/fail and revoke; CLI `--help` lists new commands; revoked MCP is not treated as smoked for list/smoke_graph.

- [x] Task 2: MCP invoke oracle (cheap)
  - What: Beyond ping/describe, define a cheap invoke oracle (e.g. invoke with `--help` or fixture args) that records pass/fail + evidence in smoke_report or sibling invoke_report. Do not invent product code; wrap existing capability_tools invoke path.
  - Files: `pipeline/mcp_factory.py`, `scripts/mcp_factory.py`, `test_mcp_factory.py`
  - Done when: one automated test proves invoke oracle success and failure paths without live overnight; report JSON on disk under mcps/{slug}/.

- [x] Task 3: Wire graph smoke to MCP block honesty
  - What: Update `smoke_node` / docs so MCP nodes prefer invoke-oracle or re-smoke report when present; keep cheap presence fallback documented. Path-safe slugs already required — do not regress.
  - Files: `pipeline/goal_graph.py`, `test_goal_graph.py`, `COMMANDS.md`
  - Done when: tests show MCP with failed/missing invoke/smoke fails graph smoke; smoked+invoke-ok can pass; COMMANDS.md distinguishes presence vs invoke.

- [x] Task 4: Provenance / version fields on MCP manifest
  - What: Ensure mcp_manifest.v1 (or adjacent) carries capability_slug, content or wrap version, last_smoke_at, optional content hash; re-smoke updates timestamps. Minimal — no full supply-chain product.
  - Files: `pipeline/mcp_factory.py`, `test_mcp_factory.py`
  - Done when: wrap + re-smoke leave stable fields tests can assert; schema version documented in module docstring.

- [x] Task 5: Docs + feature matrix smoke check
  - What: COMMANDS.md MCP + goal_compose smoke section updated for v1. Optionally add one HARD check to `scripts/factory_feature_matrix.py` for re-smoke or revoke in isolated temp PIPELINE_DIR (skip if matrix already oversized — then document manual command instead).
  - Files: `COMMANDS.md`, `scripts/factory_feature_matrix.py` (optional), `notes/agi-lmaooo2.md` (P4 status)
  - Done when: operator can follow COMMANDS for wrap → smoke → invoke → re-smoke → revoke; notes P4 marked in progress or v0 partial with honest bullets.

- [x] Task 6: Verification suite
  - What: Run focused tests and fix regressions.
  - Files: `test_mcp_factory.py`, `test_goal_graph.py`, related
  - Done when: `python -m pytest test_mcp_factory.py test_goal_graph.py -q` passes on Windows workspace.

## Out of scope
- External GitHub auto-ingest (Phase 4 of master plan)
- Graph engineer product (Phase 7)
- Full field_prove for every MCP
- Software factory seed from plan-factories handoffs
- Changing troubleshoot consumer behavior (already complete)
- Unattended Ollama model pulls

## Notes
- Factory root = this repo; paths are relative to factory root (not a nested workspace/ product tree).
- Prefer soft llm_route only if any agent is added; MCP factory v1 should stay mostly non-LLM.
- Keep MCP factory loop separate from software factory and from goal_compose (compose only triggers enqueue).
