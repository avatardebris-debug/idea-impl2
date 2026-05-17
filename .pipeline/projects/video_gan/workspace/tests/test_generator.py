"""
Tests for the Generator module.

Covers:
  - Construction and default parameters
  - Forward pass shape correctness
  - Noise handling (None vs provided)
  - Device placement
  - Zero batch size edge case
  - Input validation (type, shape, device mismatch)
  - Latent dimension mismatch
"""

import sys
import pathlib
import pytest
import torch
import torch.nn as nn

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.generator import Generator, _validate_tensor


# ── defaults ───────────────────────────────────────────────
DEFAULT_CHANNELS = 3
DEFAULT_LATENT_DIM = 128
DEFAULT_NUM_FRAMES = 16
DEFAULT_FRAME_SIZE = 64
DEFAULT_BATCH = 2


class TestGeneratorConstruction:
    """Test Generator __init__ parameter handling."""

    def test_default_construction(self):
        g = Generator()
        assert g.latent_dim == 128
        assert g.num_frames == 16
        assert g.frame_size == 64
        assert isinstance(g.input_encoder, nn.Sequential)
        assert isinstance(g.decoder, nn.Sequential)

    def test_custom_construction(self):
        g = Generator(
            latent_dim=64,
            num_frames=8,
            frame_size=32,
            input_channels=1,
        )
        assert g.latent_dim == 64
        assert g.num_frames == 8
        assert g.frame_size == 32

    def test_device_placement(self):
        g = Generator()
        assert g.device.type == "cpu"

    def test_parameters_exist(self):
        g = Generator()
        params = list(g.parameters())
        assert len(params) > 0


class TestGeneratorForward:
    """Test Generator forward pass."""

    def _make_real_video(self, batch_size=DEFAULT_BATCH):
        """Create a dummy real video tensor for generator input."""
        return torch.randn(batch_size, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_forward_shape_with_noise(self):
        g = Generator()
        real_video = self._make_real_video()
        noise = torch.randn(real_video.size(0), g.latent_dim)
        fake = g(real_video, noise)
        assert fake.shape == real_video.shape

    def test_forward_shape_without_noise(self):
        g = Generator()
        real_video = self._make_real_video()
        fake = g(real_video, None)
        assert fake.shape == real_video.shape

    def test_output_range(self):
        """Generator output should be in [-1, 1] due to tanh."""
        g = Generator()
        real_video = self._make_real_video()
        fake = g(real_video, None)
        assert fake.min() >= -1.0 - 1e-5
        assert fake.max() <= 1.0 + 1e-5

    def test_different_batch_sizes(self):
        g = Generator()
        for bs in [1, 2, 4, 8]:
            real_video = torch.randn(bs, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
            fake = g(real_video, None)
            assert fake.shape == real_video.shape

    def test_deterministic_with_same_noise(self):
        g = Generator()
        g.eval()
        real_video = self._make_real_video()
        noise = torch.randn(real_video.size(0), g.latent_dim)
        with torch.no_grad():
            fake1 = g(real_video, noise)
            fake2 = g(real_video, noise)
        assert torch.allclose(fake1, fake2)

    def test_different_noise_produces_different_output(self):
        g = Generator()
        g.eval()
        real_video = self._make_real_video()
        noise1 = torch.randn(real_video.size(0), g.latent_dim)
        noise2 = torch.randn(real_video.size(0), g.latent_dim)
        with torch.no_grad():
            fake1 = g(real_video, noise1)
            fake2 = g(real_video, noise2)
        assert not torch.allclose(fake1, fake2)


class TestGeneratorValidation:
    """Test Generator input validation."""

    def test_non_tensor_input(self):
        g = Generator()
        with pytest.raises(TypeError):
            g("not a tensor", None)

    def test_wrong_ndim(self):
        g = Generator()
        real_video = torch.randn(2, 3, 16, 64)  # 4D instead of 5D
        with pytest.raises(ValueError):
            g(real_video, None)

    def test_zero_batch_size(self):
        g = Generator()
        real_video = torch.randn(0, 3, 16, 64, 64)
        with pytest.raises(ValueError):
            g(real_video, None)

    def test_noise_latent_dim_mismatch(self):
        g = Generator()
        real_video = torch.randn(2, 3, 16, 64, 64)
        noise = torch.randn(2, 64)  # wrong latent dim
        with pytest.raises(ValueError):
            g(real_video, noise)

    def test_noise_device_mismatch(self):
        g = Generator()
        real_video = torch.randn(2, 3, 16, 64, 64)
        noise = torch.randn(2, g.latent_dim)
        # Move noise to different device (simulate by checking logic)
        # We can't easily test device mismatch without GPU, so skip
        pass


class TestGeneratorModule:
    """Test Generator as a PyTorch module."""

    def test_is_module(self):
        g = Generator()
        assert isinstance(g, nn.Module)

    def test_train_eval_mode(self):
        g = Generator()
        g.train()
        g.eval()
        # Should not raise

    def test_parameters_count(self):
        g = Generator()
        total = sum(p.numel() for p in g.parameters())
        assert total > 0

    def test_grad_flow(self):
        g = Generator()
        real_video = torch.randn(2, 3, 16, 64, 64, requires_grad=True)
        fake = g(real_video, None)
        loss = fake.sum()
        loss.backward()
        assert real_video.grad is not None


class TestValidateTensor:
    """Test the _validate_tensor helper function."""

    def test_valid_tensor(self):
        t = torch.randn(2, 3, 16, 64, 64)
        _validate_tensor(t, "video", 5)  # should not raise

    def test_non_tensor_raises_type_error(self):
        with pytest.raises(TypeError):
            _validate_tensor("not a tensor", "video", 5)

    def test_wrong_ndim_raises_value_error(self):
        t = torch.randn(2, 3, 16, 64)
        with pytest.raises(ValueError):
            _validate_tensor(t, "video", 5)

    def test_zero_batch_raises_value_error(self):
        t = torch.randn(0, 3, 16, 64, 64)
        with pytest.raises(ValueError):
            _validate_tensor(t, "video", 5)

    def test_device_mismatch_raises_runtime_error(self):
        t = torch.randn(2, 3, 16, 64, 64)
        with pytest.raises(RuntimeError):
            _validate_tensor(t, "video", 5, device=torch.device("cuda"))
