# Comprehensive / Deep Review (Grok Build factory track)

Optional whole-phase (or last-phase) quality pass. Does **not** replace ship-prove,
GitHub publish, or shared complete gates.

## When this runs

- `GROK_BUILD_DEEP_REVIEW=1` for every grok_build phase, or
- `GROK_BUILD_DEEP_REVIEW_LAST=1` on the project’s last planned phase

## Output

Write to `phases/phase_N/deep_review.md`:

```markdown
# Deep Review — Phase {N}

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
3. Read full `workspace/`, all phase tasks, and master plan.

## Handoff

After complete, existing paths still apply:

- GitHub publish on `complete` / `field_proven` (if enabled)
- ship-prove via `scripts/run_ship_prove.sh` / `.ps1`

Say DONE after writing `deep_review.md`.
