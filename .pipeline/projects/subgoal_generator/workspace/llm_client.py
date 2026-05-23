"""LLM client abstraction supporting multiple providers."""

from __future__ import annotations

from openai import OpenAI


class LLMClient:
    """Thin wrapper around an OpenAI-compatible chat completion API."""

    def __init__(
        self,
        provider: str = "openai",
        api_key: str | None = None,
        base_url: str | None = None,
        model: str = "gpt-4o-mini",
        **extra_kwargs: object,
    ) -> None:
        self.provider = provider
        self.model = model
        self.extra_kwargs = extra_kwargs

        # Build the client — all providers use the OpenAI SDK compatible interface
        self.client = OpenAI(
            api_key=api_key or "",
            base_url=base_url,
        )

    def complete(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the assistant's text response."""
        return self._chat_completion(prompt)

    def chat_completion(self, prompt: str) -> str:
        """Alias for complete() — used by tests that mock this method name."""
        return self._chat_completion(prompt)

    def _chat_completion(self, prompt: str) -> str:
        """Internal method that does the actual API call."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            **self.extra_kwargs,
        )
        return response.choices[0].message.content or ""
