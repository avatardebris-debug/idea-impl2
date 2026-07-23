# Pipeline Command Reference

Quick reference for all commands needed to manage the autonomous pipeline
across local Windows and cloud (Vast.ai / RunPod) instances.

---

## Quality & ops flags

**Task checkbox honesty:** phase advance and full `complete` are blocked while any
`- [ ]` remain in `phases/phase_*/tasks.md`. Review **FAIL** counts as blocking even
if Blocking Bugs says None. Force-advance is refused while checkboxes are open.
Executor must mark tasks `[x]` when Done-when is met (no bulk auto-check).

**File rescue hints:** when the executor auto-moves stray files into the real
project workspace, it writes `state/file_rescue.json` + `state/file_rescue_hint.md`
and injects that block into the **next** executor prompt so the model knows the
canonical path and what was moved.

**Legacy-compatible defaults:** `PIPELINE_REQUIRE_TESTS` and `PIPELINE_STRUCTURAL_GATE`
default **off** so existing in-flight workspaces without tests still validate.
Turn them **on** for strict quality / pre-release runs.

| Variable | Default | Effect |
|---|---|---|
| `PIPELINE_POLISH_FIRST=1` | off | List mode drains `polish_queue.md` before seeding greenfield ideas |
| `PIPELINE_STRUCTURAL_GATE=1` | **off** | Enable local import-graph gate in validator (third-party missing = warning only) |
| `PIPELINE_REQUIRE_TESTS=1` | **off** | Fail validation when code exists but no tests collected |
| `PIPELINE_INVOKE_BEFORE_SEED=1` | off | Skip seeding when a verified capability strongly matches the idea |
| `CAPABILITY_REUSE_MIN_SCORE` | `4.0` | Score threshold for hard reuse skip |
| `PIPELINE_FORCE_ADVANCE_QUALITY_RISK=0` | on (risk tag default) | Set `=0` to skip quality_risk on force-advance |
| `CORPUS_GATE_POLICY=enforce` | `warn` | Block finetune corpus collect on gate failure |

### Dual-engine (Grok Build factory track)

**Default remains classic multi-agent.** Grok Build is optional and only owns
implement → validate → review → fix for projects with `"engine": "grok_build"`.
Planners (`idea_planner`, `phase_planner`) stay classic in v1. **Orca is not used.**

Shared gates still apply: task checkboxes, review FAIL, complete, GitHub publish, ship-prove.

