"""Scorer: compute weighted global similarity score."""

import numpy as np

from sim_real_comparator.models import FrameResult, GlobalResult


def compute_phash_similarity(phash_distance: float) -> float:
    """Convert pHash distance to similarity.

    Args:
        phash_distance: pHash distance in [0, 1].

    Returns:
        pHash similarity in [0, 1].
    """
    return 1.0 - phash_distance


def compute_color_distance(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Compute normalized mean absolute color distance between two frames.

    Args:
        frame_a: First frame as numpy array (H, W, C).
        frame_b: Second frame as numpy array (H, W, C).

    Returns:
        Color distance in [0, 1].
    """
    # Ensure both are float for computation
    fa = frame_a.astype(np.float64)
    fb = frame_b.astype(np.float64)
    # Mean absolute difference per pixel, then normalize to [0, 1]
    # Max possible per-pixel diff for uint8 is 255*3 = 765
    diff = np.mean(np.abs(fa - fb))
    return float(diff / 765.0)


def compute_global_score(frame_results: list[FrameResult]) -> GlobalResult:
    """Compute a weighted global similarity score from per-frame results.

    The global score is a weighted average of:
      - SSIM (weight 0.25): higher is more similar
      - pHash similarity (weight 0.25): 1 - phash_distance, higher is more similar
      - CLIP cosine similarity (weight 0.25): higher is more similar
      - Color similarity (weight 0.25): 1 - color_distance, higher is more similar

    Args:
        frame_results: List of per-frame results.

    Returns:
        GlobalResult with aggregated scores.
    """
    if not frame_results:
        return GlobalResult(
            global_score=0.0,
            avg_ssim=0.0,
            avg_phash_similarity=0.0,
            avg_clip_similarity=0.0,
            avg_color_distance=0.0,
            weights={"ssim": 0.25, "phash": 0.25, "clip": 0.25, "color": 0.25},
        )

    n = len(frame_results)
    avg_ssim = sum(f.ssim for f in frame_results) / n
    avg_phash_similarity = sum(
        compute_phash_similarity(f.phash_distance) for f in frame_results
    ) / n
    avg_clip_similarity = sum(f.clip_similarity for f in frame_results) / n
    avg_color_distance = sum(f.color_distance for f in frame_results) / n

    weights = {"ssim": 0.25, "phash": 0.25, "clip": 0.25, "color": 0.25}
    global_score = (
        weights["ssim"] * avg_ssim
        + weights["phash"] * avg_phash_similarity
        + weights["clip"] * avg_clip_similarity
        + weights["color"] * (1.0 - avg_color_distance)
    )

    # Clamp to [0, 1]
    global_score = max(0.0, min(1.0, global_score))

    return GlobalResult(
        global_score=global_score,
        avg_ssim=avg_ssim,
        avg_phash_similarity=avg_phash_similarity,
        avg_clip_similarity=avg_clip_similarity,
        avg_color_distance=avg_color_distance,
        weights=weights,
    )
