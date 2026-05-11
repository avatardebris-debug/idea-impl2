"""LLM client for thesis generation.

Wraps the OpenAI or local LLM API with retry logic and error handling
specific to the generation pipeline.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from openai import OpenAI

from ..config import settings

logger = logging.getLogger(__name__)


class GenerationLLMClient:
    """LLM client optimized for thesis generation tasks."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        self._client = OpenAI(api_key=api_key or settings.openai_api_key, base_url=base_url)
        self._model = model or settings.openai_model
        self._max_retries = 3
        self._retry_delay = 1.0

    async def generate(self, system: str, user: str) -> str:
        """Generate text with retry logic."""
        last_error = None
        for attempt in range(self._max_retries):
            try:
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self._sync_generate,
                    system,
                    user,
                )
                return response
            except Exception as e:
                last_error = e
                logger.warning("Generation attempt %d failed: %s", attempt + 1, e)
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(self._retry_delay * (2 ** attempt))
        raise last_error  # type: ignore[misc]

    def _sync_generate(self, system: str, user: str) -> str:
        """Synchronous generation call."""
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=4000,
        )
        return response.choices[0].message.content or ""
