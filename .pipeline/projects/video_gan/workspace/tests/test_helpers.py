"""
Helper utilities for video_gan tests.

Provides standalone functions (not pytest fixtures) that can be imported
directly by test modules.
"""

import torch
import numpy as np


# ── defaults ──────────────────────────────────────────────────────────
DEFAULT_CHANNELS = 3
DEFAULT_NUM_FRAMES = 16
DEFAULT_FRAME_SIZE = 64
DEFAULT_LATENT_DIM = 128
DEFAULT_BATCH = 2


def make_mock_tensor(*shape, dtype=torch.float32, device="cpu"):
    """Create a random torch tensor on the given device."""
    return torch.randn(*shape, dtype=dtype, device=device)


def make_mock_real_video(batch_size=DEFAULT_BATCH, channels=DEFAULT_CHANNELS,
                         num_frames=DEFAULT_NUM_FRAMES, frame_size=DEFAULT_FRAME_SIZE,
                         device="cpu"):
    """Create a fake 'real' video tensor (batch, C, F, H, W)."""
    return torch.randn(batch_size, channels, num_frames, frame_size, frame_size, device=device)


def make_mock_noise(batch_size=DEFAULT_BATCH, latent_dim=DEFAULT_LATENT_DIM, device="cpu"):
    """Create a latent noise tensor."""
    return torch.randn(batch_size, latent_dim, device=device)


def make_mock_numpy_video(batch_size=DEFAULT_BATCH, num_frames=DEFAULT_NUM_FRAMES,
                          frame_size=DEFAULT_FRAME_SIZE, channels=DEFAULT_CHANNELS):
    """Create fake numpy video frames (batch, F, H, W, C) in [0, 255]."""
    h, w = frame_size, frame_size
    return np.random.randint(0, 256, size=(batch_size, num_frames, h, w, channels)).astype(np.float32)


def make_constant_numpy_video(value=128.0, batch_size=DEFAULT_BATCH, num_frames=DEFAULT_NUM_FRAMES,
                              frame_size=DEFAULT_FRAME_SIZE, channels=DEFAULT_CHANNELS):
    """Create constant-value numpy video frames."""
    h, w = frame_size, frame_size
    return np.full((batch_size, num_frames, h, w, channels), value, dtype=np.float32)
