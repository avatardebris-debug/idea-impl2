## Phase 2: Practice / Drill System

**Goal:** SM-2 spaced repetition engine + CLI drill loop + SQLite session tracking.

**Deliverables:**
- `scheduler.py` — SM-2 algorithm (quality 0-5 → interval in days → next_review date)
- `session_db.py` — SQLite: clips table, reviews table, next_review date per clip
- `drill_cli.py` — `python -m video_babbel_enhanced drill --deck clips/` → interactive loop
- Practice modes: phrase drill (L1 → attempt L2 → reveal), listening drill (hear L2 → type), shadowing (L2 audio plays, subtitle delayed 1s)
- Dual subtitle overlay on clips (ffmpeg drawtext or external .srt)
- Export: `--export-anki` produces .apkg deck (audio clip + L2 text + L1 gloss)

**Success Criteria:**
- [ ] SM-2 scheduler correctly computes next_review dates from quality scores
- [ ] Drill loop presents clips, accepts user input, scores, and stores result
- [ ] SQLite db persists across sessions — picks up where left off
- [ ] Anki export produces valid .apkg file importable by Anki desktop
- [ ] All tests pass

---

