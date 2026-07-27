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

## CLI (parse structure from target — no fixed templates)

**Important:** A bare title like `"small indie game studio"` does **not** invent departments.
Pass the actual parts to deconstruct (lists, hierarchy, credits lines).

```text
# Structured org (file recommended for multi-line)
python scripts/deconstructor.py build --mode org --target-file hospital.txt
python scripts/deconstructor.py build --mode org --target "Emergency: triage nurse, attending
Radiology: MRI tech, radiologist"

# Credits list
python scripts/deconstructor.py build --mode credits --target "Director - A
Programmer - B
Tester - C"

# Prose cue
python scripts/deconstructor.py build --mode org --target "departments include emergency, radiology, and pharmacy"

python scripts/deconstructor.py plan-fill --id <id>
python scripts/deconstructor.py from-json --path my_inventory.json
python scripts/deconstructor.py validate --id <id>
python scripts/deconstructor.py list
```

Exit codes: `0` ok, `1` critique fail, `2` needs_structure (bare title / unparseable).

Store: `$PIPELINE_DIR/deconstructs/{id}.json` schema `deconstruct.v0`.

## Accepted target shapes

| Shape | Example |
|-------|---------|
| Hierarchy / bullets | `Hospital` then `- Emergency` / `  - triage nurse` |
| Header: children | `Radiology: MRI tech, radiologist` |
| Credits | `Director - Alice` |
| CSV | `Director, Producer, Programmer` |
| Prose cue | `departments include X, Y, and Z` |
| Supplied JSON | `from-json` with full candidate objects |

## Agent workflow

1. Clarify **what** is being deconstructed (not the universe).
2. **Extract real parts** (roles, depts, tools) into structured text — do not rely on a canned template.
3. Pick **mode**; run `build` / `--target-file` or `from-json`.
4. If status `needs_structure`, the target was a bare title — add structure and re-run.
5. Read `critique` — size budget (≤20), closed classes, oracle_hint.
6. `plan-fill` → skill/prompt via register→sandbox→promote; mcp_simple via factory.
7. Do **not** mark `production_graph: true`.

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
