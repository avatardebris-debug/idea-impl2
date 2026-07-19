# Plan: per-project GitHub for pipeline outputs

**Status:** implemented (local always on hooks; GitHub push opt-in) — **auto tool-from-GitHub stays deferred**  
**Date:** 2026-07-18  
**Code:** `pipeline/github_publish.py`, `scripts/publish_project_github.py`, hooks in `project_phase._mark_complete` + `ship_evaluator`  
**Depends on:** none of Orca; Orca becomes easier later if this exists
==
gh auth login
# or: $env:GITHUB_TOKEN = "ghp_..."

$env:PIPELINE_GITHUB_ORG = "avatardebris-debug"
$env:PIPELINE_GITHUB_REPO_PREFIX = "pipe-"
$env:PIPELINE_GITHUB_VISIBILITY = "private"

cd C:\Users\avata\.grok\worktrees\aicompete-idea-impl\idea-impl2
python scripts/publish_project_github.py --slug ship_canary --push
--- 
session
$env:GITHUB_TOKEN = "ghp_...."   # paste token
$env:PIPELINE_GITHUB_ORG = "avatardebris-debug"
$env:PIPELINE_GITHUB_REPO_PREFIX = "pipe-"
$env:PIPELINE_GITHUB_VISIBILITY = "private"
$env:GIT_COMMIT_AUTHOR = "Your Name <you@email.com>"

cd C:\Users\avata\.grok\worktrees\aicompete-idea-impl\idea-impl2
python scripts/publish_project_github.py --slug ship_canary --push
==
## Goals

1. Each pipeline project can become a **real git repo** (at least local).  
2. **Completed** (and optionally **field_proven**) projects can be **pushed to GitHub** as standalone repos (or monorepo packages — default: **one remote repo per slug**).  
3. Wiring is **non-essential**: runner/pipeline works if GitHub is off, unauthenticated, or push fails.  
4. Leaves a clean surface for future Orca / multi-PR worktrees without requiring Orca now.

## Non-goals (now)

- Auto-discover / install tools from random GitHub (deferred; separate note).  
- Public “app store.”  
- Replacing `scripts/sync_output_repo.py` (that syncs the **whole** `PIPELINE_DIR` output tree as one repo — different job).  
- Forcing every in-flight project onto GitHub mid-build (optional later).

## Existing related pieces

| Piece | Role |
|-------|------|
| `scripts/sync_output_repo.py` | Commit/push **entire** `PIPELINE_DIR` (projects + state + corpus…) |
| `pipeline/project_complete.py` | `is_project_complete` / full complete + field_proven |
| `dep_policy.is_full_complete` | Status rules |
| No per-slug git init/push today | Gap this plan fills |

Two layers can coexist:

- **Output mono-repo** = factory state backup (`thepipeline` / `.pipeline`).  
- **Per-project repos** = shippable software units for agents, PRs, Orca, humans.

---

## Design choices

### When to git-init

| Option | Pros | Cons |
|--------|------|------|
| A. On **seed** | Always have history | Many empty/noise repos; mid-fail projects |
| B. On **complete** / **field_proven** only | Clean; matches “push completed ideas” | No history of build process unless you export workspace as initial commit |
| C. On seed **local only**; push only on complete | Best balance | Slightly more logic |

**Recommend C:**  
- `git init` (+ `.gitignore`) when project is created or first time we touch publish.  
- **Push** only on terminal quality statuses (see below).

### When to push (timer vs sequence)

| Mode | Verdict |
|------|---------|
| **Every 25m in runner** | Bad as primary: couples network/gh auth to main loop; noisy; unclear “what changed” |
| **On sequence (event)** | **Primary:** when status becomes `complete` or `field_proven` (configurable) |
| **Optional sweep** | Secondary: CLI or rare idle job to catch missed publishes — not a 25m heartbeat |

**Recommend: event-driven hook + optional manual/CLI backfill.**

```
phase done → status complete
              → publish_project_to_github(slug)   # best-effort, non-blocking
ship → field_proven
              → publish again (or first time if only_on_field_proven)
```

If publish fails: log + write `phases/ship/github_publish.md` or `state/github_status.json`; **do not** fail the project status.

### Config (env / flags)

```text
PIPELINE_GITHUB_PUBLISH=0          # default off — runner unchanged
PIPELINE_GITHUB_PUBLISH=1          # enable
PIPELINE_GITHUB_ORG=avatardebris-debug
PIPELINE_GITHUB_REPO_PREFIX=pipe-  # repo name = prefix + slug
PIPELINE_GITHUB_VISIBILITY=private # private|public
PIPELINE_GITHUB_ON=complete,field_proven   # which statuses trigger push
PIPELINE_GITHUB_REMOTE=origin
# Auth: GITHUB_TOKEN or gh auth (existing user session)
```

### Repo layout (what gets committed) — **LOCKED: whole project**

Publish the **entire** `projects/<slug>/` tree as the GitHub repo root (operator choice 2026-07-18):

```
projects/<slug>/          → becomes GitHub repo root
  workspace/              # product code
  state/                  # current_idea.json, plans, etc.
  phases/                 # phase specs, tasks, ship field tests/results
  (other project files)
```

**Why whole project (operator):** plans/phases explain what it is and help work backwards; preserves material useful for finetune pair recovery later.

Still add root `.gitignore`: `__pycache__`, `.venv`, `.env`, `*.pyc`, large artifacts, secrets.  
Optional root `README.md` pointing at `workspace/` as the runnable product.

### Naming

- GitHub repo: `{PREFIX}{slug}` e.g. `pipe-ship_canary`  
- Or single org with topics `pipeline-output`  
- Avoid colliding with factory `idea-impl2` / `idea` repos

