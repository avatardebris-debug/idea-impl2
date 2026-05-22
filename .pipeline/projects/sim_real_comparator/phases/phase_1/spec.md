## Phase 1: MVP — Frame Extraction + SSIM + pHash + JSON Report

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

#