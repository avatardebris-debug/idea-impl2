## Phase 6 — AI Video Generation

**Goal:** Produce short video clips or shot lists from storyboard prompts and animatic timing, via pluggable video-generation APIs.

**Description:**
1. **Shot List Generator** — Breaks each animatic segment into shots with prompt, duration, and camera metadata.
2. **Video Provider Adapter** — Unified interface for Runway, Pika, Sora-class APIs (configurable, optional).
3. **Prompt Packaging** — Combines storyboard prompts, character visual anchors, and world bible style into provider-specific payloads.
4. **Clip Registry** — Tracks generated clip IDs, paths, status, and retry metadata per shot.
5. **Rough Assembly Export** — Concatenation manifest (FFmpeg-friendly) linking clips to animatic timeline slots.

**Deliverable:**
- `video/shots.json` — shot list with prompts, durations, and provider params
- `video/clips/` — generated clips or placeholder stubs when API unavailable
- `video/assembly.json` — clip order mapped to animatic segments

**Dependencies:**
- Phase 2 (storyboard prompts)
- Phase 4 (animatic timing)
- Phase 5 optional (dialogue audio for mux)

**Success Criteria:**
- [ ] Each animatic segment has at least one shot definition with a complete generation prompt
- [ ] Provider adapter runs in dry-run mode without API keys (CI-safe)
- [ ] Clip registry records success/failure per shot with reproducible prompt hash
- [ ] Assembly export references animatic segment IDs for sync
- [ ] User can swap video provider without changing shot list schema

---

#