| Variable | Default | Effect |
|---|---|---|
| `PIPELINE_ENGINE` | `classic` | `classic` = today’s agents. `grok_build` = set `"engine": "grok_build"` on **new seeds only** |
| `PIPELINE_ENGINE_GROK_FRACTION` | `0` | Canary: fraction of new seeds (0–1) get grok_build when `PIPELINE_ENGINE` is not forced to grok_build |
| `PIPELINE_ENGINE_FALLBACK` | `classic` | Documented fallback target (always classic in v1) |
| `GROK_BUILD_CMD` | unset | CLI template with `{workspace}` `{prompt_file}` `{skill}` `{log_file}` |
| `GROK_BUILD_DRY_RUN=1` | off | Log intended command under `phases/phase_N/grok_<step>.log` without executing |
| `GROK_BUILD_TIMEOUT_S` | `1800` | Per-step subprocess timeout |
| `GROK_BUILD_DEEP_REVIEW=1` | off | Run optional deep review skill every grok phase |
| `GROK_BUILD_DEEP_REVIEW_LAST=1` | off | Deep review only on last planned phase |
| `GROK_BUILD_BACKEND` | `auto` | `auto` = CLI if `GROK_BUILD_CMD` set else `pipeline_llm`; `cli` = require grok.exe template; `pipeline_llm` = ollama/qwen/openai via `llm_interface` |
| `GROK_BUILD_ALLOW_PIPELINE_LLM` | on | When `auto` and no CLI, use pipeline LLM for skill steps |
| `GROK_BUILD_PROVIDER` / `GROK_BUILD_MODEL` | fall back to `PIPELINE_*` | Provider/model for `pipeline_llm` build steps |
| `GROK_BUILD_THIN_SHIP` | on | After grok_build complete, run in-process field plan+run → `field_proven` / `ship_insufficient` (skip classic thermo) |
| `GROK_BUILD_PLAN_SKILLS` | on | Before implement: run `idea_plan` if no `master_plan.md`, `phase_plan` if no `tasks.md` (Grok skills `idea-plan` / `phase-plan`) |
| `GROK_BUILD_ALLOW_PARALLEL` | off | Allow `--parallel-seeds`/`--executors` >1 with `PIPELINE_ENGINE=grok_build` (default refuse — serial v1) |
| `GROK_BUILD_STALE_S` | `3600` | Clear stuck `grok_driver_running` if state older than this many seconds |
| `FIELD_REWORK_MAX_ATTEMPTS` | `3` | Thin-ship / field rework entries before `deeper_work_needed` |
| `FIELD_REWORK_MAX_MINUTES` | `45` | Accumulative field rework wall minutes before `deeper_work_needed` |
| `FIELD_REWORK_MAX_TOKENS` | `2500000` | Accumulative measured tokens (agent_timing / llm_calls; Grok CLI ~log char÷4 fallback) |
| `FIELD_IDLE_PARK_MINUTES` | `20` | Empty-queue + no LLM for this long on field_testing → `deeper_work_needed` so seed continues |
| `BUDGET_ACTIVE_CLOCK` | on | Budget uses active work, not calendar sleep gaps |
| `BUDGET_IDLE_GAP_MINUTES` | `45` | Idle longer than this pauses the budget clock |
| `BUDGET_BE1_AUTO_RETRY` | on | Strike-1 `budget_exceeded` → clean resume |
| `BUDGET_BE2` | on | Strike-2 → debug or thin_field path flag |
| `BUDGET_BE3_BLOCKER` | on | Strike-3 → `blocker_report.v1` + manager menu |
| `BUDGET_PREREQ_RESET` | on | Reset unlocked BE prereq once when seed blocked by requires |
| `FIELD_PLAN_ENGINE` | `auto` | Field plan source: `auto` \| `grok` \| `pipeline_llm` \| `heuristic` \| `none` |
| `FIELD_PLAN_PROVIDER` / `FIELD_PLAN_MODEL` | fall back to `PIPELINE_*` | Overrides for field plan LLM only |
| `FIELD_SHIP_USEFULNESS` | on | Write `phases/ship/usefulness_report.md` (honesty; goal_fitness later) |
| `FIELD_SHIP_ALLOW_CLASSIC` | off | Allow thin field ship for classic-engine projects (bulk port of `complete`) |
| `FIELD_SHIP_BULK` | off | Force thin-ship eligibility for bulk CLI |
| `FIELD_SHIP_STATUSES` | `complete` | Comma statuses bulk/ship-prove thin path may pick |
| `FIELD_SHIP_REPAIR` | on | On field FAIL: bridge repair chain (not full grok_build) |
| `FIELD_SHIP_REPAIR_MAX` | `3` | Max steps: 1=field_fail_repair, 2=+debug, 3=+code_review, 4=+comprehensive report |
| `FIELD_SHIP_REPAIR_BACKEND` | `auto` | `auto`/`cli`/`pipeline_llm` for repair skill steps |
| `PRE_FORCE_SYSTEMATIC_DEBUG` | on | Classic: one systematic-debugging executor pass before force-advance |
| `PIPELINE_COMPLETE_PYTEST` | on | At complete: re-run pytest; red (or force_advanced) → `complete_with_bugs` |
| `PIPELINE_COMPLETE_PYTEST_TIMEOUT` | (pytest internal) | Per-test timeout hint for complete gate |
| `PIPELINE_CLOUD` | off | Cloud layout (`.pipeline/`); also enables cloud parallel + bus-wake defaults |
| `PIPELINE_CLOUD_PARALLEL_SEEDS` | `2` when cloud | Default `--parallel-seeds` when `PIPELINE_CLOUD=1` and CLI not passed |
| `PIPELINE_CLOUD_EXECUTORS` | `2` when cloud | Default `--executors` when `PIPELINE_CLOUD=1` and CLI not passed |
| `PIPELINE_PROJECT_LOCK` | on when cloud | Per-slug lock file so multi-executors do not work the same project |
| `PIPELINE_PROJECT_LOCK_STALE_S` | `1800` | Mtime fallback when lock PID unknown; live PID never reclaimed by age alone |
| `PIPELINE_TIMEOUT_LOCK_JOIN_S` | `30` | After phase timeout, grace-join handle thread; if dead, release lock; if alive, start reaper |
| `PIPELINE_ZOMBIE_LOCK_HARD_S` | `3600` | Max hold for zombie project lock before force-release |
| `PIPELINE_BUS_WAKE` | on when cloud | Touch `state/bus_wake` on send; agents short-poll mtime/token (0.2–1s) |
| `PIPELINE_BUS_WAKE_TIMEOUT` | `0.5` | Seconds between wake checks when `PIPELINE_BUS_WAKE=1` |
| `PIPELINE_GROK_SIDECAR` | `0` | Optional **serial** one-shot Grok implement/fix for stuck classic phases (not default cloud path) |
| `PIPELINE_GROK_SIDECAR_MIN_RETRIES` | `3` | Min fix retries before sidecar may run (manager / PHASE_STUCK; uses real payload retry_count) |

### Cloud classic parallel (not Grok-Build parallel)

With `PIPELINE_CLOUD=1`, if you do **not** pass `--parallel-seeds` / `--executors`, the runner
applies `PIPELINE_CLOUD_PARALLEL_SEEDS` (default **2**) and `PIPELINE_CLOUD_EXECUTORS`
(default **2**). Explicit CLI always wins. Grok-Build engine sessions stay **serial (1)**.

```bash
export PIPELINE_CLOUD=1
# Uses seeds=2 executors=2 unless overridden:
python pipeline/runner.py --from-list --provider ollama --model "$PIPELINE_MODEL" --time-limit 600
# Explicit override:
python pipeline/runner.py --from-list --parallel-seeds 1 --executors 1 ...
```

**Project lock:** the SQLite bus serializes *message* claim only. With multiple executors,
`PIPELINE_PROJECT_LOCK` (default on under cloud) uses `projects/<slug>/state/project.lock`
so two agents do not process the same slug at once.

**Bus wake:** `MessageBus.send` touches `state/bus_wake`. Agents short-poll instead of only
long idle sleeps. Disable: `PIPELINE_BUS_WAKE=0`.

