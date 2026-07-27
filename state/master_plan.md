# Master Plan: Factory capability ladder — compose, trace, external, graph

## Goal

Grow a **versioned capability map** (graph.v1) and **measurable factories** so goals compile to proven blocks, missing nodes spawn the right factory, and **traces** teach better policy — without building a second brain or unattended “download the internet.” This plan sequences remaining work after shipped foundations: goal_compose (compile / plan-factories / smoke P3 / attempt), goal_trace, troubleshoot consumer, block_registry promote, deconstructor LLM, llm_route, MCP wrap v0 / MCP factory v1.

## Foundations already shipped (do not re-implement)

| Area | Status |
|------|--------|
| Software factory → field path | Strong but **field_proven claim integrity is Phase 2** |
| goal_compose compile + critique + plan-factories + attempt + smoke P3 | v0–v1 |
| MCP factory wrap + re-smoke + revoke + invoke oracle | **Phase 1 done** |
| block_registry register→sandbox→promote→attach | v0 |
| Deconstructor LLM + schema + plan-fill | v0 |
| llm_route soft Ollama→xAI | done |
| Troubleshoot gate emit + serial consumer | v0 done |
| goal_trace.v1 + connector smoke traces | largely done; unified outcomes Phase 3 |

### How Grok Build field works today (honest)

| Path | Author of tests | Runner | Judge / status |
|------|-----------------|--------|----------------|
| **Thin field ship** (`field_ship`) | `FIELD_PLAN_ENGINE=grok` / `pipeline_llm` / heuristic / existing — **not** auto-load of skill SKILL.md | **Deterministic** `field_test_runner` | Dual gate: `field_test_passed` on runner; `field_proven` only ADEQUATE + min bars (`field_prove_gate`) |
| **Classic agents** | `field_test_planner` | runner | `ship_evaluator` ADEQUATE + re-run + min bars |
| **Interactive** | `/field-test` skill: plan → run → stop before self-proven | shell / runner | Must not claim field_proven without dual gate |

Repair bridge uses **skill-style** steps (`field_repair`) and may invoke Grok CLI with field prompts — still not the same as forcing the skill file as the only author.

## Phase 1: MCP factory v1 — real block discipline
- **Status**: **DONE** (re-smoke, revoke, invoke oracle, path safety, graph honesty)
- **Dependencies**: none

## Phase 2: Field-prove integrity — author ≠ runner ≠ evaluator
- **Status**: **DONE** (dual gate + skill + docs)
- **Description**: Stop overclaiming `field_proven`. Split **author** (plan tests), **runner** (only execution oracle), **evaluator** (adversarial adequacy of plan+results vs idea aim). Dual gate: mechanical pass ≠ product proven. Amend `/field-test` skill and thin field_ship / ship_evaluator path so Grok Build and interactive skills agree.
- **Deliverable**: `pipeline/field_prove_gate.py`; hardened `ship_evaluator`; field-test skill rewrite; field_ship status rules; min P*/I* counts; fixture tests; COMMANDS + notes.
- **Dependencies**: Phase 1 done
- **Success criteria**:
  - Runner is sole source of command pass/fail evidence
  - `field_proven` requires runner all_passed **and** evaluator ADEQUATE (closed verdict)
  - Weak plan (help/syntax-only) cannot reach field_proven in fixtures
  - `/field-test` skill cannot claim FIELD PASS without results evidence; cannot self-author and self-prove in one uncritical step
  - Docs state what field_proven does / does not mean

## Phase 3: Unified goal_trace outcomes + learning hygiene
- **Status**: **DONE** (closed outcomes + train_weight helpers; ≥3 writers; docs)
- **Description**: Extend goal_trace family so compose, promote, connector, troubleshoot recovery, field_proven events, and (later) external ingest share outcomes: `proven | failed | deeper | revoked | human_rejected` + `failure_class` + `train_weight`. Never high-weight train on untrusted external or weak field claims.
- **Deliverable**: `pipeline/goal_trace.py` helpers; wire ≥3 writers; tests; docs.
- **Dependencies**: Phase 2 preferred (so field_proven outcome is honest)
- **Success criteria**:
  - Closed outcome enum + helpers used by ≥3 writers
  - field_proven / ship_insufficient map into outcomes with sensible train_weight
  - Explicit rule: no high train_weight on untrusted external success or baseline-only field pass

