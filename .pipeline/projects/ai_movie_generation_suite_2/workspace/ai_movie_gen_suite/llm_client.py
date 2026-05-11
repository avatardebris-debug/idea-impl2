"""LLM client for the AI Movie Generation Suite.

Provides a unified interface for interacting with OpenAI and Anthropic LLMs.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from ai_movie_gen_suite.config import LLMConfig

logger = logging.getLogger(__name__)


class LLMMessage(BaseModel):
    """A single message in a conversation.

    Attributes:
        role: Message role ('system', 'user', or 'assistant').
        content: Message content.
    """

    role: str = Field(description="Message role (system, user, or assistant)")
    content: str = Field(description="Message content")

    def to_dict(self) -> Dict[str, str]:
        """Convert message to a dictionary."""
        return {"role": self.role, "content": self.content}


class LLMResponse(BaseModel):
    """Response from an LLM API call.

    Attributes:
        content: The response content.
        model: The model that generated the response.
        usage: Token usage information.
        finish_reason: Reason the model stopped generating.
    """

    content: str = Field(description="Response content")
    model: str = Field(description="Model that generated the response")
    usage: Dict[str, int] = Field(default_factory=dict, description="Token usage information")
    finish_reason: Optional[str] = Field(None, description="Reason the model stopped generating")

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to a dictionary."""
        return {
            "content": self.content,
            "model": self.model,
            "usage": self.usage,
            "finish_reason": self.finish_reason,
        }


