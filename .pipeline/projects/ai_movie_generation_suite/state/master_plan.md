# AI Movie Generation Suite — Master Implementation Plan

## 1. Core Deliverable

A multi-stage screenplay development pipeline that transforms a story concept into production-ready creative assets:

- **Save-the-Beats beat sheet** (Blake Snyder methodology)
- **Full screenplay** with formatted scenes and dialogue
- **Detailed scene descriptions** (visual direction, camera notes, mood)
- **Character descriptions** with consistent visual identity
- **Storyboard/image generation prompts** (optimized for AI image models)
- **3D character/world export pipeline** for Unreal Engine 5 (or equivalent)

The suite is designed as a modular pipeline where each stage produces structured, machine-readable output that feeds the next stage. The MVP ships the screenplay writing pipeline; visual and 3D integration phases extend it outward.

---

## 2. Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Movie Generation Suite                    │
├──────────┬──────────┬──────────────┬────────────┬──────────────┤
│  Phase 1 │ Phase 2  │   Phase 3    │ Phase 4*   │ Phase 5*     │
│ (MVP)    │          │              │            │              │
├──────────┴──────────┴──────────────┴────────────┴──────────────┤
│                      Core Pipeline Engine                       │
│  (Story → Beats → Script → Scenes → Characters → Assets)       │
├─────────────────────────────────────────────────────────────────┤
│                    Shared Data Models & Storage                  │
│  (JSON/YAML project files, character registry, beat registry)   │
├─────────────────────────────────────────────────────────────────┤
│                    LLM Orchestration Layer                      │
│  (GPT-4/Claude/local models, prompt templates, context mgmt)    │
└─────────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

- **Project-centric data model:** Each movie project is a self-contained directory with typed JSON/YAML files for beats, scripts, characters, scenes, and assets.
- **LLM-agnostic core:** The pipeline uses a pluggable LLM interface. Default providers: OpenAI GPT-4o, Claude 3.5 Sonnet, local models via Ollama.
- **Prompt templates as first-class artifacts:** All prompts for image/storyboard generation are stored as reusable templates with variable substitution.
- **Character consistency via registry:** A character registry enforces consistent descriptions across all stages (appearance, voice, personality, costume notes).
- **Extensible asset pipeline:** Asset export formats (FBX, USD, GLTF) are plug-in modules. UE5 integration is one plugin among potential others (Godot, Blender).

---

## 3. Phase Breakdown

### Phase 1 — Screenplay Writing Core (MVP)

**Goal:** Ship a functional screenplay development tool that takes a story concept and produces a complete beat sheet, full script, scene descriptions, and dialogue.

**Description:**
This phase builds the core pipeline:
1. **Beat Sheet Generator** — Uses Save-the-Cat (Blake Snyder) beat structure. User provides a logline; the system generates a structured beat sheet with all 15 beats mapped.
2. **Script Writer** — Expands each beat into formatted screenplay scenes using industry-standard format (Final Draft-compatible).
3. **Scene Description Engine** — For each scene, generates detailed visual direction: setting, lighting, camera angles, mood, action beats.
4. **Dialogue Generator** — Produces character-specific dialogue with voice differentiation.
5. **Project Manager** — CLI/GUI for managing projects, saving/loading, and navigating between beats, scenes, and characters.

**Deliverable:**
- A working CLI (with optional simple web UI) that accepts a logline and outputs:
  - `beats.json` — structured beat sheet
  - `script.fdx` (or `.fdx`-compatible JSON) — formatted screenplay
  - `scenes/` directory — detailed scene descriptions per scene
  - `characters.json` — initial character roster with basic descriptions
- All output is machine-readable and structured for downstream phases.

**Dependencies:**
- None (standalone MVP)
- Requires LLM API access (GPT-4o or Claude 3.5 Sonnet recommended)

**Success Criteria:**
- [ ] User can input a logline and generate a complete Save-the-Cat beat sheet (15 beats)
- [ ] Beat sheet is exportable to standard screenplay format
- [ ] Script is generated with proper scene headings, action lines, character names, and dialogue
- [ ] Scene descriptions include visual direction, camera notes, and mood
- [ ] Dialogue is character-consistent (each character has a distinguishable voice)
- [ ] Project can be saved and reloaded without data loss
- [ ] User can edit any beat/scene/character and regenerate downstream content

