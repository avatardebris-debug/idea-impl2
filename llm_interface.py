"""
llm_interface.py
Model-agnostic LLM adapter layer.

Swap providers with a single string:
    llm = get_llm("openai")
    llm = get_llm("claude")
    llm = get_llm("gemini")
    llm = get_llm("ollama", model="qwen3.6:35b-a3b-q4_K_M")
    llm = get_llm("grok", model="grok-3")   # requires XAI_API_KEY env var
"""

from __future__ import annotations
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL


def _ollama_http_timeout_s() -> int:
    """Wall-clock seconds to wait for Ollama HTTP response (cloud 35B needs headroom)."""
    raw = os.environ.get("OLLAMA_HTTP_TIMEOUT", "900")
    try:
        return max(60, int(raw))
    except ValueError:
        return 900


# ---------------------------------------------------------------------------
# Shared response dataclass — provider-neutral
# ---------------------------------------------------------------------------

@dataclass
class TokenUsage:
    """Token usage statistics from a single LLM call."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tokens_per_second: float = 0.0   # output tok/s (Ollama only; 0 for cloud providers)


@dataclass
class Message:
    role: str                        # "assistant" | "tool"
    content: str = ""
    tool_calls: list[dict] = field(default_factory=list)   # [{name, args}]
    usage: TokenUsage | None = None


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class LLMBase(ABC):
    """All providers must implement this single method."""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> Message:
        """Send messages and return a normalised Message."""


# ---------------------------------------------------------------------------
# OpenAI  (pip install openai)
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
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature
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
                import json
                tool_calls.append({
                    "id": tc.id,
                    "name": tc.function.name,
                    "args": json.loads(tc.function.arguments),
                })

        # Extract token usage
        usage = None
        if hasattr(resp, 'usage') and resp.usage:
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
# Anthropic / Claude  (pip install anthropic)
# ---------------------------------------------------------------------------

class ClaudeAdapter(LLMBase):
    def __init__(self, model: str = "claude-opus-4-5", temperature: float = 0.7):
        try:
            import anthropic
        except ImportError:
            raise ImportError("pip install anthropic")
        self.client = anthropic.Anthropic()
        self.model = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import anthropic

        # Claude keeps system separate
        system = ""
        filtered = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        kwargs: dict[str, Any] = dict(
            model=self.model,
            max_tokens=4096,
            messages=filtered,
            temperature=self.temperature,
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [
                {
                    "name": t["name"],
                    "description": t.get("description", ""),
                    "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
                }
                for t in tools
            ]

        resp = self.client.messages.create(**kwargs)

        tool_calls = []
        text = ""
        for block in resp.content:
            if block.type == "text":
                text += block.text
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "args": block.input,
                })

        # Extract token usage
        usage = None
        if hasattr(resp, 'usage') and resp.usage:
            usage = TokenUsage(
                prompt_tokens=getattr(resp.usage, 'input_tokens', 0),
                completion_tokens=getattr(resp.usage, 'output_tokens', 0),
                total_tokens=(getattr(resp.usage, 'input_tokens', 0)
                              + getattr(resp.usage, 'output_tokens', 0)),
            )

        return Message(role="assistant", content=text, tool_calls=tool_calls, usage=usage)


# ---------------------------------------------------------------------------
# Google Gemini  (pip install google-generativeai)
# ---------------------------------------------------------------------------

class GeminiAdapter(LLMBase):
    def __init__(self, model: str = "gemini-1.5-pro", temperature: float = 0.7):
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError("pip install google-generativeai")
        import os
        genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
        self.genai = genai
        self.model_name = model
        self.temperature = temperature

    def chat(self, messages, tools=None) -> Message:
        import json

        # Convert messages to Gemini format
        history = []
        system_instruction = None
        for m in messages:
            if m["role"] == "system":
                system_instruction = m["content"]
            elif m["role"] == "user":
                history.append({"role": "user", "parts": [m["content"]]})
            elif m["role"] == "assistant":
                history.append({"role": "model", "parts": [m["content"]]})

        generation_config = self.genai.types.GenerationConfig(
            temperature=self.temperature
        )
        model = self.genai.GenerativeModel(
            self.model_name,
            system_instruction=system_instruction,
            generation_config=generation_config,
        )
        chat = model.start_chat(history=history[:-1] if history else [])
        last_user = history[-1]["parts"][0] if history else ""

        resp = chat.send_message(last_user)

        # Extract token usage from Gemini
        usage = None
        if hasattr(resp, 'usage_metadata') and resp.usage_metadata:
            um = resp.usage_metadata
            usage = TokenUsage(
                prompt_tokens=getattr(um, 'prompt_token_count', 0),
                completion_tokens=getattr(um, 'candidates_token_count', 0),
                total_tokens=getattr(um, 'total_token_count', 0),
            )

        return Message(role="assistant", content=resp.text, tool_calls=[], usage=usage)


# ---------------------------------------------------------------------------
# Ollama  (no pip dependency — uses stdlib urllib against the REST API)
# ---------------------------------------------------------------------------

class OllamaAdapter(LLMBase):
    """
    Talks to Ollama via its REST API directly (no SDK).

    This avoids the ollama Python SDK's Pydantic validation, which crashes
    when models like Qwen3.5 return tool-call arguments as a JSON string
    instead of a pre-parsed dict.
    """

    def __init__(
        self,
        model: str = DEFAULT_PIPELINE_MODEL,
        temperature: float = 0.2,
        base_url: str | None = None,
        num_ctx: int = 16384,
        think: bool | None = None,
        slug: str = "",
    ):
        self.model = model
        self.temperature = temperature
        self.base_url = (base_url or "http://localhost:11434").rstrip("/")
        self.num_ctx = num_ctx
        self.think = think   # None=model default, False=no CoT, True=force CoT
        self.slug = slug     # project slug for KV-cache namespacing; "" = no cache
        # Per-adapter context store: {cache_key -> context list}
        # Populated by kv_cache module; lives for the lifetime of this adapter instance.
        self._kv_slug_active: bool = bool(slug)
        # Last Ollama singleflight lock wait (ms); set inside chat()
        self._last_lock_wait_ms: float = 0.0

    def _normalize_messages(self, messages: list[dict]) -> list[dict]:
        """
        Ollama requires tool_call arguments as dicts, not JSON strings.
        agent.py stores them as json.dumps() strings (OpenAI convention).
        Convert before sending.
        """
        import json as _json
        normalized = []
        for msg in messages:
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                fixed_tcs = []
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    args = fn.get("arguments", {})
                    if isinstance(args, str):
                        try:
                            args = _json.loads(args)
                        except _json.JSONDecodeError:
                            args = {"raw": args}
                    fixed_tcs.append({
                        "id": tc.get("id", ""),
                        "function": {
                            "name": fn.get("name", ""),
                            "arguments": args,   # must be dict for Ollama
                        },
                    })
                msg = dict(msg, tool_calls=fixed_tcs)
            normalized.append(msg)
        return normalized

    def _ollama_is_alive(self) -> bool:
        """Check if Ollama server is reachable."""
        import urllib.request
        import urllib.error
        try:
            with urllib.request.urlopen(f"{self.base_url}/api/tags", timeout=10) as r:
                return r.status == 200
        except Exception:
            return False

    def _try_restart_ollama(self) -> None:
        """Best-effort attempt to restart the Ollama server process."""
        import subprocess
        import time
        import logging
        log = logging.getLogger(__name__)
        try:
            subprocess.run(["pkill", "-f", "ollama serve"], capture_output=True)
            time.sleep(3)
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            log.warning("OllamaAdapter: attempted ollama serve restart")
            time.sleep(8)  # give it time to come up
        except Exception as exc:
            log.warning("OllamaAdapter: restart attempt failed: %s", exc)

    def chat(self, messages, tools=None, *, request_timeout: int | None = None) -> Message:
        import json as _json
        import time
        import logging
        import urllib.request
        import urllib.error

        log = logging.getLogger(__name__)
        timeout_s = request_timeout if request_timeout is not None else _ollama_http_timeout_s()
        max_retries = 0 if request_timeout is not None else 5

        options: dict[str, Any] = {
            "temperature": self.temperature,
            "num_ctx": self.num_ctx,
        }

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": self._normalize_messages(messages),
            "stream": False,
            "options": options,
            "keep_alive": -1,   # pin model in VRAM; prevents Ollama from unloading between calls
        }
        # think is a top-level field in Ollama API, NOT inside options
        if self.think is not None:
            payload["think"] = self.think
        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]

        data = _json.dumps(payload).encode("utf-8")

        # --------------- KV-cache fast path --------------------------------
        # When a project slug is set and the request has no tool calls in the
        # message history, use /api/generate with context reuse instead of
        # /api/chat.  This skips re-tokenising the static system prefix on
        # every step of the ReAct loop (~30-40% of prompt tokens).
        #
        # We fall back to /api/chat (no cache) when:
        #   - No slug is set (standalone usage)
        #   - The messages contain tool_calls (multi-turn tool history needs
        #     the full message structure that /api/generate doesn't support)
        _has_tool_history = any(
            m.get("role") == "tool" or (m.get("role") == "assistant" and m.get("tool_calls"))
            for m in messages
        )
        _use_kv_cache = self._kv_slug_active and not _has_tool_history and not tools
        _kv_resp: dict | None = None

        if _use_kv_cache:
            try:
                from pipeline.kv_cache import get_cache as _get_kv_cache
                from pipeline.ollama_lock import ollama_singleflight

                _cache = _get_kv_cache()
                # Extract system + last user message for /api/generate
                _system = next(
                    (m["content"] for m in messages if m.get("role") == "system"), ""
                )
                _user = next(
                    (m["content"] for m in reversed(messages) if m.get("role") == "user"), ""
                )
                _kv_opts = {
                    "temperature": self.temperature,
                    "num_ctx": self.num_ctx,
                }
                if self.think is not None:
                    _kv_opts["think"] = self.think  # type: ignore[assignment]
                with ollama_singleflight() as _wait_ms:
                    self._last_lock_wait_ms = float(_wait_ms or 0)
                    _kv_resp = _cache.generate(
                        model=self.model,
                        system=_system,
                        prompt=_user,
                        slug=self.slug,
                        options=_kv_opts,
                        timeout=timeout_s,
                    )
            except Exception:
                _kv_resp = None  # fall back to /api/chat on any error

        # Retry with exponential backoff for transient Ollama failures (OOM/EOF/500)
        backoff = 30  # seconds — start at 30s, double each attempt
        last_error: Exception | None = None

        # If KV-cache path returned a result, skip the /api/chat round-trip
        if _kv_resp is not None:
            raw = _kv_resp
            # /api/generate wraps the response in 'response' (string), not 'message'
            # Normalise to the same structure that the /api/chat path produces.
            raw["message"] = {"content": raw.get("response", ""), "role": "assistant"}
        else:
            from pipeline.ollama_lock import ollama_singleflight

            for attempt in range(max_retries + 1):
                req = urllib.request.Request(
                    f"{self.base_url}/api/chat",
                    data=data,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                try:
                    with ollama_singleflight() as _wait_ms:
                        self._last_lock_wait_ms = float(_wait_ms or 0)
                        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                            raw = _json.loads(resp.read().decode("utf-8"))
                    break  # success — exit retry loop

                except urllib.error.HTTPError as e:
                    body = e.read().decode("utf-8", errors="replace")[:400]
                    last_error = RuntimeError(f"Ollama HTTP {e.code}: {body}")
                    # Only retry on 500 (crash/OOM) — surface 4xx immediately
                    if e.code != 500:
                        raise last_error from e

                except urllib.error.URLError as e:
                    last_error = RuntimeError(f"Ollama connection failed: {e}")

                # Retry path — check health and wait
                if attempt < max_retries:
                    wait = min(backoff * (2 ** attempt), 300)  # cap at 5 min
                    log.warning(
                        "OllamaAdapter: attempt %d/%d failed (%s) — waiting %ds before retry",
                        attempt + 1, max_retries, last_error, wait,
                    )
                    time.sleep(wait)
                    if not self._ollama_is_alive():
                        log.warning("OllamaAdapter: Ollama appears down — attempting restart")
                        self._try_restart_ollama()
                        # Wait for model to load back into VRAM
                        time.sleep(15)
                else:
                    raise last_error  # all retries exhausted


        msg = raw.get("message", {})
        # For thinking models (Qwen3, DeepSeek-R1), the visible response may be
        # in 'content' OR 'thinking'. When think=True, reasoning goes in thinking
        # and the final answer in content. When both are present, combine them.
        thinking = msg.get("thinking", "") or ""
        content  = msg.get("content",  "") or ""
        # If content is empty but thinking has output, the model responded via CoT
        if not content and thinking:
            content = thinking

        # Parse tool calls — arguments may be a string or already a dict
        tool_calls = []
        for tc in msg.get("tool_calls", []) or []:
            fn = tc.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = _json.loads(args)
                except _json.JSONDecodeError:
                    args = {"raw": args}
            tool_calls.append({
                "id": f"ollama_{name}_{len(tool_calls)}",
                "name": name,
                "args": args,
            })

        # Token usage — Ollama returns eval_count (output tokens) and
        # eval_duration (nanoseconds spent generating output tokens).
        # Dividing gives real tok/s which we surface in the runner status line.
        usage = None
        prompt_tokens = raw.get("prompt_eval_count", 0) or 0
        completion_tokens = raw.get("eval_count", 0) or 0
        eval_duration_ns = raw.get("eval_duration", 0) or 0
        tps = 0.0
        if completion_tokens > 0 and eval_duration_ns > 0:
            tps = completion_tokens / (eval_duration_ns / 1e9)
        if prompt_tokens or completion_tokens:
            usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
                tokens_per_second=round(tps, 1),
            )
            # Write throughput to a shared state file so the runner (a separate
            # process) can display tok/s without needing inter-process comms.
            # We accumulate cumulative_tokens, cumulative_inference_s, and
            # cumulative_wall_s so the runner can show both GPU-only tok/s and
            # overall pipeline tok/s (tokens / total wall-clock time).
            try:
                import pathlib as _pl, json as _js, time as _t
                from pipeline.paths import state_dir
                _tp_path = state_dir() / "throughput.json"
                _tp_path.parent.mkdir(parents=True, exist_ok=True)
                _now = _t.time()
                # Read-modify-write (best-effort; telemetry only)
                try:
                    _existing = _js.loads(_tp_path.read_text(encoding="utf-8"))
                except Exception:
                    _existing = {}
                _first = _existing.get("first_call_at", _now)
                _existing.update({
                    "tps":                   round(tps, 1),
                    "completion_tokens":     completion_tokens,
                    "prompt_tokens":         prompt_tokens,
                    "updated_at":            _now,
                    "first_call_at":         _first,
                    # Cumulative counters (additive across all agent calls)
                    "cumulative_tokens":     _existing.get("cumulative_tokens", 0) + completion_tokens,
                    "cumulative_inference_s": round(
                        _existing.get("cumulative_inference_s", 0.0) + (eval_duration_ns / 1e9), 2
                    ),
                    "cumulative_wall_s":     round(_now - _first, 1),
                    "call_count":            _existing.get("call_count", 0) + 1,
                    # tool_s is written by agent.py execute_tool(); preserve here
                    "cumulative_tool_s":     _existing.get("cumulative_tool_s", 0.0),
                    "tool_call_count":       _existing.get("tool_call_count", 0),
                })
                _tp_path.write_text(_js.dumps(_existing, indent=2), encoding="utf-8")
            except Exception:
                pass  # non-critical — never break inference for a metric write

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

    def chat(self, messages, tools=None, *, request_timeout: int | None = None) -> Message:
        import json
        kwargs: dict[str, Any] = dict(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        if request_timeout is not None:
            kwargs["timeout"] = float(request_timeout)
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
    slug: str = "",
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
        if slug:
            kwargs["slug"] = slug
    return cls(**kwargs)

