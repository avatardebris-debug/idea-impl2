"""
llm_interface.py
Model-agnostic LLM adapter layer.

Swap providers with a single string:
    llm = get_llm("openai")
    llm = get_llm("claude")
    llm = get_llm("ollama")
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Shared response dataclass
# ---------------------------------------------------------------------------

@dataclass
class TokenUsage:
    """Token usage statistics from a single LLM call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class Message:
    """Normalised LLM response."""
    role: str
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    usage: TokenUsage | None = None


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class LLMBase(ABC):
    """All providers must implement this single method."""

    @abstractmethod
    def chat(self, messages: list[dict], tools: list[dict] | None = None) -> Message:
        """Send messages and return a normalised Message."""


# ---------------------------------------------------------------------------
# OpenAI adapter
# ---------------------------------------------------------------------------

class OpenAIAdapter(LLMBase):
    def __init__(self, model: str = "gpt-4o", temperature: float = 0.7):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai")
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import json
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        if tools:
            kwargs["tools"] = [{"type": "function", "function": t} for t in tools]
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message

        tool_calls = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                })

        usage = None
        if hasattr(resp, "usage") and resp.usage:
            usage = TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )

        return Message(
            role="assistant",
            content=choice.content or "",
            tool_calls=tool_calls,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Claude adapter
# ---------------------------------------------------------------------------

class ClaudeAdapter(LLMBase):
    def __init__(self, model: str = "claude-sonnet-4-20250514", temperature: float = 0.7):
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic")
        self.client = anthropic.Anthropic()
        self.model = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import json
        system = ""
        formatted = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                formatted.append(m)

        tool_defs = None
        if tools:
            tool_defs = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]

        resp = self.client.messages.create(
            model=self.model,
            system=system,
            messages=formatted,
            tools=tool_defs,
            temperature=self.temperature,
        )

        tool_calls = []
        content = ""
        for block in resp.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "args": block.input,
                })

        usage = TokenUsage(
            prompt_tokens=resp.usage.input_tokens or 0,
            completion_tokens=resp.usage.output_tokens or 0,
            total_tokens=(resp.usage.input_tokens or 0) + (resp.usage.output_tokens or 0),
        )

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Gemini adapter
# ---------------------------------------------------------------------------

class GeminiAdapter(LLMBase):
    def __init__(self, model: str = "gemini-2.5-pro-preview-06-05", temperature: float = 0.7):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("pip install google-generativeai")
        genai.configure()
        self.client = genai.GenerativeModel(model)
        self.model = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import json
        # Convert to Gemini format
        parts_list = []
        for m in messages:
            if m["role"] == "user":
                parts_list.append({"role": "user", "parts": [{"text": m["content"]}]})
            elif m["role"] == "assistant":
                parts_list.append({"role": "model", "parts": [{"text": m["content"]}]})

        tool_defs = None
        if tools:
            tool_defs = [
                {
                    "function_declarations": [
                        {
                            "name": t["function"]["name"],
                            "description": t["function"]["description"],
                            "parameters": t["function"]["parameters"],
                        }
                        for t in tools
                    ]
                }
            ]

        resp = self.client.generate_content(
            parts_list,
            generation_config={"temperature": self.temperature},
            tools=tool_defs,
        )

        tool_calls = []
        if resp.candidates and resp.candidates[0].content.parts:
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "function_call"):
                    fc = part.function_call
                    tool_calls.append({
                        "id": f"gc_{len(tool_calls)}",
                        "name": fc.name,
                        "args": dict(fc.args),
                    })

        content = ""
        if resp.candidates and resp.candidates[0].content.parts:
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "text"):
                    content += part.text

        usage = TokenUsage(
            prompt_tokens=getattr(resp, "usage_metadata", None) and getattr(resp.usage_metadata, "prompt_token_count", 0) or 0,
            completion_tokens=getattr(resp, "usage_metadata", None) and getattr(resp.usage_metadata, "candidates_token_count", 0) or 0,
            total_tokens=getattr(resp, "usage_metadata", None) and getattr(resp.usage_metadata, "total_token_count", 0) or 0,
        )

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Ollama adapter
# -----------------------------------------------------------------------------------

