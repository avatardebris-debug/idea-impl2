"""
Resolve which LLM backend to use for one-shot factory tools (deconstructor, etc.).

Policy matches Hermes / COMMANDS.md (device-aware):
  1. Load project .env (without overwriting existing process env).
  2. If provider is explicit (not auto) → honor it (map xai→grok; fix Ollama-only model names on xAI).
  3. Else prefer Ollama when PIPELINE_MODEL (or override) is actually in /api/tags.
  4. Else if XAI_API_KEY or GROK_API_KEY → provider=grok + grok-* model.
  5. Else raise with a clear error.

Cloud instances often set PIPELINE_PROVIDER=ollama + qwen. This workstation
typically has XAI_API_KEY in .env and may only have a tiny/wrong Ollama tag.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

_DEFAULT_XAI_MODEL = "grok-3"
_DOTENV_LOADED = False


def project_root() -> Path:
    try:
        from pipeline.pipeline_config import PROJECT_ROOT

        return Path(PROJECT_ROOT)
    except Exception:
        return Path(__file__).resolve().parent.parent


def ensure_project_dotenv(*, force: bool = False) -> bool:
    """Load PROJECT_ROOT/.env into os.environ if keys are missing. Returns True if file read."""
    global _DOTENV_LOADED
    if _DOTENV_LOADED and not force:
        return False
    env_path = project_root() / ".env"
    if not env_path.is_file():
        _DOTENV_LOADED = True
        return False
    rx = re.compile(r"^\s*(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*[\"']?(.*?)[\"']?\s*$")
    try:
        text = env_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        _DOTENV_LOADED = True
        return False
    for line in text.splitlines():
        if not line.strip() or line.strip().startswith("#"):
            continue
        m = rx.match(line)
        if not m:
            continue
        k, v = m.group(1), m.group(2)
        # Do not clobber secrets already set in the shell
        if k not in os.environ or not str(os.environ.get(k) or "").strip():
            os.environ[k] = v
    _DOTENV_LOADED = True
    return True


def xai_api_key() -> str:
    ensure_project_dotenv()
    return (
        os.environ.get("XAI_API_KEY", "").strip()
        or os.environ.get("GROK_API_KEY", "").strip()
    )


def _looks_like_xai_model(name: str) -> bool:
    n = (name or "").strip().lower()
    return n.startswith("grok-") and ":" not in n


def resolve_xai_model(configured: str = "") -> str:
    env = (
        os.environ.get("DECONSTRUCTOR_GROK_MODEL", "").strip()
        or os.environ.get("HERMES_GROK_MODEL", "").strip()
        or os.environ.get("PIPELINE_GROK_MODEL", "").strip()
    )
    if env:
        return env
    if _looks_like_xai_model(configured):
        return configured.strip()
    return _DEFAULT_XAI_MODEL


def resolve_pipeline_llm(
    provider: str | None = None,
    model: str | None = None,
    *,
    ollama_check: Any = None,
    soft_ollama: bool = False,
) -> tuple[str, str, str]:
    """Return (provider, model, reason).

    Raises ValueError when no backend can run.

    soft_ollama:
      When True, provider ``ollama`` (or empty/auto) is treated as preference only:
      if the Ollama model is missing, fall through to xAI when a key is present.
      When False, explicit ``ollama`` stays ollama even if the model is absent
      (caller will 404 — useful for force-local).
    """
    ensure_project_dotenv()

    p = (provider or "").strip().lower()
    m = (model or "").strip()

    # Soft: treat bare ollama as auto (device-aware default for this workstation)
    if soft_ollama and p in ("", "auto", "default", "any", "ollama"):
        p = ""

    # Explicit provider from CLI / caller (not auto)
    if p and p not in ("auto", "default", "any"):
        if p in ("xai", "grok"):
            return "grok", resolve_xai_model(m), "explicit provider=grok/xai"
        if p == "ollama":
            from pipeline.pipeline_config import DEFAULT_PIPELINE_MODEL

            use_m = m or os.environ.get("PIPELINE_MODEL", "").strip() or DEFAULT_PIPELINE_MODEL
            return "ollama", use_m, "explicit provider=ollama"
        # openai / claude / gemini etc.
        if not m:
            raise ValueError(f"provider={p} requires an explicit model")
        return p, m, f"explicit provider={p}"

    # Auto: same policy as Hermes
    from pipeline.hermes_runner import resolve_hermes_route

    route = resolve_hermes_route(model=m or None, provider=None, ollama_check=ollama_check)
    if route.action == "run":
        return route.provider, route.model, route.reason or route.log_label or "hermes route"

    # Hermes skip — double-check key after dotenv (hermes may have run before .env)
    key = xai_api_key()
    if key:
        return "grok", resolve_xai_model(m), "fallback xai/grok (ollama model unavailable)"

    raise ValueError(
        "No LLM backend available: Ollama does not have the configured model, "
        "and XAI_API_KEY / GROK_API_KEY is not set (checked process env and project .env). "
        "Set --provider grok --model grok-3, or install the Ollama model, or put XAI_API_KEY in .env."
    )


def apply_llm_route(
    provider: str | None = None,
    model: str | None = None,
    *,
    soft_ollama: bool = True,
    ollama_check: Any = None,
    set_environ: bool = False,
) -> tuple[str, str, str]:
    """Resolve and optionally publish PIPELINE_PROVIDER / PIPELINE_MODEL for children."""
    p, m, reason = resolve_pipeline_llm(
        provider, model, soft_ollama=soft_ollama, ollama_check=ollama_check
    )
    if set_environ:
        os.environ["PIPELINE_PROVIDER"] = p
        os.environ["PIPELINE_MODEL"] = m
    return p, m, reason