**Phase fix memory:** on validation FAIL, classic writes
`projects/<slug>/state/phase_N_fix_memory.json` (`attempts` + `banned_signatures`) and
injects banned signatures + last 3 attempts into executor fix prompts.

**LLM wait metrics (instrumentation only — no vLLM deploy):**

```bash
python -m pipeline.llm_metrics
python -m pipeline.llm_metrics --last 100 --json
# Writes: PIPELINE_DIR/metrics/llm_calls.jsonl  + activity event llm_call
```

**Optional Grok sidecar** (classic stuck rescue; serial; default off):

```bash
export PIPELINE_GROK_SIDECAR=1
export GROK_BUILD_CMD='your-grok-cli --workspace {workspace} --prompt {prompt_file} --skill {skill}'
# or dry-run: GROK_BUILD_DRY_RUN=1
# Invoked at most once per phase from manager FIX_ANALYSIS / PHASE_STUCK after min retries.
# Does not set engine=grok_build permanently. See pipeline/grok_sidecar.maybe_run_sidecar_fix.
```

**Statuses:** `complete` = phases done + final pytest clean. `complete_with_bugs` = phases done
but pytest failed at complete and/or force_advanced/quality_risk — still ship/field eligible
and unlocks deps; marks quality for corpus/ops.

**Systematic debugging:** installed for TUI under `~/.grok/skills/systematic-debugging`
(and Superpowers plugin). Pipeline does **not** auto-load skills unless injected —
field step 2 and pre-force-advance load the skill body via `pipeline.skill_load`.

**Field repair bridge** (on FAIL, no full engine re-run; **max 3 fix retries** by default):

1. `field_fail_repair` — field-test skill style (fix plan and/or minimal product code)  
2. `field_systematic_debug` — systematic debug + minimal fix  
3. `field_code_review` — focused structure review (+ tiny fix if obvious)  

Re-runs field after each step. If still FAIL → write **`phases/ship/field_evaluation.md`**
(evaluation + recommended next steps; closes the loop — no infinite retry).  
Optional 4th (`FIELD_SHIP_REPAIR_MAX=4`): LLM comprehensive report.  
Also: `field_repair_log.md`.

```bash
# Bulk field-test classic completes (no re-review / no thermo) — start small
export PIPELINE_DIR=C:/Users/avata/aicompete/thepipeline
export FIELD_SHIP_ALLOW_CLASSIC=1
export FIELD_PLAN_ENGINE=heuristic   # or pipeline_llm / auto
python scripts/bulk_thin_field_ship.py --include-classic --limit 5 --dry-run
python scripts/bulk_thin_field_ship.py --include-classic --limit 5
# Re-try prior ship_insufficient with better plans:
python scripts/bulk_thin_field_ship.py --include-classic --retry-insufficient --plan-engine pipeline_llm --limit 10
```

```bash
# Dry-run adapter smoke (no real Grok CLI required)
export GROK_BUILD_DRY_RUN=1
export GROK_BUILD_CMD='echo skill={skill} ws={workspace} >> {log_file}'
python -m pipeline.engines.grok_build --help
python -m pipeline.engines.grok_build --slug my_slug --phase 1 --step implement --dry-run

# Enable Grok Build for new seeds only (classic always remains fallback)
export PIPELINE_ENGINE=grok_build
export GROK_BUILD_CMD='your-grok-cli --workspace {workspace} --prompt {prompt_file} --skill {skill}'

# 10% canary on new seeds (while default stays classic)
export PIPELINE_ENGINE_GROK_FRACTION=0.1

# Force one in-flight project back to classic agents
# Edit projects/<slug>/state/current_idea.json → "engine": "classic"
```

**Fallback:** hard invoke failure / timeout sets `engine=classic`, logs activity
`engine_fallback`, and enqueues the classic executor. Concurrent Grok sessions
are **serial (1)** in v1. Integration hook: `pipeline.engines.hook.tick_grok_build_engines`
from the main health cycle (at most **one** grok project per health tick).

**Hard vs soft exits (driver policy)**

| Step | Hard (→ classic fallback) | Soft |
|------|---------------------------|------|
| implement | any non-success (except dry-run) | dry-run success |
| debug / review / fix | exit **127** (missing CLI) or **124** (timeout) | other non-zero: continue only if a real `review.md` with `## Verdict` exists |
| missing / incomplete review | n/a | **blocked** (FAIL stub written — **never** auto-PASS) |
| pytest red after debug | n/a | **blocked** (no advance/complete) |
| gate blocked ≥5 cycles | demote to classic | earlier cycles re-enter after backoff |

Overflow batches (`phase_N_overflow/tasks.md`) under `engine=grok_build` re-enter the
Grok driver — classic executor is **not** dual-scheduled.

**Thin ship (grok_build closed loop):** on full complete, `run_thin_field_ship` plans
`phases/ship/field_tests.md` (Grok CLI → pipeline LLM e.g. qwen → heuristic), runs
`field_test_runner`, writes results + usefulness report, sets `field_proven` or
`ship_insufficient`. Classic `--ship-prove` uses the same thin path for
`engine=grok_build` projects; other engines still queue `field_test_planner`.

