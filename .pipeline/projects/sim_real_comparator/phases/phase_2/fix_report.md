# Fix Report — Phase 2

## Current Issues
# Validation Report — Phase 2

## Summary
- Tests: 4 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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
  - Done when: `pytest tests/test_integration.py` passes; iden

## Attempt History

### Attempt 1
- **Failures**: 8 (↓ improving)
- **Previous failures**: 9

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 4 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
ape (64,64)
_______________________________________________________________________________ test_identical_videos ________________________________________________________________________________
tests/test_integration.py:40: in test_identical_videos
    frames = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_different_videos ________________________________________________________________________________
tests/test_integration.py:70: in test_different_videos
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_fps_normalization _______________________________________________________________________________
tests/test_integration.py:101: in test_fps_normalization
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(30)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
________________________________________________________________________ test_phash_distance_identical_fra
```


### Attempt 2
- **Failures**: 8 (→ stalled)
- **Previous failures**: 8

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 4 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
ape (64,64)
_______________________________________________________________________________ test_identical_videos ________________________________________________________________________________
tests/test_integration.py:40: in test_identical_videos
    frames = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_different_videos ________________________________________________________________________________
tests/test_integration.py:70: in test_different_videos
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_fps_normalization _______________________________________________________________________________
tests/test_integration.py:101: in test_fps_normalization
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(30)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
________________________________________________________________________ test_phash_distance_identical_fra
```


### Attempt 3
- **Failures**: 8 (→ stalled)
- **Previous failures**: 8

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 4 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
ape (64,64)
_______________________________________________________________________________ test_identical_videos ________________________________________________________________________________
tests/test_integration.py:40: in test_identical_videos
    frames = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_different_videos ________________________________________________________________________________
tests/test_integration.py:70: in test_different_videos
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_fps_normalization _______________________________________________________________________________
tests/test_integration.py:101: in test_fps_normalization
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(30)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
________________________________________________________________________ test_phash_distance_identical_fra
```


### Attempt 1
- **Failures**: 8 (↓ improving)
- **Previous failures**: 9

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 4 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
ape (64,64)
_______________________________________________________________________________ test_identical_videos ________________________________________________________________________________
tests/test_integration.py:40: in test_identical_videos
    frames = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_different_videos ________________________________________________________________________________
tests/test_integration.py:70: in test_different_videos
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(20)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
_______________________________________________________________________________ test_fps_normalization _______________________________________________________________________________
tests/test_integration.py:101: in test_fps_normalization
    frames_real = [np.full((64, 64, 3), i * 25, dtype=np.uint8) for i in range(30)]
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
/venv/main/lib/python3.12/site-packages/numpy/_core/numeric.py:386: in full
    multiarray.copyto(a, fill_value, casting='unsafe')
E   OverflowError: Python integer 275 out of bounds for uint8
________________________________________________________________________ test_phash_distance_identical_fra
```


### Attempt 2
- **Failures**: 8 (→ stalled)
- **Previous failures**: 8

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 7 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
r uint8
_______________________________________________________________________________ test_fps_normalization _______________________________________________________________________________
tests/test_integration.py:121: in test_fps_normalization
    assert result.returncode == 0
E   assert 1 == 0
E    +  where 1 = CompletedProcess(args=['/venv/main/bin/python', '-m', 'sim_real_comparator.cli', '--real-video', '/tmp/tmposq9zz70/real.mp4', '--sim-video', '/tmp/tmposq9zz70/sim.mp4', '--output-dir', '/tmp/tmposq9zz70/output', '--num-frames', '10', '--fps-real', '30.0', '--fps-sim', '10.0'], returncode=1, stdout='Extracting frames from /tmp/tmposq9zz70/real.mp4...\n', stderr='Traceback (most recent call last):\n  File "<frozen runpy>", line 198, in _run_module_as_main\n  File "<frozen runpy>", line 88, in _run_code\n  File "/workspace/idea impl/.pipeline/projects/sim_real_comparator/workspace/src/sim_real_comparator/cli.py", line 136, in <module>\n    cli()\n  File "/venv/main/lib/python3.12/site-packages/click/core.py", line 1485, in __call__\n    return self.main(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/venv/main/lib/python3.12/site-packages/click/core.py", line 1406, in main\n    rv = self.invoke(ctx)\n         ^^^^^^^^^^^^^^^^\n  File "/venv/main/lib/python3.12/site-packages/click/core.py", line 1269, in invoke\n    return ctx.invoke(self.callback, **ctx.params)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/venv/main/lib/python3.12/site-packages/click/core.py", line 824, in invoke\n    return callback(*args, **kwargs)\n           ^^^^^^^^^^^^^^^^^^^^^^^^^\n  File "/workspace/idea impl/.pipeline/projects/sim_real_comparator/workspace/src/sim_real_comparator/cli.py", line 45, in cli\n    real_frames = extract_frames(real_video, num_frames=num_frames)\n                  ^^^^^^^
```


### Attempt 3
- **Failures**: 8 (→ stalled)
- **Previous failures**: 8

#### Test Output
```
# Validation Report — Phase 2

## Summary
- Tests: 17 passed, 8 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 2 Tasks (acceptance scope)
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

## Test Output
```
_distance_different_frames PASSED                                                                                                             [ 86%]
tests/test_metrics.py::test_phash_distance_completely_different PASSED                                                                                                         [ 91%]
tests/test_metrics.py::test_ssim_returns_float PASSED                                                                                                                          [ 95%]
tests/test_metrics.py::test_phash_distance_returns_float PASSED                                                                                                                [100%]

====================================================================================== FAILURES ======================================================================================
_________________________________________________________________________ test_generate_heatmap_creates_png __________________________________________________________________________
tests/test_heatmaps.py:22: in test_generate_heatmap_creates_png
    result = generate_heatmap(frame_a, frame_b, output_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/heatmaps.py:42: in generate_heatmap
    heatmap[:, :, 2] = diff_norm  # Red channel = difference
    ^^^^^^^^^^^^^^^^
E   IndexError: too many indices for array: array is 2-dimensional, but 3 were indexed
____________________________________________________________________________ test_generate_heatmap_batch _____________________________________________________________________________
tests/test_heatmaps.py:33: in test_generate_heatmap_batch
    paths = generate_heatmap_batch(frames_a, frames_b, tmpdir)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
sr
```

