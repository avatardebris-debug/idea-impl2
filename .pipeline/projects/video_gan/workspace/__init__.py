"""
video_gan — Core MVP: A GAN for video generation with adversarial training.

Components:
  - Generator: Creates fake video frames from real video input.
  - Discriminator: Classifies video frames as real or fake.
  - VideoGAN: Orchestrates adversarial training between Generator and Discriminator.
  - VideoProcessor: Loads/saves video frames for training.
"""

from video_gan.generator import Generator
from video_gan.discriminator import Discriminator
from video_gan.video_gan import VideoGAN
from video_gan.video_processor import VideoProcessor

__all__ = ["Generator", "Discriminator", "VideoGAN", "VideoProcessor"]
__version__ = "0.1.0"
