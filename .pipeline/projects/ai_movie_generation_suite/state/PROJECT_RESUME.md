# Resume: AI Movie Generation Suite

## Why this project was re-opened

- `master_plan.md` now defines **7 implementation phases** (4–7 promoted from future scope).
- Phases 1–3 workspace exists; phase 2 `validation_report.md` had recorded FAIL (4 pytest issues) but workspace tests now pass after model fixes.
- Project was incorrectly in `truth.md` / `completions.jsonl` as complete with `total_phases: 3`, which unblocked dependent ideas prematurely.

## Current state (after prep)

| Field | Value |
|-------|--------|
| `status` | `phase_4_planning` |
| `phase` | `3` (last completed) |
| `total_phases` | `7` |

Phase 2 code fixes applied in workspace (`BeatSheet.title`, `Character.motivation`, `Project.model_dump` `characters` alias). No need to re-run phases 1–3 unless you want a fresh validation pass.

## Command to run

From repo root (`idea impl`):

```bash
python pipeline/runner.py --resume --provider ollama --model qwen3.6:35b-a3b-q4_K_M
```

Use **`--resume`**, not `--polish`. Status is `phase_4_planning` (not `complete`). `--polish` only re-queues projects marked `complete` or `budget_exceeded`.

Optional longer session:

```bash
python pipeline/runner.py --resume --provider ollama --model qwen3.6:35b-a3b-q4_K_M --time-limit 600 --base-budget 120 --phase-budget 45
```

## What the runner will do next

1. Pick up `ai_movie_generation_suite` at **phase 4 planning** (animatic / storyboard-to-timeline).
2. Run phase_planner → executor → validator for phases 4, 5, 6, 7 in order.
3. On true completion, append to `truth.md` / `completions.jsonl` and unblock lock-chain ideas in `master_ideas.md`.

## Lock-chain dependents (still blocked)

Until this project is **complete** after phase 7:

- `[movie player]` — requires: `ai_movie_generation_suite`
- `[dialog generator]` — requires: `ai_movie_generation_suite`
- `[director/editor]` — requires: `ai_movie_generation_suite`

## Verify phase 2 tests locally

```bash
cd .pipeline/projects/ai_movie_generation_suite/workspace
python -m pytest tests/ -q
```

Expected: all tests PASS.
