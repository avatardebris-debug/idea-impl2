"""LLM client abstraction."""

from __future__ import annotations

import asyncio
from typing import Optional

from ..config import LLMBackend
from .llm.openai_client import OpenAIClient
from .llm.local_client import LocalClient


class LLMClient:
    """Unified LLM client that delegates to OpenAI or LocalClient."""

    def __init__(self, backend: LLMBackend = LLMBackend.OPENAI):
        if backend == LLMBackend.OPENAI:
            self._client = OpenAIClient()
        else:
            self._client = LocalClient()

    async def generate(self, system: str, user: str) -> str:
        """Generate text from system and user prompts."""
        return await self._client.generate(system, user)

    async def generate_json(self, system: str, user: str) -> dict:
        """Generate JSON from system and user prompts."""
        return await self._client.generate_json(system, user)

    async def generate_with_retry(
        self,
        system: str,
        user: str,
        max_retries: int = 3,
        delay: float = 1.0,
    ) -> str:
        """Generate text with retry logic."""
        last_error = None
        for attempt in range(max_retries):
            try:
                return await self.generate(system, user)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    await asyncio.sleep(delay * (2 ** attempt))
        raise last_error  # type: ignore[misc]
