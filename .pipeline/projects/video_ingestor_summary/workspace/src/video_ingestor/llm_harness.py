"""LLM harness that abstracts over LLM providers."""

from __future__ import annotations

import json
from typing import Optional

from .config import settings


class LLMHarness:
    """Abstracts over LLM providers (OpenAI, local models)."""

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key or settings.OPENAI_API_KEY

    def generate(self, prompt: str, **kwargs) -> str:
        """Generate a text response from the LLM."""
        if self.provider == "openai":
            return self._call_openai(prompt, **kwargs)
        else:
            raise ValueError(
                f"Unsupported LLM provider: {self.provider}. "
                f"Supported providers: openai"
            )

    def _call_openai(self, prompt: str, **kwargs) -> str:
        """Call OpenAI API."""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError(
                "openai package is required for OpenAI provider. "
                "Install it with: pip install openai"
            )

        try:
            client = OpenAI(api_key=self.api_key)
            response = client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=[{"role": "user", "content": prompt}],
                temperature=kwargs.get("temperature", 0.3),
                max_tokens=kwargs.get("max_tokens", 2048),
            )
            return response.choices[0].message.content
        except Exception as e:
            raise RuntimeError(f"OpenAI API error: {e}")

    def generate_json(self, prompt: str, **kwargs) -> dict:
        """Generate a JSON response from the LLM."""
        text = self.generate(prompt, **kwargs)
        # Try to extract JSON from the response
        try:
            # Try parsing the whole response as JSON
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to find JSON in the response
            start = text.find("{")
            end = text.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                return json.loads(json_str)
            raise ValueError(f"Could not parse JSON from LLM response: {text}")
