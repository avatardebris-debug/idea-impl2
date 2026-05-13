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

