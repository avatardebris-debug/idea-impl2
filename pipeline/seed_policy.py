"""
pipeline/seed_policy.py
Unified handling when seed_from_master_list returns _SEED_EMPTY.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.run_context import RunContext

if TYPE_CHECKING:
    from pipeline.message_bus import MessageBus


class SeedEmptyAction(str, Enum):
    CONTINUE = "continue"
    STOP = "stop"
    IDEATE = "ideate"
    RETRY_IDEATION = "retry_ideation"


def on_seed_empty(
    ctx: RunContext,
    bus: "MessageBus",
    *,
    seeded_session: set[str],
    ideation_in_progress: bool,
    ideation_timed_out: bool,
) -> SeedEmptyAction:
    if ctx.mode == "polish" and ctx.polish_path:
        from pipeline.polish_mode import handle_polish_idle
        from pipeline.polish_status import print_polish_lifecycle

        if handle_polish_idle(bus, ctx.polish_path, seeded_session):
            return SeedEmptyAction.CONTINUE
        print_polish_lifecycle(
            "terminated",
            reason="polish queue exhausted",
            queue_path=str(ctx.polish_path),
        )
        return SeedEmptyAction.STOP

    if ideation_timed_out:
        return SeedEmptyAction.RETRY_IDEATION
    if not ideation_in_progress:
        return SeedEmptyAction.IDEATE
    return SeedEmptyAction.CONTINUE
