# LMAO AGI discuss — deconstructor, fractal hierarchy, form↔function

**Status:** Open design discussion. **Not a locked architecture.** Prefer reversible, shallow-depth choices.  
**Date context:** 2026-07-26  
**Pair with:** [agi-lmaooo.md](./agi-lmaooo.md) (north star), [agi-lmaooo2.md](./agi-lmaooo2.md) (block readiness / coding requirements)  
**Rule:** Concepts (this note) and capabilities (agi-lmaooo2) must stay **jointly consistent**. Neither wins alone.

---

## Why this note exists

Two complementary angles appeared in the same arc:

| Angle | Focus |
|-------|--------|
| **agi-lmaooo2** | Sockets, promote pipelines, MCP/skill/prompt factories, external ingest security, graph smoke |
| **This note** | How to **prepare information** for a future graph engineer: deconstruct orgs/work into data that *could* become graphs, without building the engineer yet |

Both aim at: **expand capabilities + flexible architecture + enough QC to scale *and* stay simple.**

---

## Core idea (hold lightly)

1. **Deconstructor** (agent/prompt role): 80/20 extract structure from messy reality (org, product, tool surface, “award-winning game studio”) into **typed candidate nodes** for later graphs.  
2. **Fractal hierarchy (shallow):** department → role/process → skill | prompt/agent | simple MCP | complex MCP/factory — stop when a node has a clear block type + oracle. Deep fractal tuning = future experiment, not v0.  
3. **Form ↔ function:**  
   - **KG / deconstructor output** ≈ linguistic *what it is / how it groups* (representation).  
   - **Workflow / factories** ≈ *how it is done* (operation).  
   - Goal-proven workflows can later **compress** into a single node in a larger map (representational memory of “we already know how to do X”).  
4. **Pre–graph engineer** may only: define candidate nodes/edges, primary/secondary use, feasibility—not full production workflows.  
5. **Do not lock ego into this.** If a simpler path serves “map matches blocks,” prefer it. Adding is easy; removing is hard—bias to **thin schemas and reversible factories**.

---

## Deconstructor role (design sketch, not implementation)

### Job

Given a promptable target (org, department, software product, Blender-scale tool surface, mission):

- Extrapolate **essential 80/20** structure.  
- Emit **machine-usable** breakdown (JSON/YAML later; markdown tables fine for v0 experiments).  
- Sort leaves by **replacement class** (closed enum, align with agi-lmaooo2 kinds):

| Class | Meaning | Next action |
|-------|---------|-------------|
| `skill` | Repeatable procedure / checklist / inject-able skill | create-skill → sandbox → promote |
| `prompt` / `agent_role` | Judgment-heavy linguistic role | create-prompt → version → socket |
| `mcp_simple` | Thin tool surface over existing software | MCP factory wrap |
| `mcp_complex` | Large surface (e.g. Blender-scale) | **Further deconstruct** or external MCP first |
| `factory` | Needs own software/MCP factory loop | Seed software factory / multi-phase project |
| `human` | Judgment/liability/identity that stays human | Explicit human node + oracle |
| `research` | Hermes / knowledge, not field_prove software | Hermes path |
| `process` / `process_series` | Ordered multi-step without new product | connector / workflow / graph later |

### Departments

Also define **departments** (or groupings):

- Can the **whole department** be replaced by: simple MCP | complex MCP | skill | single process | series of processes | still needs human org?  
- QC structures in real orgs are a **feature**: use them as **oracle/critique templates** for that subgraph (e.g. “legal review” = human gate node).

### Further deconstruction rule

If class = `mcp_complex` or `factory` or “art / animation / too big”:

- Deconstruct one more level (e.g. `art` → mediums → tasks; `animation` → ~N tool clusters).  
- Goal: keep **any single graph** at a **reasonable size** (e.g. ≤10–20 nodes per level, matching graph.v1 max-10 spirit).  
- Nested graphs later: “animation” is one node in studio graph; expands to tool-cluster graph when needed.

### Output should serve later KG—not be the KG OS

v0 deconstructor output is **candidate inventory + classification**, not production graph.v1 until:

