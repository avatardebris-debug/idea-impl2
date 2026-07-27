---
name: deconstructor
description: >
  Deconstruct an org, credits list, tool surface, or genre into typed candidate
  nodes (skill|prompt|mcp_simple|mcp_complex|factory|human|research|process) for
  later graphs. Emits deconstruct.v0 proposals only — not production graph.v1.
  Use when: /deconstructor, "deconstruct this org", "break down credits",
  "tool surface inventory", "genre systems breakdown", or before graph engineer.
---

# Deconstructor v0

**Job:** 80/20 structure from messy reality → **candidate inventory + replacement classes**.  
**Not:** production `graph.v1`, auto-attach to sockets, or auto MCP wrap.

Pair with: `notes/lmao-agi-discuss.md`, `notes/agi-lmaooo2.md`.

## Modes

| Mode | Target example | Seed focus |
|------|----------------|------------|
| `org` | small indie game studio | departments → roles |
| `credits` | NES platformer credits | credit roles → classes |
| `tool_surface` | Blender animation tools | tool clusters (not 100 flat tools) |
| `genre` | platformer | systems + difficulty ladder stubs |
| `open` | anything | single root — re-run with a named mode |

## Closed replacement classes

`skill | prompt | agent_role | mcp_simple | mcp_complex | factory | human | research | process | process_series`

| Class | Next action |
|-------|-------------|
| skill | create-skill → **register → sandbox → promote → attach** |
| prompt / agent_role | register-prompt → sandbox → promote |
| mcp_simple | `mcp_factory` wrap + smoke |
| mcp_complex | further deconstruct OR external MCP first |
| factory | software factory seed |
| human | keep human node + oracle |
| research | Hermes / knowledge |
| process / process_series | connector / workflow later |

## CLI (deterministic seeds + critique)

```text
python scripts/deconstructor.py build --mode org --target "small indie game studio"
python scripts/deconstructor.py plan-fill --id org_small-indie-game-studio
python scripts/deconstructor.py from-json --path my_inventory.json
python scripts/deconstructor.py validate --id <id>
python scripts/deconstructor.py list
```

Store: `$PIPELINE_DIR/deconstructs/{id}.json` schema `deconstruct.v0`.

## Agent workflow

1. Clarify **what** is being deconstructed (not the universe).
2. Pick **mode**; run `build` or draft candidates then `from-json`.
3. Read `critique` — fix size budget (≤20 nodes default), closed classes, oracle_hint.
4. Run `plan-fill` — fill **skill/prompt** via block_registry habit; **mcp_simple** via factory.
5. Do **not** mark `production_graph: true`. Graph engineer / graph.v1 only after critique + block resolve + smoke.

## Stop conditions

- Clear class + oracle_hint per leaf  
- Depth ≤ 2–3  
- Further split doesn’t change factory type  
- Prefer outcomes/processes over empty org titles  
- Force `human` for liability/identity/taste  

## Habit after a `skill` leaf

```text
/create-skill or write SKILL.md
python scripts/block_registry.py register-skill --name <skill> --sandbox
python scripts/block_registry.py promote --id skill_<skill>
python scripts/block_registry.py attach --socket executor.pre_task_skills --id skill_<skill>
```

## Out of scope (v0)

- Deep fractal auto-recursion  
- Graph engineer product  
- Distill of every role’s full procedure (optional second pass)  
- Difficulty-ladder optimization as required path  
- Merging knowledge + workflow graphs into one blob  
