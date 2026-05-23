# Pipeline Command Reference

Quick reference for all commands needed to manage the autonomous pipeline
across local Windows and cloud (Vast.ai / RunPod) instances.

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
# See .pipeline/docs/workflows.md

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
# export HERMES_AUTO_INSTALL=0   # fail fast, manual clone instead
# export HERMES_SKIP_PIP=1       # clone only, you install deps yourself

# Single idea (quick test)
python pipeline/runner.py "Build a Python word counter CLI" \
    --provider ollama --model qwen3.6:35b-a3b-q4_K_M

# Stop gracefully
Ctrl+C
# or kill background run:
pkill -f pipeline/runner.py
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

# After it completes, PIPELINE_MODEL is exported automatically.
# The runner picks it up without needing --model:
source .venv/bin/activate
python pipeline/runner.py --from-list --provider ollama --time-limit 600

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
- One idea per line, no sub-bullets
