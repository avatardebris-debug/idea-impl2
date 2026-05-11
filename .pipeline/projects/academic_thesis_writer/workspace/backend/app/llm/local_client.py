"""Local LLM client (Ollama-compatible API)."""

from __future__ import annotations

from typing import Optional

import requests

from ..config import settings


class LocalClient:
    """Wrapper around a local Ollama-compatible API."""

    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self._base_url = base_url or settings.local_llm_base_url
        self._model = model or settings.local_llm_model

    def generate(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Generate text using the local LLM API."""
        response = requests.post(
            f"{self._base_url}/api/generate",
            json={
                "model": self._model,
                "prompt": user_prompt,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "num_predict": kwargs.get("max_tokens", settings.max_tokens),
                    "temperature": kwargs.get("temperature", settings.temperature),
                },
            },
            timeout=120,
        )
        response.raise_for_status()
        return response.json().get("response", "")

    def generate_json(self, system_prompt: str, user_prompt: str, **kwargs) -> dict:
        """Generate structured JSON output (best-effort)."""
        text = self.generate(system_prompt, user_prompt, **kwargs)
        import json
        # Try to parse JSON from the response
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
