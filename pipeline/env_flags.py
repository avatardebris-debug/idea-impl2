"""Shared environment flag helpers for pipeline toggles."""

from __future__ import annotations

import os


_FALSE = frozenset({"0", "false", "no", "off", ""})
_TRUE = frozenset({"1", "true", "yes", "on"})


def env_bool(name: str, *, default: bool = False) -> bool:
    """Parse a boolean env var. Empty/missing → default."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    val = raw.strip().lower()
    if val in _TRUE:
        return True
    if val in _FALSE:
        return False
    return default


def env_float(name: str, *, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def env_int(name: str, *, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or not str(raw).strip():
        return default
    try:
        return int(str(raw).strip())
    except ValueError:
        return default