```bash
# Local/qwen build steps without grok.exe (optional)
export PIPELINE_ENGINE=grok_build
export GROK_BUILD_BACKEND=pipeline_llm
export PIPELINE_PROVIDER=ollama
export PIPELINE_MODEL=qwen3.6:35b-a3b-q4_K_M
export FIELD_PLAN_ENGINE=pipeline_llm   # or heuristic / auto

# Grok CLI for implement; local LLM only for field plan
export GROK_BUILD_CMD='C:\Users\avata\.grok\bin\grok.exe --cwd "{workspace}" --prompt-file "{prompt_file}" --always-approve --max-turns 40 --output-format plain'
export FIELD_PLAN_ENGINE=auto
```

### Overnight Grok from-list (P0 hardened)

```powershell
# Preflight + env freeze only
.\scripts\overnight_grok_from_list.ps1 -DryRunEnvOnly

# 30 min dry night (host must stay awake)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 30

# Full 8h night (default --fresh-list-only; no extract zip)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480

# Cloud zip after run
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480 -DoExtract

# Also orphan-requeue old in-flight (can waste hours on classic field_testing zombies)
.\scripts\overnight_grok_from_list.ps1 -TimeLimitMinutes 480 -NoFreshListOnly

# Morning report only
python scripts/overnight_report.py --log-dir $env:PIPELINE_DIR\logs\overnight_YYYYMMDD_HHMMSS
```

Runbook: `notes/2026-07-22-overnight-grok-from-list-runbook.md`  
Guards: `pipeline/engines/overnight_guard.py` (CLI assert, serial refuse, stale driver clear).  
Thin ship also runs for **`complete_with_bugs`**.  
Stuck field loops: rework caps (`FIELD_REWORK_MAX_*`) + **idle park** after `FIELD_IDLE_PARK_MINUTES` (default 20) empty-queue stall → **`deeper_work_needed`**, then seed continues.

Plan + scorecard: `notes/2026-07-19-grok-build-factory-dual-engine-plan.md`,
`notes/experiments/grok-build-engine-README.md`.

```bash
# Ops dashboard (active projects + recent activity.jsonl)
python -m pipeline.pipeline_status

# Strict quality profile (new projects / pre-release)
export PIPELINE_REQUIRE_TESTS=1
export PIPELINE_STRUCTURAL_GATE=1
# Ship-prove enables both automatically via setdefault (override with =0 before run)
# Corpus harvest (--collect-all) defaults CORPUS_GATE_POLICY=enforce

# Polish incomplete / mvp_complete projects first
export PIPELINE_POLISH_FIRST=1
python pipeline/runner.py --from-list --provider ollama --model qwen3.6:35b-a3b-q4_K_M

# Finetune harvest (prefer quality wins)
export CORPUS_GATE_POLICY=enforce
python -m pipeline.corpus_collector --collect-all
```

### Ship-prove (controlled)

Clears stale **ship-agent** bus messages, then runs field-test → evaluate.
Prompts: `pipeline/prompts/field_test_planner.md`, `ship_evaluator.md`.

```bash
# Cloud / Linux — one slug (recommended for first proof)
chmod +x scripts/run_ship_prove.sh
./scripts/run_ship_prove.sh --slug ship_canary --provider grok --model grok-4.3

# Serial ship over status=complete only (do not mass-requeue old field_test_planning)
./scripts/run_ship_prove.sh --serial --provider grok --model grok-4.3

# Detach overnight ship-prove
SHIP_PROVE_BACKGROUND=1 ./scripts/run_ship_prove.sh --serial --provider grok --model grok-4.3

# Overnight main list/polish instead of ship (safer when complete count is 0)
./scripts/run_ship_prove.sh --main-pipeline --provider ollama --model qwen3.6:35b-a3b-q4_K_M
# or: SHIP_PROVE_BACKGROUND=1 ./scripts/run_ship_prove.sh --main-pipeline ...

# Windows
.\scripts\run_ship_prove.ps1 -Slug ship_canary -Provider grok -Model grok-4.3
.\scripts\run_ship_prove.ps1 -MainPipeline
```

**Do not** run unfiltered `--ship-prove` while dozens of projects sit in `field_test_planning` /
`ship_insufficient` without clearing the ship bus — use the script. Eligibility is
`status=complete` only (terminals are skipped).

### Per-project GitHub publish

On **`complete`** and **`field_proven`**, the pipeline **local-commits** the whole
`projects/<slug>/` tree (workspace + state + phases). **Push to GitHub is opt-in** and
best-effort (never fails the project).

```bash
# Enable remote publish (private repos under your org)
export PIPELINE_GITHUB_PUBLISH=1
export PIPELINE_GITHUB_ORG=your-github-org
export PIPELINE_GITHUB_REPO_PREFIX=pipe-          # repo = pipe-<slug>
export PIPELINE_GITHUB_VISIBILITY=private
export PIPELINE_GITHUB_ON=complete,field_proven   # default
export GIT_COMMIT_AUTHOR="You <you@example.com>"
# Auth: gh auth login   OR   GITHUB_TOKEN=...

# Manual / backfill (local only)
python scripts/publish_project_github.py --slug ship_canary --local-only

# Manual push one project
python scripts/publish_project_github.py --slug ship_canary --push

# All complete + field_proven
python scripts/publish_project_github.py --all-eligible --push
```

