# Grok Build dual-engine — experiment scorecard

**Track:** optional `engine=grok_build` beside classic multi-agent pipeline  
**Orca:** excluded (not part of this track)  
**v1 scope:** planners stay classic; Grok owns implement → validate → review → fix  

Use this template when comparing classic vs grok_build on the same idea/plan.

---

## Run metadata

| Field | Classic | Grok Build |
|-------|---------|------------|
| Date | | |
| Slug | | |
| Plan frozen? (same master_plan.md) | | |
| Model / CLI | Ollama / pipeline agents | `GROK_BUILD_CMD=...` |
| `PIPELINE_ENGINE` / state.engine | classic | grok_build |
| Wall clock (phase 1) | | |
| Wall clock (full project) | | |

---

## Scorecard metrics

| Metric | Classic | Grok Build | Notes |
|--------|---------|------------|-------|
| Force-advance rate (phases) | | | |
| Open tasks at complete (`- [ ]`) | | | must be 0 |
| Pytest collected / passed | | | |
| Review FAIL count | | | |
| Engine fallback events | n/a | | `engine_fallback` in activity.jsonl |
| Ship-prove outcome | | | same scripts for both |
| Token / $ if available | | | |
| Human intervention count | | | |

---

## Gates (shared — both engines)

- Task checkboxes closed before advance/complete  
- Review `## Verdict` not FAIL  
- Complete → GitHub publish (if enabled) → ship-prove eligible  

---

## Serial / capacity (v1)

- Concurrent Grok Build phase drivers: **1** (process-wide lock)  
- Classic multi-agent capacity unchanged  

---

## Retrospective (fill after N comparison runs)

- Keep / expand / disable grok_build track:  
- Best fit project types:  
- Main failure modes:  
- Prompt/skill drift notes:  

---

## How to force classic on a slug

Edit `projects/<slug>/state/current_idea.json`:

```json
"engine": "classic"
```

Or re-seed with `PIPELINE_ENGINE=classic` (new seeds only).
