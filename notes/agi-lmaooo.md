# AGI-lmaooo — long-arc vision (capability graph → factories)

**Status:** North-star note. Near-term work stays serial and measured; this is not a mandate to build full KG/MCP OS next.

**Related:** connector smoke + goal_trace, troubleshoot consumer, truth-density, field_proven software factory, notes on held-out / goal traces.  
**Read next:** [agi-lmaooo2.md](./agi-lmaooo2.md) (block readiness before graph engineer), [lmao-agi-discuss.md](./lmao-agi-discuss.md) (deconstructor / fractal / form↔function—hold lightly).
**Plan (graph.v1 + MCP factory v0):** [docs/superpowers/plans/2026-07-26-goal-compose-mcp-factory-v0.md](../docs/superpowers/plans/2026-07-26-goal-compose-mcp-factory-v0.md)

---

## One-sentence strategy

> We grow a versioned capability graph; goals compile to subgraphs; each node is a typed lego with an oracle; missing nodes spawn the matching factory (software, connector, skill, MCP); traces train better compilation—not freer monologue.

## Core insight

Represent work as a **graph of reusable legos**. Learn to map goals onto that graph. When a node is missing, build the right **kind** of lego. Prove each edge with oracles. Scale by growing the graph, not by one giant brain.

```text
Goal → plan graph (flowchart / KG) → critique/QC graph
     → resolve each node to a lego type
     → execute edges (tools, APIs, software, connectors, MCPs)
     → measure (oracle / field / goal_proven)
     → missing node? → spawn the right factory loop
     → write back new nodes/edges + durable traces
```

## Layers

| Layer | Role | Lego types |
|--------|------|------------|
| **Graph engineering** | Architecture: nodes = capabilities/roles; edges = data/control/requires | Process model |
| **Planning / decision** | Map goal → subgraph; `reuse \| compose \| build \| research \| yield` | Policy, not execution |
| **Execution** | Call tools: software, connectors, skills, workflows, GitHub, external MCPs | Runtime |
| **MCP factory** | Separate loop when graph says “this should be an MCP” | MCP as product class |
| **QC** | Critique graph *and* each lego (schema, smoke, field, goal oracle) | Same discipline as field_prove |
| **Learning** | Traces of plan→tools→oracle; graph diffs that improved outcomes | goal_trace + finetune |

Skills/workflows selecting MCPs is fine **when selection is a node with an oracle**, not infinite meta-selection.

## Lego type enum (keep closed at first)

`software | connector | skill | mcp | external_mcp | human | research`

## Constraints (so it can scale)

1. **Graph is the map, not the mind** — reasoning produces/revises the graph under critique; execution stays dumb and measurable.
2. **Every node needs a proof contract** — deconstruction without an oracle is research, not field_proven.
3. **Factories stay separate loops** — software (have), connector compose (emerging), MCP factory (**v0 shipped**, separate), graph QC (thin). Graph *triggers* loops; it does not reimplement them.
4. **Copy-paste = interface stub + provenance** — stable ID, entrypoint, requires, status, oracle.
5. **Complexity budget** — full MCP factory + full KG OS in one push is thrash. Compose + goal policy first.

## Scale ladder (simple → medium → complex)

| Level | Example | Needs |
|-------|---------|--------|
| Simple | Run software, get the thing | Software factory + field oracle |
| Medium | Connect two systems, pass data, serve a process | Connectors + process oracle + goal_trace |
| Complex | “Award-winning game factory” via genre → difficulty → NES credits deconstruction → skills/MCP/software nodes → Blender MCP assets + QC | Nested goals, imported success graphs, many factories |

Modeling existing success (credits, skill deconstruction) is valid **when** each subgraph has acceptance oracles.

## What we already have (approx.)

