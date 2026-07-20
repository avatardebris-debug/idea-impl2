# Code review after persistent field fail (bridge)

Field still fails after repair + systematic debug. Run a **focused code-review**
on structure blocking the field Commands — not a full-repo audit.

## Paths

- **Workspace:** `{workspace}`
- **Field results:** `{field_results_path}`
- **Review output:** `{field_review_path}`
- **Project:** `{project_dir}`

## Scope

Only modules implicated by failing field tasks (CLI entrypoints, imports, tests
named in results). Do not review the whole monorepo of unrelated files.

## Output

Write `{field_review_path}`:

```markdown
# Field-focused code review

## Blocking for field
- file:line — issue — suggested fix

## Non-blocking
- ...

## Minimal fix plan
1. ...

## Verdict
FIX_NEEDED | STRUCTURE_OK_TESTS_WEAK | UNCLEAR
```

If a **tiny** structural fix clearly unblocks field (e.g. missing `if __name__`,
wrong argparse), apply it under `{workspace}` and note it. Otherwise report only.

Say DONE after writing the review (and any minimal fixes).