Status written to `projects/<slug>/state/github_status.json`.  
Whole-`PIPELINE_DIR` backup remains `scripts/sync_output_repo.py` (separate job).

Statuses: `complete` = all planned phases done; `mvp_complete` = plan exhausted early
(phase &lt; total_phases) — does **not** unlock `requires:` deps; use `--polish` or polish-first.

---

## GPU & System Monitoring

```bash
# GPU snapshot (utilization, VRAM, processes)
nvidia-smi

# Live GPU monitor (refresh every 2s)
watch -n 2 nvidia-smi

# GPU memory only
nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,utilization.gpu \
    --format=csv,noheader

# What Ollama has loaded in VRAM right now
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# CPU / RAM
htop
free -h

# Disk usage
df -h
du -sh .pipeline/
```

---

## Ollama Model Management

```bash
# List installed models (with size + last used)
ollama list

# Pull the standard pipeline model
ollama pull qwen3.6:35b-a3b-q4_K_M     # ~23GB, fits single A10/3090/4090

# Pull full MoE (needs 48GB+ — good for 2×A10)
ollama pull qwen3.6:35b

# Remove a model (free VRAM/disk)
ollama rm qwen3.5:35b
ollama rm qwen3.5:27b-q4_K_M

# Remove ALL models except qwen3.6
ollama list | awk 'NR>1 {print $1}' | grep -v "qwen3.6" | \
    xargs -I{} ollama rm {}

# Ollama server status
curl -s http://localhost:11434/api/tags | python3 -m json.tool

# Restart Ollama (if it hangs)
pkill ollama && sleep 2
OLLAMA_HOST=0.0.0.0:11434 nohup ollama serve > /tmp/ollama.log 2>&1 &

# Tail Ollama logs
tail -f /tmp/ollama.log
```

---

## Running the Pipeline

```bash
# Light model for planners/validator/manager; heavy for executor/reviewer
export PIPELINE_LIGHT_MODEL=qwen3.6:8b-q4_K_M   # optional but recommended

# Standard run (600 min time limit)
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M --time-limit 600 \
    --base-budget 120 --phase-budget 45

# Run with full MoE model (2×A10 recommended)
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b --time-limit 600

# Background / overnight run (no time limit)
nohup python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M \
    > pipeline_run.log 2>&1 &

# Follow the log
tail -f pipeline_run.log

# Resume after a crash / restart
python pipeline/runner.py --resume --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M

# Resume ai_movie_generation_suite (phases 4–7 after prep)
# State: phase_4_planning, phase=3, total_phases=7 — see
# .pipeline/projects/ai_movie_generation_suite/state/PROJECT_RESUME.md
python pipeline/runner.py --resume --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M

# Polish (missing phases on complete/budget_exceeded projects):
python reset_budget_exceeded.py --generate-polish   # refresh polish_queue.md from disk
python pipeline/runner.py --polish --provider ollama --model qwen3.6:35b-a3b-q4_K_M
# Status: .pipeline/state/polish_status.json (run_state: running | terminated)
# Mid-phase work: use --resume, not --polish. Do NOT use --ideas-file for polish (use --polish-queue).

# Capability registry (default) vs legacy pre-fork behavior
python pipeline/runner.py --from-list --provider ollama --model qwen3.6:35b-a3b-q4_K_M
python pipeline/runner.py --from-list --legacy --provider ollama --model qwen3.6:35b-a3b-q4_K_M
python scripts/build_capability_registry.py
python scripts/build_capability_registry.py --list --domain robotics
python scripts/build_capability_registry.py --graph      # scripts/capability_graph.dot
python scripts/build_capability_registry.py --blocked    # master_ideas blocked by requires:
python scripts/gen_backlog_audit.py                      # includes Blocked downstream section
# Overrides: .pipeline/state/capability_overrides.yaml then rebuild

# Tool lifecycle (Phase 6): review -> shared_lib draft; complete -> verified + promote libs;
# Hermes achieved -> hermes_task row. Metrics: .pipeline/state/capability_metrics.jsonl
python scripts/capability_metrics_report.py
# MCP (Cursor): .cursor/mcp.json → scripts/mcp_idea_capabilities_server.py
#   pip install mcp>=1.2.0
#   Tools: list/describe/suggest/invoke capabilities, registry_blocked_ideas
# Legacy line protocol: scripts/mcp_capability_server.py

# Multi-instance registry sync (cloud ↔ local):
python scripts/sync_capability_registry.py export --copy-root --metrics
git add capability_registry_export.json   # optional commit
# other machine:
python scripts/sync_capability_registry.py merge
# or: import_zip auto-merges .pipeline/state/capability_registry_export.json from zip
# full replace: python scripts/sync_capability_registry.py replace --sqlite path/to/registry.sqlite
# See .pipeline/docs/capability_registry.md

# Workflows / connectors (compose capabilities; optional self-hosted n8n):
python scripts/run_workflow.py registry_refresh
python scripts/run_workflow.py registry_refresh --export-n8n .pipeline/workflows/exports/registry_refresh.n8n.json
python scripts/run_workflow.py --n8n-health   # N8N_BASE_URL, N8N_API_KEY
# invoke_capability('registry_refresh') when status: verified in YAML
# See .pipeline/docs/workflows.md (under PIPELINE_DIR)

# P1 harness canary (CLI/API/workflow load — NOT product field_proven of bridges):
python scripts/connector_canary.py
python scripts/connector_canary.py --cli-smoke --api-smoke --require-api
# Report: $PIPELINE_DIR/metrics/connector_canary_latest.md
# Plan: notes/2026-07-22-p1-held-out-and-goal-traces.md

# P1 held-out gates (dep policy, budget ladder, canary, goal_trace sandbox):
python scripts/run_held_out.py
python scripts/run_held_out.py --json
# Report: $PIPELINE_DIR/metrics/held_out_latest.{json,md}

# Goal traces (goal_trace.v1 under $PIPELINE_DIR/goal_traces/):
# python -c "from pipeline.goal_trace import sandbox_file_exists_goal; from pathlib import Path; print(sandbox_file_exists_goal(Path('README.md'))['status'])"

# Budget yield ladder: budget_exceeded is a yield (strikes 1→2→3), not permanent death.
# Skill /blocker-identifier produces the same blocker_report.v1 schema for manual BE3.

# User steering dropbox (runner polls every 10 min; manager replies in-file):
# Edit dropbox.md at repo root — see template inside the file.
# Example:
#   ### USER msg-20260520-001
#   target: my_project_slug
#   Add export to MP4 before phase 3 review.

# Agent tools (default runner only; disabled with --legacy):
#   suggest_capabilities, list_capabilities, describe_capability, invoke_capability

# Path leak cleanup (repo scripts copied into project workspaces)
python health_check.py              # report shadow files across all projects
python health_check.py --fix        # delete import_zip/health_check/pipeline/ nests, etc.

# Hermes tasks (--hermes at end of a master_ideas line): auto-clones on first use
# hermes-agent-main/ is gitignored; runner clones https://github.com/NousResearch/hermes-agent
# and pip install -e hermes-agent-main unless HERMES_AUTO_INSTALL=0
# export HERMES_AUTO_INSTALL=1   # default — auto clone + pip on first --hermes task
# export HERMES_AUTO_INSTALL=0   # fail fast, manual clone instead
# export HERMES_INSTALL_RETRY_MINUTES=15  # after bootstrap fail, skip that idea this long
# export HERMES_INSTALL_ATTEMPTS=3       # clone/pip retries within one ensure call
# export HERMES_SKIP_PIP=1       # clone only, you install deps yourself

# Single idea (quick test)
python pipeline/runner.py "Build a Python word counter CLI" \
    --provider ollama --model qwen3.6:35b-a3b-q4_K_M

# Stop gracefully
Ctrl+C
# or kill background run:
pkill -f pipeline/runner.py
```

