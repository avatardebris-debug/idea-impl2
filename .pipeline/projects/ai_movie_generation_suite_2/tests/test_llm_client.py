"""Tests for the AI Movie Generation Suite LLM client."""

import pytest
from unittest.mock import patch, MagicMock
from ai_movie_gen_suite.llm_client import LLMClient, LLMResponse


class TestLLMResponse:
    """Tests for the LLMResponse class."""

    def test_create_llm_response(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Test content",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
        assert response.content == "Test content"
        assert response.model == "test-model"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}

    def test_llm_response_to_dict(self):
        """Test LLM response serialization."""
        response = LLMResponse(
            content="Test content",
            model="test-model",
            usage={"prompt_tokens": 10, "completion_tokens": 20},
        )
        data = response.to_dict()
        assert data["content"] == "Test content"
        assert data["model"] == "test-model"
        assert data["usage"] == {"prompt_tokens": 10, "completion_tokens": 20}


class TestLLMClient:
    """Tests for the LLMClient class."""

    def test_create_llm_client(self):
        """Test creating an LLM client."""
        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        assert client.api_key == "test_key"
        assert client.model == "test-model"
        assert client.base_url == "https://test.api.com"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_success(self, mock_post):
        """Test successful text generation."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
        )
        assert response.content == "Test response"
        assert response.model == "test-model"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_failure(self, mock_post):
        """Test failed text generation."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        with pytest.raises(Exception):
            client.generate_text(
                prompt="Test prompt",
                system_prompt="Test system prompt",
            )

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_empty_response(self, mock_post):
        """Test text generation with empty response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": ""}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
        )
        assert response.content == ""

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_temperature(self, mock_post):
        """Test text generation with custom temperature."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
            temperature=0.7,
        )
        assert response.content == "Test response"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_max_tokens(self, mock_post):
        """Test text generation with custom max tokens."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
            max_tokens=100,
        )
        assert response.content == "Test response"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_stop_words(self, mock_post):
        """Test text generation with stop words."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
            stop_words=["STOP"],
        )
        assert response.content == "Test response"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_json_response(self, mock_post):
        """Test text generation with JSON response format."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": '{"key": "value"}'}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
            response_format="json",
        )
        assert response.content == '{"key": "value"}'

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_retry(self, mock_post):
        """Test text generation with retry."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        response = client.generate_text(
            prompt="Test prompt",
            system_prompt="Test system prompt",
            retry=True,
        )
        assert response.content == "Test response"

    @patch("ai_movie_gen_suite.llm_client.requests.post")
    def test_generate_text_with_retry_failure(self, mock_post):
        """Test text generation with retry failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        client = LLMClient(
            api_key="test_key",
            model="test-model",
            base_url="https://test.api.com",
        )
        with pytest.raises(Exception):
            client.generate_text(
                prompt="Test prompt",
                system_prompt="Test system prompt",
                retry=True,
            )
