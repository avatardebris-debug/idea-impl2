# P1 held-out suite + goal/tool reasoning traces (plan)

## Have we field-proven n8n-style connectors?

**No — not as a systematic product proof.**

| What exists | Status |
|-------------|--------|
| Workflow/connector YAML engine (`workflow_runner`, `n8n_bridge`) | Code present |
| `workflows/connectors/*.yaml`, `registry_refresh` | Definitions present |
| `run_workflow.py --n8n-health` | Optional n8n ping |
| Ideator synthesis of bridge connectors | Generates draft YAML |
| **Harness canary** (`scripts/connector_canary.py`) | **P1 — proves factory interfaces** |
| Per-connector **field_proven** (end-to-end business bridge works) | **Not done** |

So: **architecture yes, field-proven concept of connectors no.**  
Canary = “CLI/API/workflow load/n8n optional work.”  
Connector field-prove = “bridge A→B produces measured outcome” (future, per slug).

---

## Held-out suite (sketch)

Immutable eval set under `PIPELINE_DIR/eval/held_out/` (never train on):

| id | Kind | Success |
|----|------|---------|
| H1 | Tiny CLI idea → field_proven via grok_build | field PASS |
| H2 | Plan-only: idea → master_plan + tasks.md schema | parse ok |
| H3 | Field repair: broken workspace + field_tests → green or deeper_work | terminal honest |
| H4 | Connector canary | HARD PASS |
| H5 | Goal sandbox (future): mock ledger +$1 | oracle |

Run: `python scripts/run_held_out.py` (TBD) → `metrics/held_out_latest.json`.  
Promote models/recipes only if held_out does not regress.

---

## GitHub + goal reasoning traces (mechanism plan)

### Goal

Collect **structured pairs** for FT:

```text
(context, goal, available_tools, plan) → (tool_calls[], observations[], outcome, oracle)
```

Not free prose only — schema for training.

### Schema (v0 `goal_trace.v1`)

```json
{
  "schema": "goal_trace.v1",
  "goal_id": "...",
  "goal_text": "Open a PR that adds README section X",
  "mode": "github|tool|hybrid",
  "started_at": "ISO",
  "ended_at": "ISO",
  "budget": {"max_tokens": 500000, "max_minutes": 30},
  "plan": [{"step": 1, "intent": "...", "tool": "github.search"}],
  "events": [
    {
      "t": "ISO",
      "type": "think|tool|observe|replan|escalate|oracle",
      "content": "...",
      "tool": "github.create_pr",
      "args": {},
      "result_snip": "...",
      "ok": true
    }
  ],
  "oracle": {"name": "pr_exists", "pass": true, "evidence": "url"},
  "status": "goal_proven|goal_failed|deeper_work_needed",
  "train_weight": 0.0
}
```

### Logging / tooling

| Piece | Role |
|-------|------|
| `pipeline/goal_trace.py` | append event, finalize trace |
| `PIPELINE_DIR/goal_traces/*.jsonl` | store |
| GitHub skill / `gh` wrapper | tool node with allow-list |
| Oracle adapters | `pr_merged`, `issue_closed`, `file_exists`, `mock_balance` |
| `enrich_record_weights` | `goal_proven` mult already reserved (4.0) |

### Workflow (assembly, not bus rewrite)

```text
supervisor: classify goal → template github_goal_v0
researcher: search repos / issues
skeptic: cheap plan attack (optional)
tool: gh clone|branch|commit|pr (sandbox org first)
oracle: measure
finalize: goal_trace + weight
```

### Direct thinking vs tools

- Always log **think** events before tool (for FT of planning).  
- Prefer tool when external truth needed; think when deciding.  
- Failures logged as first-class (recovery traces > pure success).

### Safety

- Default: dry-run / private fork / test org.  
- No auto-public publish without human policy.  
- Substrate (auth scopes, allow-list) untouchable by goal agent.

---

## Backward chain (reminder)

```text
goal_proven (oracle)
  ↑ workflow graph of bricks (skills/tools)
  ↑ field_proven software as stable world nodes
  ↑ tool/GitHub traces teach internal goal policy
  ↑ harness canary proves connectors work at all
```

## Next implementation order

1. Run `python scripts/connector_canary.py --cli-smoke --api-smoke --require-api` regularly / overnight preflight  
2. Held-out H1–H4 fixtures  
3. `goal_trace.v1` logger + one sandbox GitHub goal template  
4. Wire weights into corpus merge export if not already  
