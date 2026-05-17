"""Tests for droppain.config module."""

import os
from unittest.mock import patch

import pytest

from droppain.config import Config, ConfigurationError, get_config


class TestConfig:
    """Tests for the Config class."""

    def test_default_config(self):
        """Test default config values."""
        config = Config()
        assert config.default_currency == "USD"
        assert config.default_timezone == "UTC"
        assert config.campaign_name_prefix == "Dropship Campaign"
        assert config.default_content_length == 280
        assert config.api_timeout == 30
        assert config.api_max_retries == 3

    def test_is_shopify_configured_false(self):
        """Test is_shopify_configured returns False when credentials missing."""
        config = Config()
        assert config.is_shopify_configured is False

    def test_is_shopify_configured_true(self):
        """Test is_shopify_configured returns True when credentials present."""
        with patch.dict(os.environ, {"SHOPIFY_STORE_NAME": "mystore"}):
            config = Config(shopify_api_key="key", shopify_password="pass")
            assert config.is_shopify_configured is True

    def test_shopify_base_url(self):
        """Test shopify_base_url property."""
        with patch.dict(os.environ, {"SHOPIFY_STORE_NAME": "mystore"}):
            config = Config(shopify_api_key="key", shopify_password="pass")
            assert config.shopify_base_url == "https://key:pass@mystore.myshopify.com/admin/api/2024-01"

    def test_shopify_base_url_custom_version(self):
        """Test shopify_base_url with custom API version."""
        with patch.dict(os.environ, {"SHOPIFY_STORE_NAME": "mystore"}):
            config = Config(shopify_api_key="key", shopify_password="pass", shopify_api_version="2023-07")
            assert "2023-07" in config.shopify_base_url

    def test_store_name_required(self):
        """Test that store_name is required for Shopify."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigurationError, match="SHOPIFY_STORE_NAME"):
                Config(shopify_api_key="key", shopify_password="pass")

    def test_env_var_override(self):
        """Test that environment variables override defaults."""
        with patch.dict(os.environ, {"DEFAULT_CURRENCY": "EUR"}):
            config = Config()
            assert config.default_currency == "EUR"


class TestGetConfig:
    """Tests for get_config function."""

    def test_get_config_returns_config(self):
        """Test get_config returns a Config instance."""
        config = get_config()
        assert isinstance(config, Config)
