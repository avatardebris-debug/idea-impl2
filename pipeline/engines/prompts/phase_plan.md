# Phase Plan (Grok Build factory track)

You decompose **one master-plan phase** into checkbox tasks for implement.
Follow the skill body below (flexible ~2–8 tasks, hard max 10).

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}`
- **Master plan:** `{master_plan_path}`
- **Tasks output (write here):** `{tasks_path}`
- **Phase number N:** `{phase}`
- **Slug:** `{slug}`

## Skill body (authoritative process)

{phase_plan_skill}

## Hard requirements

1. Read Phase **{phase}** from `{master_plan_path}`. If master plan is missing, stop with a clear error in a short note file under `phases/phase_{phase}/` — do not invent a full roadmap.
2. Recon `{workspace}` so Files: match real modules.
3. Write **`{tasks_path}`** using **exact** checkbox format:

```markdown
# Phase {phase} Tasks: {title}

- [ ] Task 1: ...
  - What: ...
  - Files: ...
  - Done when: ...
```

4. Top-level tasks only with `- [ ]`. Nested What / Files / Done when. No emoji checkmarks.
5. Task count flexible; **max 10**. Include a tests/verification task when shipping product code.
6. Do **not** implement product code in this step (planning only).
7. Do **not** change project status to complete.

## Done when

- `{tasks_path}` exists with parseable `- [ ]` tasks for phase {phase} only
