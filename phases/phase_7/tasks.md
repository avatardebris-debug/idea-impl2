# Phase 7 Tasks: Ops hardening — matrix, troubleshoot docs, GitHub L1–L2 thin

- [x] Task 1: Feature matrix HARD checks for ladder surfaces
  - What: Extend `scripts/factory_feature_matrix.py` isolated HARD checks (temp PIPELINE_DIR) for recent ladder work without live overnight: (a) goal_compose smoke CLI or `smoke_graph` on a tiny verified fixture graph; (b) dual-gate field status — runner-only green stays `field_test_passed` not `field_proven` without ADEQUATE (use `decide_field_status` / field_prove_gate, no full ship run if heavy); (c) optional thin external: pin→scan→approve→promote fixture then resolve_promoted/smoke external node, or document skip if matrix size is a concern. Keep checks fast and Windows-safe.
  - Files: `scripts/factory_feature_matrix.py`, optional tiny fixtures under tests or in-matrix temp dirs
  - Done when: `python scripts/factory_feature_matrix.py` exit 0 with new HARD ids listed; each check has clear PASS/FAIL detail string.
  - Met: HARD ids `smoke_graph_fixture`, `dual_gate_field_status`, `external_promote_smoke` (temp fixtures under PIPELINE_DIR).

- [x] Task 2: Troubleshoot + health-tick operator docs accuracy
  - What: Verify COMMANDS.md matches code order (BE ladder → troubleshoot consumer limit 1 → prefer_thin with preferred_slugs). Add/refresh a short “ops map” of statuses (`ship_insufficient`, `field_test_passed`, `field_proven`, recovery actions). No consumer behavior rewrite unless a doc/code mismatch is a real bug (then minimal fix only).
  - Files: `COMMANDS.md`, `pipeline/run_loop.py` (read-only unless bug), `pipeline/troubleshoot_consumer.py` (read-only unless bug)
  - Done when: COMMANDS documents env flags, order, and what auto-acts vs escalates; no false claims about field_proven from runner alone.
  - Met: COMMANDS health-tick order + ops status map; code order verified in `run_loop.py` (no behavior change).

- [x] Task 3: GitHub L1–L2 for factory **outputs** (thin or defer)
  - What: Audit `pipeline/github_publish.py` + ship_evaluator hook. Either: (L1) ensure local git commit of `projects/<slug>/` works when enabled and is tested/documented, and (L2) optional push when `PIPELINE_GITHUB_PUBLISH=1` stays fail-soft; **or** explicitly defer L2 in master_plan/COMMANDS with reason and keep L1 docs only. Do **not** build ingest (that’s Phase 5). Do not require live GitHub network in tests (mock/subprocess dry-run or unit pure helpers).
  - Files: `pipeline/github_publish.py`, `COMMANDS.md`, optional `test_github_publish.py`, `state/master_plan.md`
  - Done when: either thin L1 (and optional L2 env) is documented + at least one unit test on pure helpers, **or** explicit “deferred” bullets in master plan Phase 7 success criteria notes and COMMANDS.
  - Met: L1+L2 thin shipped; pure helper + L2 fail-soft unit tests; COMMANDS L1/L2 table.

- [x] Task 4: Overnight / matrix smoke script note for operators
  - What: Short COMMANDS subsection: preflight matrix before overnight; dual-gate env `FIELD_SHIP_DUAL_GATE`; external promote then `--include-external` smoke. Link to existing overnight_grok_from_list if present without rewriting overnight PS1 unless broken.
  - Files: `COMMANDS.md`, optionally one line in `scripts/overnight_grok_from_list.ps1` comments
  - Done when: operator can follow docs to run matrix + understand field/external gates before a long run.
  - Met: COMMANDS overnight preflight steps 1–4; overnight PS1 header comment.

- [x] Task 5: Master plan Phase 7 close-out + verification
  - What: Mark Phase 7 DONE when criteria met; set `current_idea.json` phase→8. Run matrix + a small pytest subset if new tests added.
  - Files: `state/master_plan.md`, `state/current_idea.json`, `phases/phase_7/tasks.md`
  - Done when: `python scripts/factory_feature_matrix.py` exit 0; any new unit tests pass on Windows.

## Out of scope
- Graph engineer product (Phase 8)
- Unattended external auto-pull
- Changing field dual-gate core logic (Phase 2) except matrix checks
- Full BE3 product / dropbox redesign
- RSI / trust / captcha stacks

## Notes
- Prefer documenting deferrals over half-broken GitHub push in CI without credentials.
- Matrix stays isolated (temp PIPELINE_DIR) for HARD checks; `--live` remains optional soft.
- Factory root paths.
