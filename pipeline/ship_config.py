"""Ship-prove env helpers."""

from __future__ import annotations

import os


def skip_thermo_review() -> bool:
    return os.environ.get("SHIP_SKIP_THERMO", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def max_debug_loops() -> int:
    try:
        return max(1, int(os.environ.get("MAX_DEBUG_LOOPS", "3")))
    except ValueError:
        return 3
