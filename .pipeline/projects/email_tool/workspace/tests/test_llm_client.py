"""Tests for the LLM client."""

import pytest
from unittest.mock import Mock, patch
from email_tool.llm import LLMClient


class TestLLMClient:
    """Tests for LLMClient."""
    
    def test_init_openai(self):
        """Test initialization with OpenAI provider."""
        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="test_key")
        assert client.provider == "openai"
        assert client.model == "gpt-4o-mini"
        assert client.api_key == "test_key"
    
    def test_init_ollama(self):
        """Test initialization with Ollama provider."""
        client = LLMClient(provider="ollama", model="llama2", api_key=None)
        assert client.provider == "ollama"
        assert client.model == "llama2"
    
    def test_init_invalid_provider(self):
        """Test initialization with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(provider="invalid")
    
    def test_init_uses_env_api_key(self):
        """Test that API key is read from environment if not provided."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env_key"}):
            client = LLMClient(provider="openai", model="gpt-4o-mini")
            assert client.api_key == "env_key"
    
    def test_init_uses_env_base_url(self):
        """Test that base URL is read from environment if not provided."""
        with patch.dict("os.environ", {"OLLAMA_BASE_URL": "http://custom:11434"}):
            client = LLMClient(provider="ollama", model="llama2")
            assert client.base_url == "http://custom:11434"
    
    @patch("email_tool.llm.requests.post")
    def test_call_openai_success(self, mock_post):
        """Test successful OpenAI API call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="test_key")
        response = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100
        )
        
        assert response == "Test response"
        mock_post.assert_called_once()
    
    @patch("email_tool.llm.requests.post")
    def test_call_openai_with_system_prompt(self, mock_post):
        """Test OpenAI API call with system prompt."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response"}}]
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="test_key")
        response = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100,
            system_prompt="You are a helpful assistant."
        )
        
        assert response == "Test response"
        call_args = mock_post.call_args
        messages = call_args[1]["json"]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
    
    @patch("email_tool.llm.requests.post")
    def test_call_ollama_success(self, mock_post):
        """Test successful Ollama API call."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "message": {"content": "Ollama response"}
        }
        mock_post.return_value = mock_response
        
        client = LLMClient(provider="ollama", model="llama2")
        response = client.chat(
            messages=[{"role": "user", "content": "Hello"}],
            temperature=0.7,
            max_tokens=100
        )
        
        assert response == "Ollama response"
        mock_post.assert_called_once()
    
    @patch("email_tool.llm.requests.post")
    def test_call_openai_no_api_key(self, mock_post):
        """Test OpenAI API call without API key."""
        mock_post.side_effect = ValueError("OpenAI API key is required")
        
        client = LLMClient(provider="openai", model="gpt-4o-mini")
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            client.chat(
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,
                max_tokens=100
            )
    
    @patch("email_tool.llm.requests.post")
    def test_call_openai_api_error(self, mock_post):
        """Test OpenAI API call with error."""
        import requests
        mock_post.side_effect = requests.exceptions.RequestException("API error")
        
        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="test_key")
        with pytest.raises(Exception, match="OpenAI API call failed"):
            client.chat(
                messages=[{"role": "user", "content": "Hello"}],
                temperature=0.7,
                max_tokens=100
            )
    
    @patch("email_tool.llm.requests.get")
    def test_list_openai_models(self, mock_get):
        """Test listing OpenAI models."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [
                {"id": "gpt-4o"},
                {"id": "gpt-4o-mini"},
                {"id": "gpt-3.5-turbo"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = LLMClient(provider="openai", model="gpt-4o-mini", api_key="test_key")
        models = client.list_models()
        
        assert "gpt-4o" in models
        assert "gpt-4o-mini" in models
        assert "gpt-3.5-turbo" in models
    
    @patch("email_tool.llm.requests.get")
    def test_list_ollama_models(self, mock_get):
        """Test listing Ollama models."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "models": [
                {"name": "llama2"},
                {"name": "mistral"},
                {"name": "gemma"}
            ]
        }
        mock_get.return_value = mock_response
        
        client = LLMClient(provider="ollama", model="llama2")
        models = client.list_models()
        
        assert "llama2" in models
        assert "mistral" in models
        assert "gemma" in models


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
