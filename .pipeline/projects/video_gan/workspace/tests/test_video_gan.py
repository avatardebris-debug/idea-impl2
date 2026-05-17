"""
Tests for the VideoGAN module.

Covers:
  - Construction with default and custom models
  - train_step and train_epoch
  - generate and classify methods
  - save_checkpoint and load_checkpoint
  - Training history tracking
  - Input validation
  - Optimizer state management
"""

import sys
import pathlib
import pytest
import torch
import torch.nn as nn
import tempfile
import os

_ws = pathlib.Path(__file__).parent
if str(_ws) not in sys.path:
    sys.path.insert(0, str(_ws))

from video_gan.video_gan import VideoGAN, _validate_tensor
from video_gan.generator import Generator
from video_gan.discriminator import Discriminator


# ── defaults ───────────────────────────────────────────────────
DEFAULT_CHANNELS = 3
DEFAULT_NUM_FRAMES = 16
DEFAULT_FRAME_SIZE = 64
DEFAULT_BATCH = 2


class TestVideoGANConstruction:
    """Test VideoGAN __init__ parameter handling."""

    def test_default_construction(self):
        gan = VideoGAN()
        assert isinstance(gan.generator, Generator)
        assert isinstance(gan.discriminator, Discriminator)
        assert isinstance(gan.optimizer_g, torch.optim.Adam)
        assert isinstance(gan.optimizer_d, torch.optim.Adam)
        assert isinstance(gan.bce_loss, nn.BCEWithLogitsLoss)

    def test_custom_models(self):
        gen = Generator(latent_dim=64)
        disc = Discriminator(input_channels=1)
        gan = VideoGAN(generator=gen, discriminator=disc)
        assert gan.generator is gen
        assert gan.discriminator is disc

    def test_custom_learning_rates(self):
        gan = VideoGAN(lr_g=1e-3, lr_d=5e-4)
        assert gan.optimizer_g.param_groups[0]['lr'] == 1e-3
        assert gan.optimizer_d.param_groups[0]['lr'] == 5e-4

    def test_device_placement(self):
        gan = VideoGAN()
        assert gan.device.type == "cpu"

    def test_training_history_initialized(self):
        gan = VideoGAN()
        assert "g_loss" in gan.training_history
        assert "d_loss" in gan.training_history
        assert "d_real_acc" in gan.training_history
        assert "d_fake_acc" in gan.training_history
        assert len(gan.training_history["g_loss"]) == 0


