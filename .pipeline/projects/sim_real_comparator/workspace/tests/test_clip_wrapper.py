"""Tests for CLIP wrapper module."""

import numpy as np
from PIL import Image
import pytest

from sim_real_comparator.clip_wrapper import compute_clip_similarity


def _make_image(color: tuple, size: int = 64) -> Image.Image:
    """Create a solid-color PIL Image."""
    arr = np.full((size, size, 3), color, dtype=np.uint8)
    return Image.fromarray(arr)


def test_identical_images_similarity_near_one():
    """Identical images should have cosine similarity ≈ 1.0."""
    img = _make_image((128, 64, 200))
    sim = compute_clip_similarity(img, img)
    assert sim > 0.99, f"Identical images should have similarity ≈ 1.0, got {sim}"


def test_different_images_similarity_lower():
    """Different images should have lower similarity than identical."""
    img_a = _make_image((255, 0, 0))
    img_b = _make_image((0, 255, 0))
    sim = compute_clip_similarity(img_a, img_b)
    assert sim < 1.0, f"Different images should have similarity < 1.0, got {sim}"


def test_similarity_range():
    """Similarity should always be in [0, 1]."""
    img_a = _make_image((100, 100, 100))
    img_b = _make_image((200, 200, 200))
    sim = compute_clip_similarity(img_a, img_b)
    assert 0.0 <= sim <= 1.0, f"Similarity should be in [0, 1], got {sim}"
