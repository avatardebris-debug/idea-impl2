# Idea Plan (Grok Build factory track)

You produce a **multi-phase master plan** so later phase-plan + implement skills
can ship code. Follow the skill body below (flexible phase count 1–8).

## Absolute paths for this run (injected)

- **Project root:** `{project_dir}`
- **Workspace:** `{workspace}` (optional recon; may be empty)
- **Master plan output (write here):** `{master_plan_path}`
- **Idea / state:** `{project_dir}/state/current_idea.json`
- **Slug:** `{slug}`
- **Phase context (ignore for total count):** `{phase}`

## Skill body (authoritative process)

{idea_plan_skill}

## Hard requirements

1. Read title/description from `{project_dir}/state/current_idea.json` if present.
2. Write **`{master_plan_path}`** with Goal, Phase 1..N, Architecture Notes, Risks.
3. Phase count is **flexible (1–8)** — not forced to 3. Prefer Phase 1 = working MVP.
4. If `current_idea.json` exists, set `"total_phases"` to N (UTF-8, no BOM). Do not set status to complete.
5. Do **not** write `tasks.md` here (that is phase-plan).
6. Do **not** implement product code under workspace unless recon needs a glance.

## Done when

- `{master_plan_path}` exists with at least one phase and success criteria
- total_phases matches the plan when state JSON is present
