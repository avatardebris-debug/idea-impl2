# Validation Report — Phase 3

## Summary
- Tests: 22 passed, 1 failed, 0 errors
- Python files in workspace: 16
(Deterministic pytest — no LLM validator steps used.)

## Phase 3 Tasks (acceptance scope)
# Phase 3 Tasks

- [ ] Task 1: Implement core Phase 3 functionality
  - What: Build the primary components described in the phase spec
  - Done when: Core functionality works and is importable

- [ ] Task 2: Add tests for Phase 3
  - What: Write unit tests covering the main code paths
  - Done when: Tests pass with pytest

- [ ] Task 3: Integration and documentation
  - What: Integrate with existing phases and update README
  - Done when: Full pipeline works end-to-end

## Test Output
```
================================================================================ test session starts =================================================================================
collecting ... collected 23 items

tests/test_clip_wrapper.py::test_identical_images_similarity_near_one PASSED                                                                                                   [  4%]
tests/test_clip_wrapper.py::test_different_images_similarity_lower PASSED                                                                                                      [  8%]
tests/test_clip_wrapper.py::test_similarity_range PASSED                                                                                                                       [ 13%]
tests/test_frame_extractor.py::test_extract_frames_returns_numpy_array PASSED                                                                                                  [ 17%]
tests/test_frame_extractor.py::test_extract_frames_all_frames PASSED                                                                                                           [ 21%]
tests/test_frame_extractor.py::test_extract_frames_num_frames_limit PASSED                                                                                                     [ 26%]
tests/test_frame_extractor.py::test_extract_aligned_frames_aligned_counts PASSED                                                                                               [ 30%]
tests/test_frame_extractor.py::test_extract_aligned_frames_truncates_to_min PASSED                                                                                             [ 34%]
tests/test_frame_extractor.py::test_extract_aligned_frames_output_shapes PASSED                                                                                                [ 39%]
tests/test_heatmaps.py::test_generate_heatmap_creates_png PASSED                                                                                                               [ 43%]
tests/test_heatmaps.py::test_generate_heatmap_batch PASSED                                                                                                                     [ 47%]
tests/test_heatmaps.py::test_identical_frames_heatmap PASSED                                                                                                                   [ 52%]
tests/test_integration.py::test_identical_videos PASSED                                                                                                                        [ 56%]
tests/test_integration.py::test_different_videos FAILED                                                                                                                        [ 60%]
tests/test_integration.py::test_fps_normalization PASSED                                                                                                                       [ 65%]
tests/test_metrics.py::test_ssim_identical_frames PASSED                                                                                                                       [ 69%]
tests/test_metrics.py::test_ssim_different_frames PASSED                                                                                                                       [ 73%]
tests/test_metrics.py::test_ssim_completely_different PASSED                                                                                                                   [ 78%]
tests/test_metrics.py::test_phash_distance_identical_frames PASSED                                                                                                             [ 82%]
tests/test_metrics.py::test_phash_distance_different_frames PASSED                                                                                                             [ 86%]
tests/test_metrics.py::test_phash_distance_completely_different PASSED                                                                                                         [ 91%]
tests/test_metrics.py::test_ssim_returns_float PASSED                                                                                                                          [ 95%]
tests/test_metrics.py::test_phash_distance_returns_float PASSED                                                                                                                [100%]

====================================================================================== FAILURES ======================================================================================
_______________________________________________________________________________ test_different_videos ________________________________________________________________________________
tests/test_integration.py:97: in test_different_videos
    assert report["global"]["avg_phash_similarity"] < 0.5
E   assert 0.9375 < 0.5
================================================================================== warnings summary ==================================================================================
../../../../../../venv/main/lib/python3.12/site-packages/clip/clip.py:6
  /venv/main/lib/python3.12/site-packages/clip/clip.py:6: DeprecationWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html
    from pkg_resources import packaging

tests/test_clip_wrapper.py::test_identical_images_similarity_near_one
  /venv/main/lib/python3.12/site-packages/torch/jit/_serialization.py:176: DeprecationWarning: `torch.jit.load` is deprecated. Please switch to `torch.export`.
    warnings.warn(

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
============================================================================== short test summary info ===============================================================================
FAILED tests/test_integration.py::test_different_videos - assert 0.9375 < 0.5
===================================================================== 1 failed, 22 passed, 2 warnings in 32.72s ======================================================================

```

## Verdict: FAIL
