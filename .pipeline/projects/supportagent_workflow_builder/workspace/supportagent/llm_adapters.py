"""LLM adapters for AI-powered triage and response generation.

Supports multiple LLM providers with a unified interface.
"""

from __future__ import annotations

import abc
import json
import os
from typing import Any, Dict, List, Optional, Tuple

import yaml


class LLMProvider:
    """Enum of supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


class LLMConfig:
    """Configuration for an LLM provider."""

    def __init__(
        self,
        provider: str = LLMProvider.MOCK,
        model: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 1024,
        timeout: int = 30,
        **kwargs: Any,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.environ.get(
            f"{provider.upper()}_API_KEY", "mock-key"
        )
        self.base_url = base_url
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.extra = kwargs

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> LLMConfig:
        """Create config from dictionary."""
        return cls(**data)

    @classmethod
    def from_yaml(cls, path: str) -> LLMConfig:
        """Create config from YAML file."""
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)


class LLMMessage:
    """Represents a chat message."""

    def __init__(self, role: str, content: str, name: Optional[str] = None):
        self.role = role  # "system", "user", "assistant"
        self.content = content
        self.name = name

    def to_dict(self) -> Dict[str, str]:
        d = {"role": self.role, "content": self.content}
        if self.name:
            d["name"] = self.name
        return d


class LLMResponse:
    """Represents an LLM response."""

    def __init__(
        self,
        content: str,
        model: str,
        usage: Optional[Dict[str, int]] = None,
        finish_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.content = content
        self.model = model
        self.usage = usage or {}
        self.finish_reason = finish_reason
        self.metadata = metadata or {}

    @property
    def text(self) -> str:
        return self.content

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
            "metadata": self.metadata,
        }


class BaseLLMAdapter(abc.ABC):
    """Abstract base class for LLM adapters."""

    @abc.abstractmethod
    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Send a chat completion request."""
        ...

    @abc.abstractmethod
    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        """Send a streaming chat completion request. Yields chunks."""
        ...

    @abc.abstractmethod
    def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        """Classify text into one of the given categories.

        Returns:
            Tuple of (predicted_category, confidence_score)
        """
        ...

    @abc.abstractmethod
    def extract_json(
        self,
        text: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Extract structured data from text using LLM.

        Returns:
            Dictionary of extracted data.
        """
        ...

    def get_config(self) -> LLMConfig:
        """Return the adapter's configuration."""
        return self._config

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        ...


class MockLLMAdapter(BaseLLMAdapter):
    """Mock LLM adapter for testing and development."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or LLMConfig(provider=LLMProvider.MOCK)

    @property
    def model_name(self) -> str:
        return "mock-gpt-4o-mini"

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        # Return a mock response based on the last user message
        last_user = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user = msg.content
                break

        if last_user:
            return LLMResponse(
                content=f"Mock response to: {last_user[:50]}...",
                model=self.model_name,
                usage={"prompt_tokens": 10, "completion_tokens": 20},
                finish_reason="stop",
            )
        return LLMResponse(
            content="Mock response",
            model=self.model_name,
            usage={"prompt_tokens": 5, "completion_tokens": 10},
            finish_reason="stop",
        )

    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        response = self.chat(messages, temperature, max_tokens)
        for chunk in response.content.split():
            yield {"content": chunk + " ", "done": False}
        yield {"content": "", "done": True}

    def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        # Simple mock: return the first category with high confidence
        # but occasionally pick a random one for variety
        import random

        if "urgent" in text.lower() or "critical" in text.lower():
            return "urgent", 0.95
        elif "billing" in text.lower() or "payment" in text.lower():
            return "billing", 0.90
        elif "technical" in text.lower() or "bug" in text.lower():
            return "technical", 0.88
        elif categories:
            return categories[0], 0.70
        return "general", 0.50

    def extract_json(
        self,
        text: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        # Try to parse as JSON first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Mock extraction based on schema
        result = {}
        for field, field_schema in schema.items():
            field_type = field_schema.get("type", "string")
            if field_type == "string":
                result[field] = f"mock_{field}"
            elif field_type == "number":
                result[field] = 0
            elif field_type == "boolean":
                result[field] = False
            elif field_type == "array":
                result[field] = []
            elif field_type == "object":
                result[field] = {}
        return result


class OpenAIAdapter(BaseLLMAdapter):
    """OpenAI API adapter."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or LLMConfig(provider=LLMProvider.OPENAI)
        self._client = None

    @property
    def model_name(self) -> str:
        return self._config.model

    def _get_client(self):
        """Lazy import and create OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI as OpenAIClient
            except ImportError:
                raise ImportError(
                    "openai package is required for OpenAIAdapter. "
                    "Install it with: pip install openai"
                )
            self._client = OpenAIClient(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )
        return self._client

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()
        openai_messages = [msg.to_dict() for msg in messages]

        response = client.chat.completions.create(
            model=self._config.model,
            messages=openai_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            timeout=self._config.timeout,
            **kwargs,
        )

        choice = response.choices[0]
        return LLMResponse(
            content=choice.message.content or "",
            model=self._config.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
            },
            finish_reason=choice.finish_reason,
        )

    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        client = self._get_client()
        openai_messages = [msg.to_dict() for msg in messages]

        stream = client.chat.completions.create(
            model=self._config.model,
            messages=openai_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            stream=True,
            timeout=self._config.timeout,
            **kwargs,
        )

        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield {
                    "content": chunk.choices[0].delta.content,
                    "done": False,
                }
        yield {"content": "", "done": True}

    def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        system_prompt = f"""You are a classification assistant. Classify the input text into exactly one of these categories: {', '.join(categories)}.

Respond in JSON format only:
{{
    "category": "<one of the categories>",
    "confidence": <float between 0 and 1>,
    "reasoning": "<brief explanation>"
}}"
"""
        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        # Parse JSON response
        try:
            data = json.loads(response.content)
            category = data.get("category", categories[0] if categories else "general")
            confidence = float(data.get("confidence", 0.5))
            return category, confidence
        except (json.JSONDecodeError, ValueError):
            # Fallback: return first category
            return categories[0] if categories else "general", 0.5

    def extract_json(
        self,
        text: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        system_prompt = f"""Extract structured data from the text below according to this schema:

{json.dumps(schema, indent=2)}

Respond in JSON format only. Do not include any markdown or explanation."""

        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        # Try to parse JSON
        content = response.content.strip()
        # Remove markdown code blocks if present
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM response as JSON: {content[:200]}")


class AnthropicAdapter(BaseLLMAdapter):
    """Anthropic Claude API adapter."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or LLMConfig(provider=LLMProvider.ANTHROPIC)
        self._client = None

    @property
    def model_name(self) -> str:
        return self._config.model

    def _get_client(self):
        """Lazy import and create Anthropic client."""
        if self._client is None:
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "anthropic package is required for AnthropicAdapter. "
                    "Install it with: pip install anthropic"
                )
            self._client = Anthropic(
                api_key=self._config.api_key,
                base_url=self._config.base_url,
            )
        return self._client

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        client = self._get_client()

        # Separate system message
        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        response = client.messages.create(
            model=self._config.model,
            system=system_content,
            messages=chat_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            timeout=self._config.timeout,
            **kwargs,
        )

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=self._config.model,
            usage={
                "prompt_tokens": response.usage.input_tokens if response.usage else 0,
                "completion_tokens": response.usage.output_tokens if response.usage else 0,
            },
            finish_reason=response.stop_reason,
        )

    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        client = self._get_client()

        system_content = ""
        chat_messages = []
        for msg in messages:
            if msg.role == "system":
                system_content = msg.content
            else:
                chat_messages.append({"role": msg.role, "content": msg.content})

        stream = client.messages.stream(
            model=self._config.model,
            system=system_content,
            messages=chat_messages,
            temperature=temperature if temperature is not None else self._config.temperature,
            max_tokens=max_tokens or self._config.max_tokens,
            timeout=self._config.timeout,
            **kwargs,
        )

        with stream as s:
            for chunk in s:
                if chunk.type == "content_block_delta":
                    yield {
                        "content": chunk.delta.text,
                        "done": False,
                    }
        yield {"content": "", "done": True}

    def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        system_prompt = f"""You are a classification assistant. Classify the input text into exactly one of these categories: {', '.join(categories)}.

Respond in JSON format only:
{{
    "category": "<one of the categories>",
    "confidence": <float between 0 and 1>,
    "reasoning": "<brief explanation>"
}}"
"""
        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        try:
            data = json.loads(response.content)
            category = data.get("category", categories[0] if categories else "general")
            confidence = float(data.get("confidence", 0.5))
            return category, confidence
        except (json.JSONDecodeError, ValueError):
            return categories[0] if categories else "general", 0.5

    def extract_json(
        self,
        text: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        system_prompt = f"""Extract structured data from the text below according to this schema:

{json.dumps(schema, indent=2)}

Respond in JSON format only. Do not include any markdown or explanation."""

        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM response as JSON: {content[:200]}")


class LocalLLMAdapter(BaseLLMAdapter):
    """Local LLM adapter using Ollama or similar."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self._config = config or LLMConfig(
            provider=LLMProvider.LOCAL,
            base_url="http://localhost:11434",
        )
        self._base_url = self._config.base_url or "http://localhost:11434"

    @property
    def model_name(self) -> str:
        return self._config.model

    def chat(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        import requests

        payload = {
            "model": self._config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature if temperature is not None else self._config.temperature,
            "max_tokens": max_tokens or self._config.max_tokens,
            "stream": False,
        }

        response = requests.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=self._config.timeout,
        )
        response.raise_for_status()
        data = response.json()

        return LLMResponse(
            content=data.get("message", {}).get("content", ""),
            model=self._config.model,
            usage={},
            finish_reason=data.get("done_reason"),
        )

    def chat_stream(
        self,
        messages: List[LLMMessage],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs: Any,
    ):
        import requests

        payload = {
            "model": self._config.model,
            "messages": [msg.to_dict() for msg in messages],
            "temperature": temperature if temperature is not None else self._config.temperature,
            "max_tokens": max_tokens or self._config.max_tokens,
            "stream": True,
        }

        response = requests.post(
            f"{self._base_url}/api/chat",
            json=payload,
            timeout=self._config.timeout,
            stream=True,
        )

        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield {
                    "content": data.get("message", {}).get("content", ""),
                    "done": data.get("done", False),
                }

    def classify(
        self,
        text: str,
        categories: List[str],
        **kwargs: Any,
    ) -> Tuple[str, float]:
        system_prompt = f"""You are a classification assistant. Classify the input text into exactly one of these categories: {', '.join(categories)}.

Respond in JSON format only:
{{
    "category": "<one of the categories>",
    "confidence": <float between 0 and 1>,
    "reasoning": "<brief explanation>"
}}"
"""
        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        try:
            data = json.loads(response.content)
            category = data.get("category", categories[0] if categories else "general")
            confidence = float(data.get("confidence", 0.5))
            return category, confidence
        except (json.JSONDecodeError, ValueError):
            return categories[0] if categories else "general", 0.5

    def extract_json(
        self,
        text: str,
        schema: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        system_prompt = f"""Extract structured data from the text below according to this schema:

{json.dumps(schema, indent=2)}

Respond in JSON format only. Do not include any markdown or explanation."""

        messages = [
            LLMMessage("system", system_prompt),
            LLMMessage("user", text),
        ]

        response = self.chat(messages, temperature=0.0, **kwargs)

        content = response.content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            content = "\n".join(lines)

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            raise ValueError(f"Failed to parse LLM response as JSON: {content[:200]}")


def create_llm_adapter(
    provider: str = LLMProvider.MOCK,
    config: Optional[LLMConfig] = None,
) -> BaseLLMAdapter:
    """Factory function to create an LLM adapter.

    Args:
        provider: The LLM provider to use.
        config: Optional configuration.

    Returns:
        An LLM adapter instance.
    """
    adapters = {
        LLMProvider.MOCK: MockLLMAdapter,
        LLMProvider.OPENAI: OpenAIAdapter,
        LLMProvider.ANTHROPIC: AnthropicAdapter,
        LLMProvider.LOCAL: LocalLLMAdapter,
    }

    adapter_class = adapters.get(provider)
    if adapter_class is None:
        raise ValueError(f"Unknown LLM provider: {provider}")

    return adapter_class(config)
