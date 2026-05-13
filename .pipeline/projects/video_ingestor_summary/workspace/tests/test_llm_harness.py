"""Tests for video_ingestor.llm_harness."""

import pytest
from unittest.mock import patch, MagicMock

from video_ingestor.llm_harness import LLMHarness


class TestLLMHarness:
    def test_generate_with_openai(self):
        """Test generating text with OpenAI provider."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Hello, world!"
            result = harness.generate("Test prompt")
            assert result == "Hello, world!"
            mock_call.assert_called_once_with("Test prompt")

    def test_generate_with_unsupported_provider(self):
        """Test generating text with unsupported provider."""
        harness = LLMHarness(provider="unsupported")
        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            harness.generate("Test prompt")

    def test_generate_json_with_valid_json(self):
        """Test generating JSON with valid JSON response."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = '{"key": "value"}'
            result = harness.generate_json("Test prompt")
            assert result == {"key": "value"}

    def test_generate_json_with_wrapped_json(self):
        """Test generating JSON with JSON wrapped in text."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = 'Here is the JSON: {"key": "value"}'
            result = harness.generate_json("Test prompt")
            assert result == {"key": "value"}

    def test_generate_json_with_invalid_json(self):
        """Test generating JSON with invalid JSON response."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Not valid JSON"
            with pytest.raises(ValueError, match="Could not parse JSON"):
                harness.generate_json("Test prompt")

    def test_call_openai_with_mock(self):
        """Test calling OpenAI API with mocked response."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Test response"))]

        with patch('video_ingestor.llm_harness.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.return_value = mock_response
            result = harness._call_openai("Test prompt")
            assert result == "Test response"

    def test_call_openai_with_error(self):
        """Test calling OpenAI API with error."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        from openai import APIError
        with patch('video_ingestor.llm_harness.OpenAI') as mock_openai:
            mock_openai.return_value.chat.completions.create.side_effect = APIError(
                "Test error", response=MagicMock(), body=None
            )
            with pytest.raises(Exception, match="OpenAI API error"):
                harness._call_openai("Test prompt")

    def test_generate_with_temperature(self):
        """Test generating text with custom temperature."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Hello, world!"
            result = harness.generate("Test prompt", temperature=0.7)
            assert result == "Hello, world!"

    def test_generate_with_max_tokens(self):
        """Test generating text with custom max_tokens."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Hello, world!"
            result = harness.generate("Test prompt", max_tokens=100)
            assert result == "Hello, world!"

    def test_generate_with_system_prompt(self):
        """Test generating text with system prompt (kwargs are passed through)."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Hello, world!"
            result = harness.generate("Test prompt", system_prompt="You are a helpful assistant")
            assert result == "Hello, world!"
            # Verify kwargs are passed through to _call_openai
            mock_call.assert_called_once_with("Test prompt", system_prompt="You are a helpful assistant")

    def test_generate_json_with_array_response(self):
        """Test generating JSON with array response."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = '[{"key": "value1"}, {"key": "value2"}]'
            result = harness.generate_json("Test prompt")
            assert result == [{"key": "value1"}, {"key": "value2"}]

    def test_generate_json_with_nested_json(self):
        """Test generating JSON with nested JSON response."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = '{"outer": {"inner": "value"}}'
            result = harness.generate_json("Test prompt")
            assert result == {"outer": {"inner": "value"}}

    def test_generate_with_empty_prompt(self):
        """Test generating text with empty prompt."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = "Response to empty prompt"
            result = harness.generate("")
            assert result == "Response to empty prompt"

    def test_generate_json_with_empty_prompt(self):
        """Test generating JSON with empty prompt."""
        harness = LLMHarness(provider="openai", api_key="test-key")

        with patch.object(harness, '_call_openai') as mock_call:
            mock_call.return_value = '{"key": "value"}'
            result = harness.generate_json("")
            assert result == {"key": "value"}