---

### Phase 2 — Character Consistency & Visual Planning

**Goal:** Add robust character management, visual identity systems, and AI image/storyboard prompt generation.

**Description:**
This phase extends the pipeline with:
1. **Character Registry** — Deep character profiles with: physical appearance, voice notes, personality traits, backstory, costume descriptions, and a "visual anchor" (key visual reference). Characters are versioned and cross-referenced across all scenes.
2. **Character Consistency Engine** — Ensures characters are described identically across all scenes. Generates a "character sheet" prompt optimized for AI image generation (Midjourney, DALL-E, Stable Diffusion).
3. **Storyboard Prompt Generator** — For each scene, generates AI image generation prompts with:
   - Character appearance (pulled from registry)
   - Scene composition, camera angle, lighting, mood
   - Style guidance (e.g., "cinematic, 35mm film, anamorphic lens")
   - Negative prompts and parameters
4. **Visual Mood Board** — Aggregates generated prompts and allows users to collect reference images per scene/character.
5. **Scene-to-Image Pipeline** — Optional integration with image generation APIs (Midjourney via Discord bot, DALL-E API, or local Stable Diffusion) to produce actual storyboard frames.

**Deliverable:**
- `characters.json` — enriched character registry with visual anchors and cross-scene consistency
- `storyboard_prompts/` — per-scene AI image prompts with parameters
- `mood_boards/` — per-character and per-scene visual reference collections
- Optional: live image generation integration (configurable per user)

**Dependencies:**
- Phase 1 (screenplay core must be complete)
- Image generation API access (optional for MVP of this phase)

**Success Criteria:**
- [ ] Character registry enforces consistent visual descriptions across all scenes
- [ ] Each character has a generated "character sheet" prompt for AI image models
- [ ] Each scene has 1-3 storyboard prompts with camera, lighting, and style guidance
- [ ] Prompts are optimized for the target image model (user-selectable)
- [ ] Mood boards can be assembled and exported per character and per scene
- [ ] User can generate actual storyboard images (if API connected) and review them

---

### Phase 3 — 3D World & Character Export Pipeline

**Goal:** Enable export of characters and environments into 3D pipelines (starting with Unreal Engine 5) for previsualization and final production.

**Description:**
This phase adds the bridge between creative writing and 3D production:
1. **3D Character Description Generator** — Translates character registry entries into 3D character specifications:
   - Body proportions, facial structure, skin texture notes
   - Costume topology and material specifications
   - Rigging requirements (humanoid, proportions, facial blendshapes)
   - Export format recommendations (FBX, USD, GLTF)
2. **Environment/World Builder** — Generates scene environment descriptions suitable for 3D world creation:
   - Spatial layout, dimensions, architectural style
   - Material and lighting specifications
   - Consistent world bible (all scenes share the same world rules)
3. **UE5 Integration Pipeline** — Export formats and workflows for Unreal Engine 5:
   - FBX character export with rigging metadata
   - USD scene export for environment previsualization
   - MetaHuman-compatible character descriptions (for MetaHuman Creator integration)
   - Blueprint integration for scene sequencing
4. **World Consistency Engine** — Maintains a "world bible" ensuring all scenes, characters, and environments share consistent rules (physics, art style, color palette, scale).
5. **Previsualization Pipeline** — Optional: generates basic UE5 Blueprints or USD scenes from the world bible for rough previsualization.

**Deliverable:**
- `characters_3d/` — per-character 3D specifications and export-ready files
- `environments/` — per-scene environment descriptions and 3D asset specs
- `world_bible.json` — consistent world rules, art direction, and style guide
- `ue5_export/` — UE5-compatible export files (FBX, USD, Blueprint templates)
- Integration scripts for importing characters and environments into UE5

**Dependencies:**
- Phase 2 (character registry and visual descriptions must be complete)
- UE5 installed (for testing integration)
- 3D asset pipeline knowledge (FBX/USD export, MetaHuman workflow)

