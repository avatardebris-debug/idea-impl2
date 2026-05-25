"""
pipeline/seed_policy.py
Unified handling when seed_from_master_list returns _SEED_EMPTY.
"""

from __future__ import annotations

import time
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from pipeline.run_context import RunContext
from pipeline.seeding import _SEED_EMPTY, _request_ideation, _seeded_this_session

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


def apply_seed_empty(
    seeded: str,
    bus: "MessageBus",
    run_ctx: RunContext | None,
    *,
    ideation_in_progress: bool,
    ideation_requested_at: float,
    ideation_timeout_s: float,
) -> tuple[bool, float, bool]:
    """
    Handle _SEED_EMPTY via on_seed_empty.

    Returns (ideation_in_progress, ideation_requested_at, stop_requested).
    """
    if seeded != _SEED_EMPTY:
        return ideation_in_progress, ideation_requested_at, False
    if not run_ctx:
        return ideation_in_progress, ideation_requested_at, False

    timed_out = (
        ideation_in_progress
        and ideation_requested_at > 0
        and time.time() - ideation_requested_at > ideation_timeout_s
    )
    action = on_seed_empty(
        run_ctx,
        bus,
        seeded_session=_seeded_this_session,
        ideation_in_progress=ideation_in_progress,
        ideation_timed_out=timed_out,
    )
    if action == SeedEmptyAction.STOP:
        return ideation_in_progress, ideation_requested_at, True
    if action == SeedEmptyAction.RETRY_IDEATION:
        print("  ⏰ Ideation timed out — retrying...")
        return False, 0.0, False
    if action == SeedEmptyAction.IDEATE:
        _request_ideation(bus)
        return True, time.time(), False
    return ideation_in_progress, ideation_requested_at, False
