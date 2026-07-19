# Fix From Review (Grok Build factory track)

A prior review marked this phase **FAIL** or left open task checkboxes. Fix only
what is needed to clear blocking issues.

## Read first

1. `phases/phase_N/review.md` — Blocking Bugs and Verdict
2. `phases/phase_N/tasks.md` — any remaining `- [ ]`
3. `workspace/` current code

## Instructions

1. Address each Blocking Bug with a minimal, correct code change.
2. Finish open tasks and mark `- [x]` only when Done-when is met.
3. Re-run or update tests if they failed.
4. Do not drive-by refactors unrelated to the review.
5. Do not set project status to complete — runner owns gates.

## After fixes

Prefer that a re-review can set:

```markdown
## Blocking Bugs
- None

## Verdict
PASS — review issues resolved
```

Say DONE when fixes are applied.
