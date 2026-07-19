# Debug Validate Fail (Grok Build factory track)

Pytest / structural validation failed for this phase. Diagnose and fix so tests pass.

## Read first

1. `phases/phase_N/validation_report.md` (if present)
2. `phases/phase_N/tasks.md`
3. `workspace/` and `workspace/tests/`
4. Step log under `phases/phase_N/grok_debug.log` if present

## Instructions

1. Reproduce the failure from the validation report (missing import, assertion, syntax).
2. Fix the root cause in the workspace (not by deleting tests unless a test is wrong and the task says so).
3. Ensure required packages are declared if the project uses a requirements file.
4. Keep changes scoped to the phase.
5. Leave tasks checkboxes accurate (`[x]` only when Done-when met).

## Done when

- Validation would PASS (or no tests collected if the phase never required tests)
- No new regressions introduced intentionally

Say DONE after applying the fix.
