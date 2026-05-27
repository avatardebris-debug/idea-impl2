"""
pipeline/rolling_context.py — Rolling N-step context window per agent per project.

Stores the last N prompt/response exchange pairs per (agent_role, project_slug)
so agents can load recent context without re-reading all workspace files.

PufferLib parallel: trajectory segment window (n-step lookback).
Instead of one-step myopic processing (read files → generate → write files),
agents maintain a rolling N-step window of prior exchanges, giving the model
continuity across calls without re-assembling full context from disk each time.

Usage:
    from pipeline.rolling_context import RollingContext, get_context_store

    store = get_context_store()                         # process singleton

    # After each agent call:
    store.push(slug="video_pow", role="executor",
               prompt=task_prompt, response=llm_response)

    # Before the next agent call:
    recent = store.get_recent(slug="video_pow", role="executor", n=3)
    # recent is a list of {"prompt": ..., "response": ..., "timestamp": ...}
    # Inject into system prompt as compressed prior context.

Storage:
    Persisted to .pipeline/projects/<slug>/state/rolling_context.json
    so it survives agent restarts. Each file is small (3 exchanges × ~4k chars).
"""
from __future__ import annotations

import json
import pathlib
import threading
import time
from typing import Any

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
from pipeline.paths import get_pipeline_dir

_DEFAULT_N = 3          # exchanges to retain per (role, slug)
_MAX_CHARS  = 8000      # max chars per exchange (prompt + response) to prevent bloat


def _truncate(s: str, max_chars: int = _MAX_CHARS) -> str:
    if len(s) > max_chars:
        return s[:max_chars] + "\n...[truncated]"
    return s


class RollingContext:
    """Thread-safe rolling context window store."""

    def __init__(self, n: int = _DEFAULT_N) -> None:
        self._n = n
        self._lock = threading.Lock()
        # In-memory cache of recently pushed exchanges
        # {slug: {role: [exchange, ...]}}  (list is ordered oldest→newest)
        self._mem: dict[str, dict[str, list[dict]]] = {}

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def push(
        self,
        slug: str,
        role: str,
        prompt: str,
        response: str,
        metadata: dict | None = None,
    ) -> None:
        """Append an exchange to the rolling window, persisting to disk."""
        entry = {
            "timestamp": time.time(),
            "prompt":    _truncate(prompt),
            "response":  _truncate(response),
        }
        if metadata:
            entry["meta"] = metadata

        with self._lock:
            slug_ctx = self._mem.setdefault(slug, {})
            window = slug_ctx.setdefault(role, [])
            window.append(entry)
            # Keep only last N
            if len(window) > self._n:
                slug_ctx[role] = window[-self._n:]
            # Persist
            self._save(slug)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_recent(
        self,
        slug: str,
        role: str,
        n: int | None = None,
    ) -> list[dict]:
        """Return the last n exchanges for (slug, role).

        Loads from disk on first access (cache miss).
        Returns [] if no history exists.
        """
        with self._lock:
            if slug not in self._mem:
                self._load(slug)
            window = self._mem.get(slug, {}).get(role, [])
            limit = n or self._n
            return list(window[-limit:])

    def format_for_prompt(
        self,
        slug: str,
        role: str,
        n: int | None = None,
        separator: str = "\n\n---\n\n",
    ) -> str:
        """Return recent exchanges formatted as a compact context block for injection.

        Format:
            [Prior exchange 1 — 3m ago]
            PROMPT: ...
            RESPONSE: ...
            [Prior exchange 2 — 1m ago]
            ...
        """
        exchanges = self.get_recent(slug, role, n)
        if not exchanges:
            return ""
        now = time.time()
        parts = []
        for i, ex in enumerate(exchanges, 1):
            age = now - ex.get("timestamp", now)
            age_str = f"{int(age // 60)}m ago" if age >= 60 else f"{int(age)}s ago"
            parts.append(
                f"[Prior exchange {i} — {age_str}]\n"
                f"PROMPT: {ex['prompt'][:1200]}\n"
                f"RESPONSE: {ex['response'][:2000]}"
            )
        return separator.join(parts)

    def invalidate(self, slug: str) -> None:
        """Evict all memory for a slug (e.g. when project moves to a new phase)."""
        with self._lock:
            self._mem.pop(slug, None)
            self._state_file(slug).unlink(missing_ok=True)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    @staticmethod
    def _state_file(slug: str) -> pathlib.Path:
        return get_pipeline_dir() / "projects" / slug / "state" / "rolling_context.json"

    def _save(self, slug: str) -> None:
        """Persist current in-memory window for slug to disk (call under lock)."""
        try:
            sf = self._state_file(slug)
            sf.parent.mkdir(parents=True, exist_ok=True)
            sf.write_text(json.dumps(self._mem.get(slug, {}), indent=2), encoding="utf-8")
        except Exception:
            pass  # non-critical

    def _load(self, slug: str) -> None:
        """Load persisted window for slug into memory (call under lock)."""
        try:
            sf = self._state_file(slug)
            if sf.exists():
                data = json.loads(sf.read_text(encoding="utf-8"))
                # Trim to current N in case N changed between runs
                for role, window in data.items():
                    if isinstance(window, list):
                        data[role] = window[-self._n:]
                self._mem[slug] = data
            else:
                self._mem[slug] = {}
        except Exception:
            self._mem[slug] = {}


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_store: RollingContext | None = None
_store_lock = threading.Lock()


def get_context_store(n: int = _DEFAULT_N) -> RollingContext:
    """Return the process-level rolling context singleton."""
    global _store
    if _store is None:
        with _store_lock:
            if _store is None:
                _store = RollingContext(n=n)
    return _store