class OllamaAdapter(LLMBase):
    def __init__(
        self,
        model: str = "qwen3:32b",
        temperature: float = 0.7,
        base_url: str = "http://localhost:11434",
        num_ctx: int = 16384,
        think: bool | None = None,
    ):
        try:
            import ollama
        except ImportError:
            raise ImportError("pip install ollama")
        self.model = model
        self.temperature = temperature
        self.base_url = base_url
        self.num_ctx = num_ctx
        self.think = think
        self.client = ollama.Client(host=base_url)

    def chat(self, messages, tools=None) -> Message:
        import json
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            options={
                "temperature": self.temperature,
                "num_ctx": self.num_ctx,
            },
        )
        if self.think is not None:
            kwargs["options"]["thinking"] = {"type": "enabled", "budget_tokens": 1024} if self.think else {"type": "disabled"}

        if tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t["function"]["name"],
                        "description": t["function"]["description"],
                        "parameters": t["function"]["parameters"],
                    },
                }
                for t in tools
            ]

        resp = self.client.chat(**kwargs)

        tool_calls = []
        if resp.message.tool_calls:
            for tc in resp.message.tool_calls:
                tool_calls.append({
                    "id": tc.get("id", f"tc_{len(tool_calls)}"),
                    "name": tc["function"]["name"],
                    "args": json.loads(tc["function"]["arguments"]) if isinstance(tc["function"]["arguments"], str) else tc["function"]["arguments"],
                })

        prompt_tokens = resp.get("prompt_eval_count", 0) or 0
        completion_tokens = resp.get("eval_count", 0) or 0
        content = resp.message.content or ""

        usage = None
        if prompt_tokens or completion_tokens:
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            )

        return Message(
            role="assistant",
            content=content,
            tool_calls=tool_calls,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# xAI / Grok  (OpenAI-compatible API — pip install openai)
# Docs: https://docs.x.ai/api
# Set env var: XAI_API_KEY=xai-...
# ---------------------------------------------------------------------------

class GrokAdapter(LLMBase):
    """
    xAI Grok via its OpenAI-compatible REST API.
    Uses the openai SDK pointed at https://api.x.ai/v1.
    Requires XAI_API_KEY environment variable.

    Recommended models:
        grok-3            — most capable, best for complex coding
        grok-3-fast       — faster, lower cost
        grok-3-mini       — lightweight reasoning model
        grok-3-mini-fast  — fastest / cheapest
    """

    BASE_URL = "https://api.x.ai/v1"
    DEFAULT_MODEL = "grok-3"

    def __init__(self, model: str = DEFAULT_MODEL, temperature: float = 0.7):
        import os
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("pip install openai  # Grok uses the OpenAI-compatible SDK")
        api_key = os.environ.get("XAI_API_KEY")
        if not api_key:
            raise EnvironmentError(
                "XAI_API_KEY is not set. "
                "Get your key at https://console.x.ai and set:\n"
                "  export XAI_API_KEY=xai-..."
            )
        self.client = OpenAI(api_key=api_key, base_url=self.BASE_URL)
        self.model = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import json
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        if tools:
            kwargs["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]
            kwargs["tool_choice"] = "auto"

        resp = self.client.chat.completions.create(**kwargs)
        choice = resp.choices[0].message

        tool_calls = []
        if choice.tool_calls:
            for tc in choice.tool_calls:
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                })

        usage = None
        if hasattr(resp, "usage") and resp.usage:
            usage = TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )

        return Message(
            role="assistant",
            content=choice.content or "",
            tool_calls=tool_calls,
            usage=usage,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

PROVIDERS = {
    "openai": OpenAIAdapter,
    "claude": ClaudeAdapter,
    "gemini": GeminiAdapter,
    "ollama": OllamaAdapter,
    "grok":   GrokAdapter,
}


def get_llm(
    provider: str = "openai",
    model: str | None = None,
    temperature: float = 0.7,
    base_url: str | None = None,
    num_ctx: int = 16384,
    think: bool | None = None,
) -> LLMBase:
    """
    Return a model-agnostic LLM adapter.

    Args:
        provider:    "openai" | "claude" | "gemini" | "ollama" | "grok"
        model:       Optional model override (uses provider default if None)
        temperature: Sampling temperature (0.0–1.0, default 0.7)
        base_url:    Optional base URL for remote instances (Ollama only)
        num_ctx:     Ollama context window size (default 16384)
        think:       Qwen3 thinking mode (Ollama only)

    Grok setup:
        export XAI_API_KEY=xai-...   # from https://console.x.ai
        python pipeline/runner.py --provider grok --model grok-3 ...
    """
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider '{provider}'. Choose from: {list(PROVIDERS)}")
    cls = PROVIDERS[provider]
    kwargs: dict[str, Any] = {"temperature": temperature}
    if model:
        kwargs["model"] = model
    if provider == "ollama":
        if base_url:
            kwargs["base_url"] = base_url
        kwargs["num_ctx"] = num_ctx
        if think is not None:
            kwargs["think"] = think
    return cls(**kwargs)
