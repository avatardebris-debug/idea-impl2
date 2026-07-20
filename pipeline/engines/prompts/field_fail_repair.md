# Field Fail Repair (bridge — not full grok_build)

Field tests failed. Act like the **field-test skill** fail path: classify, fix
plan and/or minimal product code, do **not** rebuild the whole project.

## Absolute paths

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}`
- **Field tests plan:** `{field_tests_path}`
- **Field results (failed):** `{field_results_path}`
- **Master plan:** `{master_plan_path}`
- **Capability claims:** `{project_dir}/state/capability_claims.md`
- **Fix report output:** `{field_fix_report_path}`
- **Slug:** `{slug}`

## Read first

1. `{field_results_path}` — which tasks FAIL and output tails
2. `{field_tests_path}` — Commands / Expect
3. Workspace modules actually on disk
4. Master plan / claims for product aim

## Classify each failure

| Class | Meaning | Action |
|-------|---------|--------|
| **bad_plan** | Hallucinated module/flag/path | Fix `field_tests.md` only |
| **product_bug** | Real code/test fails product aim | Minimal fix under `{workspace}` |
| **env** | Missing dep / path | Cheap fix or note in fix report |
| **factory** | Pipeline path issues | Note only — do not thrash product |

## Do

1. Prefer **bad_plan** fixes when Command doesn't match real modules.
2. For **product_bug**: smallest change so failed Commands pass; no drive-by refactors.
3. Emit files with fences when using pipeline_llm:
   ```
   file:phases/ship/field_tests.md
   ...
   file:relative/path.py
   ...
   file:phases/ship/field_fix_report.md
   ...
   ```
4. Write **`{field_fix_report_path}`** always:

```markdown
# Field fix report
- Classification: bad_plan | product_bug | env | mixed
- Failed tasks: ...
- Root cause: ...
- Changes: ...
- Next: re-run field tests
```

5. Do **not** set project status complete/field_proven — runner owns that.

Say DONE when plan/code and fix report are updated.
