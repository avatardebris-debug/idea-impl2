"""
VideoGAN — Orchestrates adversarial training between Generator and Discriminator.

Provides the training loop, loss computation, and evaluation utilities
for the video GAN system.
"""

import torch
import torch.nn as nn
from typing import Optional, Dict, List, Tuple

from video_gan.generator import Generator
from video_gan.discriminator import Discriminator
from video_gan.video_processor import VideoProcessor


def _validate_tensor(tensor, name, expected_ndim, device=None):
    """Validate a tensor input for VideoGAN.

    Args:
        tensor: Input tensor to validate.
        name: Name of the parameter (for error messages).
        expected_ndim: Expected number of dimensions.
        device: Expected device.

    Raises:
        TypeError: If tensor is not a torch.Tensor.
        ValueError: If tensor has wrong shape or zero batch size.
        RuntimeError: If device doesn't match expected device.
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor, got {type(tensor).__name__}")
    if tensor.ndim != expected_ndim:
        raise ValueError(f"{name} must have {expected_ndim} dimensions (batch, channels, frames, height, width), got {tensor.ndim}D")
    if tensor.size(0) == 0:
        raise ValueError(f"{name} batch size must be > 0, got 0")
    if device is not None and tensor.device != device:
        raise RuntimeError(f"{name} device mismatch: expected {device}, got {tensor.device}")


class VideoGAN:
    """Video GAN trainer: coordinates Generator and Discriminator."""

    def __init__(
        self,
        generator: Optional[Generator] = None,
        discriminator: Optional[Discriminator] = None,
        lr_g: float = 2e-4,
        lr_d: float = 2e-4,
        beta1: float = 0.5,
        device: Optional[torch.device] = None,
    ):
        """
        Args:
            generator: Generator instance. Created if None.
            discriminator: Discriminator instance. Created if None.
            lr_g: Learning rate for the generator.
            lr_d: Learning rate for the discriminator.
            beta1: Beta1 parameter for Adam optimizer.
            device: Device to train on. Defaults to CUDA if available.
        """
        self.device = device or (torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu"))

        # Create default models if not provided
        if generator is None:
            self.generator = Generator().to(self.device)
        else:
            self.generator = generator.to(self.device)

        if discriminator is None:
            self.discriminator = Discriminator().to(self.device)
        else:
            self.discriminator = discriminator.to(self.device)

        # Optimizers
        self.optimizer_g = torch.optim.Adam(
            self.generator.parameters(), lr=lr_g, betas=(beta1, 0.999)
        )
        self.optimizer_d = torch.optim.Adam(
            self.discriminator.parameters(), lr=lr_d, betas=(beta1, 0.999)
        )

        # Loss function
        self.bce_loss = nn.BCEWithLogitsLoss()

        # Training state
        self.training_history: Dict[str, List[float]] = {
            "g_loss": [],
            "d_loss": [],
            "d_real_acc": [],
            "d_fake_acc": [],
        }

    def train_step(
        self,
        real_video: torch.Tensor,
        noise: Optional[torch.Tensor] = None,
    ) -> Dict[str, float]:
        """Perform one training step (one discriminator update + one generator update).

        Args:
            real_video: Real video tensor of shape (batch, channels, frames, height, width).
            noise: Latent noise tensor. If None, random noise is generated.

        Returns:
            Dictionary with loss values for this step.

        Raises:
            TypeError: If real_video is not a torch.Tensor.
            ValueError: If real_video has wrong shape or zero batch size.
            RuntimeError: If noise device doesn't match real_video device.
        """
        _validate_tensor(real_video, "real_video", 5, self.device)

        if noise is not None:
            _validate_tensor(noise, "noise", 2, self.device)
            if noise.size(1) != self.generator.latent_dim:
                raise ValueError(f"noise latent dimension must be {self.generator.latent_dim}, got {noise.size(1)}")

        batch_size = real_video.size(0)
        real_labels = torch.ones(batch_size, 1, device=self.device)
        fake_labels = torch.zeros(batch_size, 1, device=self.device)

        # ---- Train Discriminator ----
        self.discriminator.train()
        self.generator.eval()

        # Real video classification
        real_scores, _ = self.discriminator(real_video)
        d_real_loss = self.bce_loss(real_scores, real_labels)

        # Generate fake video
        with torch.no_grad():
            fake_video = self.generator(real_video, noise)

        # Fake video classification
        fake_scores, _ = self.discriminator(fake_video.detach())
        d_fake_loss = self.bce_loss(fake_scores, fake_labels)

        # Discriminator loss
        d_loss = d_real_loss + d_fake_loss

        self.optimizer_d.zero_grad()
        d_loss.backward()
        self.optimizer_d.step()

        # ---- Train Generator ----
        self.generator.train()
        self.discriminator.eval()

        # Generate fake video (generator gradients flow through discriminator)
        fake_video = self.generator(real_video, noise)
        fake_scores, _ = self.discriminator(fake_video)

        # Generator tries to make discriminator classify fakes as real
        g_loss = self.bce_loss(fake_scores, real_labels)

        self.optimizer_g.zero_grad()
        g_loss.backward()
        self.optimizer_g.step()

        # Compute accuracies
        d_real_acc = (real_scores > 0).float().mean().item()
        d_fake_acc = (fake_scores < 0).float().mean().item()

        step_losses = {
            "g_loss": g_loss.item(),
            "d_loss": d_loss.item(),
            "d_real_acc": d_real_acc,
            "d_fake_acc": d_fake_acc,
        }

        # Record history
        for key, value in step_losses.items():
            self.training_history[key].append(value)

        return step_losses

    def train_epoch(
        self,
        real_videos: torch.Tensor,
        batch_size: int = 8,
        noise: Optional[torch.Tensor] = None,
    ) -> Dict[str, float]:
        """Train for one epoch over the dataset.

        Args:
            real_videos: All real video data, shape (total_samples, channels, frames, height, width).
            batch_size: Mini-batch size.
            noise: Pre-generated noise tensor. If None, random noise is used per batch.

        Returns:
            Average loss values for the epoch.

        Raises:
            TypeError: If real_videos is not a torch.Tensor.
            ValueError: If real_videos has wrong shape, zero batch size, or invalid batch_size.
        """
        _validate_tensor(real_videos, "real_videos", 5, self.device)

        if not isinstance(batch_size, int) or batch_size <= 0:
            raise ValueError(f"batch_size must be a positive integer, got {batch_size}")
        total_samples = real_videos.size(0)
        epoch_losses = {"g_loss": 0.0, "d_loss": 0.0, "d_real_acc": 0.0, "d_fake_acc": 0.0}
        num_batches = 0

        for start in range(0, total_samples, batch_size):
            end = min(start + batch_size, total_samples)
            batch_real = real_videos[start:end].to(self.device)

            batch_noise = None
            if noise is not None:
                batch_noise = noise[start:end]

            step_losses = self.train_step(batch_real, batch_noise)

            for key in epoch_losses:
                epoch_losses[key] += step_losses[key]
            num_batches += 1

        for key in epoch_losses:
            epoch_losses[key] /= num_batches

        return epoch_losses

    def generate(self, real_video: torch.Tensor, noise: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Generate fake video from real video input.

        Args:
            real_video: Real video tensor of shape (batch, channels, frames, height, width).
            noise: Latent noise tensor. If None, random noise is generated.

        Returns:
            Fake video tensor of shape (batch, channels, frames, height, width).

        Raises:
            TypeError: If real_video is not a torch.Tensor.
            ValueError: If real_video has wrong shape or zero batch size.
            RuntimeError: If noise device doesn't match real_video device.
        """
        _validate_tensor(real_video, "real_video", 5, self.device)

        if noise is not None:
            _validate_tensor(noise, "noise", 2, self.device)
            if noise.size(1) != self.generator.latent_dim:
                raise ValueError(f"noise latent dimension must be {self.generator.latent_dim}, got {noise.size(1)}")
        self.generator.eval()
        with torch.no_grad():
            return self.generator(real_video, noise)

    def classify(self, video: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """Classify video as real or fake.

        Args:
            video: Video tensor of shape (batch, channels, frames, height, width).

        Returns:
            real_scores: Scores in [0, 1] indicating probability of being real.
            features: Intermediate feature map.

        Raises:
            TypeError: If video is not a torch.Tensor.
            ValueError: If video has wrong shape or zero batch size.
            RuntimeError: If video device doesn't match model device.
        """
        _validate_tensor(video, "video", 5, self.device)
        self.discriminator.eval()
        with torch.no_grad():
            scores, features = self.discriminator(video)
            scores = torch.sigmoid(scores)
            return scores, features

    def save_checkpoint(self, path: str) -> None:
        """Save training checkpoint.

        Args:
            path: File path to save the checkpoint.
        """
        torch.save(
            {
                "generator_state": self.generator.state_dict(),
                "discriminator_state": self.discriminator.state_dict(),
                "optimizer_g_state": self.optimizer_g.state_dict(),
                "optimizer_d_state": self.optimizer_d.state_dict(),
                "training_history": self.training_history,
            },
            path,
        )

    def load_checkpoint(self, path: str) -> None:
        """Load training checkpoint.

        Args:
            path: File path to load the checkpoint from.
        """
        checkpoint = torch.load(path, map_location=self.device)
        self.generator.load_state_dict(checkpoint["generator_state"])
        self.discriminator.load_state_dict(checkpoint["discriminator_state"])
        self.optimizer_g.load_state_dict(checkpoint["optimizer_g_state"])
        self.optimizer_d.load_state_dict(checkpoint["optimizer_d_state"])
        self.training_history = checkpoint.get("training_history", self.training_history)

    def get_training_history(self) -> Dict[str, List[float]]:
        """Return the training history."""
        return self.training_history
