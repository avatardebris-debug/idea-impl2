"""Tests for Agent Config and Presets."""

import pytest
import os
from pathlib import Path

from drop_servicing_tool.agent_config import (
    AgentConfig,
    AgentConfigList,
    AgentMode,
    ProviderType,
    get_preset,
)


class TestProviderType:
    """Tests for ProviderType enum."""

    def test_provider_values(self):
        """Test ProviderType has expected values."""
        assert ProviderType.OPENAI.value == "openai"
        assert ProviderType.ANTHROPIC.value == "anthropic"
        assert ProviderType.GEMINI.value == "gemini"
        assert ProviderType.OLLAMA.value == "ollama"

    def test_provider_from_string(self):
        """Test creating ProviderType from string."""
        assert ProviderType("openai") == ProviderType.OPENAI
        assert ProviderType("anthropic") == ProviderType.ANTHROPIC
        assert ProviderType("gemini") == ProviderType.GEMINI
        assert ProviderType("ollama") == ProviderType.OLLAMA


class TestAgentMode:
    """Tests for AgentMode enum."""

    def test_mode_values(self):
        """Test AgentMode has expected values."""
        assert AgentMode.AUTO.value == "auto"
        assert AgentMode.STEP.value == "step"
        assert AgentMode.FREEFORM.value == "freeform"

    def test_mode_from_string(self):
        """Test creating AgentMode from string."""
        assert AgentMode("auto") == AgentMode.AUTO
        assert AgentMode("step") == AgentMode.STEP
        assert AgentMode("freeform") == AgentMode.FREEFORM


class TestAgentConfig:
    """Tests for AgentConfig model."""

    def test_valid_config_creation(self):
        """Test creating a valid AgentConfig."""
        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
            mode=AgentMode.AUTO,
            temperature=0.7
        )
        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4o-mini"
        assert config.mode == AgentMode.AUTO
        assert config.temperature == 0.7

    def test_config_defaults(self):
        """Test AgentConfig default values."""
        config = AgentConfig(provider=ProviderType.OPENAI, model="test")
        assert config.mode == AgentMode.AUTO
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.system_prompt_override is None
        assert config.fallback_models == []

    def test_config_with_all_fields(self):
        """Test AgentConfig with all fields set."""
        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            mode=AgentMode.STEP,
            temperature=0.5,
            max_tokens=2048,
            system_prompt_override="Custom system prompt",
            fallback_models=["gpt-3.5-turbo"]
        )
        assert config.mode == AgentMode.STEP
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.system_prompt_override == "Custom system prompt"
        assert config.fallback_models == ["gpt-3.5-turbo"]

    def test_config_mode_validation(self):
        """Test that invalid mode is rejected."""
        with pytest.raises(ValueError):
            AgentConfig(provider=ProviderType.OPENAI, model="test", mode="invalid_mode")


class TestAgentConfigList:
    """Tests for AgentConfigList model."""

    def test_empty_config_list(self):
        """Test creating empty AgentConfigList."""
        config_list = AgentConfigList()
        assert config_list.configs == []

    def test_config_list_with_configs(self):
        """Test creating AgentConfigList with configs."""
        configs = [
            AgentConfig(provider=ProviderType.OPENAI, model="gpt-4o"),
            AgentConfig(provider=ProviderType.ANTHROPIC, model="claude-3-opus")
        ]
        config_list = AgentConfigList(configs=configs)
        assert len(config_list.configs) == 2

    def test_config_list_default(self):
        """Test AgentConfigList default configs."""
        config_list = AgentConfigList()
        # Should remain empty when no explicit configs provided
        # Default configs are available via fast/balanced/quality attributes
        assert len(config_list.configs) == 0
        # But fast/balanced/quality should have defaults
        assert config_list.fast is not None
        assert config_list.balanced is not None
        assert config_list.quality is not None

    def test_config_list_get_by_provider(self):
        """Test getting config by provider."""
        configs = [
            AgentConfig(provider=ProviderType.OPENAI, model="gpt-4o"),
            AgentConfig(provider=ProviderType.ANTHROPIC, model="claude-3-opus")
        ]
        config_list = AgentConfigList(configs=configs)

        openai_config = config_list.get_config_by_provider(ProviderType.OPENAI)
        assert openai_config is not None
        assert openai_config.provider == ProviderType.OPENAI

        anthropic_config = config_list.get_config_by_provider(ProviderType.ANTHROPIC)
        assert anthropic_config is not None
        assert anthropic_config.provider == ProviderType.ANTHROPIC

    def test_config_list_get_nonexistent_provider(self):
        """Test getting config for nonexistent provider."""
        config_list = AgentConfigList()
        with pytest.raises(KeyError):
            config_list.get_config_by_provider(ProviderType.OLLAMA)


