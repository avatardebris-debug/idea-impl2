# Overnight Grok Build from-list — runbook (P0)

## Goal

Unattended:

```text
seed (engine=grok_build) → plan skills if needed → implement/review
  → complete / complete_with_bugs → thin field ship
  → field_proven | ship_insufficient → next idea
```

until `--time-limit` or list empty.

## Hard requirements

1. **Host stays awake** (AC power, sleep disabled). Sleep freezes Grok mid-step.
2. **One stream only** — no concurrent `bulk_thin_field_ship` or second from-list.
3. **Serial** — `--parallel-seeds 1 --executors 1` (Grok lock is v1 serial).
4. **Env in process** — launcher sets `GROK_BUILD_CMD`; do not rely on shell alone.
5. **Provider split (local vs cloud)**  
   - **Local (default):** `-Provider grok` + `GROK_BUILD_CMD` (Grok CLI for implement / plan skills / field; Grok API for any remaining classic agents). **No Ollama required.**  
   - **Cloud/Vast:** `-Provider ollama -Model <qwen tag>` for cheap planners; keep `GROK_BUILD_CMD` if that box also has Grok CLI, or use `GROK_BUILD_BACKEND=pipeline_llm`.

```powershell
# Local overnight (CLI + API) — default
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 30

# Cloud Ollama path
.\scripts\overnight_grok_from_list.ps1 -Provider ollama -Model qwen3.6:35b-a3b-q4_K_M -TimeLimitMinutes 480
```

## Env contract (set by launcher)

| Variable | Value |
|----------|--------|
| `PIPELINE_DIR` | Output root (`thepipeline`) |
| `PIPELINE_ENGINE` | `grok_build` |
| `GROK_BUILD_BACKEND` | `cli` |
| `GROK_BUILD_CMD` | full `grok.exe … --prompt-file …` |
| `GROK_BUILD_TIMEOUT_S` | `1800` |
| `GROK_BUILD_THIN_SHIP` | `1` |
| `GROK_BUILD_PLAN_SKILLS` | `1` |
| `FIELD_SHIP_REPAIR` | `1` |
| `FIELD_SHIP_REPAIR_BACKEND` | `cli` |
| `PIPELINE_GROK_SIDECAR` | `0` |

## Launch (Windows)

From factory repo:

```powershell
# 30 min dry night (default: --fresh-list-only)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 30

# Full night (8h)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480

# Env/preflight only
.\scripts\overnight_grok_from_list.ps1 -DryRunEnvOnly

# Include orphan re-queue of old in-flight (classic noise)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480 -NoFreshListOnly
```

### Stuck field projects (e.g. video_babbel_enhanced)

Not blacklisted forever. Thin ship / ship re-queue may retry with **accumulative** caps:

| Env | Default | Meaning |
|-----|---------|---------|
| `FIELD_REWORK_MAX_ATTEMPTS` | 3 | Field/thin-ship entries |
| `FIELD_REWORK_MAX_MINUTES` | 45 | Sum of wall minutes across attempts |
| `FIELD_REWORK_MAX_TOKENS` | **2_500_000** | Sum of measured LLM tokens (fairer across fast API vs slow local) |

Token sources: `state/agent_timing.jsonl` + `metrics/llm_calls.jsonl` for the slug during each attempt; if none, rough estimate from `grok_*.log` / prompt sizes (÷4).

When **any** cap is exceeded → status **`deeper_work_needed`** (terminal; not infinite tokens/time).  
Still polishable later if you want a human/deeper pass.

Logs: `$PIPELINE_DIR/logs/overnight_YYYYMMDD_HHMMSS/`

- `preflight.json`
- `runner.log` / `runner.err.log`
- `MORNING.md` + `morning_rows.json`
- `extract.log` (unless `-SkipExtract`)

## Manual equivalent

```powershell
$env:PIPELINE_DIR = "C:\Users\avata\aicompete\thepipeline"
$env:PIPELINE_ENGINE = "grok_build"
$env:GROK_BUILD_BACKEND = "cli"
$env:GROK_BUILD_CMD = 'C:\Users\avata\.grok\bin\grok.exe --cwd "{workspace}" --prompt-file "{prompt_file}" --always-approve --max-turns 40 --output-format plain'
$env:GROK_BUILD_THIN_SHIP = "1"
$env:GROK_BUILD_PLAN_SKILLS = "1"
$env:FIELD_SHIP_REPAIR = "1"
$env:FIELD_SHIP_REPAIR_BACKEND = "cli"
$env:PIPELINE_GROK_SIDECAR = "0"
cd C:\Users\avata\.grok\worktrees\aicompete-idea-impl\idea-impl2
python -u pipeline/runner.py --from-list --parallel-seeds 1 --executors 1 --time-limit 480 --provider ollama --model $env:PIPELINE_MODEL
python scripts/overnight_report.py --log-dir $env:PIPELINE_DIR\logs\manual_morning
python extract.py
```

## Factory guards (code)

| Guard | Behavior |
|-------|----------|
| CLI assert | `PIPELINE_ENGINE=grok_build` + CLI backend + empty `GROK_BUILD_CMD` → **exit 2** |
| Serial assert | parallel seeds/executors >1 without `GROK_BUILD_ALLOW_PARALLEL=1` → **exit 2** |
| Stale driver | Clears stuck `grok_driver_running` after `GROK_BUILD_STALE_S` (default 3600s) |
| Thin ship | Runs for `complete` **and** `complete_with_bugs` |
| Plan skills | `idea_plan` / `phase_plan` before implement if artifacts missing |

## Morning checklist

1. Open `MORNING.md` — field_proven / ship_insufficient / in-flight counts  
2. Kill orphan `grok.exe` if any  
3. Import zip on home machine if Vast: `python import_zip.py <zip> --yes`  
4. Spot-check one `phases/ship/field_test_results.md`  

## Resume after crash

1. Same env contract  
2. `--from-list` or `--resume`  
3. Stale `grok_driver_running` auto-clears after timeout or use report to find stuck slugs  

## Out of scope (not P0)

- Multi-Grok parallel  
- Goal-proven  
- Multi-Vast automation mesh  
- Fine-tune loop  