**Success Criteria:**
- [ ] Character descriptions include 3D-ready specifications (proportions, rigging, materials)
- [ ] World bible enforces consistency across all scenes and characters
- [ ] Characters can be exported as FBX/USD with proper rigging metadata
- [ ] Environments can be exported as USD for UE5 previsualization
- [ ] UE5 import pipeline works end-to-end (characters + environments load correctly)
- [ ] World bible can be exported as a style guide for human artists

---

## 4. Architecture Notes

### Data Model (Core)

```
project/
├── project.json              # Project metadata, logline, genre, tone
├── beats.json                # Save-the-Cat beat sheet (15 beats)
├── script.json               # Formatted screenplay (scene-by-scene)
├── characters.json           # Character registry (Phase 1+)
├── characters_3d/            # 3D character specs (Phase 3+)
│   ├── {char_id}/
│   │   ├── description.json
│   │   ├── visual_anchor.png
│   │   └── export.fbx
├── scenes/
│   ├── {scene_id}/
│   │   ├── description.json  # Visual direction, camera, mood
│   │   └── storyboard_prompts.json
├── storyboard_prompts/       # AI image prompts (Phase 2+)
│   ├── {scene_id}.json
├── mood_boards/              # Visual references (Phase 2+)
│   ├── characters/
│   └── scenes/
├── world_bible.json          # World consistency rules (Phase 3+)
└── ue5_export/               # UE5 integration files (Phase 3+)
    ├── blueprints/
    ├── characters/
    └── environments/
```

### Technology Stack (Recommended)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Core language | Python 3.11+ | LLM ecosystem, rapid prototyping |
| LLM interface | OpenAI API / Anthropic API / Ollama | Flexible provider support |
| Prompt management | Jinja2 templates | Reusable, versioned prompts |
| Data storage | JSON + YAML | Human-readable, version-controllable |
| CLI | Click or Typer | Simple, familiar interface |
| Web UI (optional) | Streamlit or Gradio | Rapid prototyping, no build step |
| 3D export | PyFBX / USD Python API | Industry-standard formats |
| UE5 integration | Python scripting in UE5 | Blueprint automation |

### Consistency Strategy

- **Character consistency:** A single `characters.json` registry is the source of truth. Every scene description, storyboard prompt, and 3D spec pulls from this registry. Any change to a character propagates to all downstream artifacts.
- **World consistency:** The `world_bible.json` defines immutable world rules (art style, physics, color palette, scale). The consistency engine validates all scenes against these rules and flags deviations.
- **Version control:** All project files are plain text (JSON/YAML), making them git-friendly. The project directory itself is the versionable unit.

---

## 5. Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **LLM output quality is inconsistent** | High | Use structured output schemas (JSON mode, function calling). Implement a validation layer that checks output against expected schemas. Allow manual editing at every stage. |
| **Character consistency degrades across long scripts** | High | Implement a character context window that summarizes each character's current state. Use retrieval-augmented generation to pull character details into each scene prompt. |
| **3D export pipeline is complex and fragile** | Medium | Start with MetaHuman-compatible descriptions (simpler rigging). Use USD as the intermediate format (more robust than FBX for complex scenes). Phase 3 can be optional/advanced. |
| **UE5 integration requires specialized knowledge** | Medium | Provide pre-built Blueprint templates and Python scripts. Document the import process thoroughly. Make UE5 integration optional — the core pipeline works without it. |
| **Image generation API costs at scale** | Medium | Allow users to bring their own API keys. Support local Stable Diffusion as a free alternative. Cache generated images to avoid re-generation. |
| **Scope creep into full movie production** | High | Explicitly scope this tool as a *pre-production* suite. The deliverable is creative assets and planning documents, not actual rendered video. Future phases can add rendering if needed. |
| **Prompt engineering for image models is model-specific** | Medium | Abstract prompt generation behind a provider interface. Maintain separate prompt templates per target model (Midjourney, DALL-E, SDXL). Allow custom prompt templates. |

---

### Phase 4 — Storyboard to Animatic

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

### Phase 5 — AI Voice & Audio

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

### Phase 6 — AI Video Generation

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

### Phase 7 — Collaborative Editing & Review

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
