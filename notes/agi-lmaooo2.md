# AGI-lmaooo2 — Pre–graph-engineer block readiness (prior discussion)

**Status:** Design / readiness note. **P1–P2 (sockets + skill/prompt promote) shipped v0** — `pipeline/block_registry.py`, CLI `scripts/block_registry.py`, tests `test_block_registry.py`.  
**Date context:** 2026-07-26 session (after graph.v1 + MCP factory v0).  
**Parent north star:** [agi-lmaooo.md](./agi-lmaooo.md)  
**Companion conceptual discussion:** [lmao-agi-discuss.md](./lmao-agi-discuss.md)  
**Related:** [2026-07-23-budget-ladder-trust-and-status.md](./2026-07-23-budget-ladder-trust-and-status.md) (graph engineer deferred), [2026-07-22-p1-held-out-and-goal-traces.md](./2026-07-22-p1-held-out-and-goal-traces.md)

---

## Thesis

**Graph engineer only makes sense when the system’s “blocks” are trustworthy, discoverable, and insertable under the same discipline that made software field_prove work.**

Knowledge graph + graph engineer without that is a map of fiction. The aim of the graph engineer is to **match the map to real capabilities**—not invent a second brain that ignores the factory.

---

## Same bar for every lego type

| Stage | Software (have) | Skill / prompt | MCP | Workflow-from-graph |
|--------|-----------------|----------------|-----|---------------------|
| Author | plan → implement | create-skill (TUI); **no create-prompt** | wrap verified cap (v0) | graph.v1 compile (thin) |
| Gate | review, complete-gate | mostly none | smoke ping/describe | critique missing/oracle |
| Prove | field_tests → field_proven | none | smoke ≠ field | no whole-graph smoke yet |
| Register | registry + requires | skill_load roots only | kind=mcp row | graphs/*.json |
| Insert into runtime | invoke_capability | inject ad hoc | invoke via MCP | policy enqueue only |
| Recover | troubleshoot consumer | none | none | none |
| Learn | finetune + goal_trace | not systematic | factory traces | policy traces |

Until skill/prompt/MCP/**workflow** each have something like the software columns, the graph engineer stays deferred as a *product*.

---

## What we have vs gaps (skills / prompts / sockets)

| Piece | Reality |
|--------|---------|
| **create-skill** | Interactive Grok skill → `SKILL.md`. Not a factory: no review, mission/security gate, socket attach, or sandbox-before-promote. |
| **Agentic prompts** | `pipeline/prompts/*.md` + agent roles; static, hand-edited. |
| **skill_load** | Find + inject skill markdown into pipeline context. |
| **Empty block / role socket** | **v0 shipped.** `pipeline/block_registry.py` sockets: `executor.pre_task_skills`, `manager.blocker_skill`, `goal.policy_skill`, `phase_planner.skill`. Attach only `verified` (or `sandboxed` if socket allows). Store: `$PIPELINE_DIR/state/block_registry/`. |
| **create-a-prompt skill** | **Missing.** No QC’d authoring of role prompts. Register existing prompt files as draft blocks yes (`register_block_from_prompt_file`). |
| **Skill/prompt promote pipeline** | **v0 shipped (static).** register draft → sandbox (file/size/secrets/frontmatter) → promote verified → attach. CLI: `scripts/block_registry.py`. goal_trace mode=`block_promote`. No critic/mission LLM yet. |
| **External ingest** (GitHub / MCP market) | **Missing.** No pin/hash/scan/rank/approve. |
| **Human push approval + mute** | **Missing** — design hook later; product nice-to-have (see below). |

Default preference: **sandbox first**; never write straight into production sockets.

---

## What to build before graph engineer (layers)

### Layer A — Inventory & sockets (map can match reality)

1. **Registry kinds (closed):**  
   `software | connector | skill | prompt | mcp | external_mcp | human | research`  
   Fields: status (`draft|sandboxed|verified|revoked`), entrypoint, requires, oracle, provenance, last_smoke_at, risk_class.

2. **Role sockets (“empty blocks”)**  
   e.g. `executor.pre_task_skills[]`, `manager.blocker_skill`, `goal.policy_skill`  
   Only sandboxed-allowlisted or verified assets attach.

3. **create-prompt factory (thin)**  
   Role + mission slice + examples → draft → static checks (secrets, disallowed tools, length) → critic/human → versioned prompt.

4. **create-skill → promote**  
   create-skill → sandbox fixture tasks → critic/mission checklist → promote + attach to socket.

### Layer B — Factory discipline for MCP & workflows

5. **MCP factory beyond wrap** — versioning, revoke, re-smoke on dependency change, real invoke oracle.

6. **Workflow-from-graph factory (pre–graph-engineer)**  

```text
draft graph → structure/oracle/risk critique → freeze version
  → resolve nodes (verified only or enqueue factories)
  → per-node smoke → whole-graph smoke (cheap path)
  → goal run under budget → oracles + traces + weights
```

Graph engineer later only **authors/revises** graphs into this pipeline.

### Layer C — External world (after A–B)

7. **Ingest pipeline:** find → fetch pinned → static scan → license/provenance → sandbox → rank → human gate → `external_*` draft → promote after smoke.

8. **Human approval hook (defer product):**  
   `needs_human_approval(action, risk_class)` on disk first.  
   Later: push + “mute for N requests / D days / action_class” (customizable; one/both/neither).  
   Do not build notifications before the **state machine**.

### Layer D — Learning

9. Unified outcome schema (extend goal_trace family):  
   `proven | failed | deeper | revoked | human_rejected` + `failure_class` + `train_weight`.  
10. Never high-weight train on unverified external “success.”

---

## Prep roadmap (serial)

| Phase | Focus | Exit criteria |
|-------|--------|----------------|
| **P1** | Sockets + registry kinds skill/prompt | **v0 done** — JSON block catalog + role sockets; attach gates draft/revoked |
| **P2** | Skill/prompt promote (sandbox → verified) | **v0 done** — static sandbox + promote + revoke; executor socket hook thin |
| **P3** | Whole-graph smoke after nodes resolved | `smoke_pass` before full goal run |
| **P4** | MCP factory v1 (re-smoke, revoke, invoke oracle) | MCP as real block |
| **P5** | External ingest **manual** (pin + sandbox + human CLI) | One external asset under audit log |
| **P6** | Graph engineer (later plan) | Only authors into P3 pipeline |
| **Defer** | Push notifications + mute windows | Note until approval state exists |

---

## Blind spots (technical / ops)

- Provenance & pinning (commit SHA, content hash, license)  
- Revocation & drift when deps change  
- Skills often more privileged than CLIs (injection risk)  
- Prompt injection via skill/MCP descriptions  
- Socket conflicts / priority  
- Oracle gaming (weak oracles train cheats)  
- Shared PIPELINE_DIR races  
- Cost of full graph smoke vs cheap path  
- Human mute rules are security controls (log + expire)  
- Data egress / network allow-lists for external MCP  
- Who approved (audit for FT later)  
- Partial graph success ≠ workflow proven  
- Hermes/research vs tool sockets  

---

## Testing readiness (as of this note)

| Path | Ready? |
|------|--------|
| Internal compose / MCP wrap / feature matrix | **Yes** |
| Internal goal-achieve (simple) | **Partial** |
| GitHub as tool (dry-run / human watch) | **Thin** |
| External GitHub skill/MCP auto-ingest | **No** |
| Graph engineer product | **No** |

Sensible now: `factory_feature_matrix.py`, live one verified MCP wrap, goal_compose on a real goal id, careful GitHub sandbox—not unattended external pull.

---

## Compatibility

- Does **not** contradict agi-lmaooo: factories separate; graph is map not mind; oracles required.  
- Aligns with budget-ladder deferred: full KG / graph engineer product still later.  
- Conceptual **deconstructor** and fractal hierarchy: see [lmao-agi-discuss.md](./lmao-agi-discuss.md)—must meet the same block-readiness bar.

## Slogan (readiness)

**No map without blocks; no blocks without sockets, smoke, and promote.**