class TestGetPreset:
    """Tests for get_preset function."""

    def test_get_openai_preset(self):
        """Test getting OpenAI preset."""
        preset = get_preset("openai")
        assert preset is not None
        assert preset.provider == ProviderType.OPENAI

    def test_get_anthropic_preset(self):
        """Test getting Anthropic preset."""
        preset = get_preset("anthropic")
        assert preset is not None
        assert preset.provider == ProviderType.ANTHROPIC

    def test_get_gemini_preset(self):
        """Test getting Gemini preset."""
        preset = get_preset("gemini")
        assert preset is not None
        assert preset.provider == ProviderType.GEMINI

    def test_get_ollama_preset(self):
        """Test getting Ollama preset."""
        preset = get_preset("ollama")
        assert preset is not None
        assert preset.provider == ProviderType.OLLAMA

    def test_get_unknown_preset(self):
        """Test getting unknown preset."""
        with pytest.raises(KeyError, match="Unknown preset"):
            get_preset("unknown_preset")


class TestAgentConfigEnvironment:
    """Tests for AgentConfig with environment variables."""

    def test_config_from_env(self, monkeypatch):
        """Test creating config from environment variables."""
        monkeypatch.setenv("DST_OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("DST_OPENAI_MODEL", "gpt-4o")

        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o"
        )
        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4o"

    def test_config_with_temperature(self, monkeypatch):
        """Test config with temperature from environment."""
        monkeypatch.setenv("DST_OPENAI_API_KEY", "test_key")
        monkeypatch.setenv("DST_OPENAI_MODEL", "gpt-4o")
        monkeypatch.setenv("DST_OPENAI_TEMPERATURE", "0.5")

        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            temperature=0.5
        )
        assert config.temperature == 0.5


class TestAgentConfigValidation:
    """Tests for AgentConfig validation."""

    def test_config_requires_provider(self):
        """Test that provider is required."""
        with pytest.raises(ValueError, match="Provider is required"):
            AgentConfig(model="gpt-4o")

    def test_config_requires_model(self):
        """Test that model is required."""
        with pytest.raises(ValueError, match="Model is required"):
            AgentConfig(provider=ProviderType.OPENAI)

    def test_config_temperature_range(self):
        """Test temperature range validation."""
        # Valid temperatures
        AgentConfig(provider=ProviderType.OPENAI, model="test", temperature=0.0)
        AgentConfig(provider=ProviderType.OPENAI, model="test", temperature=1.0)
        AgentConfig(provider=ProviderType.OPENAI, model="test", temperature=0.5)

        # Invalid temperature
        with pytest.raises(ValueError, match="Temperature must be between 0 and 1"):
            AgentConfig(provider=ProviderType.OPENAI, model="test", temperature=1.5)


class TestAgentConfigSerialization:
    """Tests for AgentConfig serialization."""

    def test_config_to_dict(self):
        """Test converting config to dict."""
        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o",
            mode=AgentMode.STEP,
            temperature=0.7,
            max_tokens=2048
        )
        config_dict = config.to_dict()

        assert config_dict["provider"] == "openai"
        assert config_dict["model"] == "gpt-4o"
        assert config_dict["mode"] == "step"
        assert config_dict["temperature"] == 0.7
        assert config_dict["max_tokens"] == 2048

    def test_config_from_dict(self):
        """Test creating config from dict."""
        config_dict = {
            "provider": "openai",
            "model": "gpt-4o",
            "mode": "step",
            "temperature": 0.7,
            "max_tokens": 2048
        }
        config = AgentConfig.from_dict(config_dict)

        assert config.provider == ProviderType.OPENAI
        assert config.model == "gpt-4o"
        assert config.mode == AgentMode.STEP
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
