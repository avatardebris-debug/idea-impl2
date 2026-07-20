# Comprehensive / Deep Review (Grok Build factory track)

Optional whole-phase (or last-phase) quality pass. Does **not** replace ship-prove,
GitHub publish, or shared complete gates.

## When this runs

- `GROK_BUILD_DEEP_REVIEW=1` for every grok_build phase, or
- `GROK_BUILD_DEEP_REVIEW_LAST=1` on the project’s last planned phase

## Directory layout (important)

- Product code: **`{workspace}`**
- Tasks: **`{tasks_path}`** (never under workspace)
- Master plan: **`{master_plan_path}`**
- Soft package / `src/` layout under workspace is fine

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}`
- **Tasks file:** `{tasks_path}`
- **Master plan:** `{master_plan_path}`
- **Deep review output (write here):** `{deep_review_path}`
- **Phase number:** `{phase}`

## Output

Write to **`{deep_review_path}`**:

```markdown
# Deep Review — Phase {phase}

## Architecture
- ...

## Correctness risks
- ...

## Test gaps
- ...

## Security / abuse cases
- ...

## Ship readiness (advisory only)
- Ready / not ready for ship-prove — one paragraph

## Verdict (advisory)
PASS or CONCERNS with one-line reason
```

## Rules

1. Advisory only — the pipeline still requires closed checkboxes + non-FAIL `review.md`.
2. Be honest about production readiness; do not block advance solely from this file unless operators wire that later.
3. Read **`{workspace}`**, **`{tasks_path}`**, and **`{master_plan_path}`** (and other phase task files under `{project_dir}/phases/` if useful).
4. Do not rewrite layout style or move tasks into workspace.

## Handoff

After complete, existing paths still apply:

- GitHub publish on `complete` / `field_proven` (if enabled)
- ship-prove via `scripts/run_ship_prove.sh` / `.ps1` (same loop for classic and grok_build)

Say DONE after writing `{deep_review_path}`.
