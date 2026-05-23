"""
pipeline/pipeline_mode.py
Runtime mode flags for the idea pipeline.

--legacy on runner.py sets PIPELINE_LEGACY=1 so subprocess agents keep the
pre-registry behavior (reusable_tools.md only, no capability registry injection).
"""

from __future__ import annotations

import os


def legacy_mode() -> bool:
    """True when runner was started with --legacy."""
    return os.environ.get("PIPELINE_LEGACY", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def set_legacy_mode(enabled: bool) -> None:
    if enabled:
        os.environ["PIPELINE_LEGACY"] = "1"
    else:
        os.environ.pop("PIPELINE_LEGACY", None)
