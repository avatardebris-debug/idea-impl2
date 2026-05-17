"""
Shared pytest fixtures and helper utilities for video_gan tests.

Provides:
  - mock_tensor: generates random torch tensors on CPU
  - mock_real_video: generates a realistic fake video tensor
  - mock_noise: generates a latent noise tensor
  - mock_numpy_video: generates fake numpy video frames
  - video_gan_instance: a ready-to-use VideoGAN on CPU
"""

import sys
import pathlib
import pytest
import torch
import numpy as np

# Ensure the workspace is on sys.path so video_gan is importable
_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.generator import Generator
from video_gan.discriminator import Discriminator
from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor


# ── default hyper-parameters used across fixtures ──────────────────────
DEFAULT_CHANNELS = 3
DEFAULT_NUM_FRAMES = 16
DEFAULT_FRAME_SIZE = 64
DEFAULT_LATENT_DIM = 128
DEFAULT_BATCH = 2


# ── fixture helpers ───────────────────────────────────────────────────

@pytest.fixture
def mock_tensor():
    """Factory: create a random torch tensor on CPU."""
    def _mock_tensor(*shape, **kwargs):
        dtype = kwargs.get("dtype", torch.float32)
        return torch.randn(*shape, dtype=dtype)

    return _mock_tensor


@pytest.fixture
def mock_real_video():
    """Factory: create a fake 'real' video tensor (batch, C, F, H, W)."""
    def _mock_real_video(batch_size=DEFAULT_BATCH, channels=DEFAULT_CHANNELS,
                         num_frames=DEFAULT_NUM_FRAMES, frame_size=DEFAULT_FRAME_SIZE):
        return torch.randn(batch_size, channels, num_frames, frame_size, frame_size)

    return _mock_real_video


@pytest.fixture
def mock_noise():
    """Factory: create a latent noise tensor."""
    def _mock_noise(batch_size=DEFAULT_BATCH, latent_dim=DEFAULT_LATENT_DIM):
        return torch.randn(batch_size, latent_dim)

    return _mock_noise


@pytest.fixture
def mock_numpy_video():
    """Factory: create fake numpy video frames (batch, F, H, W, C) in [0,255]."""
    def _mock_numpy_video(batch_size=DEFAULT_BATCH, num_frames=DEFAULT_NUM_FRAMES,
                          frame_size=DEFAULT_FRAME_SIZE, channels=DEFAULT_CHANNELS):
        h, w = frame_size, frame_size
        return np.random.randint(0, 256, size=(batch_size, num_frames, h, w, channels), dtype=np.float32)

    return _mock_numpy_video


@pytest.fixture
def video_gan_instance():
    """Return a VideoGAN instance running on CPU."""
    gan = VideoGAN(
        generator=Generator(),
        discriminator=Discriminator(),
    )
    # Force CPU for deterministic tests
    gan.device = torch.device("cpu")
    gan.generator = gan.generator.to(torch.device("cpu"))
    gan.discriminator = gan.discriminator.to(torch.device("cpu"))
    return gan


@pytest.fixture
def video_processor():
    """Return a VideoProcessor with default settings."""
    return VideoProcessor(
        frame_size=(DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE),
        num_frames=DEFAULT_NUM_FRAMES,
        channels=DEFAULT_CHANNELS,
        normalize=True,
    )


@pytest.fixture
def generator():
    """Return a Generator instance on CPU."""
    return Generator().to(torch.device("cpu"))


@pytest.fixture
def discriminator():
    """Return a Discriminator instance on CPU."""
    return Discriminator().to(torch.device("cpu"))
