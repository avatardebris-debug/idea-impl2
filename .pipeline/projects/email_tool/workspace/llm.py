"""LLM client for interacting with language model APIs."""

import os
from typing import Any, Dict, List, Optional

import requests


class LLMClient:
    """
    Client for interacting with LLM APIs.
    
    Supports multiple providers:
    - OpenAI (gpt-4o, gpt-4o-mini, etc.)
    - Ollama (local LLMs)
    
    This client provides a unified interface for calling LLMs regardless of provider.
    """
    
    def __init__(
        self,
        provider: str = "openai",
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        Initialize the LLM client.
        
        Args:
            provider: LLM provider ('openai' or 'ollama').
            model: Model name to use.
            api_key: API key for the provider.
            base_url: Custom base URL (for Ollama or other providers).
        """
        self.provider = provider.lower()
        self.model = model
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # Validate provider
        if self.provider not in ["openai", "ollama"]:
            raise ValueError(f"Unsupported provider: {provider}. Use 'openai' or 'ollama'.")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        Send a chat request to the LLM.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'.
            temperature: Sampling temperature (0.0-1.0).
            max_tokens: Maximum tokens to generate.
            system_prompt: Optional system prompt.
            
        Returns:
            The LLM's response text.
            
        Raises:
            Exception: If the LLM call fails.
        """
        if self.provider == "openai":
            return self._call_openai(messages, temperature, max_tokens, system_prompt)
        elif self.provider == "ollama":
            return self._call_ollama(messages, temperature, max_tokens)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _call_openai(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        system_prompt: Optional[str]
    ) -> str:
        """
        Call OpenAI API.
        
        Args:
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            system_prompt: System prompt.
            
        Returns:
            The response text.
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Prepare messages
        formatted_messages = []
        
        # Add system prompt if provided
        if system_prompt:
            formatted_messages.append({"role": "system", "content": system_prompt})
        
        # Add user messages
        formatted_messages.extend(messages)
        
        # Make API call
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"OpenAI API call failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response from OpenAI API: {str(e)}")
    
    def _call_ollama(
        self,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int
    ) -> str:
        """
        Call Ollama API.
        
        Args:
            messages: Chat messages.
            temperature: Sampling temperature.
            max_tokens: Maximum tokens.
            
        Returns:
            The response text.
        """
        # Prepare messages for Ollama format
        ollama_messages = []
        for msg in messages:
            ollama_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Make API call
        url = f"{self.base_url}/api/chat"
        headers = {"Content-Type": "application/json"}
        
        payload = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Ollama API call failed: {str(e)}")
        except (KeyError, IndexError) as e:
            raise Exception(f"Invalid response from Ollama: {str(e)}")
    
    def list_models(self) -> List[str]:
        """
        List available models for the provider.
        
        Returns:
            List of available model names.
        """
        if self.provider == "openai":
            return self._list_openai_models()
        elif self.provider == "ollama":
            return self._list_ollama_models()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _list_openai_models(self) -> List[str]:
        """List OpenAI models."""
        if not self.api_key:
            raise ValueError("OpenAI API key is required.")
        
        url = "https://api.openai.com/v1/models"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return [model["id"] for model in result.get("data", [])]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list OpenAI models: {str(e)}")
    
    def _list_ollama_models(self) -> List[str]:
        """List Ollama models."""
        url = f"{self.base_url}/api/tags"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return [model["name"] for model in result.get("models", [])]
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to list Ollama models: {str(e)}")
