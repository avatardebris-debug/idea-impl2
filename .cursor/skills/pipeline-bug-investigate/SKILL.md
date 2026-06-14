---
name: pipeline-bug-investigate
description: >-
  Systematically reproduces, hypothesizes, tests, plans, fixes, and verifies
  pipeline runner stalls, queue deadlocks, path resolution bugs, and agent
  failures in the idea impl repo. Use when the user reports STALL DETECTED,
  0/2 parallelizer samples, TimeoutError in agent logs, wrong pipeline output
  path, only one project showing, or regressions after thermo-nuclear refactors.
disable-model-invocation: true
---

# Pipeline Bug Investigate and Fix

End-to-end workflow for **idea impl** factory + `.pipeline` / `thepipeline` output.
Do not skip reproduction or hypothesis testing to jump straight to a patch.

## Repo layout (critical)

| Path | Role |
|------|------|
| `idea impl/` | Factory code (this git repo) |
| `idea impl/.pipeline/` | Cloud output when `PIPELINE_CLOUD=1` |
| `../thepipeline/` | Local output when sibling exists |
| `PIPELINE_DIR` env | Overrides both |

Agents run with `cwd=PROJECT_ROOT`. Hardcoded `.pipeline/...` paths in agent code
**break local runs** when output is `thepipeline`. Always use `get_pipeline_dir()`,
`project_dir(slug)`, `state_dir()` from `pipeline.paths`.

## Inputs

- **Required**: Symptom (status line, log excerpt, project slug, when it started).
- **Run first**: `python scripts/pipeline_debug.py` (cloud: `export PIPELINE_CLOUD=1`).

If reproduction needs a live runner, use `--parallel-seeds 1 --executors 1` on
single-GPU cloud until the bug is understood.

## Workflow checklist

```
- [ ] 1. Reproduce (runner + logs + pipeline_debug.py)
- [ ] 2. Hypotheses (1–4)
- [ ] 3. Test hypotheses
- [ ] 4. Fix plan (short, code-judo)
- [ ] 5. Implement fix
- [ ] 6. Verify (runner makes LLM progress / project advances)
```

---

### 1. Reproduce

1. Confirm code version: `git log -1 --oneline` (stall fixes land in `903dca0+`).
2. Run diagnostics:

```bash
cd "/workspace/idea impl"   # or local path
export PIPELINE_CLOUD=1     # cloud only
python scripts/pipeline_debug.py --slug movie_player
```

3. Capture **runner status line** (phase, pending, parallelizer).
4. Tail the **stuck agent** log (not runner stdout):

```bash
tail -40 .pipeline/logs/reviewer.out   # or executor, phase_planner
```

5. Distinguish failure types:

| Log pattern | Usually means |
|-------------|----------------|
| `socket.py line 707` / `TimeoutError: timed out` | Ollama HTTP wait expired (contention or 35B slow), **not** stale file path |
| `Constitution loaded` then silence 5+ min | Agent blocked on first LLM call |
| `phase_1_reviewing` + validation PASS + review.md exists | Redundant reviewer loop (fixed by skip-review in 903dca0) |
| `has_active_work=True` + only SHUTDOWN pending | Stale Ctrl+C signals blocking rebuild |
| pygame banner on runner console | Health check import side effect (harmless) |

**Do not** treat static code reading alone as reproduction.

---

### 2. Form hypotheses

| # | Common hypothesis | If true, we'd see… | Quick test |
|---|-----------------|-------------------|------------|
| 1 | Ollama contention (parallel seeds × executors) | `api/ps` loaded but reviewer TimeoutError ~300–900s apart | `--executors 1 --parallel-seeds 1` |
| 2 | Redundant reviewer re-queue | status `phase_N_reviewing`, review.md + validation PASS | `grep Verdict phases/phase_N/*.md` |
| 3 | Stale SHUTDOWN / processing blocks rebuild | `has_active_work` with no real tasks | `pipeline_debug.py` after discard |
| 4 | Wrong output path (hardcoded `.pipeline`) | manager/executor writes empty nested dir locally | `python -c "from pipeline.paths import get_pipeline_dir; print(get_pipeline_dir())"` |

---

### 3. Test hypotheses

Test in order. Record: **ran → result → confirms / rejects**.

**Unblock movie_player-style reviewing deadlock (no code change):**

```bash
python3 << 'PYEOF'
from pathlib import Path
import json
from pipeline.message_bus import MessageBus
from pipeline.project_rebuild import dispatch_phase_requeue

bus = MessageBus()
bus.discard_stale_shutdowns()
slug = "movie_player"
proj = Path(".pipeline/projects/movie_player")
state = json.loads((proj / "state/current_idea.json").read_text())
dispatch_phase_requeue(bus, slug, state.get("title", slug), state, proj, state["status"], log_requeue=True)
PYEOF
```

Expect on 903dca0+: `[skip-review] ... advancing` without reviewer LLM.

---

### 4. Fix plan (short)

1. **Goal** — runner completes LLM calls; active project advances; no phantom queue work.
2. **Simplest fix** — one mechanism per PR (path helper, skip-review, startup cleanup, timeout env).
3. **≤3 phases** — diagnose → minimal code fix → cloud verify with `pipeline_debug.py`.
4. **Out of scope** — drive-by refactors, new abstractions, unrelated corpus QC.
5. **Verify** — `throughput.json` call_count increases; status leaves stuck phase within 10 min.

---

### 5. Implement fix

- Use `pipeline.paths` helpers; never new hardcoded `.pipeline` strings in agent code.
- Match existing patterns in `project_rebuild.py`, `run_loop_health.py`, `startup.py`.
- Add/adjust tests in `test_review_artifacts.py` or `test_dropbox.py` when parsing/recovery logic changes.

---

### 6. Verify

1. `git pull` on cloud; restart runner with reduced parallelism.
2. Re-run `python scripts/pipeline_debug.py`.
3. Confirm:
   - No recurring TimeoutError loop for skip-review-eligible projects
   - `call_count` in throughput.json > 0 after first agent step
   - Status advances (e.g. `phase_2_planning`) or project completes

---

## Why only one project shows (movie player)

`master_ideas.md` is processed **top-to-bottom, one in-progress project at a time**
when `--from-list` is used. Line 9 is `[movie player]` — first unchecked item.

While movie player is in any non-complete status, seeding returns `_SEED_SEEDED` for
that line and **does not seed** dialog generator, director/editor, etc. Status line
`[movie player] / [[mobile access ] / ...` shows parallel seeds from **earlier**
runs, not new master_ideas entries.

To advance the list: complete or `budget_exceed` movie player, or temporarily
comment/move the line in `master_ideas.md`.

---

## Output shape (for the user)

1. **Repro** — debug script output + log excerpt
2. **Root cause** — confirmed hypothesis (not "maybe paths")
3. **Fix** — commit/files + cloud pull instructions
4. **Verification** — throughput + status after fix