---

## Architecture

```
pipeline/github_publish.py          # pure helpers: init, commit, ensure_remote, push
pipeline/project_phase.py (or       # call publish_if_configured(slug) on complete
  wherever status → complete)
pipeline/agents/ship_evaluator.py   # call on field_proven
scripts/publish_project_github.py   # CLI: one slug or --all-complete backfill
```

### Core API (sketch)

```python
def publish_project(slug: str, *, reason: str) -> PublishResult:
    """
    Best-effort. No-op if PIPELINE_GITHUB_PUBLISH off.
    1. Resolve project_dir / workspace
    2. Ensure git repo in workspace (or projects/slug/git_export/)
    3. Ensure .gitignore + README
    4. commit -Am "pipeline: {slug} ({status}) {reason}"
    5. Ensure remote (gh repo create if missing)
    6. git push -u origin main
    7. Record url in state/github_status.json
    """
```

Use `subprocess` + `gh` when available; fall back to remote URL + `GITHUB_TOKEN`.

### Sequence wiring (not timer)

1. **Complete path** — wherever `_mark_complete` / status `complete` is set, after success:  
   `maybe_publish_project(slug, trigger="complete")`  
2. **field_proven** — end of ship_evaluator success path:  
   `maybe_publish_project(slug, trigger="field_proven")`  
3. **CLI backfill** — `python scripts/publish_project_github.py --slug X` or `--all-eligible`  
4. **Runner timer** — **do not** add 25m publish loop in v1.

Optional later: idle sweep every N minutes **only if** `PIPELINE_GITHUB_PUBLISH=1` and queue empty — still not the main path.

---

## Implementation phases (PR plan)

### PR1 — Local git only (no GitHub required)

- `pipeline/github_publish.py`: `ensure_workspace_git(slug)`, `.gitignore`, initial commit  
- Call on seed **or** first complete (prefer complete for less junk)  
- CLI: `python scripts/publish_project_github.py --slug X --local-only`  
- Tests: temp project dir, init + commit, no network  

**Exit:** every complete project can be a local git repo.

### PR2 — Push to GitHub (opt-in)

- `PIPELINE_GITHUB_PUBLISH=1` + org/token  
- `gh repo create` / ensure remote / push  
- Write `state/github_status.json`: `{url, last_push, sha, error?}`  
- Best-effort; never flip project status on push failure  
- Docs in `COMMANDS.md`  

**Exit:** completed canary-class project appears on GitHub when flag on.

### PR3 — Wire into complete + field_proven sequences

- Hook complete + field_proven  
- Idempotent: push only if dirty or status advanced  
- Metrics/log line: `[github] published pipe-foo → url`  

**Exit:** unattended path works with flag on; default off preserves today’s runner.

### PR4 — Backfill + hygiene (optional)

- `--all-eligible` for existing `complete` / `field_proven`  
- Skip `ship_insufficient` unless forced  
- README template from `current_idea.json`  

### Later (not now)

- Orca worktree from `github_status.url`  
- PR-per-agent branch naming convention  
- CI workflow template in each repo  
- Auto tool discovery from GitHub (deferred note)

---

## Timer vs sequence vs placeholder — decision

| Question | Answer |
|----------|--------|
| 25m timer in runner? | **No** for publish (noise, coupling). |
| Sequence on complete / field_proven? | **Yes** — primary. |
| Placeholder only for Orca? | **No** — ship real L1/L2; Orca is a *consumer* of git, not the reason. |
| Essential for runner? | **No** — default **off**; feature flag. |
| Relationship to `sync_output_repo` | Keep both: mono output backup vs per-product repos. |

---

## Security / ops

- Default **private** repos.  
- Never commit `.env`, secrets, API keys (gitignore + scan).  
- `GITHUB_TOKEN` with `repo` scope only as needed.  
- Cloud: same env as other secrets; document in COMMANDS.  
- Rate limits: event-driven avoids spam; backfill should sleep/retry lightly.

---

## Success criteria

1. With flag **off**: zero behavior change.  
2. With flag **on**: completing a project (or field_proven) yields a GitHub URL in `state/github_status.json` when auth works.  
3. Failure to publish does not block pipeline progress.  
4. Manual CLI can publish one historical complete project.  
5. Full project tree is on GitHub (workspace + state + phases); clone is usable for agents with `workspace/` as code root.

---

## Suggested first vertical slice (when implementing)

1. PR1 local git on complete for one slug (ship_canary or next complete).  
2. PR2 push with `PIPELINE_GITHUB_PUBLISH=1` to private `pipe-<slug>`.  
3. PR3 wire hooks.  
4. Stop; use for a while before Orca glue.

## Locked operator choices

1. **Repo-per-slug** — one GitHub repo per project (`PREFIX` + slug).  
2. Publish on **both** `complete` and `field_proven` (configurable list; default both).  
3. Commit **whole `projects/<slug>`** — workspace **plus** `state/`, `phases/` (plans, ship results, etc.) so the repo explains the product, supports working backwards, and can recover finetune-related artifacts later.

### Implications of whole-project publish

- Stronger as **archive + agent context** (plan/phase/ship trail).  
- Overlaps somewhat with output mono-repo (`sync_output_repo`); still worth it for **per-product remotes** and Orca/PR trees.  
- **Must** gitignore secrets: `.env`, `*.pem`, local venvs, `__pycache__`, large binaries; never commit API keys from state if any leak in.  
- README at repo root should still say “run code under `workspace/`”.  
- External coding agents should be prompted to treat `workspace/` as the product root and `state/`/`phases/` as read-mostly context.  
