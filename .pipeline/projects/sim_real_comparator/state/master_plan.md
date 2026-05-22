# Master Plan: sim_real_comparator

## Idea Summary

Given a real video clip and a MuJoCo simulation render of the same task, compute multi-metric similarity: SSIM, perceptual hash (pHash), and CLIP embedding cosine similarity. Output per-frame heatmap + global score in [0,1]. Core evaluation tool for sim-to-real gap measurement.

## Core Deliverable

A Python library + CLI tool that:
1. Takes two video inputs (real video path/URL, simulated video path/URL).
2. Extracts aligned frames from both videos.
3. Computes per-frame similarity across three metrics: SSIM, perceptual hash distance, CLIP cosine similarity.
4. Produces per-frame heatmap overlays (PNG) saved to an output directory.
5. Computes a global [0,1] similarity score and writes a JSON report.

## Architecture Overview

```
sim_real_comparator/
├── src/
│   └── sim_real_comparator/
│       ├── __init__.py
│       ├── cli.py              # Click CLI entry point
│       ├── config.py           # Settings (env vars)
│       ├── frame_extractor.py  # Frame extraction from video files
│       ├── metrics.py          # SSIM, pHash, CLIP computation
│       ├── heatmaps.py         # Per-frame heatmap generation
│       ├── scorer.py           # Global score aggregation
│       ├── report.py           # JSON report generation
│       └── models.py           # Data classes for results
├── tests/
│   ├── test_frame_extractor.py
│   ├── test_metrics.py
│   ├── test_heatmaps.py
│   └── test_scorer.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

### Integration with `video_ingestor_summary`

The sim_real_comparator is **not** a direct consumer of video_ingestor_summary's transcription/Q&A API. However, it may **optionally** use:

- **`video_ingestor.summary`** (not needed for core functionality — this project focuses on visual similarity, not semantic Q&A).
- **`video_ingestor.EmbeddingGenerator`** — could be reused for CLIP-style embeddings if the sentence-transformers model proves suitable, but CLIP (openai/clip) is a different model family. **Decision: use openai/clip directly; no reuse needed.**
- **`video_ingestor.config.Settings`** — pattern for env-var config. **Decision: replicate the Settings pattern (not import), since sim_real_comparator has different config needs.**
- **`video_ingestor.storage.Storage`** — SQLite storage pattern. **Decision: not needed; results go to JSON + PNG files.**

**No imports from `video_ingestor_summary` are required.** The dependency is listed as a pipeline peer, not a code dependency.

### Metric Details

| Metric | Library | Output | Range |
|--------|---------|--------|-------|
| SSIM | `skimage.metrics.structural_similarity` | Per-frame float | [0,1] |
| Perceptual Hash | `imagehash` (average hash) | Hamming distance between hashes | [0,1] (normalized) |
| CLIP Cosine | `clip` (openai/clip) | Cosine similarity of image embeddings | [0,1] |

### Global Score

Weighted combination: `global_score = w_ssim * ssim + w_phash * (1 - phash_norm) + w_clip * clip_sim`
Default weights: `[0.3, 0.3, 0.4]` (CLIP weighted higher for semantic alignment).

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Frame alignment mismatch between real and sim videos | High | Allow user-specified frame range / subsampling; auto-detect via FPS |
| CLIP model download / GPU memory | Medium | Cache model; support CPU fallback; document VRAM requirements |
| Large video files consuming disk (heatmaps) | Medium | Configurable heatmap output (on/off); optional temp directory cleanup |
| FPS mismatch between real and sim renders | Medium | Frame-rate normalization: resample sim frames to match real video FPS |

## Phase Breakdown

---

### Phase 1: MVP — Frame Extraction + SSIM + pHash + JSON Report

**Description:**
Build the core pipeline: extract frames from two videos, compute SSIM and perceptual hash per frame, write per-frame results as JSON. No heatmaps yet. No CLIP.

**Deliverable:**
- CLI command: `sim-compare --real <path> --sim <path> --output <dir>`
- Frame extraction via `imageio` or `opencv`
- Per-frame SSIM + pHash computation
- JSON report: `{"frames": [{"frame_index": N, "ssim": X, "phash_distance": Y}, ...], "global_score": Z}`
- Global score computed as weighted average of normalized metrics

**Dependencies:**
- `imageio[ffmpeg]` or `opencv-python` for frame extraction
- `scikit-image` for SSIM
- `imagehash` for perceptual hash
- No external project dependencies

**Success Criteria:**
- [ ] Can extract frames from MP4 video files
- [ ] SSIM and pHash computed for every frame pair
- [ ] JSON report written with per-frame scores and global score
- [ ] Global score is in [0,1]
- [ ] CLI works end-to-end on two sample videos
- [ ] Unit tests for frame extraction, SSIM, pHash, and scorer pass

---

### Phase 2: CLIP Integration + Per-Frame Heatmaps

**Description:**
Add CLIP embedding cosine similarity as the third metric. Generate per-frame heatmap overlays (PNG) showing pixel-level difference regions. Improve frame alignment logic.

**Deliverable:**
- CLIP embedding computation using `clip` (openai/clip) or `transformers` CLIP
- Cosine similarity per frame
- Heatmap generation: difference maps rendered as color-coded overlays saved as PNG
- Updated JSON report with CLIP scores
- Frame alignment: FPS normalization, configurable frame range

**Dependencies:**
- `clip` (openai/clip) or `transformers` + `torch` for CLIP
- `matplotlib` or `PIL` + `numpy` for heatmap rendering
- Phase 1 code (frame extraction, SSIM, pHash)

**Success Criteria:**
- [ ] CLIP cosine similarity computed per frame
- [ ] Heatmap PNGs generated for each frame (saved to output dir)
- [ ] JSON report includes all three metrics per frame
- [ ] Global score updated to include CLIP component
- [ ] FPS normalization works correctly
- [ ] Heatmaps visually show difference regions
- [ ] Integration tests with real+sim video pairs pass

---

### Phase 3: Polish, CLI UX, and Evaluation Pipeline Integration

**Description:**
Improve CLI ergonomics, add batch mode (compare multiple sim videos against one real video), add config file support, and produce a polished README with example workflows. Add optional integration hooks for the broader pipeline (e.g., output format compatible with downstream evaluation dashboards).

**Deliverable:**
- Enhanced CLI: `--config`, `--weights`, `--fps`, `--frame-range`, `--no-heatmaps` flags
- Batch mode: compare one real video against multiple sim videos
- Config file (YAML) for default settings
- README with examples, installation, and sim-to-real evaluation workflow
- Optional: output in a format consumable by pipeline evaluation dashboards
- Performance optimizations: frame caching, parallel frame processing

**Dependencies:**
- Phase 2 code (all metrics, heatmaps, CLIP)
- `click` or `typer` for CLI (if not already used)
- `pyyaml` for config file support
- `tqdm` for progress bars

**Success Criteria:**
- [ ] All CLI flags work correctly
- [ ] Batch mode compares N sim videos against 1 real video in one run
- [ ] Config file loads and overrides defaults
- [ ] Heatmaps can be disabled to save disk space
- [ ] README has installation guide + 3 example workflows
- [ ] Performance: processes 30fps, 60s video in under 5 minutes (CPU)
- [ ] All tests pass (unit + integration)

---

## File Mapping: What to Import from `video_ingestor_summary`

| From `video_ingestor_summary` | Used? | Notes |
|-------------------------------|-------|-------|
| `video_ingestor.models.JobStatus` | ❌ | Not needed — no job tracking |
| `video_ingestor.models.TranscriptSegment` | ❌ | Audio transcription model, irrelevant |
| `video_ingestor.IngestionPipeline` | ❌ | Video download/transcription pipeline |
| `video_ingestor.Storage` | ❌ | SQLite job storage |
| `video_ingestor.EmbeddingGenerator` | ❌ | Sentence-transformers, not CLIP |
| `video_ingestor.VectorStore` | ❌ | ChromaDB for text search |
| `video_ingestor.Summarizer` | ❌ | LLM summarization |
| `video_ingestor.config.Settings` | ❌ | Pattern inspiration only |
| `video_ingestor.__init__.py` exports | ❌ | No imports needed |

**Conclusion:** Zero imports from `video_ingestor_summary`. The dependency is a pipeline peer for video ingestion/Q&A, not a functional dependency for visual similarity computation.

## Success Criteria (Overall Project)

- [ ] MVP (Phase 1) ships: frame extraction + SSIM + pHash + JSON report
- [ ] CLIP + heatmaps (Phase 2) ship: all three metrics + PNG heatmaps
- [ ] Polish (Phase 3) ships: batch mode, config, CLI UX, docs
- [ ] Global score is interpretable: 1.0 = identical, 0.0 = completely different
- [ ] Tool works on CPU (no GPU required, GPU optional for CLIP speedup)
- [ ] Compatible with MuJoCo render outputs (PNG frame sequences or MP4)
- [ ] All tests pass
