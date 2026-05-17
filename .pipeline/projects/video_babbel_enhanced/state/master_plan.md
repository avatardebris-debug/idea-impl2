# [video babbel enhanced] — Master Plan

## Idea Summary

**Video Babbel Enhanced** is a language learning platform that exploits the learner's existing knowledge. If you've already memorized a video in your native language, you have the perfect comprehension scaffold — the tool extracts the most pedagogically valuable phrases, presents them in both languages, and drills them using spaced repetition.

**Core method (Krashen's Comprehensible Input + frequency-ordered vocab):**
- Any uploaded video → transcribed → translated → frequency-scored → clipped
- Top N clips are the phrases covering the most high-frequency vocabulary in drillable sentence lengths
- SM-2 spaced repetition schedules reviews so the right clips resurface at the right time

**Architecture:**
```
Video Upload
    → Whisper STT (via video_ingestor_summary workspace)
    → LLM translation (via video_babbel workspace / direct LLM call)
    → Frequency Scorer (SUBTLEX word lists → score each segment)
    → Clip Extractor (ffmpeg → N short .mp4 clips + metadata.json)
    → Practice Engine (SM-2 scheduler → drill loop)
    → Web UI (Flask: upload, configure, watch, drill)
```

**Dependencies:**
- `video_ingestor_summary` — Whisper transcription with word-level timestamps
- `video_babbel` — LLM translation layer and dual-language subtitle generation
- Optional: `video_langfake` — lip sync for dubbed clip variants (Phase 3)

---

## Phase 1: Core Extraction Engine

**Goal:** Given a video file, produce a ranked set of short clips with dual-language metadata.

**Deliverables:**
- Python package `video_babbel_enhanced/`
- `transcriber.py` — thin wrapper calling video_ingestor_summary workspace
- `translator.py` — thin wrapper calling video_babbel workspace / LLM fallback
- `frequency_scorer.py` — loads SUBTLEX-US + target language word lists, scores segments
- `clip_extractor.py` — ffmpeg-based clip cutter; outputs .mp4 + per-clip JSON metadata
- `cli.py` — `python -m video_babbel_enhanced extract input.mp4 --lang es --top 50 --output clips/`
- Unit tests for scorer and extractor

**Success Criteria:**
- [ ] Given a .mp4 file and target language, CLI produces a `clips/` directory with N clips
- [ ] Each clip has a corresponding `clip_N.json` with: L1 text, L2 text, timestamps, freq_score, word_count
- [ ] Frequency scorer correctly ranks segments — shorter, more-common-word segments score higher
- [ ] Extractor produces valid .mp4 files playable with ffmpeg
- [ ] All unit tests pass

---

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

## Phase 3: Web UI + Lip Sync Integration

**Goal:** Flask web app for upload → configure → watch → drill. Optional video_langfake lip sync.

**Deliverables:**
- `app.py` — Flask app with routes: `/upload`, `/configure`, `/watch`, `/drill`, `/export`
- Upload page: drop video, select source language + target language, set N clips
- Watch page: video player with toggle L1/L2 audio track + dual subtitles
- Drill page: web-based SM-2 drill loop (JS + fetch API)
- Optional: trigger `video_langfake` workspace on selected clips → dubbed .mp4 variant
- REST API: `POST /extract`, `GET /clips`, `POST /review/{clip_id}`

**Success Criteria:**
- [ ] Web app starts with `python app.py` and is accessible at localhost:5000
- [ ] Full pipeline runnable from the UI: upload → extract → watch/drill
- [ ] L1/L2 audio track toggle works in the player
- [ ] Drill loop records scores and respects SM-2 next_review dates
- [ ] If video_langfake workspace exists, dubbed clip generation can be triggered
- [ ] All integration tests pass
