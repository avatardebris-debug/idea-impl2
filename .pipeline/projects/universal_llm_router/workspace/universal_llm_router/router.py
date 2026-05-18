"""
Universal LLM Router — routes requests across concrete LLM provider adapters.

Adapters provided:
  - OllamaAdapter  (local Ollama REST API)
  - OpenAIAdapter  (OpenAI-compatible REST API; also works with LM Studio, Together, etc.)
  - MockAdapter    (deterministic, no network — for testing)

The router wraps the shared LLMClient Protocol from the pipeline's llmclient executor,
so any existing SOPExecutor can receive a UniversalRouter in place of its llm_client arg.
"""

from __future__ import annotations

import enum
import json
import logging
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LLMClient Protocol (mirrors shared_libs/llmclient/executor.py)
# ---------------------------------------------------------------------------

class LLMClient:
    """Minimal interface every adapter must satisfy."""

    def call(self, system_prompt: str, user_prompt: str) -> str:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Concrete provider adapters
# ---------------------------------------------------------------------------

class MockAdapter(LLMClient):
    """Deterministic mock — used in tests and CI."""

    def __init__(self, response: str = "mock_response"):
        self.response = response
        self.call_count = 0

    def call(self, system_prompt: str, user_prompt: str) -> str:
        self.call_count += 1
        return json.dumps({"raw": self.response, "tokens_used": 0})


class OllamaAdapter(LLMClient):
    """Adapter for a local Ollama REST API."""

    def __init__(
        self,
        model: str = "llama3",
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "stream": False,
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        return data["message"]["content"]

    def health_check(self) -> bool:
        """Return True if the Ollama server is reachable."""
        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False


class OpenAIAdapter(LLMClient):
    """
    Adapter for OpenAI-compatible REST APIs.
    Works with:  OpenAI, Together AI, Groq, LM Studio, vLLM, etc.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o-mini",
        base_url: str = "https://api.openai.com/v1",
        timeout: int = 120,
    ):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def call(self, system_prompt: str, user_prompt: str) -> str:
        payload = json.dumps({
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }).encode()

        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]

    def health_check(self) -> bool:
        """Return True if the API endpoint answers a models list call."""
        try:
            req = urllib.request.Request(
                f"{self.base_url}/models",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            with urllib.request.urlopen(req, timeout=5):
                return True
        except Exception:
            return False


# ---------------------------------------------------------------------------
# Routing strategies
# ---------------------------------------------------------------------------

class RouteStrategy(enum.Enum):
    FALLBACK = "fallback"       # try each in order, move on if one fails
    ROUND_ROBIN = "round_robin" # distribute evenly, skip failed providers


# ---------------------------------------------------------------------------
# Route config
# ---------------------------------------------------------------------------

@dataclass
class RouteConfig:
    """Wraps a provider adapter with optional metadata."""
    provider_name: str
    adapter: LLMClient
    weight: int = 1            # reserved for future weighted round-robin
    enabled: bool = True


# ---------------------------------------------------------------------------
# Routing metrics (simple counters for observability)
# ---------------------------------------------------------------------------

@dataclass
class RouterMetrics:
    requests: int = 0
    successes: int = 0
    failures: Dict[str, int] = field(default_factory=dict)
    latency_seconds: List[float] = field(default_factory=list)

    def record_success(self, duration: float) -> None:
        self.requests += 1
        self.successes += 1
        self.latency_seconds.append(duration)

    def record_failure(self, provider: str) -> None:
        self.requests += 1
        self.failures[provider] = self.failures.get(provider, 0) + 1

    def avg_latency(self) -> float:
        if not self.latency_seconds:
            return 0.0
        return sum(self.latency_seconds) / len(self.latency_seconds)

    def summary(self) -> Dict[str, Any]:
        return {
            "requests": self.requests,
            "successes": self.successes,
            "failures": self.failures,
            "avg_latency_s": round(self.avg_latency(), 3),
        }


# ---------------------------------------------------------------------------
# Universal Router
# ---------------------------------------------------------------------------

class UniversalRouter(LLMClient):
    """
    Routes LLM `call()` requests across multiple provider adapters.

    Implements the same LLMClient interface, so it can be passed directly to
    a SOPExecutor as the llm_client argument.

    Example
    -------
    >>> router = UniversalRouter(
    ...     routes=[
    ...         RouteConfig("ollama", OllamaAdapter(model="llama3")),
    ...         RouteConfig("openai", OpenAIAdapter(api_key="sk-...")),
    ...     ],
    ...     strategy=RouteStrategy.FALLBACK,
    ... )
    >>> result = router.call("You are a helpful assistant.", "Summarize X.")
    """

    def __init__(
        self,
        routes: List[RouteConfig],
        strategy: RouteStrategy = RouteStrategy.FALLBACK,
        health_check_on_init: bool = False,
    ):
        if not routes:
            raise ValueError("At least one route must be provided.")
        self.routes = [r for r in routes if r.enabled]
        self.strategy = strategy
        self.metrics = RouterMetrics()
        self._rr_index = 0

        if health_check_on_init:
            self._log_health_checks()

    def call(self, system_prompt: str, user_prompt: str) -> str:
        """Route a single LLM call according to the configured strategy."""
        if self.strategy == RouteStrategy.ROUND_ROBIN:
            return self._call_round_robin(system_prompt, user_prompt)
        return self._call_fallback(system_prompt, user_prompt)

    # Also expose generate() so both interfaces work
    def generate(self, prompt: str, **kwargs: Any) -> str:
        return self.call(system_prompt="", user_prompt=prompt)

    # ------------------------------------------------------------------
    # Internal routing
    # ------------------------------------------------------------------

    def _call_fallback(self, system_prompt: str, user_prompt: str) -> str:
        errors: List[str] = []
        for route in self.routes:
            t0 = time.monotonic()
            try:
                result = route.adapter.call(system_prompt, user_prompt)
                self.metrics.record_success(time.monotonic() - t0)
                logger.debug(f"[router] success via {route.provider_name}")
                return result
            except Exception as exc:
                self.metrics.record_failure(route.provider_name)
                logger.warning(f"[router] {route.provider_name} failed: {exc}")
                errors.append(f"{route.provider_name}: {exc}")

        raise RuntimeError(
            f"All {len(self.routes)} routes exhausted.\n" + "\n".join(errors)
        )

    def _call_round_robin(self, system_prompt: str, user_prompt: str) -> str:
        start = self._rr_index
        errors: List[str] = []
        for _ in range(len(self.routes)):
            route = self.routes[self._rr_index]
            self._rr_index = (self._rr_index + 1) % len(self.routes)
            t0 = time.monotonic()
            try:
                result = route.adapter.call(system_prompt, user_prompt)
                self.metrics.record_success(time.monotonic() - t0)
                logger.debug(f"[router] RR success via {route.provider_name}")
                return result
            except Exception as exc:
                self.metrics.record_failure(route.provider_name)
                logger.warning(f"[router] RR {route.provider_name} failed: {exc}")
                errors.append(f"{route.provider_name}: {exc}")

        raise RuntimeError(
            f"All {len(self.routes)} routes exhausted (round-robin).\n" + "\n".join(errors)
        )

    def _log_health_checks(self) -> None:
        for route in self.routes:
            if hasattr(route.adapter, "health_check"):
                ok = route.adapter.health_check()
                status = "OK" if ok else "UNREACHABLE"
                logger.info(f"[router] health_check {route.provider_name}: {status}")
                if not ok:
                    route.enabled = False
