"""Frame extraction from video files."""

import numpy as np
import imageio.v3 as iio


def extract_frames(video_path: str, num_frames: int | None = None) -> np.ndarray:
    """Extract frames from a video file as a numpy array of shape (N, H, W, C).

    Args:
        video_path: Path to the input video file.
        num_frames: If provided, extract exactly this many frames.
            If None, extract all frames.

    Returns:
        numpy array of extracted frames.
    """
    frames = []
    reader = iio.imiter(video_path)
    for frame in reader:
        frames.append(np.array(frame))
        if num_frames is not None and len(frames) >= num_frames:
            break
    if not frames:
        raise ValueError(f"No frames could be extracted from {video_path}")
    return np.stack(frames)


def extract_aligned_frames(
    real_video_path: str, sim_video_path: str
) -> tuple[np.ndarray, np.ndarray]:
    """Extract aligned frames from two video files.

    Truncates both to the minimum frame count so frames are aligned by index.

    Args:
        real_video_path: Path to the real video file.
        sim_video_path: Path to the simulated video file.

    Returns:
        Tuple of (real_frames, sim_frames) numpy arrays with the same first dimension.
    """
    real_frames = extract_frames(real_video_path)
    sim_frames = extract_frames(sim_video_path)

    min_count = min(len(real_frames), len(sim_frames))
    real_frames = real_frames[:min_count]
    sim_frames = sim_frames[:min_count]

    return real_frames, sim_frames
