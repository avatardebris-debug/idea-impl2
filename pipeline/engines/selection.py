"""Engine selection: env default, per-project override, seed canary."""

from __future__ import annotations

import os
import random
from typing import Any

from pipeline.env_flags import env_float

ENGINE_CLASSIC = "classic"
ENGINE_GROK_BUILD = "grok_build"

_VALID = frozenset({ENGINE_CLASSIC, ENGINE_GROK_BUILD})


def normalize_engine(value: str | None) -> str:
    raw = (value or "").strip().lower()
    if raw in _VALID:
        return raw
    return ENGINE_CLASSIC


def pipeline_engine_env() -> str:
    """Global PIPELINE_ENGINE (classic when unset / unknown)."""
    return normalize_engine(os.environ.get("PIPELINE_ENGINE", ENGINE_CLASSIC))


def get_project_engine(state: dict[str, Any] | None) -> str:
    """Per-project engine from state. Defaults to classic.

    ``state["engine"]`` wins over env for in-flight projects.
    After fallback, engine is rewritten to classic so this stays honest.
    """
    if not state:
        return ENGINE_CLASSIC
    eng = normalize_engine(state.get("engine"))
    return eng


def resolve_seed_engine(*, rng: random.Random | None = None) -> str:
    """Engine for **new seeds only**.

    - ``PIPELINE_ENGINE=grok_build`` → always grok_build
    - else optional canary ``PIPELINE_ENGINE_GROK_FRACTION`` in [0, 1]
    - else classic
    """
    env = (os.environ.get("PIPELINE_ENGINE") or "").strip().lower()
    if env == ENGINE_GROK_BUILD:
        return ENGINE_GROK_BUILD

    frac = env_float("PIPELINE_ENGINE_GROK_FRACTION", default=0.0)
    if frac < 0.0:
        frac = 0.0
    if frac > 1.0:
        frac = 1.0
    if frac > 0.0:
        r = rng if rng is not None else random
        if r.random() < frac:
            return ENGINE_GROK_BUILD
    return ENGINE_CLASSIC


def force_engine_classic(state: dict[str, Any]) -> dict[str, Any]:
    """Mutate state to classic (operator / fallback). Returns state."""
    state["engine"] = ENGINE_CLASSIC
    return state
