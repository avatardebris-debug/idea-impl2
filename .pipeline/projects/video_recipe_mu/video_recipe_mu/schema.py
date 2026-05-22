"""Schema for robot recipe steps."""

from __future__ import annotations

from typing import Dict, List, TypedDict


class RobotRecipeStep(TypedDict):
    """A single atomic action step in a robot recipe.

    Attributes:
        step: Sequential step number (1-based).
        action: Atomic action verb (e.g. pick_up, place, rotate, move_to).
        object: Object identifier (string, shared across steps).
        xyz_delta: Relative movement in meters {"x": float, "y": float, "z": float}.
        duration_s: Estimated duration in seconds.
        preconditions: List of precondition strings.
        success_state: State description after this step succeeds.
    """

    step: int
    action: str
    object: str
    xyz_delta: Dict[str, float]
    duration_s: float
    preconditions: List[str]
    success_state: str