### Goals (`--goal` decomposition)

```bash
# List decomposed goals and runnable branch counts
python pipeline/runner.py --list-goals

# Attempt branches (capabilities or Hermes) for a goal tree
python pipeline/runner.py --attempt-goal GOAL_ID \
    --provider ollama --model qwen3.6:35b-a3b-q4_K_M

# Single branch only
python pipeline/runner.py --attempt-goal GOAL_ID --attempt-branch branch_1

# Goal trees live in .pipeline/goals/<id>.json (or $PIPELINE_DIR/goals/)
# Parent --goal lines stay unchecked until all branches are achieved.
```

### Output directory (`PIPELINE_DIR`)

```bash
# Local: sibling thepipeline/ if it has projects/
# Cloud: export PIPELINE_CLOUD=1 → factory/.pipeline (cloned from GitHub)
export PIPELINE_DIR=/path/to/your/.pipeline   # explicit override

# Runner prints resolved output on startup after bootstrap.
```

---

## State / Queue Management

```bash
# Check what's in the queue right now
ls -la .pipeline/queues/
wc -l .pipeline/queues/*.jsonl 2>/dev/null

# Show active project state
cat .pipeline/projects/*/state/current_idea.json | python3 -m json.tool

# Force a project to budget_exceeded (skip it)
python3 -c "
import json, pathlib, sys
slug = sys.argv[1]
p = pathlib.Path(f'.pipeline/projects/{slug}/state/current_idea.json')
d = json.loads(p.read_text())
d['status'] = 'budget_exceeded'
d['budget_note'] = 'Manually skipped'
p.write_text(json.dumps(d, indent=2))
print(f'Marked {slug} as budget_exceeded')
" YOUR_SLUG_HERE

# Force a project to complete
python3 -c "
import json, pathlib, sys
slug = sys.argv[1]
p = pathlib.Path(f'.pipeline/projects/{slug}/state/current_idea.json')
d = json.loads(p.read_text())
d['status'] = 'complete'
p.write_text(json.dumps(d, indent=2))
print(f'Marked {slug} as complete')
" YOUR_SLUG_HERE

# Clear stale queue messages for a specific project
python3 -c "
import pathlib, json, sys
slug = sys.argv[1]
cleared = 0
for q in pathlib.Path('.pipeline/queues').glob('*.jsonl'):
    lines = [l for l in q.read_text().splitlines() if l.strip()]
    kept = []
    for line in lines:
        msg = json.loads(line)
        if slug not in str(msg.get('payload', {})):
            kept.append(line)
        else:
            cleared += 1
    q.write_text('\n'.join(kept) + ('\n' if kept else ''))
print(f'Cleared {cleared} message(s) for {slug}')
" YOUR_SLUG_HERE

# Clear ALL queues (nuclear option — then restart runner)
> .pipeline/queues/idea_planner.jsonl
> .pipeline/queues/phase_planner.jsonl
> .pipeline/queues/executor.jsonl
> .pipeline/queues/validator.jsonl
> .pipeline/queues/reviewer.jsonl
> .pipeline/queues/manager.jsonl
> .pipeline/queues/ideator.jsonl
```

