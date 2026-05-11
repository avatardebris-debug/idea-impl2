"""LLM orchestration layer — provider-agnostic interface for calling LLMs."""

from __future__ import annotations

import json
import os
from typing import Any, Optional

from jinja2 import Template

from ai_movie_gen_suite.config import AppConfig


def _load_template(path: str) -> Template:
    """Load a Jinja2 template from a file."""
    with open(path, "r") as f:
        return Template(f.read())


def _call_openai(config: AppConfig, system_prompt: str, user_prompt: str) -> str:
    """Call OpenAI-compatible API (works with OpenAI, Ollama, etc.)."""
    try:
        from openai import OpenAI
    except ImportError:
        raise RuntimeError("openai package required. Install with: pip install openai")

    api_key = config.llm.api_key or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("No OpenAI API key found. Set OPENAI_API_KEY env var or configure in config.json")

    client = OpenAI(
        api_key=api_key,
        base_url=config.llm.base_url or None,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = client.chat.completions.create(
        model=config.llm.model,
        messages=messages,
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
        response_format={"type": "json_object"} if config.llm.use_json_mode else {"type": "text"},
    )

    return response.choices[0].message.content


def _call_anthropic(config: AppConfig, system_prompt: str, user_prompt: str) -> str:
    """Call Anthropic Claude API."""
    try:
        from anthropic import Anthropic
    except ImportError:
        raise RuntimeError("anthropic package required. Install with: pip install anthropic")

    api_key = config.llm.api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        raise RuntimeError("No Anthropic API key found. Set ANTHROPIC_API_KEY env var or configure in config.json")

    client = Anthropic(api_key=api_key)

    response = client.messages.create(
        model=config.llm.model,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
        temperature=config.llm.temperature,
        max_tokens=config.llm.max_tokens,
    )

    return response.content[0].text


def call_llm(
    config: AppConfig,
    system_prompt: str,
    user_prompt: str,
    provider: Optional[str] = None,
) -> str:
    """Call the configured LLM and return the raw text response."""
    provider = provider or config.llm.provider
    if provider == "anthropic":
        return _call_anthropic(config, system_prompt, user_prompt)
    else:
        # Default to OpenAI-compatible (works with OpenAI, Ollama, etc.)
        return _call_openai(config, system_prompt, user_prompt)


def call_llm_with_template(
    config: AppConfig,
    template_path: str,
    template_vars: dict[str, Any],
    system_prompt: str = "You are a helpful assistant that returns structured JSON output.",
    provider: Optional[str] = None,
) -> dict[str, Any]:
    """Render a Jinja2 template, call the LLM, and parse the JSON response."""
    template = _load_template(template_path)
    user_prompt = template.render(**template_vars)
    raw = call_llm(config, system_prompt, user_prompt, provider)
    return json.loads(raw)
