# Master Plan: Factory capability ladder — compose, trace, external, graph

## Goal

Grow a **versioned capability map** (graph.v1) and **measurable factories** so goals compile to proven blocks, missing nodes spawn the right factory, and **traces** teach better policy — without building a second brain or unattended “download the internet.” This plan sequences remaining work after shipped foundations: goal_compose (compile / plan-factories / smoke P3 / attempt), goal_trace, troubleshoot consumer, block_registry promote, deconstructor LLM, llm_route, MCP wrap v0.

## Foundations already shipped (do not re-implement)

| Area | Status |
|------|--------|
| Software factory → field_prove | Strong |
| goal_compose compile + critique + plan-factories + attempt policy | v0–v1 |
| Whole-graph smoke P3 (cheap presence) | v0 done |
| MCP factory wrap + queue + smoke report | v0 |
| block_registry register→sandbox→promote→attach | v0 |
| Deconstructor LLM + schema + plan-fill | v0 |
| llm_route soft Ollama→xAI | done |
| Troubleshoot gate emit + serial consumer | v0 done |
| goal_trace.v1 + connector smoke traces | largely done |

## Phase 1: MCP factory v1 — real block discipline
- **Description**: Promote MCP from “wrap once + smoke ping” to a first-class block: re-smoke on demand, revoke, real **invoke** oracle (not only describe), version/provenance fields, graph smoke may optionally use invoke when cheap.
- **Deliverable**: `pipeline/mcp_factory.py` + CLI + tests; graph smoke can report mcp invoke result when configured; COMMANDS.md.
- **Dependencies**: none (builds on MCP v0 + smoke P3)
- **Success criteria**:
  - `mcp_factory` supports re-smoke, revoke, and at least one invoke-oracle path with durable report
  - Tests cover wrap → smoke → invoke → revoke without live overnight
  - goal_compose / smoke_graph docs note when MCP smoke is presence-only vs invoke-oracle

## Phase 2: Unified goal_trace outcomes + learning hygiene
- **Description**: Extend goal_trace family so compose, promote, connector, troubleshoot recovery, and (later) external ingest share outcomes: `proven | failed | deeper | revoked | human_rejected` + `failure_class` + `train_weight`. Document that unverified external “success” stays low weight.
- **Deliverable**: `pipeline/goal_trace.py` (or sibling) schema helpers; wire key writers (goal_policy, connector_smoke, block_registry promote); short notes + tests; optional corpus export hook note.
- **Dependencies**: Phase 1 optional (can parallel after P1 starts; prefer after MCP oracles exist so traces have better evidence)
- **Success criteria**:
  - Closed outcome enum + helpers used by ≥3 writers
  - Attempt / smoke / promote traces include outcome fields without breaking KEEP_GOAL_TRACES default-on
  - Explicit rule in docs: no high train_weight on untrusted external success

## Phase 3: Deconstructor → draft graph bridge
- **Description**: Bridge deconstruct.v0 candidates into **draft** graph.v1 nodes/edges (knowledge inventory → map candidates), without claiming production/smoke_pass. Optional plan-fill → enqueue hints for skill/MCP/factory. Keep knowledge vs workflow graphs separate.
- **Deliverable**: `pipeline/deconstructor.py` or `goal_graph.py` helper + CLI (`deconstructor plan-graph` or `goal_compose from-deconstruct`); fixtures; tests; skill doc update.
- **Dependencies**: Phase 1–2 not hard-required; use after deconstructor LLM is stable (already)
- **Success criteria**:
  - Given a saved deconstruct id, emit draft graph under graphs/ with closed kinds + oracle_hint → oracle stubs
  - Critique runs; status never smoke_pass without separate smoke
  - Domain A vs B produce different node names (not fixed studio template)

## Phase 4: External ingest manual (P5) — pin, sandbox, human gate
- **Description**: First **manual** path for downloaded GitHub tool/software/MCP/skill: find (human-supplied URL/path) → pin commit/hash → static scan → license note → quarantine dir → sandbox checks → human CLI approve → `external_*` draft → smoke → promote. No unattended auto-pull. Audit log under PIPELINE_DIR.
- **Deliverable**: `pipeline/external_ingest.py` (or similar) + `scripts/external_ingest.py` CLI; quarantine layout; goal_trace events for pin/scan/approve; tests with fixtures (no live GitHub required).
- **Dependencies**: Phase 1 (MCP block bar); Phase 2 preferred (trace outcomes)
- **Success criteria**:
  - One fixture “external” asset can go pin → draft → smoke → promote under temp PIPELINE_DIR
  - Human gate required before promote; audit log written
  - Graph can reference `external_mcp` only after promote; compose does not git-clone at attempt time