---

## Git Workflow (Cloud → Local)

```bash
# --- On CLOUD ---
# Harvest state into a zip (run from project root)
bash harvest.sh

# --- On LOCAL (Windows PowerShell) ---
# Import latest zip (auto-detects newest in Downloads)
python import_zip.py --yes

# Import and also sync shared files
python import_zip.py --yes --shared

# Import a specific zip
python import_zip.py path/to/pipeline_extract_XXXXXXXX.zip --yes

# Push everything to git
git add .pipeline/ master_ideas.md
git commit -m "import: <describe what ran>"
git push

# --- On CLOUD ---
# Pull latest code + state
git pull

# If git pull fails (local changes conflict):
git stash          # save cloud's changes temporarily
git pull
git stash pop      # restore cloud's changes on top
# If conflict on a specific file (accept cloud version):
git checkout --theirs path/to/file.json
git add path/to/file.json
git stash drop
```

---

## Fresh Instance Setup (without cloud_setup.sh)

```bash
git clone https://github.com/avatardebris-debug/idea.git "idea impl"
cd "idea impl"
pip install pyyaml ruff pytest

# Clone output repo (cloud) or use ../thepipeline locally
export PIPELINE_CLOUD=1
git clone --depth 1 https://github.com/avatardebris-debug/pipeline.git .pipeline

# Confirm no stale models then pull the right one
ollama list
ollama rm qwen3.5:35b 2>/dev/null || true     # remove if pre-installed
ollama pull qwen3.6:35b-a3b-q4_K_M

# Run
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M --time-limit 600
```

---

## Using cloud_setup.sh (Full Setup)

```bash
chmod +x cloud_setup.sh
bash cloud_setup.sh

# After it completes, PIPELINE_MODEL and PIPELINE_CLOUD are exported.
# The runner bootstraps .pipeline/ and Hermes on first run:
source .venv/bin/activate
export PIPELINE_CLOUD=1
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b-a3b-q4_K_M --parallel-seeds 3 --executors 2 \
    --auto-tune --max-seeds 4 --time-limit 600

# Override model:
MODEL=qwen3.6:35b bash cloud_setup.sh    # full MoE (needs 48GB+)
```

---

## 2×A10 Specific (48GB VRAM)

```bash
# Full MoE model — no quantisation needed at 48GB
ollama pull qwen3.6:35b
python pipeline/runner.py --from-list --provider ollama \
    --model qwen3.6:35b --time-limit 600

# Or run TWO parallel instances on separate GPUs
# Instance 1 (GPU 0):
CUDA_VISIBLE_DEVICES=0 OLLAMA_HOST=0.0.0.0:11434 ollama serve &
# Instance 2 (GPU 1) — different port:
CUDA_VISIBLE_DEVICES=1 OLLAMA_HOST=0.0.0.0:11435 ollama serve &
# Then point each runner at a different OLLAMA_HOST
OLLAMA_HOST=http://localhost:11434 python pipeline/runner.py ...
OLLAMA_HOST=http://localhost:11435 python pipeline/runner.py ...
```

---

## Debugging

```bash
# Check agent log files
tail -f .pipeline/logs/executor.out
tail -f .pipeline/logs/validator.out
tail -f .pipeline/logs/manager.out
ls -lt .pipeline/logs/

# Check pipeline status
cat .pipeline/state/pipeline_status.json

# Check reusable tools discovered so far
cat .pipeline/state/reusable_tools.md

# List all projects and their status
python3 -c "
import json, pathlib
for p in sorted(pathlib.Path('.pipeline/projects').glob('*/state/current_idea.json')):
    try:
        d = json.loads(p.read_text())
        print(f\"{d.get('status','?'):20s} {d.get('_slug','?')}\")
    except: pass
"

# Check idea generation logs
ls .pipeline/state/idea_generation_log_*.md 2>/dev/null
cat .pipeline/state/idea_generation_log_*.md 2>/dev/null | tail -50

# Force ideator to run now (add generate_ideas message manually)
python3 -c "
from pipeline.message_bus import MessageBus, Message
import pathlib
bus = MessageBus(pathlib.Path('.pipeline/queues'))
msg = Message.create('manual','ideator','generate_ideas',{'master_ideas_path':'master_ideas.md'})
bus.send(msg)
print('Queued generate_ideas for ideator')
"
```

---

## Completion truth (`truth.md` + `completions.jsonl`)

**Source of truth:** `truth.md` (readable) and `.pipeline/state/completions.jsonl` (machine).

**Working queue:** `master_ideas.md` — copy/paste from your backup folder as usual.

Before seeding, the runner **removes** lines from `master_ideas.md` that already appear in truth
(same slug/title). Pasting an old backup will not re-queue finished work.

