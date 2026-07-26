# Goal compose policy + MCP factory v0 + agi-lmaooo work-ahead

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Evolve thin goal compose policy into a durable goal to plan to execute to oracle loop, add a **separate** MCP factory v0 that wraps verified capabilities as MCP servers, and land a minimal graph store so missing nodes can trigger the right factory without building a full KG/MCP OS.

**Architecture:** Keep factories as separate loops (software already exists; MCP is new). Goal policy classifies reuse | compose | build | research | yield | mcp. A tiny versioned graph under {PIPELINE_DIR}/graphs/ is the map (not the mind). Execution stays dumb and measured via goal_trace.v1 + oracles. MCP factory is a CLI loop that scaffolds one MCP per verified capability, smokes it, and registers kind:mcp triggered by policy/graph enqueue, never inventing servers inside run_loop.

**Tech Stack:** Python 3.11+, pipeline/goal_policy.py, goal_trace.py, goal_attempt.py, capability_tools.py, capability_registry.py, scripts/mcp_capability_server.py, pytest, PIPELINE_DIR.

**North star:** notes/agi-lmaooo.md
**Prior audit:** notes/2026-07-26-comprehensive-codebase-review.md
**Repo copy after exit plan mode:** docs/superpowers/plans/2026-07-26-goal-compose-mcp-factory-v0.md

---

## Consistency with prior notes (anti-drift)

This plan must stay **compatible** with existing factory notes. Implementers should re-read these before expanding scope.

| Note | What it locks | How this plan stays compatible |
|------|----------------|--------------------------------|
| [notes/agi-lmaooo.md](notes/agi-lmaooo.md) | North star: goals ask; compose wires; build fills holes; oracles judge; traces teach. Stages v0–v3. | This plan **is** agi-lmaooo v1 graph store + v2 MCP factory slice. Closed lego enum. Factories remain separate loops. |
| [notes/2026-07-22-p1-held-out-and-goal-traces.md](notes/2026-07-22-p1-held-out-and-goal-traces.md) | Canary ≠ product connector proof; goal_trace.v1 schema; backward chain goal_proven ← field_proven bricks ← harness canary | Reuse goal_trace.v1; MCP smoke is canary-class proof for MCP legos, not substitute for software field_proven. Held-out later may add H-case for MCP smoke (not in T0–T5). |
| [notes/2026-07-23-budget-ladder-trust-and-status.md](notes/2026-07-23-budget-ladder-trust-and-status.md) | Deferred: full KG / **graph engineer** / graph field-goal prove; Grok Workflows (Rhai) not earned; open-world trust/money later; serial factory focus | **Graph engineer product = non-goal here** (matches § deferred). Tiny graph.v1 store is *data*, not a graph-engineer agent. Do not wire mandate/trust stack. Do not embed Rhai as compose engine. |
| [notes/2026-07-18-operator-approach-fail-forward-stack.md](notes/2026-07-18-operator-approach-fail-forward-stack.md) | Volume + fail-forward; multi-identity factory; replace-yourself ladder; RSI is data engine later | MCP factory v0 is another factory identity (wrap layer), not a flagship product detour. Keep serial, measured, ugly-then-oracle. |
| [notes/2026-07-19-grok-build-factory-dual-engine-plan.md](notes/2026-07-19-grok-build-factory-dual-engine-plan.md) | classic + grok_build dual engine; software field_prove stays core | MCP wrap assumes **existing** verified software capabilities; does not replace dual-engine implement path. |
| [notes/2026-07-22-overnight-grok-from-list-runbook.md](notes/2026-07-22-overnight-grok-from-list-runbook.md) | Overnight preflight/canary; shared PIPELINE_DIR bus | T7 soft MCP drain only; never block overnight on MCP HARD fail. Keep traces for reboot recovery (already in overnight script). |
| [notes/2026-07-26-comprehensive-codebase-review.md](notes/2026-07-26-comprehensive-codebase-review.md) | PIPELINE_DIR path model; capability cwd fixes | All new MCP/graph paths under get_pipeline_dir(); reuse resolve_capability_workdir / no factory .pipeline hardcoding. |
| [notes/2026-07-18-github-tools-discovery-and-orca-bridge.md](notes/2026-07-18-github-tools-discovery-and-orca-bridge.md) | Tool discovery deferred; Hermes vs registry | Policy research still Hermes; reuse/compose stay registry/capability_tools. External MCP catalog = v3 later, not v0. |
| [notes/2026-07-18-orca-and-grok-integration.md](notes/2026-07-18-orca-and-grok-integration.md) | Orca ADE not agent factory; worktree isolation | MCP servers are stdio local wrappers under PIPELINE_DIR/mcps — not Orca rewrite. |

