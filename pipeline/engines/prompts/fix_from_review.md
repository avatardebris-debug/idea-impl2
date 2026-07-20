# Fix From Review (Grok Build factory track)

A prior review marked this phase **FAIL** or left open task checkboxes. Fix only
what is needed to clear blocking issues.

## Directory layout (important)

- Product code: **`{workspace}`** only
- Tasks checkboxes: **`{tasks_path}`** only (never under workspace)
- Review to address: **`{review_path}`**
- Package or `src/` layouts under workspace are both fine

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}`
- **Tasks file:** `{tasks_path}`
- **Review file:** `{review_path}`
- **Validation report (if any):** `{validation_report_path}`
- **Master plan:** `{master_plan_path}`
- **Phase number:** `{phase}`

## Read first

1. **`{review_path}`** — Blocking Bugs and Verdict
2. **`{tasks_path}`** — any remaining `- [ ]`
3. **`{workspace}`** — current code
4. **`{validation_report_path}`** if present

## Instructions

1. Address each Blocking Bug with a minimal, correct code change under **`{workspace}`**.
2. Finish open tasks and mark `- [x]` only in **`{tasks_path}`** when Done-when is met.
3. Re-run or update tests under `{workspace}/tests/` if they failed.
4. Do not drive-by refactors unrelated to the review.
5. Do not set project status to complete — runner owns gates.
6. Do **not** look for tasks under `workspace/`.

## After fixes

Prefer that a re-review can set:

```markdown
## Blocking Bugs
- None

## Verdict
PASS — review issues resolved
```

Say DONE when fixes are applied.
