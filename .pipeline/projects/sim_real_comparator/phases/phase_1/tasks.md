# Phase 1 Tasks

- [x] Task 1: Project scaffolding and dependencies
  - What: Create the project directory structure, pyproject.toml, requirements.txt, and README.md. Define the package layout under src/sim_real_comparator/.
  - Files: pyproject.toml, requirements.txt, README.md, src/sim_real_comparator/__init__.py
  - Done when: Project can be installed with `pip install -e .` and the package namespace is importable; all listed dependencies (imageio[ffmpeg], scikit-image, imagehash, click) are present in requirements.txt

- [ ] Task 2: Frame extraction module
  - What: Build `frame_extractor.py` that reads two video files (real and sim), extracts frames at matching indices, and returns them as numpy arrays. Handle frame count alignment (truncate to min frame count).
  - Files: src/sim_real_comparator/frame_extractor.py, tests/test_frame_extractor.py
  - Done when: Can extract frames from MP4 files; extracting from two videos returns aligned frame pairs; unit tests verify frame count alignment and numpy array output shapes

- [ ] Task 3: Metrics module (SSIM + pHash)
  - What: Build `metrics.py` with two functions: `compute_ssim(frame_a, frame_b)` returning float in [0,1], and `compute_phash_distance(frame_a, frame_b)` returning normalized Hamming distance in [0,1].
  - Files: src/sim_real_comparator/metrics.py, tests/test_metrics.py
  - Done when: SSIM returns 1.0 for identical frames and <1.0 for different frames; pHash distance returns 0.0 for identical frames and >0.0 for different frames; unit tests cover both functions with synthetic images

- [ ] Task 4: Scorer and data models
  - What: Build `models.py` with a Pydantic dataclass for per-frame results and `scorer.py` that computes a weighted global score from normalized SSIM and pHash values.
  - Files: src/sim_real_comparator/models.py, src/sim_real_comparator/scorer.py, tests/test_scorer.py
  - Done when: Global score is always in [0,1]; unit tests verify score bounds and weighted combination logic

- [ ] Task 5: Report generation
  - What: Build `report.py` that serializes per-frame results and global score to a JSON file in the output directory.
  - Files: src/sim_real_comparator/report.py
  - Done when: JSON report matches the spec format: `{"frames": [{"frame_index": N, "ssim": X, "phash_distance": Y}, ...], "global_score": Z}`; unit test verifies JSON structure and field types

- [ ] Task 6: CLI entry point and integration
  - What: Build `cli.py` with Click CLI: `sim-compare --real <path> --sim <path> --output <dir>`. Wire the full pipeline: extract frames → compute metrics → compute global score → write JSON report.
  - Files: src/sim_real_comparator/cli.py
  - Done when: CLI command runs end-to-end on two sample videos, produces JSON report in output dir, and prints the global score to stdout