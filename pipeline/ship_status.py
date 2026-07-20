"""Ship-prove status ordering and helpers."""

from __future__ import annotations

# Extends in-phase STATUS_ORDER from import_cloud_zip / project_rebuild.
SHIP_STATUS_ORDER: list[str] = [
    "field_test_planning",
    "field_testing",
    "field_test_failed",
    "field_test_passed",
    "thermo_reviewing",
    "thermo_refactoring",
    "ship_evaluating",
    "ship_insufficient",
    "field_proven",
]

TERMINAL_SHIP_STATUSES: frozenset[str] = frozenset({
    "field_proven",
    "ship_insufficient",
})


def is_ship_in_flight(status: str) -> bool:
    """True while ship-prove agents may still have work for this project."""
    if status in TERMINAL_SHIP_STATUSES:
        return False
    if status == "complete":
        return False
    if status == "budget_exceeded":
        return False
    return is_ship_status(status)


def ship_status_rank(status: str) -> int:
    try:
        return SHIP_STATUS_ORDER.index(status)
    except ValueError:
        return -1


def is_ship_status(status: str) -> bool:
    return status in SHIP_STATUS_ORDER or status.startswith("field_test")


def is_ship_prove_eligible(status: str) -> bool:
    """Projects the ship-prove loop may pick up."""
    return status in ("complete", "complete_with_bugs")
