# Dual-engine plan: Grok Build factory track (classic fallback)

**Status:** implemented Phases 0–5 (v1) — 2026-07-19  
**Constraint:** Do **not** replace the existing multi-agent pipeline. Classic engine remains default and always restorable.  
**Out of scope:** Orca (explicitly excluded from v1–v2 of this track).

---

## Goal

Add an **optional execution engine** that runs a **Grok Build–style skill chain** (implement → validate → review → fix → optional deep review → debug → advance gate) against the **same** project state on disk (`projects/<slug>/`), while the current agent graph stays available as `engine=classic`.

Success is measured by comparison runs, not by deleting classic.

---

## v1 scope (frozen)

| Area | Owner |
|------|--------|
| Seeding / master_ideas | shared |
| **idea_planner / phase_planner** | **classic only** |
| implement / validate / review / fix / debug | **grok_build** when `engine=grok_build` |
| Advance / complete / GitHub / ship-prove / corpus | **shared gates** |
| Orca | **excluded** |

---

## Non-goals

- Removing or rewriting `runner.py` core overnight loop as only path  
- Orca integration  
- Auto tool-from-GitHub  
- Replacing ship-prove / missions / GitHub publish  
- Human-must-pilot every step (target is unattended once CLI invoke is solid)

---

## Architecture (high level)

```
master_ideas / seeding / planners  (shared — classic)
              │
              ▼
     project exists: state/, phases/, workspace/
              │
     engine selector (per project or global env)
              │
     ┌────────┴────────┐
     │                 │
     ▼                 ▼
 engine=classic    engine=grok_build
 (current agents)  (skill chain driver)
     │                 │
     └────────┬────────┘
              ▼
  shared gates: checkboxes, review FAIL, complete,
  GitHub publish, ship-prove, corpus
```

**Fallback rules**

| Situation | Behavior |
|-----------|----------|
| `PIPELINE_ENGINE` unset / `classic` | Today’s behavior |
| `PIPELINE_ENGINE=grok_build` | New path for **new seeds** only (`state.engine`) |
| `PIPELINE_ENGINE_GROK_FRACTION` | Optional canary 0–1 on new seeds |
| Grok Build invoke fails / timeout | Log `engine_fallback`, set `engine=classic`, enqueue classic executor |
| Per-project override | `state/current_idea.json` → `"engine": "classic" \| "grok_build"` wins for that project |

---

## Env flags (full)

| Variable | Default | Effect |
|----------|---------|--------|
| `PIPELINE_ENGINE` | `classic` | Seed-time default for new projects |
| `PIPELINE_ENGINE_FALLBACK` | `classic` | Documented fallback (always classic in v1) |
| `PIPELINE_ENGINE_GROK_FRACTION` | `0` | Canary fraction for new seeds |
| `GROK_BUILD_CMD` | unset | Subprocess template: `{workspace}` `{prompt_file}` `{skill}` `{log_file}` |
| `GROK_BUILD_DRY_RUN` | off | Write command to log only |
| `GROK_BUILD_TIMEOUT_S` | `1800` | Per-step timeout |
| `GROK_BUILD_DEEP_REVIEW` | off | Deep review every grok phase |
| `GROK_BUILD_DEEP_REVIEW_LAST` | off | Deep review on last phase only |

---

## Skill chain (Grok Build factory track)

| Step | Logical skill / action | Writes / reads |
|------|------------------------|----------------|
| 0 | Plan already on disk | `master_plan.md`, `phases/phase_N/tasks.md` (**classic planners**) |
| 1 | **Implement** | `workspace/`, mark tasks `[x]` when done |
| 2 | **Validate** | pytest via `run_pytest` (not LLM) |
| 3 | **Code review** | `phases/phase_N/review.md` (compatible with `build_review_result`) |
| 4 | **Implement review fixes** | workspace + tasks |
| 5 | **Comprehensive review** (optional) | `deep_review.md` |
| 6 | **Debug** if validate fails | once per phase |
| 7 | **Advance gate** | checkboxes + non-FAIL review → `_advance_phase` / `_mark_complete` |
| 8 | **Ship / goal** (existing) | ship-prove, Hermes, publish — shared |

---

## Implementation map

| Phase | Deliverable | Location |
|-------|-------------|----------|
| 0 | Spec + scorecard + COMMANDS | this note, `notes/README.md`, `COMMANDS.md`, `notes/experiments/grok-build-engine-README.md` |
| 1 | CLI adapter + dry-run | `pipeline/engines/grok_build.py`, `base.py`, `classic.py` |
| 2 | Driver + hook + fallback | `pipeline/engines/driver.py`, `hook.py`, seed/planner/run_loop wiring |
| 3 | Prompt packs | `pipeline/engines/prompts/*.md` |
| 4 | Deep review + ship handoff docs | `deep_review_phase.md`, COMMANDS |
| 5 | Activity tags, serial=1, fraction canary | `selection.py`, activity events, experiment README |

**Integration points**

- Seed: `pipeline/seeding.py` sets `engine` via `resolve_seed_engine()`
- Idea planner preserves `engine` on state rewrite
- Phase planner skips classic executor when `engine=grok_build`
- Health cycle: `pipeline.engines.hook.tick_grok_build_engines` from `run_loop.py`
- Force classic on a slug: set `"engine": "classic"` in `current_idea.json`

**Serial note (v1):** concurrent Grok Build phase drivers = **1** (process lock in `driver.py`).

---

## Comparison scorecard

See `notes/experiments/grok-build-engine-README.md`. Track at least:

- force-advance rate  
- open tasks at complete  
- pytest count  
- ship-prove outcome  
- wall time  
- token/$ if available  
- `engine_fallback` events  

---

## Fallback contract (must not break)

1. Default engine remains **classic**.  
2. Any grok_build hard failure can demote that project to classic once.  
3. Shared gates (checkboxes, review FAIL, publish, ship) apply to both.  
4. Unsetting `PIPELINE_ENGINE` / unused engines package restores pre-dual behavior for new work.  
5. No Orca dependency in any phase of this plan.

---

## Operator approval checklist

- [x] Dual engine with classic default — yes  
- [x] No Orca in this plan — yes  
- [x] Planners classic in v1 — yes  
- [x] Phases 0–5 implemented — yes  

---

## Tests

```bash
python -m pytest test_engines_grok_build.py test_engines_driver.py -q
python -m pytest test_task_checkboxes.py test_file_rescue.py test_review_artifacts.py test_github_publish.py -q
```
