"""Heatmap generation for visualizing frame differences."""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generate_heatmap(frame_a: np.ndarray, frame_b: np.ndarray, output_path: str) -> str:
    """Generate a color-coded heatmap overlay showing pixel-wise differences.

    Red = high difference, green = low difference.

    Args:
        frame_a: First frame as numpy array (H, W, C) or (H, W).
        frame_b: Second frame as numpy array (H, W, C) or (H, W).
        output_path: Path to save the heatmap PNG.

    Returns:
        The output path of the saved heatmap.
    """
    # Ensure both frames are 3-channel
    if frame_a.ndim == 2:
        frame_a = np.stack([frame_a] * 3, axis=-1)
    if frame_b.ndim == 2:
        frame_b = np.stack([frame_b] * 3, axis=-1)

    # Compute absolute difference per channel, then average across channels
    diff = np.abs(frame_a.astype(np.float64) - frame_b.astype(np.float64))
    diff_single = diff.mean(axis=2)  # (H, W)
    # Normalize to [0, 1]
    max_diff = diff_single.max()
    if max_diff > 0:
        diff_norm = diff_single / max_diff
    else:
        diff_norm = np.zeros_like(diff_single)

    # Create heatmap: green=low diff, red=high diff
    # Use a colormap: green (0,1,0) -> yellow -> red (1,0,0)
    heatmap = np.zeros((diff_norm.shape[0], diff_norm.shape[1], 3), dtype=np.uint8)
    heatmap[:, :, 2] = (diff_norm * 255).astype(np.uint8)  # Red channel = difference
    heatmap[:, :, 0] = ((1.0 - diff_norm) * 255).astype(np.uint8)  # Green channel = inverse difference
    heatmap[:, :, 1] = (diff_norm * 0.5 * 255).astype(np.uint8)  # Blue channel = subtle

    # Overlay with transparency on the original frame
    alpha = 0.5
    overlay = alpha * heatmap + (1 - alpha) * frame_a.astype(np.float64) / 255.0
    overlay = np.clip(overlay, 0, 1)

    # Save
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    plt.imsave(output_path, overlay)
    return output_path


def generate_heatmap_batch(
    frames_a: list[np.ndarray],
    frames_b: list[np.ndarray],
    output_dir: str,
) -> list[str]:
    """Generate heatmaps for a batch of frame pairs.

    Args:
        frames_a: List of first frames.
        frames_b: List of second frames.
        output_dir: Directory to save heatmap PNGs.

    Returns:
        List of output file paths.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_paths = []
    for i, (fa, fb) in enumerate(zip(frames_a, frames_b)):
        output_path = os.path.join(output_dir, f"heatmap_frame_{i:04d}.png")
        generate_heatmap(fa, fb, output_path)
        output_paths.append(output_path)
    return output_paths
