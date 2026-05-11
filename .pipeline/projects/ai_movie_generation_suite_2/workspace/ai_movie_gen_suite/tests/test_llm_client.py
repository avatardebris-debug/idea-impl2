"""Tests for the LLM client module."""

import json
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from ai_movie_gen_suite.llm_client import LLMClient


class TestLLMClient:
    """Tests for the LLMClient class."""

    def test_create_default_client(self) -> None:
        """Test creating a client with default settings."""
        client = LLMClient()
        assert client.config is not None
        assert client.config["model"] == "gpt-4"
        assert client.config["temperature"] == 0.7
        assert client.config["max_tokens"] == 4096

    def test_create_client_with_custom_config(self) -> None:
        """Test creating a client with custom configuration."""
        custom_config = {
            "model": "gpt-3.5-turbo",
            "temperature": 0.5,
            "max_tokens": 2048,
        }
        client = LLMClient(config=custom_config)
        assert client.config["model"] == "gpt-3.5-turbo"
        assert client.config["temperature"] == 0.5
        assert client.config["max_tokens"] == 2048

    def test_create_client_with_empty_config(self) -> None:
        """Test creating a client with empty config uses defaults."""
        client = LLMClient(config={})
        assert client.config["model"] == "gpt-4"
        assert client.config["temperature"] == 0.7
        assert client.config["max_tokens"] == 4096

    def test_create_client_with_partial_config(self) -> None:
        """Test creating a client with partial config merges with defaults."""
        partial_config = {"model": "claude-3"}
        client = LLMClient(config=partial_config)
        assert client.config["model"] == "claude-3"
        assert client.config["temperature"] == 0.7  # default
        assert client.config["max_tokens"] == 4096  # default

    def test_create_client_with_all_custom_config(self) -> None:
        """Test creating a client with full custom config."""
        full_config = {
            "model": "claude-3-opus",
            "temperature": 0.3,
            "max_tokens": 8192,
            "api_key": "test-key",
            "base_url": "https://custom.api.com",
        }
        client = LLMClient(config=full_config)
        assert client.config["model"] == "claude-3-opus"
        assert client.config["temperature"] == 0.3
        assert client.config["max_tokens"] == 8192
        assert client.config["api_key"] == "test-key"
        assert client.config["base_url"] == "https://custom.api.com"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_success(self, mock_post: MagicMock) -> None:
        """Test successful text generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "This is the generated text."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        result = client.generate_text("Test prompt")

        assert result == "This is the generated text."
        mock_post.assert_called_once()

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_system_prompt(self, mock_post: MagicMock) -> None:
        """Test text generation with system prompt."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response with system prompt."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        result = client.generate_text(
            "Test prompt",
            system_prompt="You are a helpful assistant.",
        )

        assert result == "Response with system prompt."
        # Verify system prompt was included in the call
        call_args = mock_post.call_args
        assert call_args is not None
        body = json.loads(call_args[1]["json"])
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][0]["content"] == "You are a helpful assistant."

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_custom_model(self, mock_post: MagicMock) -> None:
        """Test text generation with custom model."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Custom model response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(config={"model": "gpt-3.5-turbo"})
        result = client.generate_text("Test prompt")

        assert result == "Custom model response."
        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert body["model"] == "gpt-3.5-turbo"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_custom_temperature(self, mock_post: MagicMock) -> None:
        """Test text generation with custom temperature."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(config={"temperature": 0.9})
        result = client.generate_text("Test prompt")

        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert body["temperature"] == 0.9

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_custom_max_tokens(self, mock_post: MagicMock) -> None:
        """Test text generation with custom max_tokens."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(config={"max_tokens": 1024})
        result = client.generate_text("Test prompt")

        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert body["max_tokens"] == 1024

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_http_error(self, mock_post: MagicMock) -> None:
        """Test handling of HTTP errors."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"
        mock_post.return_value = mock_response

        client = LLMClient()
        with pytest.raises(Exception, match="API request failed"):
            client.generate_text("Test prompt")

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_json_decode_error(self, mock_post: MagicMock) -> None:
        """Test handling of JSON decode errors."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("test", "doc", 0)
        mock_post.return_value = mock_response

        client = LLMClient()
        with pytest.raises(Exception, match="Failed to parse response"):
            client.generate_text("Test prompt")

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_missing_choices(self, mock_post: MagicMock) -> None:
        """Test handling of response missing choices."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"error": "Something went wrong"}
        mock_post.return_value = mock_response

        client = LLMClient()
        with pytest.raises(Exception, match="No choices in response"):
            client.generate_text("Test prompt")

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_empty_response(self, mock_post: MagicMock) -> None:
        """Test handling of empty response content."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        result = client.generate_text("Test prompt")
        assert result == ""

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_messages(self, mock_post: MagicMock) -> None:
        """Test text generation with a list of messages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Chat response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        result = client.generate_text(messages)

        assert result == "Chat response."
        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert len(body["messages"]) == 3

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_system_and_user_messages(self, mock_post: MagicMock) -> None:
        """Test text generation with system and user messages."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"},
        ]
        result = client.generate_text(messages)

        assert result == "Response."
        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert len(body["messages"]) == 2

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_json_response_format(self, mock_post: MagicMock) -> None:
        """Test text generation with JSON response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"key": "value"}'}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        result = client.generate_text("Test prompt", response_format={"type": "json_object"})

        assert result == '{"key": "value"}'
        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert body["response_format"]["type"] == "json_object"

    def test_config_property(self) -> None:
        """Test that config property returns the configuration."""
        client = LLMClient()
        config = client.config
        assert isinstance(config, dict)
        assert "model" in config
        assert "temperature" in config
        assert "max_tokens" in config

    def test_config_isolation(self) -> None:
        """Test that modifying config doesn't affect other clients."""
        client1 = LLMClient()
        client2 = LLMClient()

        # Modify client1's config
        client1.config["model"] = "custom-model"

        # client2 should still have default
        assert client2.config["model"] == "gpt-4"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_all_parameters(self, mock_post: MagicMock) -> None:
        """Test text generation with all parameters."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Full response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(config={"model": "gpt-4", "temperature": 0.5, "max_tokens": 2048})
        result = client.generate_text(
            "Test prompt",
            system_prompt="System prompt",
            temperature=0.8,
            max_tokens=1024,
            response_format={"type": "json_object"},
        )

        assert result == "Full response."
        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])

        # Verify all parameters are passed
        assert body["model"] == "gpt-4"
        assert body["temperature"] == 0.8
        assert body["max_tokens"] == 1024
        assert body["response_format"]["type"] == "json_object"
        assert len(body["messages"]) == 2
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_preserves_messages_order(self, mock_post: MagicMock) -> None:
        """Test that message order is preserved."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response."}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient()
        messages: List[Dict[str, str]] = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]
        client.generate_text(messages)

        call_args = mock_post.call_args
        body = json.loads(call_args[1]["json"])
        assert body["messages"][0]["content"] == "First"
        assert body["messages"][1]["content"] == "Second"
        assert body["messages"][2]["content"] == "Third"
