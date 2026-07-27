# Phase 2 Tasks: Field-prove integrity — author ≠ runner ≠ evaluator

- [x] Task 1: Dual-gate status semantics in ship path
  - What: Define clear statuses: mechanical `field_test_passed` (runner all_passed) vs `field_proven` (runner pass **and** evaluator ADEQUATE + min product/integration counts). Update thin `field_ship` so runner green alone does not set `field_proven` when evaluator is enabled (env flag default on for new honesty, or always-on if tests allow). Preserve classic agent path consistency with `ship_evaluator`.
  - Files: `pipeline/engines/field_ship.py`, `pipeline/agents/ship_evaluator.py`, `pipeline/ship_provenance.py` or maturity helpers, related tests
  - Done when: tests show runner-only pass does not yield field_proven without ADEQUATE; runner fail cannot be overridden to field_proven by LLM text alone.

- [x] Task 2: Adversarial field adequacy evaluator (harden ship_evaluator)
  - What: Prompt + parse closed verdicts: `ADEQUATE` | `NEEDS_MORE_FIELD_TESTS` | `SHIP_INSUFFICIENT` (map to existing verdicts if needed). Evaluator must assume overclaim; reject baseline/help-only plans as insufficient for product aim. Re-run or require durable `field_test_results.md` evidence. Do not let evaluator invent command passes.
  - Files: `pipeline/agents/ship_evaluator.py`, `pipeline/prompts/ship_evaluator.md` (create if missing), `pipeline/engines/prompts/` if thin path uses a pack, tests
  - Done when: fixture or unit test with weak field_tests.md + green runner-like results → not FIELD_PROVEN / ADEQUATE; strong plan + real pass structure → ADEQUATE allowed.

- [x] Task 3: Minimum product/integration bars
  - What: Enforce minimum counts (e.g. ≥N product P* and ≥M integration I* with non-trivial Expect) before ADEQUATE/`field_proven`. Document constants. Baseline B* never sufficient alone.
  - Files: `pipeline/field_test_runner.py` or shared `pipeline/field_prove_gate.py`, field_ship, ship_evaluator, tests
  - Done when: test rejects empty/baseline-only plan for proven claim.

- [x] Task 4: Amend `/field-test` skill (user + factory copy if any)
  - What: Rewrite skill workflow: (1) plan only, (2) run via commands/runner only, (3) stop before self-judging proven — require results file + optional handoff to evaluator / explicit dual-gate language. Forbid treating “wrote field_tests.md” as FIELD PASS. Note Grok Build thin ship uses plan engines, not always this skill — skill is interactive + repair style.
  - Files: `C:\Users\avata\.grok\skills\field-test\SKILL.md` (and `references/` if present); mention in factory `COMMANDS.md` or notes
  - Done when: skill text has explicit three-step separation and dual-gate claim rules; no single-step “done when file exists”.

- [x] Task 5: Thin field_ship + repair docs alignment
  - What: Document FIELD_PLAN_ENGINE vs `/field-test` skill; ensure repair path cannot promote field_proven without dual gate. Update COMMANDS.md ship/field section and `notes/agi-lmaooo2.md` field row honesty.
  - Files: `COMMANDS.md`, `notes/agi-lmaooo2.md`, `pipeline/engines/field_ship.py` comments if needed
  - Done when: operator docs state author/runner/evaluator split and overclaim risk.

- [x] Task 6: Verification suite
  - What: Add/adjust tests for dual gate + weak plan; run focused pytest.
  - Files: `test_field_ship.py` / `test_ship_evaluator.py` / new `test_field_prove_gate.py` as appropriate
  - Done when: `python -m pytest` on new/touched field-prove tests passes on Windows; no regression in field_test_runner baseline tests if present.

## Out of scope
- Full re-plan of classic multi-agent overnight topology
- External ingest (Phase 5)
- goal_trace outcome enum bulk (Phase 3) — only minimal hooks if required for dual gate
- Human push notifications for field_proven
- Graph engineer

## Notes
- Grok Build **does not always** load the field-test skill file; thin ship uses `field_test_plan` prompt via grok CLI / pipeline_llm. Fix **both** skill and engine paths.
- Runner remains non-LLM. Evaluator is separate LLM role with closed verdicts.
- Factory root paths.
