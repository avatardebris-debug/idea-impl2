"""Tests for ai_movie_gen_suite config module."""

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ai_movie_gen_suite.config import AppConfig, CONFIG_FILENAME, LLMConfig, load_config, save_config


class TestLLMConfig:
    def test_llm_config_defaults(self):
        config = LLMConfig()
        assert config.provider == "openai"
        assert config.model == "gpt-4o"
        assert config.api_key == ""
        assert config.base_url is None
        assert config.temperature == 0.7
        assert config.max_tokens == 4096

    def test_llm_config_custom_values(self):
        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test_key",
            base_url="http://localhost:8080",
            temperature=0.5,
            max_tokens=2048,
        )
        assert config.provider == "anthropic"
        assert config.model == "claude-3"
        assert config.api_key == "test_key"
        assert config.base_url == "http://localhost:8080"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048

    def test_llm_config_temperature_validation(self):
        with pytest.raises(ValidationError):
            LLMConfig(temperature=-0.1)

        with pytest.raises(ValidationError):
            LLMConfig(temperature=2.1)

    def test_llm_config_temperature_boundary(self):
        config_min = LLMConfig(temperature=0.0)
        assert config_min.temperature == 0.0

        config_max = LLMConfig(temperature=2.0)
        assert config_max.temperature == 2.0

    def test_llm_config_max_tokens_validation(self):
        with pytest.raises(ValidationError):
            LLMConfig(max_tokens=0)

    def test_llm_config_serialization(self):
        config = LLMConfig(
            provider="anthropic",
            model="claude-3",
            api_key="test_key",
            temperature=0.5,
            max_tokens=2048,
        )
        data = config.model_dump()
        assert data["provider"] == "anthropic"
        assert data["model"] == "claude-3"
        assert data["api_key"] == "test_key"
        assert data["temperature"] == 0.5
        assert data["max_tokens"] == 2048
        assert data["base_url"] is None
        assert data["provider"] == "anthropic"


class TestAppConfig:
    def test_app_config_defaults(self):
        config = AppConfig()
        assert config.llm.provider == "openai"
        assert config.output_dir == "./output"
        assert config.project_root == "./projects"
        assert config.prompt_dir == "./ai_movie_gen_suite/prompts"
        assert config.use_json_mode is True

    def test_app_config_custom_values(self):
        config = AppConfig(
            output_dir="./custom_output",
            project_root="./custom_projects",
            use_json_mode=False,
        )
        assert config.output_dir == "./custom_output"
        assert config.project_root == "./custom_projects"
        assert config.use_json_mode is False

    def test_app_config_serialization(self):
        config = AppConfig(
            output_dir="./custom_output",
            use_json_mode=False,
        )
        data = config.model_dump()
        assert data["output_dir"] == "./custom_output"
        assert data["use_json_mode"] is False
        assert "llm" in data
        assert data["llm"]["provider"] == "openai"

    def test_app_config_from_dict(self):
        data = {
            "llm": {
                "provider": "anthropic",
                "model": "claude-3",
                "api_key": "test_key",
                "temperature": 0.5,
                "max_tokens": 2048,
            },
            "output_dir": "./custom_output",
            "use_json_mode": False,
        }
        config = AppConfig(**data)
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3"
        assert config.output_dir == "./custom_output"
        assert config.use_json_mode is False


class TestLoadConfig:
    def test_load_config_defaults(self):
        config = load_config()
        assert config.llm.provider == "openai"
        assert config.output_dir == "./output"

    def test_load_config_from_file(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_data = {
            "llm": {
                "provider": "anthropic",
                "model": "claude-3",
                "api_key": "test_key",
                "temperature": 0.5,
                "max_tokens": 2048,
            },
            "output_dir": "./custom_output",
            "project_root": "./custom_projects",
            "prompt_dir": "./custom_prompts",
            "use_json_mode": False,
        }
        config_file.write_text(json.dumps(config_data))

        config = load_config(str(config_file))
        assert config.llm.provider == "anthropic"
        assert config.llm.model == "claude-3"
        assert config.llm.api_key == "test_key"
        assert config.llm.temperature == 0.5
        assert config.llm.max_tokens == 2048
        assert config.output_dir == "./custom_output"
        assert config.project_root == "./custom_projects"
        assert config.prompt_dir == "./custom_prompts"
        assert config.use_json_mode is False

    def test_load_config_nonexistent_file(self, tmp_path):
        config_file = tmp_path / "nonexistent.json"
        config = load_config(str(config_file))
        assert config.llm.provider == "openai"

    def test_load_config_invalid_json(self, tmp_path):
        config_file = tmp_path / "invalid.json"
        config_file.write_text("not valid json")

        with pytest.raises(ValueError):
            load_config(str(config_file))

    def test_load_config_invalid_config(self, tmp_path):
        config_file = tmp_path / "invalid_config.json"
        config_data = {
            "llm": {
                "provider": "openai",
                "model": "gpt-4o",
                "temperature": 3.0,  # Invalid temperature
            },
        }
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValidationError):
            load_config(str(config_file))


class TestSaveConfig:
    def test_save_config_creates_file(self, tmp_path):
        config = AppConfig(
            llm=LLMConfig(
                provider="anthropic",
                model="claude-3",
                api_key="test_key",
                temperature=0.5,
                max_tokens=2048,
            ),
            output_dir="./custom_output",
            use_json_mode=False,
        )
        config_file = tmp_path / CONFIG_FILENAME
        save_config(config, str(config_file))

        assert config_file.exists()

    def test_save_config_writes_correct_content(self, tmp_path):
        config = AppConfig(
            llm=LLMConfig(
                provider="anthropic",
                model="claude-3",
                api_key="test_key",
                temperature=0.5,
                max_tokens=2048,
            ),
            output_dir="./custom_output",
            use_json_mode=False,
        )
        config_file = tmp_path / CONFIG_FILENAME
        save_config(config, str(config_file))

        content = json.loads(config_file.read_text())
        assert content["llm"]["provider"] == "anthropic"
        assert content["llm"]["model"] == "claude-3"
        assert content["llm"]["api_key"] == "test_key"
        assert content["llm"]["temperature"] == 0.5
        assert content["llm"]["max_tokens"] == 2048
        assert content["output_dir"] == "./custom_output"
        assert content["use_json_mode"] is False

    def test_save_config_overwrites_existing(self, tmp_path):
        config1 = AppConfig(
            llm=LLMConfig(provider="openai", model="gpt-4o"),
            output_dir="./output1",
        )
        config2 = AppConfig(
            llm=LLMConfig(provider="anthropic", model="claude-3"),
            output_dir="./output2",
        )
        config_file = tmp_path / CONFIG_FILENAME

        save_config(config1, str(config_file))
        save_config(config2, str(config_file))

        content = json.loads(config_file.read_text())
        assert content["llm"]["provider"] == "anthropic"
        assert content["output_dir"] == "./output2"

    def test_save_config_creates_parent_directory(self, tmp_path):
        config = AppConfig()
        config_file = tmp_path / "subdir" / CONFIG_FILENAME
        save_config(config, str(config_file))

        assert config_file.exists()
