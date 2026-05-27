"""
pipeline/kv_cache.py — Ollama KV-cache reuse for prompt prefix caching.

Wraps the Ollama /api/generate endpoint to reuse the model's KV cache
between calls within the same project. The system prompt (role definition,
tool descriptions) is tokenised ONCE per project per session; subsequent
calls pass back the cached context token IDs and skip re-tokenising the
prefix. This eliminates ~30-40% of prompt token processing per agent call.

Usage (in agent_process.py or agent.py):
    from pipeline.kv_cache import OllamaKVCache
    cache = OllamaKVCache()                       # singleton, one per process
    response = cache.generate(
        model="qwen3:6b",
        system=system_prompt,                     # the heavy, static prefix
        prompt=user_message,                      # the lightweight, changing part
        slug="video_pow",                         # project key for cache namespacing
        options={"temperature": 0.4, "num_ctx": 16384},
    )

Cache invalidation:
    - Per (model, slug, hash(system)) key
    - Evicted automatically when the slug's workspace changes (mtime check)
    - Max 8 entries in memory (LRU) to bound RAM usage

PufferLib parallel:
    This is equivalent to PufferLib's KV-cache for observations: "environments
    write observations directly to the buffers used for training" — we skip the
    re-encoding cost by reusing the already-computed prefix representation.
"""
from __future__ import annotations

import hashlib
import json as _json
import os
import pathlib
import threading
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from typing import Any

_PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
from pipeline.paths import get_pipeline_dir

_OLLAMA_BASE = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
_DEFAULT_TIMEOUT = 600   # seconds — long enough for a 16k context generation


class OllamaKVCache:
    """Thread-safe Ollama KV-cache wrapper with LRU eviction.

    Safe to share across threads (one lock per entry operation).
    """

    MAX_ENTRIES = 8

    def __init__(self, base_url: str = _OLLAMA_BASE) -> None:
        self._base = base_url.rstrip("/")
        self._cache: OrderedDict[str, dict] = OrderedDict()   # key -> {context, mtime_slug}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        model: str,
        system: str,
        prompt: str,
        slug: str = "",
        options: dict | None = None,
        stream: bool = False,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> dict:
        """Call /api/generate with KV-cache reuse.

        Returns the full Ollama response dict (same as raw API).
        The 'context' field is saved and reused on subsequent calls.
        """
        cache_key = self._make_key(model, system, slug)
        cached_ctx = self._get_context(cache_key, slug)

        payload: dict[str, Any] = {
            "model":      model,
            "prompt":     prompt,
            "system":     system,
            "stream":     stream,
            "options":    options or {},
            "keep_alive": -1,   # pin model in VRAM between steps
        }
        if cached_ctx:
            # Pass cached context → server skips re-encoding the system prefix
            payload["context"] = cached_ctx

        raw_bytes = _json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base}/api/generate",
            data=raw_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = _json.loads(r.read().decode("utf-8"))

        # Save returned context for next call
        if "context" in data and data["context"]:
            self._put_context(cache_key, data["context"], slug)

        return data

    def invalidate(self, slug: str) -> int:
        """Evict all cache entries for a given project slug. Returns count evicted."""
        with self._lock:
            keys_to_del = [k for k in self._cache if f":{slug}:" in k]
            for k in keys_to_del:
                del self._cache[k]
            return len(keys_to_del)

    def clear(self) -> None:
        """Clear all cached contexts."""
        with self._lock:
            self._cache.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_key(model: str, system: str, slug: str) -> str:
        sys_hash = hashlib.md5(system.encode(), usedforsecurity=False).hexdigest()[:12]
        return f"{model}:{slug}:{sys_hash}"

    def _workspace_mtime(self, slug: str) -> float:
        """Return latest mtime across the project workspace (or 0 if not found)."""
        ws = get_pipeline_dir() / "projects" / slug / "workspace"
        if not ws.exists():
            return 0.0
        try:
            mtimes = [f.stat().st_mtime for f in ws.rglob("*") if f.is_file()]
            return max(mtimes) if mtimes else 0.0
        except Exception:
            return 0.0

    def _get_context(self, key: str, slug: str) -> list | None:
        """Return cached context if still valid, else None."""
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            # Invalidate if workspace changed since we cached
            if slug:
                cur_mtime = self._workspace_mtime(slug)
                if cur_mtime > entry.get("mtime", 0.0):
                    del self._cache[key]
                    return None
            # LRU: move to end
            self._cache.move_to_end(key)
            return entry["context"]

    def _put_context(self, key: str, context: list, slug: str) -> None:
        """Store context, evicting oldest entry if at capacity."""
        with self._lock:
            self._cache[key] = {
                "context": context,
                "mtime": self._workspace_mtime(slug) if slug else 0.0,
                "saved_at": time.time(),
            }
            self._cache.move_to_end(key)
            # Evict oldest if over capacity
            while len(self._cache) > self.MAX_ENTRIES:
                self._cache.popitem(last=False)


# ---------------------------------------------------------------------------
# Module-level singleton — import once, share across all agent instances
# ---------------------------------------------------------------------------
_kv_cache: OllamaKVCache | None = None
_kv_lock = threading.Lock()


def get_cache() -> OllamaKVCache:
    """Return the process-level KV cache singleton."""
    global _kv_cache
    if _kv_cache is None:
        with _kv_lock:
            if _kv_cache is None:
                _kv_cache = OllamaKVCache()
    return _kv_cache


# ---------------------------------------------------------------------------
# Convenience invalidation hook — call from executor after writing workspace
# ---------------------------------------------------------------------------

def invalidate_on_write(slug: str) -> None:
    """
    Invalidate the KV-cache for a project slug after the executor writes files.

    The validator and reviewer must NOT inherit the executor's cached prefix —
    their system prompts differ, so they always get a fresh encoding anyway.
    But we also drop the executor's own entry so the next retry cycle starts
    with a clean slate (avoids inheriting a prefix from a bad code state).

    Usage in executor (agents/executor.py), after writing workspace files:
        from pipeline.kv_cache import invalidate_on_write
        invalidate_on_write(self._current_slug)
    """
    try:
        get_cache().invalidate(slug)
    except Exception:
        pass  # non-critical — never block the executor for a cache op
