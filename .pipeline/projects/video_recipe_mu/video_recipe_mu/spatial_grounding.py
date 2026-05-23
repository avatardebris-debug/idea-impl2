"""Spatial grounding module — estimate xyz_delta from key frames and visual cues."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class KeyFrame:
    """A single key frame extracted from a video."""

    frame_index: int
    timestamp_s: float
    description: str
    objects: List[str]  # detected object labels
    bounding_boxes: List[Dict[str, float]] = field(default_factory=list)
    # bounding boxes: [{"label": str, "x": float, "y": float, "w": float, "h": float}, ...]


@dataclass
class SpatialGroundingResult:
    """Result of spatial grounding for a single step."""

    step: int
    xyz_delta: Dict[str, float]  # {"x": float, "y": float, "z": float}
    confidence: float  # 0.0 - 1.0
    method: str  # how the delta was estimated
    notes: str = ""


def _estimate_delta_from_bounding_boxes(
    prev_boxes: List[Dict[str, float]],
    curr_boxes: List[Dict[str, float]],
    image_width: int,
    image_height: int,
    focal_length_px: float,
    object_width_m: float,
) -> Dict[str, float]:
    """Estimate xyz_delta from bounding box displacement between two frames.

    Uses simple pinhole camera model:
    - x_delta from horizontal pixel shift
    - z_delta from bounding box size change (distance proxy)
    - y_delta assumed zero unless vertical shift is significant
    """
    x_delta = 0.0
    z_delta = 0.0
    y_delta = 0.0

    if prev_boxes and curr_boxes:
        # Match objects by label (simple first-match)
        for prev_box in prev_boxes:
            label = prev_box.get("label", "")
            curr_box = None
            for cb in curr_boxes:
                if cb.get("label", "") == label:
                    curr_box = cb
                    break
            if curr_box is None:
                continue

            # Horizontal displacement → x_delta
            prev_cx = prev_box["x"] + prev_box["w"] / 2
            curr_cx = curr_box["x"] + curr_box["w"] / 2
            dx_px = curr_cx - prev_cx
            # Convert pixel shift to meters using focal length
            if focal_length_px > 0:
                # Approximate: x_m = dx_px * object_width_m / (2 * focal_length_px)
                x_delta = dx_px * object_width_m / (2 * focal_length_px)

            # Box width change → z_delta (distance proxy)
            prev_w = prev_box["w"]
            curr_w = curr_box["w"]
            if prev_w > 0 and focal_length_px > 0:
                # z_m = focal_length_px * object_width_m / box_width_px
                prev_z = focal_length_px * object_width_m / prev_w
                curr_z = focal_length_px * object_width_m / curr_w
                z_delta = curr_z - prev_z

            # Vertical displacement → y_delta (smaller effect)
            prev_cy = prev_box["y"] + prev_box["h"] / 2
            curr_cy = curr_box["y"] + curr_box["h"] / 2
            dy_px = curr_cy - prev_cy
            if focal_length_px > 0:
                y_delta = dy_px * object_width_m / (2 * focal_length_px)

    return {"x": round(x_delta, 4), "y": round(y_delta, 4), "z": round(z_delta, 4)}


def estimate_xyz_delta_from_frames(
    prev_frame: Optional[KeyFrame],
    curr_frame: KeyFrame,
    camera_focal_length_px: float = 1000.0,
    estimated_object_width_m: float = 0.1,
) -> Dict[str, float]:
    """Estimate xyz_delta between two key frames.

    Args:
        prev_frame: Previous key frame (None for first frame → zero delta).
        curr_frame: Current key frame.
        camera_focal_length_px: Estimated camera focal length in pixels.
        estimated_object_width_m: Estimated real-world width of tracked object.

    Returns:
        Dict with keys "x", "y", "z" in meters.
    """
    if prev_frame is None:
        return {"x": 0.0, "y": 0.0, "z": 0.0}

    return _estimate_delta_from_bounding_boxes(
        prev_frame.bounding_boxes,
        curr_frame.bounding_boxes,
        image_width=1920,  # default HD width
        image_height=1080,
        focal_length_px=camera_focal_length_px,
        object_width_m=estimated_object_width_m,
    )


def ground_steps_with_key_frames(
    steps: List[Dict[str, Any]],
    key_frames: List[KeyFrame],
    camera_focal_length_px: float = 1000.0,
    estimated_object_width_m: float = 0.1,
) -> List[SpatialGroundingResult]:
    """Ground a list of recipe steps using key frames for spatial estimation.

    Matches steps to key frames by timestamp proximity and object labels.

    Args:
        steps: List of step dicts (from LLM extraction).
        key_frames: List of KeyFrame objects extracted from video.
        camera_focal_length_px: Camera focal length in pixels.
        estimated_object_width_m: Estimated real-world object width.

    Returns:
        List of SpatialGroundingResult objects.
    """
    results: List[SpatialGroundingResult] = []

    for i, step in enumerate(steps):
        step_time = step.get("timestamp_s", 0.0)

        # Find closest key frame
        closest_idx = 0
        min_dist = float("inf")
        for j, kf in enumerate(key_frames):
            dist = abs(kf.timestamp_s - step_time)
            if dist < min_dist:
                min_dist = dist
                closest_idx = j

        # Get previous key frame for delta estimation
        prev_kf = key_frames[closest_idx - 1] if closest_idx > 0 else None
        curr_kf = key_frames[closest_idx]

        xyz_delta = estimate_xyz_delta_from_frames(
            prev_kf, curr_kf, camera_focal_length_px, estimated_object_width_m
        )

        # Confidence based on bounding box overlap and proximity
        confidence = 1.0
        if prev_kf is None:
            confidence = 0.3  # no baseline
        elif min_dist > 5.0:
            confidence = 0.2  # too far in time
        elif not prev_kf.bounding_boxes or not curr_kf.bounding_boxes:
            confidence = 0.4  # no visual data

        results.append(
            SpatialGroundingResult(
                step=step.get("step", i + 1),
                xyz_delta=xyz_delta,
                confidence=confidence,
                method="bounding_box_displacement",
                notes=f"matched to frame {curr_kf.frame_index} at t={curr_kf.timestamp_s:.1f}s",
            )
        )

    return results


def infer_xyz_delta_from_text(
    step_description: str,
    default_delta: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Infer xyz_delta from textual description when visual data is unavailable.

    Uses keyword heuristics to estimate movement direction.

    Args:
        step_description: Text description of the action.
        default_delta: Fallback delta if no keywords match.

    Returns:
        Dict with keys "x", "y", "z" in meters.
    """
    if default_delta is None:
        default_delta = {"x": 0.0, "y": 0.0, "z": 0.0}

    text = step_description.lower()

    # Directional keywords
    direction_map = {
        "left": {"x": -0.1, "y": 0.0, "z": 0.0},
        "right": {"x": 0.1, "y": 0.0, "z": 0.0},
        "up": {"x": 0.0, "y": 0.0, "z": 0.1},
        "down": {"x": 0.0, "y": 0.0, "z": -0.1},
        "forward": {"x": 0.0, "y": 0.1, "z": 0.0},
        "backward": {"x": 0.0, "y": -0.1, "z": 0.0},
        "toward": {"x": 0.05, "y": 0.0, "z": 0.0},
        "away": {"x": -0.05, "y": 0.0, "z": 0.0},
    }

    result = {"x": 0.0, "y": 0.0, "z": 0.0}
    matched = False

    for keyword, delta in direction_map.items():
        if keyword in text:
            for axis in ("x", "y", "z"):
                result[axis] += delta[axis]
            matched = True

    if not matched:
        return default_delta

    return {axis: round(result[axis], 4) for axis in ("x", "y", "z")}
