"""OpenAI API client wrapper."""

from __future__ import annotations

from typing import Optional

from openai import OpenAI

from ..config import settings


class OpenAIClient:
    """Wrapper around the OpenAI API."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self._client = OpenAI(api_key=api_key or settings.openai_api_key)
        self._model = model or settings.openai_model

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Generate text using the OpenAI API."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
        )
        return response.choices[0].message.content or ""

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        """Generate structured JSON output."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            max_tokens=kwargs.get("max_tokens", settings.max_tokens),
            temperature=kwargs.get("temperature", settings.temperature),
        )
        import json
        return json.loads(response.choices[0].message.content or "{}")
