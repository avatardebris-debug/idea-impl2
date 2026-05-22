## Phase 7 — Collaborative Editing & Review

**Goal:** Enable multi-user review, version branching, and conflict-safe edits on project artifacts.

**Description:**
1. **Project Version Graph** — Git-friendly branching metadata for beats, script, characters, and animatic overrides.
2. **Review Workflow** — Comment threads per scene/beat with approve/request-changes states.
3. **Merge Rules** — Field-level merge for JSON artifacts (characters registry, scene descriptions) with conflict markers.
4. **Audit Log** — Who changed what, when, and which pipeline phase produced each revision.
5. **Export for Lock-Chain Ideas** — Stable API surface for movie player, dialog generator, and director/editor dependents.

**Deliverable:**
- `collab/reviews.json` — review state and comments per artifact path
- `collab/versions/` — branch pointers and merge resolution records
- `collab/audit.jsonl` — append-only change log
- Documented stable export paths under `project/` for downstream `[lock]` ideas

**Dependencies:**
- Phases 1–6 (full artifact set to review and version)

**Success Criteria:**
- [ ] Two users can propose edits to the same scene without silent overwrites
- [ ] Review workflow supports approve and request-changes on beat, scene, and script units
- [ ] Merged project reloads through existing CLI with no data loss
- [ ] Audit log captures agent and human edits with timestamps
- [ ] Project marked `complete` only after Phase 7 validation passes (unblocks `requires: ai_movie_generation_suite`)

---

## 6. Extended Pipeline Notes

Phases 4–7 extend pre-production into timed preview, audio, video clips, and team review. They remain **pre-production** scope: creative assets and planning documents, not final rendered feature films.

| Phase | Focus |
|-------|--------|
| 4 | Animatic timing |
| 5 | Voice & dialogue audio |
| 6 | AI video clips |
| 7 | Collaboration & release gate |

---

## 7. Implementation Order Summary

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
(screenplay) (visuals)   (3D/UE5)   (animatic)  (audio)     (video)     (collab)
```

**Total phases:** 7. Phases 1–3 are complete in workspace; phases 4–7 resume via `--resume` after `total_phases` is set to 7.

**Downstream lock-chain:** `movie player`, `dialog generator`, and `director/editor` in `master_ideas.md` require `ai_movie_generation_suite` to reach `complete` after all 7 phases.