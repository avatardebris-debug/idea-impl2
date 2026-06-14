---
name: idea-impl-regression-audit
description: >-
  Systematic post-refactor audit of the entire idea impl factory repo after
  thermo-nuclear-quality-code-review or large changes. Reproduces failures,
  ranks hypotheses, tests evidence, plans minimal fixes, and verifies with
  compile/import audits plus an optional pipeline smoke idea. Use when the
  pipeline runner regressed, paths seem wrong, master_ideas seeding behaves
  unexpectedly, or the user asks to audit idea impl as a whole.
disable-model-invocation: true
---

# Idea Impl Regression Audit

Whole-repo workflow for **idea impl** (factory code), not just cloud runner ops.
Pair with `pipeline-bug-investigate` when a specific stall is already running.

## Architecture (do not confuse)

| Layer | Location | Git |
|-------|----------|-----|
| Factory | `idea impl/` | `avatardebris-debug/idea` |
| Output | `thepipeline/` (local) or `idea impl/.pipeline/` (cloud) | private pipeline repo |
| Queue file | `master_ideas.md` in factory | working copy, not completion truth |

Completion truth: `truth.md` + `.pipeline/state/completions.jsonl` + project `status=complete`.

## Workflow checklist

```
- [ ] 1. Baseline audit (scripts, no runner)
- [ ] 2. Reproduce runner failure OR smoke idea
- [ ] 3. Hypotheses (1–4)
- [ ] 4. Test hypotheses
- [ ] 5. Short fix plan (code-judo)
- [ ] 6. Implement + verify audit + smoke
```

---

### 1. Baseline audit (always run first)

```bash
cd "idea impl"
python scripts/idea_impl_audit.py --smoke-imports
python scripts/pipeline_debug.py          # cloud: export PIPELINE_CLOUD=1
```

Record: compile errors, hardcoded `.pipeline` paths, import failures, first unchecked master_ideas line.

**Common post-thermo-nuclear regressions:**

- Hardcoded `.pipeline/...` instead of `get_pipeline_dir()` / `project_dir()` / `state_dir()`
- Broken imports from moved modules (`project_ops`, `paths`, `review_artifacts`)
- Message bus API drift (`has_active_work`, dedupe, SHUTDOWN handling)
- Seeding logic misunderstood (see below)

---

### 2. Reproduce

**A. Full runner (real project)**

```bash
export PIPELINE_CLOUD=1   # cloud only
python pipeline/runner.py --from-list --provider ollama --model <model> \
  --parallel-seeds 1 --executors 1 --auto-tune --max-seeds 2
```

**B. Smoke idea (isolated, recommended after refactors)**

Bypasses master_ideas serial lock — tests factory end-to-end:

```bash
export PIPELINE_CLOUD=1
python pipeline/runner.py \
  --idea "Smoke test: CLI hello counter prints 0-9" \
  --provider ollama --model <model> \
  --parallel-seeds 1 --executors 1
```

Success = phase advances within ~15 min, `throughput.json` call_count > 0, agent logs grow.

**C. Do not** treat reading code alone as reproduction.

---

### 3. Hypotheses template

| # | Hypothesis | If true, we'd see… | Quick test |
|---|------------|-------------------|------------|
| 1 | Path resolution broken | writes to wrong/empty dir | `idea_impl_audit.py` path section |
| 2 | Queue duplication | `phase_planner: pending=4` same slug | `pipeline_debug.py` |
| 3 | Ollama contention | TimeoutError in agent logs | 1 seed, 1 executor |
| 4 | Serial seed lock | only first `[ ]` in master_ideas runs | audit seeding section |

---

### 4. Why only "movie player" (master_ideas is serial)

`seed_from_master_list()` scans **top → bottom** and stops at the **first** unchecked line:

1. Finds `[ ] [movie player]` (line 9)
2. Sees project already in progress → returns `_SEED_SEEDED`
3. **Never reaches** dialog generator, robotics items, goal decompositions below

Other unchecked lines are **waiting in queue**, not ignored forever.

**Separate from master_ideas:** `.pipeline/projects/` may contain **hundreds** of folders from past runs (complete, stuck, polish). Those are **not** the same as "what master_ideas will seed next."

To work on something else:

- **Complete** movie player (or mark `[x]` + move to truth if truly done), OR
- **Temporarily move** movie player line below a smoke idea, OR
- Use **`--idea "..."`** for one-off smoke test

`[[lock]]` on movie player means budget lock — does not skip the line; it still blocks serial seeding.

---

### 5. Fix plan (thermo-nuclear-plan compressed)

1. **Goal** — factory + runner advance projects; audits pass.
2. **Simplest fix** — one root cause per commit; no new frameworks.
3. **≤3 phases** — paths → queue/seed → verify smoke.
4. **Out of scope** — unrelated corpus QC, new agents, drive-by refactors.
5. **Verify** — `idea_impl_audit.py` clean + smoke idea completes phase 1.

---

### 6. Verify

```bash
python scripts/idea_impl_audit.py --smoke-imports
python scripts/pipeline_debug.py --slug <slug>
# throughput.json call_count > 0 after smoke run
```

---

## Output for user

1. **Baseline** — audit script results
2. **Root cause** — confirmed hypothesis (with evidence)
3. **Fixes** — commits / files
4. **Smoke result** — smoke idea or movie_player phase advance
5. **master_ideas** — what blocks the queue and how to unblock

## Related skills

- `pipeline-bug-investigate` — live runner stall (TimeoutError, 0/2 samples)
- thermo-nuclear-quality-code-review — pre-change review (run audit **after** large batches)
