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

#