### Vocabulary lock (from budget-ladder note §7)

| Term | Meaning in this plan |
|------|----------------------|
| **workflow / connector** | Factory YAML + run_workflow / compose policy |
| **Grok Workflows (Rhai)** | Deferred enhancement — **not** the v0 compose engine |
| **graph.v1** | Versioned JSON under graphs/ — representation only |
| **graph engineer** | Future agent/product that authors large graphs — **out of scope**; may consume graph.v1 later |
| **MCP factory** | Separate loop wrapping verified capabilities — peer to software factory, not a replacement |

### Compatibility rules for implementers

1. Do not invent a graph-engineer agent, field-prove-the-graph product, or knowledge-graph OS in this epic.
2. Do not soft-skip requires: or weaken field_proven as world nodes.
3. Do not put MCP factory inside run_loop health tick as mandatory work (queue + CLI; optional soft drain only).
4. Prefer extending goal_trace.v1 / recovery history patterns over new trace schemas unless versioned.
5. If a task would contradict agi-lmaooo constraints (graph is map not mind; factories separate; oracle per node), stop and re-read that note.

### Future plans (explicit handoff)

When this epic is done, a **later** plan may cover: graph engineer (author/critique large graphs), external MCP catalog, success-model import, graph self-improve under oracles — all still bound by agi-lmaooo and the deferred list in the budget-ladder note.


---

## Current baseline (do not re-implement)

| Piece | Status |
|-------|--------|
| pipeline/goal_policy.py | Classifies reuse/compose/build/research/yield; execute_policy + goal_trace |
| goal_attempt._attempt_capability | Calls classify + execute_policy |
| scripts/mcp_capability_server.py | Phase-8 single stdio server: list/describe/suggest/invoke |
| Connector smoke + process oracle | Structural + hard-coded process fixture |
| Capability paths under PIPELINE_DIR | Fixed (High) |
| Troubleshoot consumer + overnight hygiene | Landed |

Gaps: no persistent plan graph; no mcp policy; no MCP product factory; no graphs/ store; no missing-mcp enqueue.

## Non-goals

- Full KG OS / **graph engineer agent product** (deferred in budget-ladder note; future plan only)
- Graph field-goal prove as a product track
- External MCP marketplace / catalog (agi-lmaooo v3 later)
- Nest factory as only tool; RSI/meta evaluator as runtime
- Open-world trust / funds / captcha mandate stack
- Replacing software field_prove with MCP
- Grok Workflows (Rhai) as compose engine for v0
- Soft-skip requires: as default policy

## Serial tracks

| Track | Name | Outcome |
|-------|------|---------|
| T0 | Paths | graphs_dir / mcps_dir |
| T1 | Graph store v1 | graph.v1 compile + critique + save/load |
| T2 | Goal policy v1 | POLICY_MCP + enqueue signal |
| T3 | MCP queue | pending/done job files |
| T4 | MCP factory v0 | wrap + smoke + register |
| T5 | Wire | graph missing mcp -> enqueue; goal_compose CLI |
| T6 | Docs | COMMANDS.md + agi-lmaooo |
| T7 | Optional overnight soft drain | -DrainMcpQueue |

## File map

| File | Role |
|------|------|
| pipeline/paths.py | graphs_dir(), mcps_dir() |
| pipeline/goal_graph.py | NEW graph.v1 |
| pipeline/goal_policy.py | POLICY_MCP |
| pipeline/goal_attempt.py | optional graph compile |
| pipeline/mcp_factory.py | NEW wrap/smoke/register |
| pipeline/mcp_queue.py | NEW job queue |
| scripts/mcp_factory.py | CLI |
| scripts/goal_compose.py | CLI |
| test_goal_graph.py | tests |
| test_mcp_factory.py | tests |
| COMMANDS.md | ops |
| notes/agi-lmaooo.md | status |

PIPELINE_DIR layout:
`
graphs/{goal_id}.json
mcps/{mcp_slug}/manifest.json, server.py, smoke_report.json
queues/mcp_factory/pending|done/{job_id}.json
`

## Schemas

### graph.v1
schema, goal_id, goal_text, created_at, updated_at, status (draft|critiqued|executable|blocked),
nodes[{id, kind: software|connector|skill|mcp|external_mcp|human|research, slug, label, status: verified|draft|missing|unknown, oracle, requires}],
edges[{from, to, kind: data|control|requires}], critique{ok, issues}.

### mcp_manifest.v1
schema, mcp_slug, wraps_capability, transport: stdio_jsonl, server_path, tools[ping,invoke,describe], status draft|smoked|verified, created_at.