- critique,  
- block resolution,  
- smoke  

(from agi-lmaooo2 workflow-from-graph pipeline).

---

## Fractal hierarchy without deep recursion

**Intended shape:**

```text
Org / goal (top)
  → departments / major processes
      → roles / tool clusters
          → skill | prompt | mcp_simple | (stop) or mcp_complex → one more level
```

**Stop conditions (important):**

- Node has clear replacement class + candidate oracle.  
- Or depth ≥ 2–3 (default max).  
- Or further split doesn’t change action (no new factory type).

**Future experiment only:** deconstruct *agents themselves* into smaller efficiency measurements. Explicitly **out of scope** for first deconstructor.

**Pre–graph engineer path:**

```text
deconstruct → candidate nodes/edges + primary/secondary use
  → size/feasibility eval (can this be sum of existing verified blocks?)
  → only then graph.v1 / graph engineer fill
```

So work can be a **sum of already-built parts** before anything new is constructed—same spirit as capability reuse before greenfield software.

---

## MCP factory nuance (elicit surface)

For existing software → MCP:

- Factory should eventually **elicit** commands/features/tools (help crawl, API inventory, Blender-scale hundreds of tools).  
- That inventory is itself a **graph of tool clusters** (e.g. “animation” covers ~10 toolcalls).  
- High-level KG node “animation” should not dump 100 tools into one flat graph; **cluster then bind**.  
- Complex MCP may mean: external MCP first (Blender) + deconstruct our *use* of it into primary workflows—not reimplement Blender.

---

## Form, function, and “brain” metaphors (keep honest)

Useful framing:

| Layer | Role |
|-------|------|
| Representational (KG / deconstructor labels) | What it *means* / how it groups |
| Operational (workflows, toolcalls, factories) | How it is *done* |
| Proven compression | goal_proven subgraph → single reusable node (neuro-associative *analogy*, not claim of biological equivalence) |

Interesting long-arc thought: encoding form↔function could go beyond words (tables, codes, visual atlases, reverse-engineered mappings). **For the factory now:** stay at **words / roles / few lego types**. Forks later.

Transformers + tools + KG-as-map can go far without requiring SNN-as-core. Specialized models (vision, ranking, GNN over graphs) remain optional **plugins**, not the harness spine.

**Do not** treat brain metaphor as implementation requirement. Treat it as **inspiration for layered representation + operation + memory of proven work.**

---

## How this fits agi-lmaooo2 (merge concepts + requirements)

| Concept (this note) | Requirement (agi-lmaooo2) |
|---------------------|---------------------------|
| Deconstructor emits replacement classes | Classes ⊆ registry kinds; no free-text mush |
| Department → process series | Becomes graph.v1 edges only after critique |
| Sum of parts before build | Reuse verified blocks; enqueue factories for gaps |
| Fractal shallow | graph.v1 max nodes; nested graphs by reference later |
| Complex MCP further deconstruct | Avoid 100-tool flat nodes; cluster oracles |
| Compress goal_proven to node | Only after field/goal proof—same as field_proven world nodes |
| create-prompt / create-skill | Needed to *fill* prompt/skill classes deconstructor proposes |
| External first for complex MCP | Ingest pipeline + security before auto-wire |

**Compatibility rule:** Deconstructor must not skip sockets, smoke, or promote. It only **proposes**.

---

## What not to lock in yet

- Exact JSON schema for deconstructor output (table is enough to experiment).  
- Deep fractal auto-recursion.  
- Full org OS or “replace company” productization.  
- Brain/SNN architecture claims.  
- Graph engineer product (still deferred).  
- Push notifications (hook design only—see agi-lmaooo2).

**Bias:** Prefer a **deconstructor prompt + fixture eval** over a permanent multi-agent org platform.

---

## Blind spots (conceptual + practical)

