# Comprehensive snapshot after field still fails (bridge, report-only)

Last resort after field-test repair, systematic debug, and focused code-review.
Produce an **advisory** comprehensive snapshot — **do not** mass-edit the codebase.

## Paths

- **Workspace:** `{workspace}`
- **Field results:** `{field_results_path}`
- **Prior reports:** `{project_dir}/phases/ship/`
- **Output:** `{field_comprehensive_path}`

## Write

`{field_comprehensive_path}`:

```markdown
# Comprehensive field gap report (advisory)

## Product aim vs reality
...

## Why field still fails
...

## Systemic risks (top 5)
| Severity | Area | Evidence | Effort |

## Recommended next (pick one)
1. Human fix + re-field
2. New phase / feature expand
3. Accept ship_insufficient
4. Full grok_build re-implement (expensive — last resort)

## Do not
- Claim field_proven
- Rewrite the whole project in this step
```

Say DONE after the report is written.