## Phase 5: Compose policy + smoke for external nodes
- **Description**: goal_policy / goal_compose treat promoted external nodes like other legos for reuse/mcp; smoke_graph handles external_mcp with same path safety + provenance checks; attempt traces mark external provenance and low train_weight until goal_proven.
- **Deliverable**: updates to `goal_policy.py`, `goal_graph.py` smoke_*, `goal_compose` docs; tests.
- **Dependencies**: Phase 4
- **Success criteria**:
  - attempt/reuse path can invoke or fail closed on external node with clear status
  - smoke_graph rejects unpinned or draft external
  - goal_trace shows provenance + train_weight default low

## Phase 6: Ops hardening — troubleshoot BE handoffs, feature matrix, GitHub L1–L2 thin
- **Description**: Tighten overnight path: document/confirm troubleshoot consumer ↔ BE ladder handoffs; extend factory_feature_matrix for smoke + MCP v1 + optional external fixture; thin **GitHub support for factory project outputs** (L1 local git / L2 push) as **publish surface**, not ingest — only if cheap and separate from P4–P5.
- **Deliverable**: matrix checks; COMMANDS overnight section; optional `github_publish` hardening; no auto-ingest.
- **Dependencies**: Phases 1–2 primarily; Phase 4 optional
- **Success criteria**:
  - feature_matrix HARD checks include graph smoke CLI and MCP re-smoke/revoke when isolated
  - Documented order: ladder → troubleshoot consumer → thin field (already code; docs/tests stay green)
  - GitHub L1–L2 either shipped thin or explicitly deferred in Out of scope with reason

## Phase 7: Graph engineer thin + success-model import (later)
- **Description**: Thin **graph engineer** that only authors/revises graphs into the existing pipeline (critique → resolve → smoke → attempt). Optional import of a small “success model” / credits fixture graph with gold oracles. No full KG OS, no RSI primary driver, no open-world trust stack.
- **Deliverable**: agent or CLI that proposes graph.v1 diffs under budget; import fixture; tests; notes update.
- **Dependencies**: Phases 1–5 preferred (blocks trustworthy)
- **Success criteria**:
  - Engineer cannot mark smoke_pass without calling smoke_graph
  - At least one imported fixture graph re-smokes and attempt traces
  - Explicit non-goals listed (trust/funds/captcha, god meta-evaluator, nest-system-as-only-tool)

## Architecture Notes

```text
Goal / need
  → (optional) deconstructor LLM → deconstruct.v0 candidates
  → (optional) external ingest P5 → pin/scan/human → external_* promote
  → goal_compose compile → critique → plan-factories (MCP queue / software handoff)
  → resolve nodes (verified only or enqueue)
  → smoke_graph (cheap → later invoke oracles)
  → attempt: classify reuse|compose|build|research|mcp|yield → execute + goal_trace
  → overnight: field ship → troubleshoot emit → consumer re-arm/yield → BE ladder
```

- **Closed lego kinds:** `software | connector | skill | prompt | mcp | external_mcp | human | research`  
- **Factories stay separate loops** — graph triggers, does not reimplement.  
- **llm_route:** soft Ollama if model present else xAI from `.env` on workstations.  
- **Knowledge vs workflow graphs** stay separate until goal_proven packaging.  
- Plans and tasks live under `state/` and `phases/` of this factory repo (meta-roadmap), not under `workspace/`.

## Risks

- External auto-ingest before strong MCP/skill smoke → supply-chain thrash  
- Softening graph smoke to “presence only” forever → map of fiction  
- Graph engineer before sockets/smoke → architecture cosplay  
- Over-merging deconstructor, compose, and Hermes into one god agent  
- High train_weight on unverified external successes  
- Shared PIPELINE_DIR races during overnight + manual ingest  
- Scope creep into RSI / mandate / open-world trust in this ladder  

## Phase count
- total_phases: 7

## Suggested implement order

1 → 2 (or 2 slightly after 1) → 3 → 4 → 5 → 6 → 7  

Parallelism only: Phase 3 can start after deconstructor exists (now); Phase 6 docs/matrix can track 1–2. **Do not** start Phase 4 unattended pull before Phase 1 MCP bar.