| Blind spot | Note |
|------------|------|
| **False replaceability** | Many “roles” are liability/identity/trust, not skill text—force `human` class. |
| **Org charts ≠ work** | Real work is informal; deconstructor must prefer *outcomes/processes* over titles. |
| **Over-decomposition** | Too many nodes → unmaintainable map; enforce size budgets. |
| **Under-decomposition** | “Art” as one node hides unworkable MCP surface. |
| **Classification politics** | “Replace with AI” is a product decision; keep classes as *technical fit*, not HR policy. |
| **Oracle vacuum** | Clean classification without oracles = pretty lies. |
| **Ego lock** | First schema will be wrong; version `deconstruct.v0` so redo is cheap. |
| **Dual path confusion** | Concept notes vs code requirements must not fork two irreconcilable designs—cross-link always. |
| **Compression too early** | Don’t collapse to one node until goal_proven/field_proven. |
| **External MCP trust** | “Fine external first” still needs pin/scan/sandbox (agi-lmaooo2 Layer C). |

---

## Deconstruct vs distill (keep separate until proven one agent can do both)

| Role | Job | Hard / easy |
|------|-----|-------------|
| **Deconstructor** | Structure: roles, departments, replacement *classes*, candidate edges, size budgets | Hard when domain is huge |
| **Distiller** (maybe separate) | Procedure: what they *do*, typical tools, tasks, modern replacements, quality bars, “how a credit role actually works” | Hard in research depth; easy as a *follow-on prompt* once structure exists |
| **Router / chooser** | Which deconstructor (or mode) to call for this target | Meta, thin |

**Principle:** If one prompt can do a hard thing (org → classes), it can often do an easy follow-on (role → tasks/tools)—but **shipping one god deconstructor** that also plans difficulty ladders, researches history, and reverse-engineers teams is how schemas rot. Prefer:

```text
router → deconstruct_structure → (optional) distill_role_tasks → research_pass (Hermes)
  → difficulty_ladder plan → feasibility / min-cover optimization → candidate graphs (still not production)
```

v0 may be **one open-ended deconstructor** with a strong “what are you deconstructing?” system prompt, plus **named modes** (org | credits | tool_surface | genre) before inventing deconstructor1..N services.

---

## Multi-deconstructor options (don’t overbuild)

| Approach | When |
|----------|------|
| **A. One skill + mode arg** | Default v0: `deconstruct(mode=org|credits|tool|genre, target=…)` |
| **B. Router skill chooses mode** | When modes diverge in schema enough to confuse one prompt |
| **C. deconstructor_org / _credits / _tools** | Only after A fails eval fixtures |
| **Open-ended + explicit target** | Always: “deconstruct *this*, not the universe” |

Hard super-goal (“award-winning modern game factory”) is a **goal chain**, not one deconstructor call.

---

## Worked pattern: award-winning game factory (conceptual pipeline)

Not a build ticket—shows how pieces compose:

```text
1. Identify exemplars (award-winning games) — research / Hermes
2. Deconstruct genres (structure)
3. Difficulty ladder (meta-plan, not deep fractal):
   v1 Atari/early PC → v2 NES/low → … → modern
   Each level: fork prior graph, replan, raise bar
4. For genre × era: model best performers (credits → roles)
5. Distill each role: tasks, tools, modern counterparts, QC they had / should have
6. Classify replacement: skill | prompt | mcp_simple | mcp_complex | factory | human | process
7. Reverse-engineer public build stories (research) → map to modern MCP/skill stack
8. Optimization pass: “max roles covered by min high-quality MCPs/skills”
   → collapse 2 dozen credits → 5–10 composite nodes where safe
9. Emit candidate *knowledge* inventory + candidate *workflow* sketch
10. ONLY THEN graph.v1 / factories / smoke (agi-lmaooo2) — replan allowed often
```

**Difficulty ladder** is Tim-Ferriss-adjacent: start easy, progressive overload, replan—not one-shot modern AAA.

**Min-cover optimization** (“least MCPs that replace most skills at quality bar”) is a **second pass** after classification, not instead of honest role distillation. Watch for false replaceability (human/liability).

---

## Three graph kinds (keep separate until convergence is earned)

| Graph kind | Contents | When “done” |
|------------|----------|-------------|
| **Knowledge / inventory graph** | Genres, roles, tools, quality bars, research citations, “what exists” | Informative; **no** claim of runnable |
| **Operational / architecture graph** | Factories, sockets, MCPs, skills as system capabilities we *have* | Registry-truth aligned |
| **Workflow / goal graph** | Ordered process for a concrete goal (graph.v1 production path) | goal_proven / smoke_pass |

