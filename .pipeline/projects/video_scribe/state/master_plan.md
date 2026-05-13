# Video Scribe — Master Implementation Plan

## Idea Summary

**Video Scribe** translates videos into rich, structured scene descriptions powered by an LLM. For every scene in a video, the system produces detailed prose covering: visual content, camera techniques (pan, tilt, zoom, dolly, tracking, etc.), lighting, composition, transitions between scenes, and stylistic notes.

---

## Architecture Overview

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Video Input │────▶│  Scene Segmenter │────▶│  Key Frame       │
│  (mp4, mov,  │     │  (frame diffs,   │     │  Extractor       │
│   avi, etc.) │     │   ML models)     │     │  (one per scene) │
└─────────────┘     └──────────────────┘     └────────┬─────────┘
                                                       │
                                                       ▼
┌─────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Output      │◀────│  Description     │◀────│  VLM / LLM       │
│  (markdown,  │     │  Assembler &     │     │  Analysis        │
│   JSON, etc.)│     │  Context Enrich. │     │  (per frame)     │
└─────────────┘     └──────────────────┘     └──────────────────┘
```

### Key Components

| Component | Responsibility |
|---|---|
| **Video Loader** | Open video files, decode frames, handle formats |
| **Scene Segmenter** | Detect scene boundaries via frame-difference analysis or ML |
| **Key Frame Extractor** | Pick representative frames per scene (mid-scene, high-variance) |
| **VLM Analyzer** | Send key frames to a Vision-Language Model for per-frame analysis |
| **Description Assembler** | Stitch per-frame analyses into coherent scene descriptions |
| **Context Enricher** | Use LLM to add cross-scene context, transitions, camera technique notes |
| **Output Formatter** | Render final descriptions in chosen format (markdown, JSON, etc.) |

### Technology Decisions (Default)

- **Video processing:** `ffmpeg` (via `moviepy` or `opencv`)
- **Scene detection:** Frame-difference thresholding (Phase 1), optional `scenedetect` library
- **VLM:** OpenAI GPT-4o / Anthropic Claude multimodal (configurable)
- **LLM context enrichment:** Same provider as VLM, text-only mode
- **Output:** Markdown + JSON (structured)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| VLM API cost for long videos | High | Batch frames, cache results, allow local model fallback (e.g., LLaVA) |
| Scene boundary detection errors | Medium | Use multiple strategies (frame diff + color histogram + audio cue); allow manual adjustment |
| Context window limits for LLM | Medium | Chunk scenes, use hierarchical summarization, maintain a running scene synopsis |
| VLM latency for real-time use | Medium | Async processing, queue-based pipeline, progress reporting |
| Video format compatibility | Low | Rely on ffmpeg for universal decode support |
| Description quality varies by content | Medium | Provide prompt templates tuned for cinematography; allow user customization |

---

## Phase 1 — MVP: Single-Scene Frame-to-Description Pipeline

> **Goal:** Prove the core loop works — feed a video clip into the system, get back a written scene description.

### Description

Build the end-to-end pipeline for a single short video clip (≤30 seconds). This phase establishes:
1. Frame extraction from a video file
2. One key frame per clip
3. Sending that frame to a VLM with a structured prompt
4. Returning the resulting scene description as text

This is the smallest useful thing because it validates the entire value chain: video input → visual analysis → LLM description → human-readable output.

### Deliverable

- A runnable CLI tool (`video_scribe.py`) that accepts a video file path and outputs a scene description to stdout or a file.
- Supports `.mp4` and `.mov` input.
- Uses a configurable VLM provider (default: GPT-4o).
- Output is a markdown-formatted scene description including:
  - Scene content summary
  - Notable visual elements
  - Camera position/angle (inferred)
  - Lighting and color notes

### Dependencies

- Python 3.10+
- `opencv-python` or `moviepy` for frame extraction
- OpenAI or Anthropic API key (for VLM)
- `ffmpeg` installed on the system

### Success Criteria

- [ ] Given a 30-second video clip, the tool produces a scene description in under 60 seconds (including API latency).
- [ ] The description includes at least 3 distinct visual observations (e.g., subject, setting, lighting).
- [ ] The tool handles common video formats (mp4, mov) without errors.
- [ ] The pipeline is runnable with a single command: `python video_scribe.py input.mp4 --output description.md`

### Architecture Notes for Phase 1

- Frame extraction: Use `opencv` to sample frames at 1fps, pick the middle frame as the key frame.
- VLM prompt template: Hardcoded prompt asking for cinematographic analysis (camera angle, composition, lighting, subject matter).
- No scene segmentation yet — the entire clip is treated as one scene.
- Single-threaded, synchronous processing.

---

## Phase 2 — Full Video Pipeline: Multi-Scene Processing & Coherent Descriptions

> **Goal:** Process complete videos of arbitrary length, segment them into scenes, and produce a structured, multi-scene description document.

### Description

Extend the Phase 1 pipeline to handle full-length videos. Key additions:
1. **Scene segmentation** — automatically detect scene boundaries using frame-difference analysis and/or color histogram comparison.
2. **Multi-frame per scene** — extract 2-3 key frames per scene (start, middle, end) for richer analysis.
3. **Cross-scene context** — use the LLM to generate transition descriptions between consecutive scenes.
4. **Structured output** — produce a well-organized document with scene headers, timestamps, and consistent formatting.
5. **Batched VLM calls** — process scenes in parallel where possible to reduce total runtime.

### Deliverable

- A CLI tool that accepts any video file and outputs a complete multi-scene description document.
- Automatic scene boundary detection with configurable sensitivity.
- Output format: Markdown document with per-scene sections including:
  - Scene number and timestamp range
  - Scene content description (multi-frame synthesis)
  - Camera techniques detected (pan, tilt, zoom, dolly, tracking, cut, fade, dissolve, etc.)
  - Transition description to the next scene
  - Lighting, composition, and mood notes
- JSON output option for programmatic consumption.
- Progress indicator during processing.

### Dependencies

- All Phase 1 dependencies.
- `scenedetect` or custom frame-difference algorithm for scene segmentation.
- Async/parallel processing library (e.g., `concurrent.futures` or `asyncio`).
- Prompt templates for multi-frame synthesis and transition detection.

### Success Criteria

- [ ] Given a 5-minute video, the tool correctly identifies ≥90% of obvious scene boundaries (validated against manual ground truth).
- [ ] The output document contains accurate descriptions for every detected scene.
- [ ] Transition descriptions between consecutive scenes are coherent and accurate.
- [ ] Total processing time for a 5-minute video is under 10 minutes (including API calls).
- [ ] JSON output is valid and contains all scene data in a structured schema.

### Architecture Notes for Phase 2

- Scene segmentation: Use frame-difference thresholding (default: 15% pixel change between consecutive frames) with a minimum scene duration of 2 seconds to avoid false positives.
- Key frame selection: Pick frames at 25%, 50%, and 75% of each scene's duration.
- VLM batching: Send up to 3 frames per scene in a single multimodal API call.
- Context enrichment: After all scenes are analyzed, run a second LLM pass to generate transition descriptions and a global summary.
- Output assembly: Build a markdown document with consistent headers, timestamps, and scene metadata.

---

## Phase 3 — Polish & Advanced Features

> **Goal:** Elevate quality, add advanced camera/transition detection, improve UX, and make the system production-ready.

### Description

This phase focuses on quality improvements and feature additions that make Video Scribe a polished, production-grade tool:

1. **Advanced camera technique detection** — Use frame-level optical flow and metadata to detect specific camera movements (pan, tilt, zoom, dolly, tracking, crane, handheld shake) rather than relying solely on VLM inference.
2. **Transition classification** — Detect and classify transitions between scenes (cut, fade to black, dissolve, wipe, iris, jump cut) using both visual analysis and temporal proximity.
3. **Audio analysis** — Incorporate audio cues (dialogue detection, music changes, sound effects) to enrich scene descriptions.
4. **Prompt customization** — Allow users to customize the analysis depth and style (e.g., "screenwriter mode," "director's notes," "technical breakdown").
5. **Export formats** — Add support for screenplay format (Final Draft XML, Fountain), storyboard text, and HTML.
6. **Caching & resuming** — Cache VLM results per frame so re-runs are fast; support resuming interrupted processing.
7. **API / Web interface** — Optional REST API endpoint and simple web UI for non-CLI users.
8. **Local model fallback** — Support running VLM locally (e.g., LLaVA, Qwen-VL) for privacy or cost-sensitive use cases.

### Deliverable

- A polished CLI tool with advanced detection capabilities.
- Camera technique detection accuracy ≥80% on a test set of 50 clips.
- Transition classification accuracy ≥85% on the same test set.
- Audio-enhanced scene descriptions (optional, toggle via CLI flag).
- Multiple export formats: markdown, JSON, Fountain screenplay, HTML.
- Result caching layer (SQLite or file-based) for fast re-runs.
- Optional REST API (`/analyze`, `/status`, `/results` endpoints).
- Local model support via `llama.cpp` or `transformers` backend.
- Comprehensive documentation and example outputs.

### Dependencies

- All Phase 1 and Phase 2 dependencies.
- `pydantic` for API models.
- `fastapi` or `flask` for REST API.
- `librosa` or `pydub` for audio analysis.
- `opencv` optical flow modules for camera movement detection.
- `fountain` library for screenplay export.
- Local VLM models (LLaVA, Qwen-VL) via `transformers` or `llama.cpp`.

### Success Criteria

- [ ] Camera technique detection achieves ≥80% accuracy on a curated test set of 50 clips.
- [ ] Transition classification achieves ≥85% accuracy on the same test set.
- [ ] Audio-enhanced descriptions add meaningful, accurate context in ≥90% of test cases.
- [ ] Re-running a processed video with cached results takes <10% of the original time.
- [ ] All export formats produce valid, well-formatted output.
- [ ] REST API handles concurrent requests without data corruption.
- [ ] Local model mode produces descriptions within 2x the latency of cloud VLM.
- [ ] Documentation includes setup guide, API reference, example outputs, and troubleshooting.

### Architecture Notes for Phase 3

- Camera detection: Combine optical flow analysis (for motion vectors) with VLM inference for robust detection.
- Transition detection: Use both visual analysis (frame similarity at boundaries) and temporal gap analysis.
- Audio pipeline: Run separate audio analysis pass, extract dialogue timestamps, music segments, and silence gaps; merge with visual descriptions.
- Caching: Store frame hashes + VLM responses in SQLite keyed by file path and frame timestamp.
- API: FastAPI with async endpoints; process queue backed by `celery` or `rq`.
- Local models: Abstract VLM provider behind a trait/interface so cloud and local backends are interchangeable.

---

## Phase Summary

| Phase | Scope | Key Value |
|---|---|---|
| **1 — MVP** | Single-clip, single-scene frame → description | Proves the core pipeline works end-to-end |
| **2 — Full Pipeline** | Multi-scene, full video, structured output | Handles real-world videos with coherent multi-scene descriptions |
| **3 — Polish** | Advanced detection, UX, exports, API, local models | Production-ready, high-quality, flexible tool |

---

## Open Questions

1. **Which VLM provider is the default?** GPT-4o offers good multimodal quality; Claude is competitive on reasoning. Consider making this configurable from day one.
2. **Should audio analysis be in Phase 2 or 3?** Audio adds significant complexity. Phase 3 is safer for an MVP-first approach.
3. **Real-time vs. batch?** This plan assumes batch processing. Real-time streaming would require a different architecture (streaming frame analysis, incremental description generation).
4. **Monetization?** If this becomes a product, consider per-minute pricing, subscription tiers, or self-hosted licensing.
