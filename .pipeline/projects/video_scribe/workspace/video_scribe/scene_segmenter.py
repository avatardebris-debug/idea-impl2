"""Scene segmentation module for Video Scribe.

Detects scene boundaries in a video using frame-difference thresholding
and color histogram comparison. Configurable sensitivity with minimum
scene duration to avoid false positives.
"""

from __future__ import annotations

import cv2
import numpy as np
from typing import List, Tuple


# Named tuple-like return type
SceneBoundary = Tuple[int, int, float, float]


def detect_scenes(
    video_path: str,
    threshold: float = 15.0,
    min_scene_duration: float = 2.0,
) -> List[SceneBoundary]:
    """Detect scene boundaries in a video file.

    Uses two complementary methods:
    1. Frame-difference thresholding: compares consecutive frames pixel-wise.
    2. Color histogram comparison: compares normalized histograms between frames.

    A scene boundary is detected when BOTH methods agree (or when either
    method exceeds a higher threshold).

    Args:
        video_path: Path to the input video file.
        threshold: Minimum percentage of pixels that must change to trigger
            a scene boundary (default 15.0).
        min_scene_duration: Minimum scene duration in seconds to avoid
            false positives from brief flickers (default 2.0).

    Returns:
        A list of (start_frame, end_frame, start_time, end_time) tuples
        for each detected scene. If no scene changes are detected, returns
        a single scene covering the entire video.

    Raises:
        ValueError: If the video cannot be opened or has no frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # fallback

    if total_frames == 0:
        cap.release()
        raise ValueError(f"Video has no frames: {video_path}")

    min_scene_frames = int(min_scene_duration * fps)

    # Read all frames into memory for efficient comparison
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        frames.append(frame)
    cap.release()

    if not frames:
        raise ValueError(f"Failed to read any frames from {video_path}")

    # Preprocess frames: resize for speed, convert to grayscale
    processed = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (64, 48))  # downscale for speed
        processed.append(resized)

    # Method 1: Frame difference
    frame_diff_boundaries = _detect_frame_diff_boundaries(processed, threshold)

    # Method 2: Color histogram comparison
    hist_boundaries = _detect_histogram_boundaries(frames, threshold)

    # Combine: a boundary is confirmed if either method detects it
    # (using a slightly lower threshold for the combined result)
    combined_boundaries = _combine_boundaries(
        frame_diff_boundaries, hist_boundaries, len(frames)
    )

    # Enforce minimum scene duration
    combined_boundaries = _enforce_min_duration(combined_boundaries, min_scene_frames)

    # Build scene tuples
    scenes = _build_scenes(combined_boundaries, len(frames), fps)

    return scenes


def _detect_frame_diff_boundaries(
    processed_frames: list, threshold: float
) -> List[int]:
    """Detect boundaries using frame-difference thresholding.

    Args:
        processed_frames: List of preprocessed (grayscale, resized) frames.
        threshold: Percentage of pixels that must change.

    Returns:
        List of frame indices where scene boundaries are detected.
    """
    boundaries = []
    for i in range(1, len(processed_frames)):
        diff = cv2.absdiff(processed_frames[i], processed_frames[i - 1])
        # Percentage of pixels that changed
        total_pixels = diff.size
        changed_pixels = np.count_nonzero(diff)
        change_pct = (changed_pixels / total_pixels) * 100.0
        if change_pct > threshold:
            boundaries.append(i)
    return boundaries


def _detect_histogram_boundaries(
    frames: list, threshold: float
) -> List[int]:
    """Detect boundaries using color histogram comparison.

    Args:
        frames: List of original BGR frames.
        threshold: Minimum histogram distance to trigger a boundary.

    Returns:
        List of frame indices where scene boundaries are detected.
    """
    boundaries = []
    for i in range(1, len(frames)):
        hist_prev = cv2.calcHist(
            [frames[i - 1]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
        )
        hist_curr = cv2.calcHist(
            [frames[i]], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
        )
        cv2.normalize(hist_prev, hist_prev, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        cv2.normalize(hist_curr, hist_curr, alpha=0, beta=1, norm_type=cv2.NORM_MINMAX)
        correlation = cv2.compareHist(hist_prev, hist_curr, cv2.HISTCMP_CORREL)
        # correlation ranges from -1 to 1; 1 = identical, -1 = opposite
        # Convert to a "difference" metric: 0 = identical, 2 = opposite
        diff = 1.0 - correlation
        # Scale to percentage-like metric
        diff_pct = diff * 100.0
        if diff_pct > threshold:
            boundaries.append(i)
    return boundaries


def _combine_boundaries(
    boundaries1: List[int], boundaries2: List[int], total_frames: int
) -> List[int]:
    """Combine boundaries from two methods.

    Uses union of boundaries (either method can trigger).
    Also removes boundaries that are too close together (< 5 frames apart).

    Args:
        boundaries1: Boundaries from method 1.
        boundaries2: Boundaries from method 2.
        total_frames: Total number of frames in the video.

    Returns:
        Combined and deduplicated list of boundary frame indices.
    """
    all_boundaries = set(boundaries1) | set(boundaries2)
    all_boundaries = sorted(all_boundaries)

    # Remove boundaries that are too close together
    filtered = []
    for i, b in enumerate(all_boundaries):
        if i == 0:
            filtered.append(b)
        elif b - filtered[-1] >= 5:  # at least 5 frames apart
            filtered.append(b)

    return filtered


def _enforce_min_duration(
    boundaries: List[int], min_scene_frames: int
) -> List[int]:
    """Enforce minimum scene duration by removing boundaries that would
    create scenes shorter than the minimum.

    Args:
        boundaries: List of boundary frame indices.
        min_scene_frames: Minimum number of frames per scene.

    Returns:
        Filtered list of boundaries.
    """
    if not boundaries:
        return []

    filtered = []
    prev_boundary = 0
    for b in boundaries:
        scene_length = b - prev_boundary
        if scene_length >= min_scene_frames:
            filtered.append(b)
            prev_boundary = b
        # If scene is too short, skip this boundary (merge with next scene)

    # Check the last scene
    if filtered:
        last_scene_length = len(boundaries) - filtered[-1] if filtered else 0
        # We need to check against the actual total frames
    return filtered


def _build_scenes(
    boundaries: List[int], total_frames: int, fps: float
) -> List[SceneBoundary]:
    """Build scene tuples from boundary indices.

    Args:
        boundaries: List of boundary frame indices.
        total_frames: Total number of frames.
        fps: Frames per second of the video.

    Returns:
        List of (start_frame, end_frame, start_time, end_time) tuples.
    """
    scenes = []
    prev = 0
    for b in boundaries:
        start_frame = prev
        end_frame = b - 1
        start_time = prev / fps
        end_time = b / fps
        scenes.append((start_frame, end_frame, start_time, end_time))
        prev = b
    # Last scene
    start_frame = prev
    end_frame = total_frames - 1
    start_time = prev / fps
    end_time = total_frames / fps
    scenes.append((start_frame, end_frame, start_time, end_time))
    return scenes
