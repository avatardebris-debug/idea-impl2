## Phase 5 — AI Voice & Audio

**Goal:** Generate dialogue audio and voice-direction metadata from the screenplay, with per-character voice profiles.

**Description:**
1. **Voice Profile Registry** — Extends character registry with TTS/voice-clone parameters (pitch, pace, accent, emotion range).
2. **Dialogue-to-Audio Pipeline** — Converts `DialogueLine` entries to audio segment specs with emotion and delivery tags.
3. **Batch TTS Integration** — Pluggable provider interface (ElevenLabs, OpenAI TTS, local Piper/Coqui) with BYO API keys.
4. **Lip-Sync Hints** — Exports phoneme/timing stubs for Phase 6 video or external lip-sync tools.
5. **Audio Assembly Manifest** — Ordered WAV/MP3 paths or URLs plus mix notes (dialogue vs music vs SFX lanes).

**Deliverable:**
- `audio/voice_profiles.json` — per-character voice settings
- `audio/dialogue_segments/` — segment specs and generated clips (when API configured)
- `audio/assembly_manifest.json` — ordered timeline for animatic sync

**Dependencies:**
- Phase 1 (script and dialogue)
- Phase 4 (animatic timing for alignment)

**Success Criteria:**
- [ ] Every dialogue line in the script has a corresponding audio segment spec
- [ ] Voice profiles are consistent per character across all scenes
- [ ] Provider interface works with at least one local/offline fallback (no API required for CI)
- [ ] Assembly manifest aligns segment start times with animatic timeline
- [ ] Regenerating a scene's dialogue updates only that scene's audio specs

---

#