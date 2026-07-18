# Explore Orca + Grok Build + idea-impl

**Status:** note only — do not build now  
**Date:** 2026-07-18  
**Context:** desire for less rigid, self-reconfiguring architecture; self-developing agents

## Intent

**Explore using Orca** as a way to construct something:

- a little **less rigid** than the current multi-agent factory graph, and  
- more capable of **reconfiguring its own architecture** (within safety bounds).

Orca also has **Grok Build support**, which may be a path to **“port” Grok** (this class of
assistant) into the factory loop — so a combined system can choose tools, skills, and
workflows rather than only the fixed idea-impl agent roles.

## Target shape (sketch)

```
                    ┌─────────────────┐
  person  ─────────►│  Conversational  │  (see agent-ui note)
                    │  front agent     │
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           ▼                 ▼                 ▼
    idea-impl factory    Orca (flexible     Grok Build
    (plan/code/ship)     reconfig / graph)  (skills, tools,
                                            coding sessions)
           └─────────────────┼─────────────────┘
                             ▼
                    self-developing loop:
                    pick best tools/skills,
                    improve process + products
```

## Why it matters

- Fixed role map (planner → executor → validator → ship) is strong for **unattended
  overnight builds**, but weak for **meta-level redesign** of the factory itself.
- Orca-style flexibility + Grok skills could close the gap between “run the pipeline”
  and “improve the pipeline and the assistant together.”
- Aligns with soft value **improve ability to improve** and caution/slack notes: any
  self-rewrite needs brakes (backup, human approve, field-prove critical paths).

## Cautions (do not ignore later)

- Elon-style delete/reduce complexity still conflicts with bolting on a third runtime
  without a clear win.
- Self-modifying architecture without snapshots + restore is how systems collapse.
- Porting “Grok into the system” is integration design, not a single API key.

## Non-goals for now

- No Orca dependency in `requirements.txt`.
- No attempt to run Grok Build skills inside `pipeline/runner.py` without a design pass.
- Keep overnight ship-prove / main pipeline working as the proven path.

## Next time we pick this up

1. Read current Orca + Grok Build integration docs (what is actually supported).
2. Decide: Orca *hosts* idea-impl, or idea-impl *calls* Orca, or a thin orchestrator above both.
3. Define a minimal experiment (one reconfigurable workflow) that does not replace the bus.