### mcp_factory_job.v1
schema, job_id, capability_slug, reason, goal_id, status pending|done|failed, created_at.

---

### Task 0: Paths

- [ ] Write test_graphs_and_mcps_dirs (tmp PIPELINE_DIR)
- [ ] Add graphs_dir/mcps_dir to pipeline/paths.py and __all__
- [ ] pytest test_goal_graph.py::test_graphs_and_mcps_dirs -q
- [ ] Commit: feat(paths): add graphs_dir and mcps_dir

### Task 1: goal_graph.py

API: compile_goal_graph(text, goal_id, route_hits=None, max_nodes=10), critique_graph, save_graph, load_graph.

Rules: nodes from router hits + connectors; max 10; linear control edges; critique fails on missing nodes / missing oracle names; no LLM in compile v1.

- [ ] Failing tests compile/critique/save/load
- [ ] Implement pipeline/goal_graph.py
- [ ] pytest test_goal_graph.py -q
- [ ] Commit: feat(goal_graph): graph.v1 compile critique persistence

### Task 2: POLICY_MCP

- [ ] Classify mcp when kind==mcp or text suggests wrap
- [ ] execute_policy mcp: mcp_queue.enqueue_wrap; goal_trace deeper_work_needed oracle mcp_factory_enqueued
- [ ] build: metrics/goal_build_handoffs.jsonl only
- [ ] tests in test_goal_policy.py
- [ ] Commit: feat(goal_policy): mcp policy enqueues factory job

### Task 3: mcp_queue.py

- [ ] queue_dir, enqueue_wrap, list_pending, mark_done
- [ ] tests
- [ ] Commit: feat(mcp_queue): file-based MCP factory jobs

### Task 4: mcp_factory v0

Only wrap verified capabilities (no product codegen).
Scaffold mcps/mcp_{slug}/server.py stdio JSONL ping/describe/invoke via capability_tools.
manifest.json, smoke_report.json, registry kind=mcp, goal_trace mode=mcp_factory.

CLI:
`
python scripts/mcp_factory.py wrap --slug CAP
python scripts/mcp_factory.py smoke --mcp-slug mcp_CAP
python scripts/mcp_factory.py drain-queue --limit 1
python scripts/mcp_factory.py list
`

- [ ] tests with entrypoint override
- [ ] implement + CLI
- [ ] pytest
- [ ] Commit: feat(mcp_factory): v0 wrap capability as stdio MCP + smoke

### Task 5: Wire + goal_compose CLI

- [ ] plan_factory_actions: missing mcp nodes -> enqueue_wrap
- [ ] software missing: handoff log only
- [ ] scripts/goal_compose.py: compile, plan-factories, attempt
- [ ] Commit: feat(goal_compose): CLI and enqueue missing MCPs

### Task 6: Docs

- [ ] COMMANDS.md + notes/agi-lmaooo.md status
- [ ] Commit: docs: goal compose + MCP factory v0

### Task 7 optional: overnight soft drain

- [ ] -DrainMcpQueue non-HARD after queue has traffic

---

## Work-ahead after plan

| Stage | What |
|-------|------|
| v1 complete | attempt_goal always saves graph for non-hermes |
| v2 complete | missing mcp nodes become smoked MCPs E2E |
| v3 later | external MCP catalog; success-model graphs; self-improve |
| Parallel | one product connector oracle |
| Later | build policy -> seed/ladder without thrash |

## Testing

`
pytest test_goal_graph.py test_mcp_factory.py test_goal_policy.py -q
# regression:
pytest test_connector_smoke.py test_troubleshoot_consumer.py test_pipeline_paths.py -q
`

## Risks

| Risk | Mitigation |
|------|------------|
| Second software factory | v0 only wraps verified capabilities |
| run_loop bloat | file queue + CLI; no health-tick until T7 |
| Path bugs | PIPELINE_DIR helpers only |
| KG creep | max 10 nodes; linear edges; no LLM compile v1 |

## Acceptance

1. graphs/mcps paths + graph.v1 tested
2. mcp policy enqueues (no inline invent)
3. wrap+smoke produces server/manifest/smoke_report + registry kind=mcp
4. COMMANDS + agi-lmaooo updated
5. related tests green

## Spec coverage

| agi-lmaooo | Task |
|------------|------|
| policy compose/reuse/build/research | exists + T2 mcp |
| durable traces | exists + T4 |
| graph store + critique | T1 |
| MCP factory separate | T3-T4 |
| graph trigger MCP | T5 |
| external MCP / success models | deferred v3 |
| meta evaluator / nest | deferred |

## Execution

Ship T0-T5 per-task commits; T6 docs; T7 optional.

1. Subagent-driven (recommended)
2. Inline with checkpoints

Which approach?
