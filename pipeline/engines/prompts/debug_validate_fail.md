# Debug Validate Fail (Grok Build factory track)

Pytest / structural validation failed for this phase. Diagnose and fix so tests pass.

## Directory layout (important)

- Product code + tests: under **`{workspace}`** (package or `src/` ok)
- Tasks: **`{tasks_path}`** only — never under workspace
- Do **not** create `workspace/workspace/`

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}`
- **Tasks file:** `{tasks_path}`
- **Validation report:** `{validation_report_path}`
- **Master plan:** `{master_plan_path}`
- **Phase number:** `{phase}`

## Read first

1. **`{validation_report_path}`** (if present)
2. **`{tasks_path}`**
3. **`{workspace}`** and `{workspace}/tests/`
4. Step log under `{project_dir}/phases/phase_{phase}/grok_debug.log` if present

## Instructions

1. Reproduce the failure from the validation report (missing import, assertion, syntax).
2. Fix the root cause under **`{workspace}`** (not by deleting tests unless a test is wrong and the task says so).
3. Ensure required packages are declared if the project uses a requirements file at workspace root.
4. Keep changes scoped to the phase.
5. Leave task checkboxes accurate in **`{tasks_path}`** (`[x]` only when Done-when met).
6. Do not set project status to complete — runner owns gates.

## Done when

- Validation would PASS (or no tests collected if the phase never required tests)
- No new regressions introduced intentionally

Say DONE after applying the fix.
