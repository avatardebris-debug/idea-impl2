# Phase 2 Tasks

- [x] Task 1: Add CLIP dependencies and CLIP embedding module
  - What: Install openai/clip and torch. Create `clip_wrapper.py` that loads the CLIP model (ViT-B/32), computes image embeddings, and returns cosine similarity between two PIL Images.
  - Files: requirements.txt, pyproject.toml (add clip, torch dependencies), src/sim_real_comparator/clip_wrapper.py
  - Done when: `compute_clip_similarity(img_a, img_b)` returns a float in [0,1]; `pip install` succeeds with new deps; unit test in `tests/test_clip_wrapper.py` verifies cosine similarity of identical images ≈ 1.0

- [ ] Task 2: Update data models to include CLIP score
  - What: Extend `FrameResult` to include `clip_similarity: float` (ge=0.0, le=1.0). Extend `GlobalResult` to include per-metric averages (`avg_ssim`, `avg_phash_similarity`, `avg_clip_similarity`) and updated weights (ssim 0.33, phash 0.33, clip 0.34).
  - Files: src/sim_real_comparator/models.py
  - Done when: `FrameResult` has `clip_similarity` field; `GlobalResult` has `avg_ssim`, `avg_phash_similarity`, `avg_clip_similarity`, and `weights` fields; Pydantic validation passes for valid ranges

- [ ] Task 3: Update scorer to include CLIP component
  - What: Modify `compute_global_score` to accept `clip_similarity` per frame and compute the updated weighted global score. Add helper `compute_phash_similarity` (1 - phash_distance) for clarity.
  - Files: src/sim_real_comparator/scorer.py
  - Done when: Global score formula = 0.33*avg_ssim + 0.33*avg_phash_similarity + 0.34*avg_clip_similarity; output `GlobalResult` includes all per-metric averages; unit test verifies score is in [0,1] for known inputs

- [ ] Task 4: Create heatmap generation module
  - What: Create `heatmaps.py` with `generate_heatmap(frame_a, frame_b, output_path)` that computes pixel-wise absolute difference, normalizes it, and renders as a color-coded overlay (e.g., red=high difference, green=low difference) saved as PNG. Also create `generate_heatmap_batch(frames_a, frames_b, output_dir)` for batch processing.
  - Files: src/sim_real_comparator/heatmaps.py, requirements.txt (add matplotlib), pyproject.toml (add matplotlib)
  - Done when: `generate_heatmap` produces a valid PNG file; heatmap visually highlights difference regions; `generate_heatmap_batch` processes a list of frame pairs and returns list of output paths; test in `tests/test_heatmaps.py` verifies PNG output exists and is non-empty

- [ ] Task 5: Create report module with CLIP scores and update CLI
  - What: Create `report.py` that serializes `FrameResult` (now with clip_similarity) and `GlobalResult` to JSON. Create `cli.py` with Click CLI that wires the full pipeline: extract frames → compute SSIM/pHash/CLIP → generate heatmaps → compute global score → write JSON report. CLI flags: --real-video, --sim-video, --output-dir, --num-frames, --fps-real, --fps-sim, --frame-start, --frame-end.
  - Files: src/sim_real_comparator/report.py, src/sim_real_comparator/cli.py
  - Done when: CLI command `sim-compare` runs end-to-end; JSON report contains per-frame ssim, phash_distance, clip_similarity and global score with per-metric averages; heatmap PNGs saved to output dir; `--fps-real` and --fps-sim` flags trigger FPS normalization; `--frame-start` and `--frame-end` constrain frame range

- [ ] Task 6: Integration tests with synthetic video pairs
  - What: Create `tests/test_integration.py` that generates two synthetic "videos" (numpy arrays) — one identical and one with known pixel differences — runs the full CLI pipeline, and asserts: JSON report has correct metric values, heatmaps are generated, global score is ≈1.0 for identical videos and <0.5 for different videos.
  - Files: tests/test_integration.py
  - Done when: `pytest tests/test_integration.py` passes; identical video pair yields global_score > 0.9; different video pair yields global_score < 0.5; all three metrics present in JSON output