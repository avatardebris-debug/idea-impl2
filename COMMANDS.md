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