class TestVideoGANTrainStep:
    """Test VideoGAN.train_step method."""

    def _make_real_video(self, batch_size=DEFAULT_BATCH):
        return torch.randn(batch_size, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_train_step_returns_losses(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        losses = gan.train_step(real_video)
        assert "g_loss" in losses
        assert "d_loss" in losses
        assert "d_real_acc" in losses
        assert "d_fake_acc" in losses

    def test_train_step_losses_are_floats(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        losses = gan.train_step(real_video)
        for key, val in losses.items():
            assert isinstance(val, float)

    def test_train_step_updates_history(self):
        gan = VideoGAN()
        initial_len = len(gan.training_history["g_loss"])
        real_video = self._make_real_video()
        gan.train_step(real_video)
        assert len(gan.training_history["g_loss"]) == initial_len + 1

    def test_train_step_with_noise(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        noise = torch.randn(real_video.size(0), gan.generator.latent_dim)
        losses = gan.train_step(real_video, noise)
        assert "g_loss" in losses

    def test_train_step_updates_optimizer_params(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        initial_g_params = [p.clone() for p in gan.generator.parameters()]
        gan.train_step(real_video)
        for orig, new in zip(initial_g_params, gan.generator.parameters()):
            assert not torch.allclose(orig, new)

    def test_train_step_zero_batch_raises(self):
        gan = VideoGAN()
        real_video = torch.randn(0, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        with pytest.raises(ValueError):
            gan.train_step(real_video)

    def test_train_step_wrong_ndim_raises(self):
        gan = VideoGAN()
        real_video = torch.randn(2, 3, 16, 64)  # 4D
        with pytest.raises(ValueError):
            gan.train_step(real_video)

    def test_train_step_non_tensor_raises(self):
        gan = VideoGAN()
        with pytest.raises(TypeError):
            gan.train_step("not a tensor")

    def test_train_step_noise_dim_mismatch(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        noise = torch.randn(2, 64)  # wrong latent dim
        with pytest.raises(ValueError):
            gan.train_step(real_video, noise)


class TestVideoGANTrainEpoch:
    """Test VideoGAN.train_epoch method."""

    def _make_real_videos(self, total=8):
        return torch.randn(total, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_train_epoch_returns_losses(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        losses = gan.train_epoch(real_videos, batch_size=2)
        assert "g_loss" in losses
        assert "d_loss" in losses

    def test_train_epoch_updates_history(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        initial_len = len(gan.training_history["g_loss"])
        gan.train_epoch(real_videos, batch_size=2)
        assert len(gan.training_history["g_loss"]) > initial_len

    def test_train_epoch_batch_size_1(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        losses = gan.train_epoch(real_videos, batch_size=1)
        assert losses["g_loss"] > 0

    def test_train_epoch_invalid_batch_size(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        with pytest.raises(ValueError):
            gan.train_epoch(real_videos, batch_size=0)

    def test_train_epoch_negative_batch_size(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        with pytest.raises(ValueError):
            gan.train_epoch(real_videos, batch_size=-1)

    def test_train_epoch_non_int_batch_size(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        with pytest.raises(ValueError):
            gan.train_epoch(real_videos, batch_size=2.5)

    def test_train_epoch_wrong_tensor_type(self):
        gan = VideoGAN()
        with pytest.raises(TypeError):
            gan.train_epoch("not a tensor", batch_size=2)

    def test_train_epoch_average_losses(self):
        gan = VideoGAN()
        real_videos = self._make_real_videos()
        losses = gan.train_epoch(real_videos, batch_size=2)
        # Losses should be averaged over batches
        assert isinstance(losses["g_loss"], float)
        assert losses["g_loss"] > 0


class TestVideoGANGenerate:
    """Test VideoGAN.generate method."""

    def _make_real_video(self, batch_size=DEFAULT_BATCH):
        return torch.randn(batch_size, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_generate_returns_tensor(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        fake = gan.generate(real_video)
        assert isinstance(fake, torch.Tensor)

    def test_generate_output_shape(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        fake = gan.generate(real_video)
        assert fake.shape == real_video.shape

    def test_generate_with_noise(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        noise = torch.randn(real_video.size(0), gan.generator.latent_dim)
        fake = gan.generate(real_video, noise)
        assert fake.shape == real_video.shape

    def test_generate_no_grad(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        fake = gan.generate(real_video)
        assert not fake.requires_grad

    def test_generate_zero_batch_raises(self):
        gan = VideoGAN()
        real_video = torch.randn(0, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        with pytest.raises(ValueError):
            gan.generate(real_video)

    def test_generate_wrong_ndim_raises(self):
        gan = VideoGAN()
        real_video = torch.randn(2, 3, 16, 64)  # 4D
        with pytest.raises(ValueError):
            gan.generate(real_video)

    def test_generate_non_tensor_raises(self):
        gan = VideoGAN()
        with pytest.raises(TypeError):
            gan.generate("not a tensor")

    def test_generate_noise_dim_mismatch(self):
        gan = VideoGAN()
        real_video = self._make_real_video()
        noise = torch.randn(2, 64)  # wrong latent dim
        with pytest.raises(ValueError):
            gan.generate(real_video, noise)


class TestVideoGANClassify:
    """Test VideoGAN.classify method."""

    def _make_video(self, batch_size=DEFAULT_BATCH):
        return torch.randn(batch_size, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)

    def test_classify_returns_scores_and_features(self):
        gan = VideoGAN()
        video = self._make_video()
        scores, features = gan.classify(video)
        assert isinstance(scores, torch.Tensor)
        assert isinstance(features, torch.Tensor)

    def test_classify_scores_shape(self):
        gan = VideoGAN()
        video = self._make_video()
        scores, _ = gan.classify(video)
        assert scores.shape[0] == video.size(0)
        assert scores.shape[1] == 1

    def test_classify_scores_range(self):
        gan = VideoGAN()
        video = self._make_video()
        scores, _ = gan.classify(video)
        assert scores.min() >= 0.0 - 1e-5
        assert scores.max() <= 1.0 + 1e-5

    def test_classify_no_grad(self):
        gan = VideoGAN()
        video = self._make_video()
        scores, _ = gan.classify(video)
        assert not scores.requires_grad

    def test_classify_zero_batch_raises(self):
        gan = VideoGAN()
        video = torch.randn(0, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        with pytest.raises(ValueError):
            gan.classify(video)

    def test_classify_wrong_ndim_raises(self):
        gan = VideoGAN()
        video = torch.randn(2, 3, 16, 64)  # 4D
        with pytest.raises(ValueError):
            gan.classify(video)

    def test_classify_non_tensor_raises(self):
        gan = VideoGAN()
        with pytest.raises(TypeError):
            gan.classify("not a tensor")


class TestVideoGANCheckpoint:
    """Test VideoGAN save_checkpoint and load_checkpoint methods."""

    def test_save_and_load_checkpoint(self):
        gan = VideoGAN()
        real_video = torch.randn(2, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        gan.train_step(real_video)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name

        try:
            gan.save_checkpoint(path)
            assert os.path.exists(path)

            gan2 = VideoGAN()
            gan2.load_checkpoint(path)

            # Check that states are loaded
            assert torch.allclose(
                gan.generator.state_dict()['input_encoder.0.weight'],
                gan2.generator.state_dict()['input_encoder.0.weight']
            )
            assert torch.allclose(
                gan.discriminator.state_dict()['main.0.weight'],
                gan2.discriminator.state_dict()['main.0.weight']
            )
        finally:
            os.unlink(path)

    def test_load_checkpoint_updates_history(self):
        gan = VideoGAN()
        real_video = torch.randn(2, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        gan.train_step(real_video)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name

        try:
            gan.save_checkpoint(path)

            gan2 = VideoGAN()
            gan2.load_checkpoint(path)

            assert len(gan2.training_history["g_loss"]) == 1
        finally:
            os.unlink(path)

    def test_load_checkpoint_missing_history(self):
        """Test loading checkpoint without training_history key."""
        gan = VideoGAN()
        real_video = torch.randn(2, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        gan.train_step(real_video)

        with tempfile.NamedTemporaryFile(suffix=".pt", delete=False) as f:
            path = f.name

        try:
            # Save without training_history
            checkpoint = {
                "generator_state": gan.generator.state_dict(),
                "discriminator_state": gan.discriminator.state_dict(),
                "optimizer_g_state": gan.optimizer_g.state_dict(),
                "optimizer_d_state": gan.optimizer_d.state_dict(),
            }
            torch.save(checkpoint, path)

            gan2 = VideoGAN()
            gan2.load_checkpoint(path)

            # Should have default empty history
            assert len(gan2.training_history["g_loss"]) == 0
        finally:
            os.unlink(path)


class TestVideoGANGetHistory:
    """Test VideoGAN.get_training_history method."""

    def test_get_history_returns_dict(self):
        gan = VideoGAN()
        history = gan.get_training_history()
        assert isinstance(history, dict)

    def test_get_history_has_expected_keys(self):
        gan = VideoGAN()
        history = gan.get_training_history()
        assert "g_loss" in history
        assert "d_loss" in history
        assert "d_real_acc" in history
        assert "d_fake_acc" in history

    def test_get_history_after_training(self):
        gan = VideoGAN()
        real_video = torch.randn(2, DEFAULT_CHANNELS, DEFAULT_NUM_FRAMES, DEFAULT_FRAME_SIZE, DEFAULT_FRAME_SIZE)
        gan.train_step(real_video)
        history = gan.get_training_history()
        assert len(history["g_loss"]) == 1
