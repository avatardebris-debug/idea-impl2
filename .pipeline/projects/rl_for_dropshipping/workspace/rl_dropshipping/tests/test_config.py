"""Tests for configuration loading."""

import pytest
import pathlib

from rl_dropshipping.src.config.settings import load_settings, get_env_params, get_market_params


class TestLoadSettings:
    """Tests for load_settings function."""

    def test_load_default(self):
        """Test loading default settings."""
        config = load_settings()
        assert isinstance(config, dict)
        assert "env" in config
        assert "market" in config
        assert "training" in config
        assert "logging" in config

    def test_env_params(self):
        """Test environment parameters."""
        config = load_settings()
        env_params = get_env_params(config)
        assert "episode_length" in env_params
        assert "n_competitors" in env_params
        assert "n_consumers" in env_params
        assert "initial_budget" in env_params
        assert "max_inventory" in env_params

    def test_market_params(self):
        """Test market parameters."""
        config = load_settings()
        market_params = get_market_params(config)
        assert "base_conversion_rate" in market_params
        assert "ad_effectiveness" in market_params
        assert "competition_intensity" in market_params

    def test_env_values(self):
        """Test environment parameter values."""
        config = load_settings()
        env_params = get_env_params(config)
        assert env_params["episode_length"] == 30
        assert env_params["n_competitors"] == 5
        assert env_params["n_consumers"] == 1000
        assert env_params["initial_budget"] == 1000.0
        assert env_params["max_inventory"] == 100

    def test_market_values(self):
        """Test market parameter values."""
        config = load_settings()
        market_params = get_market_params(config)
        assert market_params["base_conversion_rate"] == 0.05
        assert market_params["ad_effectiveness"] == 0.5
        assert market_params["competition_intensity"] == 0.3

    def test_training_params(self):
        """Test training parameters."""
        config = load_settings()
        assert config["training"]["n_episodes"] == 1000
        assert config["training"]["learning_rate"] == 0.001
        assert config["training"]["discount_factor"] == 0.99
        assert config["training"]["epsilon_start"] == 1.0
        assert config["training"]["epsilon_end"] == 0.01
        assert config["training"]["epsilon_decay"] == 0.995

    def test_logging_params(self):
        """Test logging parameters."""
        config = load_settings()
        assert config["logging"]["log_interval"] == 10
        assert config["logging"]["save_interval"] == 100
        assert config["logging"]["log_dir"] == "./logs"
