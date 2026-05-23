"""JSON report generation for sim_real_comparator results."""

import json
import os
from sim_real_comparator.models import FrameResult, GlobalResult


def serialize_frame_result(frame: FrameResult) -> dict:
    """Serialize a FrameResult to a dict."""
    return {
        "frame_index": frame.frame_index,
        "ssim": frame.ssim,
        "phash_distance": frame.phash_distance,
        "clip_similarity": frame.clip_similarity,
        "color_distance": frame.color_distance,
    }


def serialize_global_result(global_result: GlobalResult) -> dict:
    """Serialize a GlobalResult to a dict."""
    return {
        "global_score": global_result.global_score,
        "avg_ssim": global_result.avg_ssim,
        "avg_phash_similarity": global_result.avg_phash_similarity,
        "avg_clip_similarity": global_result.avg_clip_similarity,
        "avg_color_distance": global_result.avg_color_distance,
        "weights": global_result.weights,
    }


def write_report(
    frame_results: list[FrameResult],
    global_result: GlobalResult,
    output_dir: str,
) -> str:
    """Write the full JSON report to output_dir.

    Args:
        frame_results: List of per-frame results.
        global_result: Aggregated global result.
        output_dir: Directory to save the report.

    Returns:
        Path to the written JSON report.
    """
    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, "report.json")
    report = {
        "frames": [serialize_frame_result(f) for f in frame_results],
        "global": serialize_global_result(global_result),
    }
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    return report_path
