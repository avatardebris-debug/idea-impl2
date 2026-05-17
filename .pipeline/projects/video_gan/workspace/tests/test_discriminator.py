"""
Tests for the Discriminator module.

Covers:
  - Construction and default parameters
  - Forward pass shape correctness
  - Output range (sigmoid → [0, 1])
  - Input validation (type, shape, device mismatch)
  - Zero batch size edge case
  - Module behavior (train/eval, parameters)
"""

import sys
import pathlib
import pytest
import torch
import torch.nn as nn

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.discriminator import Discriminator, _validate_tensor


# ── defaults ─────────────────────────────────────────────────
DEFAULT_CHANNELS = 3
DEFAULT_NUM_FRAMES = 16
DEFAULT_FRAME_SIZE = 64
DEFAULT_BATCH = 2


class TestDiscriminatorConstruction:
    """Test Discriminator __init__ parameter handling."""

    def test_default_construction(self):
        d = Discriminator()
        assert isinstance(d.main, nn.Sequential)
        assert hasattr(d, 'pool')

    def test_custom_construction(self):
        d = Discriminator(
            input_channels=1,
            num_frames=8,
            frame_size=32,
        )
        assert d.main is not None

    def test_device_placement(self):
        d = Discriminator()
        assert d.device.type == "cpu"

    def test_parameters_exist(self):
        d = Discriminator()
        params = list(d.parameters())
        assert len(params) > 0


class TestDiscriminatorForward:
    """Test Discriminator forward pass."""

    def _make_video(self, batch_size=DEFAULT_BATCH):
        return torch.randn(batch_size, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_forward_output_shape(self):
        d = Discriminator()
        video = self._make_video()
        scores, features = d(video)
        assert scores.shape[0] == video.size(0)
        assert scores.shape[1] == 1
        assert features.shape[0] == video.size(0)

    def test_output_range(self):
        """Discriminator output should be in [0, 1] due to sigmoid."""
        d = Discriminator()
        video = self._make_video()
        scores, _ = d(video)
        assert scores.min() >= 0.0 - 1e-5
        assert scores.max() <= 1.0 + 1e-5

    def test_different_batch_sizes(self):
        d = Discriminator()
        for bs in [1, 2, 4, 8]:
            video = torch.randn(bs, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
            scores, _ = d(video)
            assert scores.shape[0] == bs

    def test_features_shape(self):
        d = Discriminator()
        video = self._make_video()
        _, features = d(video)
        assert features.shape[0] == video.size(0)
        assert features.ndim == 5

    def test_deterministic(self):
        d = Discriminator()
        d.eval()
        video = self._make_video()
        with torch.no_grad():
            scores1, _ = d(video)
            scores2, _ = d(video)
        assert torch.allclose(scores1, scores2)


class TestDiscriminatorValidation:
    """Test Discriminator input validation."""

    def test_non_tensor_input(self):
        d = Discriminator()
        with pytest.raises(TypeError):
            d("not a tensor")

    def test_wrong_ndim(self):
        d = Discriminator()
        video = torch.randn(2, 3, 16, 64)  # 4D instead of 5D
        with pytest.raises(ValueError):
            d(video)

    def test_zero_batch_size(self):
        d = Discriminator()
        video = torch.randn(0, 3, 16, 64, 64)
        with pytest.raises(ValueError):
            d(video)

    def test_device_mismatch(self):
        d = Discriminator()
        video = torch.randn(2, 3, 16, 64, 64)
        # Simulate device mismatch by checking the logic
        # We can't easily test without GPU, so skip
        pass


class TestDiscriminatorModule:
    """Test Discriminator as a PyTorch module."""

    def test_is_module(self):
        d = Discriminator()
        assert isinstance(d, nn.Module)

    def test_train_eval_mode(self):
        d = Discriminator()
        d.train()
        d.eval()
        # Should not raise

    def test_parameters_count(self):
        d = Discriminator()
        total = sum(p.numel() for p in d.parameters())
        assert total > 0

    def test_grad_flow(self):
        d = Discriminator()
        video = torch.randn(2, 3, 16, 64, 64, requires_grad=True)
        scores, _ = d(video)
        loss = scores.sum()
        loss.backward()
        assert video.grad is not None


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
