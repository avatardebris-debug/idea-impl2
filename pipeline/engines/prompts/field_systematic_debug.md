# Systematic debug after field fail (bridge — step 2 of max 3)

Field still fails after field-test repair. Follow the **full systematic-debugging
skill** (injected below). This is field step 2 only — not an infinite loop.

## Paths

- **Workspace:** `{workspace}`
- **Field results:** `{field_results_path}`
- **Field tests:** `{field_tests_path}`
- **Prior fix report:** `{field_fix_report_path}`
- **Debug report:** `{field_debug_report_path}`
- **Project:** `{project_dir}`
- **Slug:** `{slug}`

## Iron law

NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST.

## Skill body (systematic-debugging)

{systematic_debugging_skill}

## Field-specific rules

1. Reproduce failed Commands from workspace root (absolute python if needed).
2. One hypothesis at a time; smallest product defect under `{workspace}`.
3. Do not invent modules; do not full-rewrite the project.
4. Write `{field_debug_report_path}`:

```markdown
# Field debug report
- Repro: ...
- Root cause: ...
- Hypothesis tested: ...
- Fix: files + behavior
- Residual risk: ...
```

5. Prefer file fences: `file:path` then content.
6. After your fix, the pipeline re-runs field tests (you do not set field_proven).

Say DONE after fix + debug report.
