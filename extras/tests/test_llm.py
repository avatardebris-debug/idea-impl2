"""Tests for ai_movie_gen_suite llm module."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.config import AppConfig, LLMConfig
from ai_movie_gen_suite.llm import (
    _call_openai,
    _call_anthropic,
    call_llm,
    call_llm_with_template,
    _load_template,
)


class TestLoadTemplate:
    def test_load_template(self, tmp_path):
        template_file = tmp_path / "test.jinja2"
        template_file.write_text("Hello {{ name }}!")
        template = _load_template(str(template_file))
        assert template.render(name="World") == "Hello World!"

    def test_load_template_nonexistent(self):
        with pytest.raises(FileNotFoundError):
            _load_template("/nonexistent/path/template.jinja2")


class TestCallOpenAI:
    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_success(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        result = _call_openai(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_openai_class.assert_called_once_with(
            api_key="test_key",
            base_url=None,
        )

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_with_base_url(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o", base_url="http://localhost:8080"))
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        _call_openai(config, "system", "user")
        mock_openai_class.assert_called_once_with(
            api_key="test_key",
            base_url="http://localhost:8080",
        )

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_no_api_key(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="", model="gpt-4o"))
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="No OpenAI API key found"):
                _call_openai(config, "system", "user")

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_uses_env_var(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="", model="gpt-4o"))
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict(os.environ, {"OPENAI_API_KEY": "env_key"}):
            result = _call_openai(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_openai_class.assert_called_once_with(
            api_key="env_key",
            base_url=None,
        )

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_json_mode(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o", temperature=0.5, max_tokens=100))
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        _call_openai(config, "system", "user")
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.5,
            max_tokens=100,
            response_format={"type": "json_object"},
        )

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_no_json_mode(self, mock_openai_class):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o", temperature=0.5, max_tokens=100), use_json_mode=False)
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='{"result": "ok"}'))]
        mock_client.chat.completions.create.return_value = mock_response

        _call_openai(config, "system", "user")
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "system"},
                {"role": "user", "content": "user"},
            ],
            temperature=0.5,
            max_tokens=100,
            response_format={"type": "text"},
        )

    @patch("ai_movie_gen_suite.llm.OpenAI")
    def test_call_openai_import_error(self, mock_openai_class):
        mock_openai_class.side_effect = ImportError("No module named 'openai'")
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        with pytest.raises(RuntimeError, match="openai package required"):
            _call_openai(config, "system", "user")


class TestCallAnthropic:
    @patch("ai_movie_gen_suite.llm.Anthropic")
    def test_call_anthropic_success(self, mock_anthropic_class):
        config = AppConfig(llm=LLMConfig(provider="anthropic", api_key="test_key", model="claude-3"))
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "ok"}')]
        mock_client.messages.create.return_value = mock_response

        result = _call_anthropic(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_client.messages.create.assert_called_once_with(
            model="claude-3",
            system="system",
            messages=[{"role": "user", "content": "user"}],
            temperature=0.7,
            max_tokens=4096,
        )

    @patch("ai_movie_gen_suite.llm.Anthropic")
    def test_call_anthropic_no_api_key(self, mock_anthropic_class):
        config = AppConfig(llm=LLMConfig(provider="anthropic", api_key="", model="claude-3"))
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(RuntimeError, match="No Anthropic API key found"):
                _call_anthropic(config, "system", "user")

    @patch("ai_movie_gen_suite.llm.Anthropic")
    def test_call_anthropic_uses_env_var(self, mock_anthropic_class):
        config = AppConfig(llm=LLMConfig(provider="anthropic", api_key="", model="claude-3"))
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "ok"}')]
        mock_client.messages.create.return_value = mock_response

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env_key"}):
            result = _call_anthropic(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_anthropic_class.assert_called_once_with(api_key="env_key")

    @patch("ai_movie_gen_suite.llm.Anthropic")
    def test_call_anthropic_import_error(self, mock_anthropic_class):
        mock_anthropic_class.side_effect = ImportError("No module named 'anthropic'")
        config = AppConfig(llm=LLMConfig(provider="anthropic", api_key="test_key", model="claude-3"))
        with pytest.raises(RuntimeError, match="anthropic package required"):
            _call_anthropic(config, "system", "user")


class TestCallLLM:
    @patch("ai_movie_gen_suite.llm._call_openai")
    def test_call_llm_default_provider(self, mock_openai):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        mock_openai.return_value = '{"result": "ok"}'
        result = call_llm(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_openai.assert_called_once_with(config, "system", "user")

    @patch("ai_movie_gen_suite.llm._call_openai")
    @patch("ai_movie_gen_suite.llm._call_anthropic")
    def test_call_llm_anthropic_provider(self, mock_anthropic, mock_openai):
        config = AppConfig(llm=LLMConfig(provider="anthropic", api_key="test_key", model="claude-3"))
        mock_anthropic.return_value = '{"result": "ok"}'
        result = call_llm(config, "system", "user")
        assert result == '{"result": "ok"}'
        mock_anthropic.assert_called_once_with(config, "system", "user")
        mock_openai.assert_not_called()

    @patch("ai_movie_gen_suite.llm._call_openai")
    @patch("ai_movie_gen_suite.llm._call_anthropic")
    def test_call_llm_explicit_provider(self, mock_anthropic, mock_openai):
        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        mock_openai.return_value = '{"result": "ok"}'
        result = call_llm(config, "system", "user", provider="openai")
        assert result == '{"result": "ok"}'
        mock_openai.assert_called_once_with(config, "system", "user")
        mock_anthropic.assert_not_called()


class TestCallLLMWithTemplate:
    @patch("ai_movie_gen_suite.llm.call_llm")
    @patch("ai_movie_gen_suite.llm._load_template")
    def test_call_llm_with_template_success(self, mock_load_template, mock_call_llm, tmp_path):
        template_file = tmp_path / "test.jinja2"
        template_file.write_text("Hello {{ name }}!")
        mock_load_template.return_value = MagicMock(render=MagicMock(return_value="Hello World!"))
        mock_call_llm.return_value = '{"result": "ok"}'

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        result = call_llm_with_template(
            config,
            str(template_file),
            {"name": "World"},
            system_prompt="Be helpful",
        )
        assert result == {"result": "ok"}
        mock_call_llm.assert_called_once_with(
            config,
            "Be helpful",
            "Hello World!",
            None,
        )

    @patch("ai_movie_gen_suite.llm.call_llm")
    @patch("ai_movie_gen_suite.llm._load_template")
    def test_call_llm_with_template_custom_provider(self, mock_load_template, mock_call_llm, tmp_path):
        template_file = tmp_path / "test.jinja2"
        template_file.write_text("Hello {{ name }}!")
        mock_load_template.return_value = MagicMock(render=MagicMock(return_value="Hello World!"))
        mock_call_llm.return_value = '{"result": "ok"}'

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        call_llm_with_template(
            config,
            str(template_file),
            {"name": "World"},
            provider="anthropic",
        )
        mock_call_llm.assert_called_once_with(
            config,
            "You are a helpful assistant that returns structured JSON output.",
            "Hello World!",
            "anthropic",
        )

    @patch("ai_movie_gen_suite.llm.call_llm")
    @patch("ai_movie_gen_suite.llm._load_template")
    def test_call_llm_with_template_invalid_json(self, mock_load_template, mock_call_llm, tmp_path):
        template_file = tmp_path / "test.jinja2"
        template_file.write_text("Hello {{ name }}!")
        mock_load_template.return_value = MagicMock(render=MagicMock(return_value="Hello World!"))
        mock_call_llm.return_value = "not valid json"

        config = AppConfig(llm=LLMConfig(provider="openai", api_key="test_key", model="gpt-4o"))
        with pytest.raises(json.JSONDecodeError):
            call_llm_with_template(config, str(template_file), {"name": "World"})
