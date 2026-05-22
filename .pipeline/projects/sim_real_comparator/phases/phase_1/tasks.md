# Phase 1 Tasks

- [ ] Task 1: Project scaffolding and dependencies
  - What: Create the project directory structure, pyproject.toml, requirements.txt, and README.md. Define the package layout under src/sim_real_comparator/.
  - Files: pyproject.toml, requirements.txt, README.md, src/sim_real_comparator/__init__.py
  - Done when: Project can be installed with `pip install -e .` and the package namespace is importable; all listed dependencies (imageio[ffmpeg], scikit-image, imagehash, click) are in requirements.txt

- [ ] Task 2: Frame extraction module
  - What: Build `frame_extractor.py` that reads frames from two video files (real and sim) using `imageio` or `opencv`, aligns them by index, and returns a list of (real_frame, sim_frame) tuples as numpy arrays.
  - Files: src/sim_real_comparator/frame_extractor.py
  - Done when: Given two MP4 files of equal or overlapping duration, the module extracts frames at a configurable rate (default: 1 fps), trims to the shorter video, and returns aligned frame pairs as numpy arrays; unit test in tests/test_frame_extractor.py passes

- [ ] Task 3: Metrics module (SSIM + pHash)
  - What: Build `metrics.py` with functions to compute per-frame SSIM (via skimage) and perceptual hash distance (via imagehash). Normalize pHash distance to [0,1] by dividing by max hash bits.
  - Files: src/sim_real_comparator/metrics.py
  - Done when: `compute_ssim(frame_a, frame_b)` returns a float in [0,1]; `compute_phash_distance(frame_a, frame_b)` returns a float in [0,1]; unit tests in tests/test_metrics.py pass for identical frames (SSIM=1.0, pHash=0.0) and random frames (scores < 1.0)

- [ ] Task 4: Scorer module (global score aggregation)
  - What: Build `scorer.py` that takes per-frame SSIM and normalized pHash values and computes a weighted global score in [0,1]. Default weights: 0.5 SSIM, 0.5 pHash.
  - Files: src/sim_real_comparator/scorer.py
  - Done when: `compute_global_score(ssim_values, phash_values)` returns a float in [0,1]; unit test in tests/test_scorer.py passes — identical frames yield score=1.0, completely different frames yield score near 0

- [ ] Task 5: Report module and data models
  - What: Build `models.py` with dataclasses for per-frame results and the full report. Build `report.py` that serializes the report to JSON.
  - Files: src/sim_real_comparator/models.py, src/sim_real_comparator/report.py
  - Done when: `models.py` defines `FrameResult(frame_index, ssim, phash_distance)` and `ComparisonReport(frames, global_score)` dataclasses; `report.py` writes a JSON file with the exact schema `{"frames": [{"frame_index": N, "ssim": X, "phash_distance": Y}, ...], "global_score": Z}`; unit test in tests/test_report.py validates JSON output

- [ ] Task 6: CLI entry point and integration
  - What: Build `cli.py` with Click CLI that accepts `--real`, `--sim`, and `--output` arguments, wires together frame extraction, metrics, scoring, and report writing.
  - Files: src/sim_real_comparator/cli.py
  - Done when: Running `sim-compare --real <mp4> --sim <mp4> --output <dir>` extracts frames, computes SSIM + pHash, writes a JSON report to the output directory, and exits with code 0; end-to-end test with two sample MP4 files succeeds
