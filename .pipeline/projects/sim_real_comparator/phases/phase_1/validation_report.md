# Validation Report — Phase 1

## Summary
- Tests: 4 passed, 10 failed, 0 errors
- Python files in workspace: 9
(Deterministic pytest — no LLM validator steps used.)

## Phase 1 Tasks (acceptance scope)
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

## Test Output
```
rame_extractor.py:19: in test_extract_frames_returns_numpy_array
    result = extract_frames(video_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
___________________________________________________________________________ test_extract_frames_all_frames ___________________________________________________________________________
tests/test_frame_extractor.py:27: in test_extract_frames_all_frames
    result = extract_frames(video_path)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
________________________________________________________________________ test_extract_frames_num_frames_limit ________________________________________________________________________
tests/test_frame_extractor.py:34: in test_extract_frames_num_frames_limit
    result = extract_frames(video_path, num_frames=8)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
_____________________________________________________________________ test_extract_aligned_frames_aligned_counts _____________________________________________________________________
tests/test_frame_extractor.py:43: in test_extract_aligned_frames_aligned_counts
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:43: in extract_aligned_frames
    real_frames = extract_frames(real_video_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
____________________________________________________________________ test_extract_aligned_frames_truncates_to_min ____________________________________________________________________
tests/test_frame_extractor.py:52: in test_extract_aligned_frames_truncates_to_min
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:43: in extract_aligned_frames
    real_frames = extract_frames(real_video_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
_____________________________________________________________________ test_extract_aligned_frames_output_shapes ______________________________________________________________________
tests/test_frame_extractor.py:61: in test_extract_aligned_frames_output_shapes
    real_frames, sim_frames = extract_aligned_frames(real_path, sim_path)
                              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:43: in extract_aligned_frames
    real_frames = extract_frames(real_video_path)
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/frame_extractor.py:19: in extract_frames
    with iio.imiter(video_path) as reader:
E   TypeError: 'generator' object does not support the context manager protocol
________________________________________________________________________ test_phash_distance_identical_frames ________________________________________________________________________
tests/test_metrics.py:36: in test_phash_distance_identical_frames
    distance = compute_phash_distance(frame, frame)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/metrics.py:54: in compute_phash_distance
    phash_a = imagehash.phash(imagehash.ImageWrapper(gray_a))
                              ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
________________________________________________________________________ test_phash_distance_different_frames ________________________________________________________________________
tests/test_metrics.py:43: in test_phash_distance_different_frames
    distance = compute_phash_distance(frame_a, frame_b)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/metrics.py:54: in compute_phash_distance
    phash_a = imagehash.phash(imagehash.ImageWrapper(gray_a))
                              ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
______________________________________________________________________ test_phash_distance_completely_different ______________________________________________________________________
tests/test_metrics.py:50: in test_phash_distance_completely_different
    distance = compute_phash_distance(frame_a, frame_b)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/metrics.py:54: in compute_phash_distance
    phash_a = imagehash.phash(imagehash.ImageWrapper(gray_a))
                              ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
_________________________________________________________________________ test_phash_distance_returns_float __________________________________________________________________________
tests/test_metrics.py:63: in test_phash_distance_returns_float
    distance = compute_phash_distance(frame, frame)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
src/sim_real_comparator/metrics.py:54: in compute_phash_distance
    phash_a = imagehash.phash(imagehash.ImageWrapper(gray_a))
                              ^^^^^^^^^^^^^^^^^^^^^^
E   AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
============================================================================== short test summary info ===============================================================================
FAILED tests/test_frame_extractor.py::test_extract_frames_returns_numpy_array - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_frame_extractor.py::test_extract_frames_all_frames - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_frame_extractor.py::test_extract_frames_num_frames_limit - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_frame_extractor.py::test_extract_aligned_frames_aligned_counts - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_frame_extractor.py::test_extract_aligned_frames_truncates_to_min - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_frame_extractor.py::test_extract_aligned_frames_output_shapes - TypeError: 'generator' object does not support the context manager protocol
FAILED tests/test_metrics.py::test_phash_distance_identical_frames - AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
FAILED tests/test_metrics.py::test_phash_distance_different_frames - AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
FAILED tests/test_metrics.py::test_phash_distance_completely_different - AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
FAILED tests/test_metrics.py::test_phash_distance_returns_float - AttributeError: module 'imagehash' has no attribute 'ImageWrapper'
============================================================================ 10 failed, 4 passed in 1.03s ============================================================================

```

## Verdict: FAIL