```bash
# After copying master_ideas from backup — trim completed lines manually
python extract.py --pipeline-dir .pipeline --sync-ideas

# Rebuild truth.md from all complete projects + jsonl
python extract.py --rebuild-truth

# Health check --fix: marks validation_gap complete + updates truth + trims queue
python health_check.py --fix
```

On `✅ completed all phases!` the runner appends to truth/jsonl (with **description**) and trims that line from `master_ideas.md`.

**Descriptions:** stored in `completions.jsonl` (full, up to 2000 chars) and a short `desc:` line in `truth.md`.
Also kept in `.pipeline/projects/<slug>/state/current_idea.json` on disk.

**budget_exceeded:** NOT added to truth and NOT trimmed from `master_ideas.md` — still on your queue.
Retry with `python reset_budget_exceeded.py --reset-all` (only touches project state, not truth).

---

## Grok Build sidecar (GPU offload)

Grok handles planning/implement/debrief; the runner keeps **executor on Ollama**.
Artifacts (`tasks.md`, `workspace/`, `validation_report.md`) stay the harvest + truth contract.

```bash
# Paths + validation state for a project phase
python -m pipeline.grok_sidecar status --slug my_project --phase 1

# JSON pack to paste into a Grok session (tasks, plans, reports)
python -m pipeline.grok_sidecar context --slug my_project --phase 1

# Deterministic pytest (same as validator agent) — no GPU
python -m pipeline.grok_sidecar validate --slug my_project --phase 1

# After Grok implement: template → fill → import to bug_resolutions.jsonl
python -m pipeline.grok_sidecar debrief-template --slug my_project --phase 1
# edit .pipeline/projects/<slug>/phases/phase_1/grok_debrief.json
python -m pipeline.grok_sidecar record-bugs --slug my_project --phase 1 \
    --file .pipeline/projects/my_project/phases/phase_1/grok_debrief.json

# Provenance for finetune (input=tasks, output=workspace at PASS)
python -m pipeline.grok_sidecar provenance --slug my_project --phase 1 --implementer grok_build
```

**Typical Grok workflow:** `context` → implement in `workspace/` → `validate` → fill debrief → `record-bugs` → `provenance`.
Runner still owns completions/truth; run `harvest.py` as usual after PASS.

---

## Finetune corpus QC (weighted export + polish refresh)

Output lives under `thepipeline/finetune_corpus/` (or `PIPELINE_DIR/finetune_corpus`).

```bash
# Overview
python -m pipeline.corpus_workflow status

# Closeout gate audit (default warn; enforce blocks bad collects)
python -m pipeline.corpus_workflow audit
$env:CORPUS_GATE_POLICY = "enforce"
python -m pipeline.corpus_workflow audit --policy enforce
# Slow quality_scorer per project (single-project: python -m pipeline.corpus_gate --audit SLUG)
python -m pipeline.corpus_gate --audit --with-scorer

# Export training file (canonical rows only, tier weights in JSONL)
python -m pipeline.corpus_workflow export --merge-policy weighted

# After --polish fixes: refresh corpus for done queue entries
python -m pipeline.corpus_workflow refresh-polish

# Suggest polish_queue lines from gate failures
python -m pipeline.corpus_workflow polish-candidates --append-queue
```

**On project complete:** gate runs automatically (`warn` by default). Polish runs set
`corpus_force_refresh_on_complete` so the next completion bumps `corpus_generation`.

**Retroactive harvest** (skips gate): `python -m pipeline.corpus_collector --collect-all --skip-gate`

Low-level: `corpus_collector`, `corpus_qc`, `corpus_gate`, `corpus_polish` modules.

### SFT train on weighted export

```bash
pip install torch transformers datasets trl peft accelerate  # GPU machine only

python -m pipeline.corpus_workflow export --merge-policy weighted
python -m pipeline.finetune.sft_train --dry-run
python -m pipeline.finetune.sft_train --export-formatted
python -m pipeline.finetune.sft_train --train --model Qwen/Qwen2.5-Coder-1.5B-Instruct --max-steps 100
```

Uses `train_weight` via `WeightedRandomSampler` (tier A/B/C from corpus QC).

---

## master_ideas.md Format

```markdown
- [ ] **[Title of idea]** — [One sentence description.]
- [ ] **[Dependent idea]** — [Description. requires: slug_of_dependency]
- [x] **[Completed idea]** — [Already done — runner marks these automatically]
```

Rules:
- `- [ ]` = unchecked (will be picked up by runner)
- `- [x]` = done (runner marks these after completion)
- `requires:` = comma-separated slugs that must be `complete` first
- `[tetra]` = idea uses Throng6 tetra_meta_learn toolcall; phase_template `phase_tetra` runs grounding validation on complete
- One idea per line, no sub-bullets

---

## Throng6 / Tetra integration (Phase 6)

```bash
# From throng6 repo
echo '{"tool":"tetra_meta_learn","env":{"type":"mario_ascii"},"budget_steps":400,"outer_cycles":2}' | python -m throng6 toolcall

# From idea impl repo
python pipeline/tools/tetra_meta_learn.py

# Register capability (includes tetra_meta_learn)
python scripts/build_capability_registry.py --list | findstr tetra

# Harness project validation
python .pipeline/projects/tetra_meta_learn_harness/workspace/validate_tetra.py
```

Set `TETRA_GROUNDING_THRESHOLD=0.35` (default) for capability promotion via grounding court.