| Piece | Status |
|-------|--------|
| Software factory | Strong (seed → build → thin-ship → field_proven) |
| Connectors | YAML + seed one-shot + structural/process smoke |
| Goals / goal_trace | Schema + sandbox + connector_smoke traces (**v0 largely done**) |
| Skills / agents | Grok skills, pipeline agents |
| Troubleshoot gate + consumer | Emit + serial health-tick act/yield (**v0 largely done**) |
| Overnight hygiene | Canary + connector smoke + truth-density + incomplete-run recovery (**v0 largely done**) |
| Thin goal compose policy | `reuse \| compose \| build \| research \| yield \| mcp` + goal_trace (**v0 largely done**) |
| Tiny graph store (graph.v1) | **IMPLEMENTED** — `pipeline/goal_graph.py` + `scripts/goal_compose.py` |
| MCP factory | **IMPLEMENTED v0** — wrap/smoke/queue (`pipeline/mcp_factory.py`, `scripts/mcp_factory.py`); separate loop, not overnight-mandatory |
| Graph engineer product | Deferred (data store ≠ engineer agent) |
| External MCP catalog / self-improve | Later (v3+) |

## Staged roadmap

### v0 (near-term — honor path without OS cosplay) — **largely done**

- Durable traces by default (goal_traces, recovery_history, consumer history) so reboot does not erase policy memory. **Shipped.**
- Troubleshoot consumer acts on `last_recovery_*` (re-arm thin or yield to BE ladder). **Shipped.**
- Overnight hygiene: canary + connector smoke + truth-density; recover incomplete overnight reports after shutdown. **Shipped.**
- Thin **goal compose policy**: classify `reuse | compose | build | research | yield | mcp` on attempt; always goal_trace. **Shipped.**

### v1 — **IMPLEMENTED** (tiny graph store)

- Tiny graph store under `PIPELINE_DIR/graphs/` (nodes/edges JSON). **`pipeline/goal_graph.py`**
- Goal → 3–10 node flowchart from registry + connectors only.
- Graph critique: missing requires, unverified node, no oracle.
- CLI: `python scripts/goal_compose.py compile|plan-factories|attempt`

### v2 — **IMPLEMENTED v0** (MCP factory separate loop)

- MCP factory as **separate** loop: wrap one verified capability as MCP + smoke. **Shipped v0.**
- Graph trigger: missing `kind:mcp` enqueues factory (not inline invent). **Shipped.**
- CLI: `python scripts/mcp_factory.py wrap|smoke|drain-queue|list`
- Plan: [docs/superpowers/plans/2026-07-26-goal-compose-mcp-factory-v0.md](../docs/superpowers/plans/2026-07-26-goal-compose-mcp-factory-v0.md)

### v3

- External MCP catalog as candidate nodes (still need smoke).
- Import “success model” graphs (e.g. NES pipeline) with gold oracles.
- Self-improve: tweak graph → evaluate → keep if oracle improves.

### Later (explicitly deferred)

- **Graph engineer product** (author/critique large graphs) — tiny graph.v1 store is data only; engineer agent still deferred. Prerequisites: [agi-lmaooo2.md](./agi-lmaooo2.md); candidate **deconstructor** prep: [lmao-agi-discuss.md](./lmao-agi-discuss.md).
- Nest whole system as the only tool.
- Open-world trust / funds / captcha mandate stack.
- RSI successor improver as primary driver.
- Meta evaluator as god runtime (evaluator over traces only).

## Near-term implementation map (this pass)

| Track | Deliverable | Status |
|-------|-------------|--------|
| **A** | Troubleshoot consumer durable history + confirm run_loop tick | largely done |
| **B** | Overnight: smoke, truth-density, incomplete-run recovery report, keep traces env | largely done |
| **C** | Goal policy classify + compose attempt + goal_trace always | largely done |
| **D** | graph.v1 + MCP factory v0 (separate loop) | **done** — plan 2026-07-26 |

## Slogan

**Goals ask; compose wires; build fills holes; oracles judge; traces teach.**