**Rule:** Do **not** merge these into one blob early. Some knowledge graphs **never** need a workflow (pure reference). Some workflows attach to a thin knowledge spine. Convergence into “one artifact” only when a **goal_proven** package wants a single portable representation—and even then, archive the three sources.

---

## Meta-learning frame (Ferriss DISSS / CFE — analogy only)

Borrow the *shape* of skill acquisition, aimed at **system capability**, not human speed-learning:

| Ferriss-ish idea | Factory translation |
|------------------|---------------------|
| Deconstruction | Deconstructor → structure + classes |
| Selection | Primary/secondary use; min-cover; difficulty ladder pick |
| Sequencing | v1→v2 eras; freeze graph versions; replan |
| Stakes | Oracles / field_prove / goal_proven |
| Compression | Proven subgraph → single reusable node |
| Feedback | Traces + weights; later RLHF/applied RL **parked** |

Distillation ≈ encoding expert procedure into **skills/prompts/MCP surfaces/code** so the harness can approximate base function; superhuman is optional later via better models + iteration.

---

## Where Grok Workflows (Rhai) fit (still fuzzy—good)

From budget-ladder vocabulary: **factory workflow/connector ≠ Grok Workflows (Rhai).**

Tentative placement (revisit):

| Layer | Rhai? |
|-------|--------|
| Deconstruct / research / distill | No—agents/prompts/Hermes |
| Overnight / factory health | Maybe later orchestration |
| **Proven, stable multi-step process** after goal_proven | **Candidate:** encode boring reliable paths as Rhai so runtime doesn’t re-reason |
| Graph engineer authoring | No—must stay evaluable before Rhai |

Earn Rhai by **compressing proven workflows**, not by using Rhai to invent unproven ones.

---

## Future plan seeds (for a later plan doc—not this note’s job to implement)

When ready to plan implementation, candidate epic order:

1. **Deconstructor v0** — **IMPLEMENTED** — `pipeline/deconstructor.py` + `scripts/deconstructor.py` + `.grok/skills/deconstructor/SKILL.md` + `test_deconstructor.py`. Schema `deconstruct.v0`; modes org|credits|tool_surface|genre|open; seed + from-json + critique + plan-fill. Store: `$PIPELINE_DIR/deconstructs/`. Not production graph.v1.  
2. **Socket + skill/prompt promote** (agi-lmaooo2 P1–P2)—**v0 done** (`block_registry`). Habit: register→sandbox→promote; `--sandbox` on register.  
3. **Graph smoke** (P3); keep knowledge vs workflow graphs separate.  
4. **MCP surface elicit + cluster** (help crawl → tool clusters).  
5. **Manual external pin path**.  
6. **Difficulty-ladder / min-cover as optional planner steps** (after deconstruct works on fixtures).  
7. **Graph engineer** only after 1–5 feel boring.  
8. **Rhai** only for proven compressed paths.

Inform plan from **both** notes; reject tasks that only do concepts without sockets/oracles, or only sockets without a way to *source* node candidates.

---

## Imagination (optional, park)

Flexible architecture + QC + goal-proven compression *could* become a general form↔function substrate (far beyond the factory). Obscure uses exist. **Park.** Factory success metric remains:

> Simple aims still work; complex aims decompose into proven blocks without thrash.

---

## Discussion stance (for future agents)

- Operator is **thinking out loud**—treat as options, not mandates.  
- Challenge design if it fights “map matches blocks” or forces redo of working software factory.  
- Prefer **additive reversible layers** over grand rewrites.  
- Record decisions in plans when something becomes implementable; keep speculation in notes.

---

## Slogans

**Deconstruct to classes; promote to blocks; map only what is real.**  
**Representation without operation is poetry; operation without representation doesn’t scale.**  
**Fractal, but shallow—until measurement says go deeper.**  
**Knowledge graph ≠ workflow graph until proof forces a package.**  
**Hard super-goals are chains of deconstruct + research + ladder—not one prompt.**
