"""Project-wide configuration for the drop_servicing_tool package.

All path constants are evaluated lazily so that environment variable
overrides set by test fixtures (or at runtime) take effect.
"""

from __future__ import annotations

import os
from pathlib import Path

# Base directory of the package
_PACKAGE_DIR = Path(__file__).resolve().parent

# Default paths
_DEFAULT_SOPS_DIR = _PACKAGE_DIR.parent / "sops"
_DEFAULT_PROMPTS_DIR = _PACKAGE_DIR.parent / "prompts"
_DEFAULT_OUTPUT_DIR = _PACKAGE_DIR.parent / "output"


def _get_dir(env_key: str, default: Path) -> Path:
    """Return the directory for *env_key*, falling back to *default*."""
    val = os.environ.get(env_key)
    if val:
        return Path(val)
    return default


# ── Lazy path accessors ────────────────────────────────────────────────

def get_sops_dir() -> Path:
    """Return the SOPs directory, resolved lazily from env or default."""
    return _get_dir("DST_SOPS_DIR", _DEFAULT_SOPS_DIR)


def get_prompts_dir() -> Path:
    """Return the prompts directory, resolved lazily from env or default."""
    return _get_dir("DST_PROMPTS_DIR", _DEFAULT_PROMPTS_DIR)


def get_output_dir() -> Path:
    """Return the output directory, resolved lazily from env or default."""
    return _get_dir("DST_OUTPUT_DIR", _DEFAULT_OUTPUT_DIR)


# ── Module-level constants (evaluated at import time) ───────
# These use the lazy accessors but are evaluated once at import time.
# For dynamic env var support, use the getter functions instead.
OUTPUT_DIR = get_output_dir()
SOPS_DIR = get_sops_dir()
PROMPTS_DIR = get_prompts_dir()


# ── LLM settings (defaults — can be overridden via env vars) ───────

LLM_PROVIDER = os.environ.get("DST_LLM_PROVIDER", "openai")
LLM_MODEL = os.environ.get("DST_LLM_MODEL", "gpt-4o-mini")
LLM_API_KEY = os.environ.get("DST_LLM_API_KEY", "")
