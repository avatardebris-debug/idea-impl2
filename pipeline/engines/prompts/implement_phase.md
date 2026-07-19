# Implement Phase (Grok Build factory track)

You are implementing **one phase** of a project on disk. Planners already wrote
the plan and tasks file. Your job is code + checkbox honesty only.

## Directory layout (important)

Pipeline projects look like this — **do not invent a different layout**:

```
{project_dir}/                 ← project root (NOT the shell cwd for product imports)
  state/master_plan.md
  phases/phase_{phase}/tasks.md
  workspace/                   ← product code root (often the CLI --cwd)
    <package_name>/            ← normal Python package (e.g. ship_canary/main.py)
    tests/
```

- **`tasks.md` is NEVER under `workspace/`.** It lives only under `phases/`.
- **`workspace/<slug>/` as a package folder is NORMAL** (so `python -m ship_canary.main` works).
  That is not a mistake and not “double nesting” of the pipeline workspace.
- Do **not** create `workspace/workspace/` or put tasks inside the package tree.

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace (product code root):** `{workspace}`
- **Tasks file (checkboxes):** `{tasks_path}`
- **Master plan:** `{master_plan_path}`
- **Phase number:** `{phase}`

## Instructions

1. Read the tasks file at **`{tasks_path}`** (absolute path above). If it is missing, check
   `{project_dir}/phases/phase_{phase}/tasks.md` — do **not** look under `workspace/` for it.
2. Read the phase section of the master plan at `{master_plan_path}`.
3. Implement tasks in order. Write product code under `{workspace}` (package subdirs OK).
4. Add or update tests under `{workspace}/tests/` when the phase needs verification.
5. When a task’s Done-when is truly met, mark that line `- [x]` in **`{tasks_path}` only**.
   **Do not** bulk-check boxes. **Do not** mark complete if work is incomplete.
6. Do **not** change `state/current_idea.json` status to `complete` — the pipeline owns advance/complete.
7. Do **not** invent new phases. Stay within this phase’s tasks.
8. Prefer reusing existing modules in the workspace over reimplementation.

## Done

- Finished tasks are `[x]` in `{tasks_path}`
- Workspace imports cleanly (package layout under workspace is fine)
- Tests exist if the phase called for them
- Leave a short note if something is blocked

Say DONE when implement work for this phase is finished.
