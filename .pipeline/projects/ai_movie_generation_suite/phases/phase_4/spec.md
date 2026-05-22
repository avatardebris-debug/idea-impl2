## Phase 4 — Storyboard to Animatic

**Goal:** Turn storyboard frames and scene metadata into a timed animatic sequence with pacing, transitions, and placeholder audio guidance.

**Description:**
This phase bridges static storyboards and motion preview:
1. **Animatic Timeline Builder** — Maps scenes and storyboard frames to a timeline with duration, transition type, and beat alignment.
2. **Pacing Engine** — Suggests hold times per frame from dialogue length, action beats, and genre/tone presets.
3. **Transition Planner** — Cut, dissolve, wipe, and match-cut notes derived from scene descriptions and camera notes.
4. **Audio Placeholder Track** — Music mood and SFX cue suggestions per segment (no full mix required).
5. **Animatic Export** — Machine-readable animatic spec (JSON) plus optional EDL/XML for editors.

**Deliverable:**
- `animatic/` — per-project timeline JSON, frame order, durations, transitions
- `animatic/audio_cues.json` — music/SFX/voiceover placeholder cues per segment
- CLI command to render a simple preview manifest (frame list + timings) for downstream tools

**Dependencies:**
- Phase 2 (storyboard prompts and mood boards)
- Phase 3 optional (3D previz metadata can enrich timing)

**Success Criteria:**
- [ ] Each scene with storyboard prompts has at least one timed segment on the animatic timeline
- [ ] Timeline exports as structured JSON with scene_id, duration_ms, transition, and beat_ref
- [ ] Pacing respects dialogue line count and scene description mood
- [ ] User can regenerate animatic from updated storyboards without losing manual timing overrides
- [ ] Downstream phases can read animatic JSON without custom parsing

---

#