## Phase 4: Deconstructor → draft graph bridge
- **Description**: Bridge deconstruct.v0 candidates into **draft** graph.v1 nodes/edges without claiming smoke_pass. Keep knowledge vs workflow separate.
- **Deliverable**: helper + CLI; fixtures; tests; skill doc.
- **Dependencies**: Phase 1–3 not hard-required
- **Success criteria**:
  - deconstruct id → draft graph under graphs/; critique runs; no auto smoke_pass
  - Domain A vs B differ

## Phase 5: External ingest manual (P5) — pin, sandbox, human gate
- **Description**: Manual path for GitHub tool/software/MCP/skill: pin → scan → quarantine → human CLI → external_* draft → smoke → promote. No unattended auto-pull.
- **Deliverable**: `pipeline/external_ingest.py` + CLI; audit log; traces; tests with fixtures.
- **Dependencies**: Phase 1; Phase 2–3 preferred
- **Success criteria**:
  - One fixture asset pin → promote under temp PIPELINE_DIR
  - Human gate required; compose never git-clones at attempt time

## Phase 6: Compose policy + smoke for external nodes
- **Description**: goal_policy / smoke_graph / attempt treat promoted external nodes with provenance + low train_weight until goal/field proven.
- **Deliverable**: policy + smoke updates; tests; docs.
- **Dependencies**: Phase 5
- **Success criteria**:
  - smoke rejects draft/unpinned external
  - traces show low train_weight by default

## Phase 7: Ops hardening — troubleshoot BE, feature matrix, GitHub L1–L2 thin
- **Description**: Matrix/docs for smoke + MCP v1 + field dual gate; optional GitHub **outputs** L1–L2 (publish), not ingest.
- **Deliverable**: matrix checks; COMMANDS; optional github_publish.
- **Dependencies**: Phases 1–2
- **Success criteria**:
  - HARD checks for dual-gate field path or documented manual
  - GitHub L1–L2 shipped thin or explicitly deferred

## Phase 8: Graph engineer thin + success-model import (later)
- **Description**: Thin graph engineer only authors into critique→resolve→smoke→attempt. Optional success-model import. No KG OS / RSI / trust stack.
- **Deliverable**: agent/CLI; import fixture; tests.
- **Dependencies**: Phases 1–6 preferred
- **Success criteria**:
  - Cannot mark smoke_pass without smoke_graph
  - One imported fixture re-smokes + traces

## Architecture Notes

```text
Field prove (Phase 2 target):
  author → field_tests.md
  runner (no LLM) → field_test_results.md  [only execution truth]
  evaluator (separate LLM, critical) → ship_evaluation.md
       verdict: ADEQUATE | NEEDS_MORE_FIELD_TESTS | SHIP_INSUFFICIENT
  field_proven := runner.all_passed AND ADEQUATE AND min product/integration bars

Grok Build thin ship (Phase 2):
  plan engine (grok CLI / pipeline_llm / none) → runner → dual gate
  field_test_passed on all_passed; field_proven only ADEQUATE + min bars
  /field-test skill: interactive plan→run→stop; not auto thin-ship author
```

## Risks

- Evaluator still soft if not adversarial + dual-gated on runner  
- Renaming statuses breaks overnight consumers — migrate carefully  
- Skill vs engine drift if only one path is fixed  
- External auto-ingest before honest field/MCP bars  

## Phase count
- total_phases: 8

## Suggested implement order

1 (done) → **2 (field integrity)** → 3 (traces) → 4 → 5 → 6 → 7 → 8
