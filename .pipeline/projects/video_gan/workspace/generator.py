"""
Generator — Creates fake video frames from real video input using a GAN generator network.

The generator takes a real video as input and produces a fake video that
attempts to fool the discriminator.
"""

import torch
import torch.nn as nn
from typing import Optional


def _validate_tensor(tensor, name, expected_ndim, device=None):
    """Validate a tensor input for the Generator.

    Args:
        tensor: Input tensor to validate.
        name: Name of the parameter (for error messages).
        expected_ndim: Expected number of dimensions.
        device: Expected device.

    Raises:
        TypeError: If tensor is not a torch.Tensor.
        ValueError: If tensor has wrong shape or device mismatch.
    """
    if not isinstance(tensor, torch.Tensor):
        raise TypeError(f"{name} must be a torch.Tensor, got {type(tensor).__name__}")
    if tensor.ndim != expected_ndim:
        raise ValueError(f"{name} must have {expected_ndim} dimensions (batch, channels, frames, height, width), got {tensor.ndim}D")
    if tensor.size(0) == 0:
        raise ValueError(f"{name} batch size must be > 0, got 0")
    if device is not None and tensor.device != device:
        raise RuntimeError(f"{name} device mismatch: expected {device}, got {tensor.device}")


class Generator(nn.Module):
    """Video GAN Generator: maps real video frames to fake video frames."""

    def __init__(
        self,
        input_channels: int = 3,
        latent_dim: int = 128,
        num_frames: int = 16,
        frame_size: int = 64,
        output_channels: int = 3,
    ):
        """
        Args:
            input_channels: Number of channels in input frames (e.g., 3 for RGB).
            latent_dim: Dimension of the latent noise vector.
            num_frames: Number of frames in the video sequence.
            frame_size: Spatial size of each frame (frame_size x frame_size).
            output_channels: Number of channels in output frames.
        """
        super().__init__()

        self.latent_dim = latent_dim
        self.num_frames = num_frames
        self.frame_size = frame_size

        # After input_encoder: (64, num_frames, frame_size//2, frame_size//2)
        # Conv3d with stride=(1,2,2) keeps frames unchanged, halves spatial dims
        enc_frames = num_frames
        enc_h = frame_size // 2
        enc_w = frame_size // 2

        # Encode the real video input
        self.input_encoder = nn.Sequential(
            nn.Conv3d(input_channels, 64, kernel_size=(3, 4, 4), stride=(1, 2, 2), padding=(1, 1, 1)),
            nn.BatchNorm3d(64),
            nn.LeakyReLU(0.2, inplace=True),
        )

        # Latent noise injection — project to match encoded feature shape
        self.noise_proj = nn.Linear(latent_dim, 64 * enc_frames * enc_h * enc_w)

        # Decoder — generates fake video frames
        # Input to decoder: (batch, 128, num_frames, frame_size//2, frame_size//2)
        # Output: (batch, output_channels, num_frames, frame_size, frame_size)
        # Two upsampling steps: (h//2) -> h
        self.decoder = nn.Sequential(
            # Step 1: (128, F, H/2, W/2) -> (64, F, H, W)
            nn.ConvTranspose3d(128, 64, kernel_size=(3, 4, 4), stride=(1, 2, 2), padding=(1, 1, 1)),
            nn.BatchNorm3d(64),
            nn.LeakyReLU(0.2, inplace=True),

            # Step 2: (64, F, H, W) -> (32, F, H, W) — no upsampling, just channel reduction
            nn.Conv3d(64, 32, kernel_size=(3, 3, 3), stride=(1, 1, 1), padding=(1, 1, 1)),
            nn.BatchNorm3d(32),
            nn.LeakyReLU(0.2, inplace=True),

            # Step 3: (32, F, H, W) -> (3, F, H, W) — no upsampling, just channel reduction
            nn.Conv3d(32, output_channels, kernel_size=(3, 3, 3), stride=(1, 1, 1), padding=(1, 1, 1)),
            nn.Tanh(),
        )

    @property
    def device(self):
        """Return the device of the first parameter, or CPU if no parameters."""
        return next(self.parameters()).device if len(list(self.parameters())) > 0 else torch.device("cpu")

    def forward(self, real_video: torch.Tensor, noise: Optional[torch.Tensor] = None) -> torch.Tensor:
        """Generate fake video frames.

        Args:
            real_video: Real video tensor of shape (batch, channels, frames, height, width).
            noise: Latent noise tensor. If None, random noise is generated.

        Returns:
            Fake video tensor of shape (batch, output_channels, frames, height, width).

        Raises:
            TypeError: If real_video is not a torch.Tensor.
            ValueError: If real_video has wrong shape or zero batch size.
            RuntimeError: If noise device doesn't match real_video device.
        """
        _validate_tensor(real_video, "real_video", 5, self.device)

        if noise is not None:
            _validate_tensor(noise, "noise", 2, self.device)
            if noise.size(1) != self.latent_dim:
                raise ValueError(f"noise latent dimension must be {self.latent_dim}, got {noise.size(1)}")

        batch_size = real_video.size(0)

        # Encode real video
        encoded = self.input_encoder(real_video)

        # Generate and project noise
        if noise is None:
            noise = torch.randn(batch_size, self.latent_dim, device=real_video.device)
        noise_proj = self.noise_proj(noise).view(encoded.shape)

        # Concatenate encoded features with noise
        combined = torch.cat([encoded, noise_proj], dim=1)

        # Decode to fake video
        fake_video = self.decoder(combined)

        return fake_video
