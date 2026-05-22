"""Frame extraction and key frame selection.

Opens a video file, decodes frames using OpenCV, and selects one
representative key frame per clip (mid-scene frame or highest-variance frame).
Also supports multi-frame extraction per scene.
"""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image
from typing import List, Tuple

from video_scribe.scene_segmenter import SceneBoundary


def extract_key_frame(video_path: str) -> Image.Image:
    """Extract a single key frame from a video file.

    Selects the frame closest to the 50% mark of the video duration.
    If the video is very short (< 10 frames), selects the middle frame.

    Args:
        video_path: Path to the input video file (mp4, mov, avi, etc.).

    Returns:
        A PIL Image of the selected key frame.

    Raises:
        ValueError: If the video cannot be opened or has no frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total_frames == 0:
        cap.release()
        raise ValueError(f"Video has no frames: {video_path}")

    # Select frame closest to 50% mark
    target_index = total_frames // 2

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_index)
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        raise ValueError(f"Failed to read frame {target_index} from {video_path}")

    # Convert BGR (OpenCV) to RGB (PIL)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)

    return pil_image


def extract_multi_frames(
    video_path: str,
    scenes: List[SceneBoundary],
) -> List[List[Image.Image]]:
    """Extract 2-3 key frames per scene from a video.

    For each scene, extracts frames at 25%, 50%, and 75% of the scene's
    duration. For scenes shorter than 1 second (in frames), falls back
    to a single frame at the scene midpoint.

    Args:
        video_path: Path to the input video file.
        scenes: List of (start_frame, end_frame, start_time, end_time) tuples
            from scene_segmenter.detect_scenes.

    Returns:
        A list of lists of PIL Images — one inner list per scene,
        each containing 2-3 frames.

    Raises:
        ValueError: If the video cannot be opened or has no frames.
    """
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video file: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0

    all_frames: List[Image.Image] = []
    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            break
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        all_frames.append(Image.fromarray(frame_rgb))
    cap.release()

    if not all_frames:
        raise ValueError(f"Failed to read any frames from {video_path}")

    result: List[List[Image.Image]] = []

    for start_frame, end_frame, start_time, end_time in scenes:
        scene_length = end_frame - start_frame + 1

        if scene_length < int(1.0 * fps):
            # Scene shorter than 1 second — single midpoint frame
            mid_index = start_frame + scene_length // 2
            mid_index = min(mid_index, len(all_frames) - 1)
            result.append([all_frames[mid_index]])
        else:
            # Extract frames at 25%, 50%, 75% of the scene
            positions = [0.25, 0.50, 0.75]
            frames_for_scene: List[Image.Image] = []
            for pos in positions:
                idx = int(start_frame + pos * scene_length)
                idx = max(start_frame, min(idx, end_frame))
                idx = min(idx, len(all_frames) - 1)
                frames_for_scene.append(all_frames[idx])
            result.append(frames_for_scene)

    return result