class LLMClient:
    """Unified LLM client supporting OpenAI and Anthropic providers.

    Attributes:
        config: LLM configuration.
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """Initialize the LLM client.

        Args:
            config: LLM configuration. If None, loads from environment.
        """
        self.config = config or LLMConfig.from_env()
        self._validate_config()
        self._client = self._init_client()

    def _validate_config(self) -> None:
        """Validate the configuration."""
        if not self.config.api_key and not os.environ.get("FIVERR_LLM_API_KEY"):
            raise ValueError(
                f"API key is required for {self.config.provider}. "
                "Set it in config or FIVERR_LLM_API_KEY environment variable."
            )

    def _init_client(self) -> Any:
        """Initialize the provider-specific client.

        Returns:
            The initialized client object.

        Raises:
            ImportError: If the required provider library is not installed.
        """
        if self.config.provider == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "OpenAI library not installed. Install with: pip install openai"
                )
            api_key = self.config.api_key or os.environ.get("FIVERR_LLM_API_KEY", "")
            if self.config.base_url:
                return OpenAI(api_key=api_key, base_url=self.config.base_url)
            return OpenAI(api_key=api_key)

        elif self.config.provider == "anthropic":
            try:
                from anthropic import Anthropic
            except ImportError:
                raise ImportError(
                    "Anthropic library not installed. Install with: pip install anthropic"
                )
            api_key = self.config.api_key or os.environ.get("FIVERR_LLM_API_KEY", "")
            return Anthropic(api_key=api_key)

        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")

    def _prepare_messages(self, messages: List[LLMMessage]) -> Tuple[List[Dict[str, str]], str]:
        """Prepare messages for the API call.

        Args:
            messages: List of messages to send.

        Returns:
            Tuple of (formatted messages, system message).
        """
        system_messages = [m for m in messages if m.role == "system"]
        user_messages = [m for m in messages if m.role == "user"]
        assistant_messages = [m for m in messages if m.role == "assistant"]

        system_msg = system_messages[-1].content if system_messages else ""
        formatted_messages = [m.to_dict() for m in user_messages + assistant_messages]

        return formatted_messages, system_msg

    def _call_openai(self, messages: List[Dict[str, str]], system_msg: str) -> LLMResponse:
        """Call the OpenAI API.

        Args:
            messages: Formatted messages.
            system_msg: System message.

        Returns:
            LLMResponse object.
        """
        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": [{"role": "system", "content": system_msg}] + messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if self.config.use_json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url

        response = self._client.chat.completions.create(**kwargs)

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            finish_reason=response.choices[0].finish_reason,
        )

    def _call_anthropic(self, messages: List[Dict[str, str]], system_msg: str) -> LLMResponse:
        """Call the Anthropic API.

        Args:
            messages: Formatted messages.
            system_msg: System message.

        Returns:
            LLMResponse object.
        """
        kwargs: Dict[str, Any] = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
        }

        if system_msg:
            kwargs["system"] = system_msg

        response = self._client.messages.create(**kwargs)

        return LLMResponse(
            content=response.content[0].text if response.content else "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    def chat(
        self,
        messages: List[LLMMessage],
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> LLMResponse:
        """Send a chat request to the LLM.

        Args:
            messages: List of messages to send.
            retries: Number of retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            LLMResponse object.

        Raises:
            ValueError: If the API key is not set.
            Exception: If the API call fails after retries.
        """
        self._validate_config()

        formatted_messages, system_msg = self._prepare_messages(messages)

        last_exception = None
        for attempt in range(retries + 1):
            try:
                if self.config.provider == "openai":
                    return self._call_openai(formatted_messages, system_msg)
                elif self.config.provider == "anthropic":
                    return self._call_anthropic(formatted_messages, system_msg)
                else:
                    raise ValueError(f"Unsupported provider: {self.config.provider}")

            except Exception as e:
                last_exception = e
                logger.warning(
                    f"API call failed (attempt {attempt + 1}/{retries + 1}): {e}"
                )
                if attempt < retries:
                    time.sleep(retry_delay)

        raise last_exception  # type: ignore[misc]

    def generate(
        self,
        messages: List[LLMMessage],
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> LLMResponse:
        """Generate a response from the LLM (alias for chat).

        Args:
            messages: List of messages to send.
            retries: Number of retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            LLMResponse object.
        """
        return self.chat(messages, retries, retry_delay)

    def chat_with_json(
        self,
        messages: List[LLMMessage],
        retries: int = 3,
        retry_delay: float = 1.0,
    ) -> Dict[str, Any]:
        """Send a chat request and parse the JSON response.

        Args:
            messages: List of messages to send.
            retries: Number of retry attempts.
            retry_delay: Delay between retries in seconds.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            json.JSONDecodeError: If the response is not valid JSON.
        """
        response = self.chat(messages, retries, retry_delay)

        if not response.content:
            raise ValueError("Empty response from LLM")

        try:
            return json.loads(response.content)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.debug(f"Raw response: {response.content}")
            raise

    def get_usage(self, response: LLMResponse) -> Dict[str, int]:
        """Get token usage from a response.

        Args:
            response: The LLM response.

        Returns:
            Dictionary with token usage information.
        """
        return response.usage

    def get_cost_estimate(self, response: LLMResponse) -> float:
        """Estimate the cost of a response.

        Args:
            response: The LLM response.

        Returns:
            Estimated cost in USD.
        """
        # Pricing per 1M tokens (as of 2024)
        pricing = {
            "gpt-4o": {"prompt": 5.0, "completion": 15.0},
            "gpt-4o-mini": {"prompt": 0.15, "completion": 0.6},
            "claude-3-opus": {"prompt": 15.0, "completion": 75.0},
            "claude-3-sonnet": {"prompt": 3.0, "completion": 15.0},
            "claude-3-haiku": {"prompt": 0.25, "completion": 1.25},
        }

        model = response.model.lower()
        pricing_info = None
        for key, price in pricing.items():
            if key in model:
                pricing_info = price
                break

        if not pricing_info:
            logger.warning(f"Unknown model pricing for {model}, using default rates")
            pricing_info = {"prompt": 5.0, "completion": 15.0}

        usage = response.usage
        prompt_cost = (usage.get("prompt_tokens", 0) / 1_000_000) * pricing_info["prompt"]
        completion_cost = (usage.get("completion_tokens", 0) / 1_000_000) * pricing_info["completion"]

        return round(prompt_cost + completion_cost, 6)
