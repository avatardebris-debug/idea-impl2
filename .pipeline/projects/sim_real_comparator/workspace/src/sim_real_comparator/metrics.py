"""Similarity metrics: SSIM and perceptual hash distance."""

import numpy as np
import imagehash
from skimage.metrics import structural_similarity


def compute_ssim(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Compute SSIM between two frames.

    Args:
        frame_a: First frame as numpy array (H, W, C) or (H, W).
        frame_b: Second frame as numpy array (H, W, C) or (H, W).

    Returns:
        SSIM score in [0, 1]. 1.0 means identical structure.
    """
    # Convert to grayscale for SSIM if needed
    if frame_a.ndim == 3 and frame_a.shape[2] == 3:
        gray_a = np.dot(frame_a[..., :3], [0.2989, 0.5870, 0.1140])
        gray_b = np.dot(frame_b[..., :3], [0.2989, 0.5870, 0.1140])
    else:
        gray_a = frame_a
        gray_b = frame_b

    gray_a = gray_a.astype(np.float64)
    gray_b = gray_b.astype(np.float64)

    score = structural_similarity(gray_a, gray_b, data_range=255.0)
    return float(max(0.0, min(1.0, score)))


def compute_color_distance(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Compute normalized color distance between two frames.

    Args:
        frame_a: First frame as numpy array (H, W, C).
        frame_b: Second frame as numpy array (H, W, C).

    Returns:
        Color distance in [0, 1]. 0.0 means identical colors.
    """
    if frame_a.ndim == 3 and frame_a.shape[2] == 3:
        diff = np.abs(frame_a.astype(np.float64) - frame_b.astype(np.float64))
        max_diff = 255.0
        return float(np.mean(diff) / max_diff)
    return 0.0


def compute_phash_distance(frame_a: np.ndarray, frame_b: np.ndarray) -> float:
    """Compute normalized Hamming distance between perceptual hashes of two frames.

    Args:
        frame_a: First frame as numpy array (H, W, C) or (H, W).
        frame_b: Second frame as numpy array (H, W, C) or (H, W).

    Returns:
        Normalized Hamming distance in [0, 1]. 0.0 means identical pHash.
    """
    # Convert to grayscale if needed
    if frame_a.ndim == 3 and frame_a.shape[2] == 3:
        gray_a = np.dot(frame_a[..., :3], [0.2989, 0.5870, 0.1140])
        gray_b = np.dot(frame_b[..., :3], [0.2989, 0.5870, 0.1140])
    else:
        gray_a = frame_a
        gray_b = frame_b

    gray_a = gray_a.astype(np.uint8)
    gray_b = gray_b.astype(np.uint8)

    from PIL import Image
    img_a = Image.fromarray(gray_a)
    img_b = Image.fromarray(gray_b)
    phash_a = imagehash.phash(img_a)
    phash_b = imagehash.phash(img_b)

    hamming = phash_a - phash_b  # returns Hamming distance
    max_distance = 64  # default pHash size is 8x8 = 64 bits
    return float(hamming / max_distance)
