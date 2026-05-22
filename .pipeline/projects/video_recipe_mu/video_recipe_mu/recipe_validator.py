"""Validate and normalize recipe steps against the schema."""

from __future__ import annotations

from typing import Dict, List, Optional, Set

from video_recipe_mu.schema import RobotRecipeStep

# Valid action verbs (extensible)
VALID_ACTIONS: Set[str] = {
    "pick_up", "place", "rotate", "move_to", "grip", "release",
    "sweep", "wipe", "spray", "pour", "cut", "assemble", "disassemble",
    "inspect", "calibrate", "clean", "apply", "press", "slide",
    "lift", "lower", "turn", "push", "pull", "align", "fasten",
    "unfasten", "insert", "remove", "adjust", "position", "deposit",
    "grab", "drop", "scan", "measure", "drill", "screw", "unscrew",
}

# Valid xyz_delta keys
VALID_XYZ_KEYS: Set[str] = {"x", "y", "z"}


def validate_steps(steps: List[RobotRecipeStep]) -> List[str]:
    """Validate a list of recipe steps.

    Returns a list of error messages (empty if all valid).
    """
    errors: List[str] = []

    for i, step in enumerate(steps):
        step_errors = validate_single_step(step, i + 1)
        errors.extend(step_errors)

    # Cross-step validation
    cross_errors = validate_cross_step(steps)
    errors.extend(cross_errors)

    return errors


def validate_single_step(step: RobotRecipeStep, step_num: int) -> List[str]:
    """Validate a single step against schema constraints."""
    errors: List[str] = []

    # Check required fields
    if not step.get("action"):
        errors.append(f"Step {step_num}: 'action' is required")
    if not step.get("object"):
        errors.append(f"Step {step_num}: 'object' is required")

    # Validate action is a known verb
    action = step.get("action", "")
    if action and action not in VALID_ACTIONS:
        errors.append(
            f"Step {step_num}: unknown action '{action}'. "
            f"Valid actions: {sorted(VALID_ACTIONS)}"
        )

    # Validate xyz_delta structure
    xyz = step.get("xyz_delta", {})
    if not isinstance(xyz, dict):
        errors.append(f"Step {step_num}: 'xyz_delta' must be a dict")
    else:
        for key in xyz:
            if key not in VALID_XYZ_KEYS:
                errors.append(
                    f"Step {step_num}: invalid xyz_delta key '{key}'. "
                    f"Valid keys: {sorted(VALID_XYZ_KEYS)}"
                )
        # Ensure all three axes are present
        for key in VALID_XYZ_KEYS:
            if key not in xyz:
                errors.append(
                    f"Step {step_num}: xyz_delta missing key '{key}'"
                )

    # Validate duration is positive
    duration = step.get("duration_s", 0)
    if duration <= 0:
        errors.append(f"Step {step_num}: 'duration_s' must be positive")

    # Validate preconditions is a list
    preconditions = step.get("preconditions", [])
    if not isinstance(preconditions, list):
        errors.append(f"Step {step_num}: 'preconditions' must be a list")

    return errors


def validate_cross_step(steps: List[RobotRecipeStep]) -> List[str]:
    """Validate relationships between steps."""
    errors: List[str] = []

    if not steps:
        return errors

    # Check step numbers are sequential
    expected_nums = list(range(1, len(steps) + 1))
    actual_nums = [s["step"] for s in steps]
    if actual_nums != expected_nums:
        errors.append(
            f"Step numbers not sequential: expected {expected_nums}, "
            f"got {actual_nums}"
        )

    # Check for duplicate objects (warn, not error)
    objects = [s["object"] for s in steps]
    seen: Dict[str, int] = {}
    for i, obj in enumerate(objects):
        if obj in seen:
            errors.append(
                f"Object '{obj}' appears in steps {seen[obj]} and {i + 1}. "
                f"Consider using unique identifiers."
            )
        seen[obj] = i + 1

    return errors


def normalize_steps(steps: List[RobotRecipeStep]) -> List[RobotRecipeStep]:
    """Normalize steps to ensure consistent format."""
    normalized: List[RobotRecipeStep] = []

    for i, step in enumerate(steps):
        # Default xyz_delta
        xyz = step.get("xyz_delta", {})
        xyz = {
            "x": float(xyz.get("x", 0.0)),
            "y": float(xyz.get("y", 0.0)),
            "z": float(xyz.get("z", 0.0)),
        }

        # Default duration
        duration = float(step.get("duration_s", 1.0))
        if duration <= 0:
            duration = 1.0

        # Default preconditions
        preconditions = step.get("preconditions", [])
        if not isinstance(preconditions, list):
            preconditions = []

        normalized.append(RobotRecipeStep(
            step=i + 1,
            action=str(step.get("action", "")),
            object=str(step.get("object", "")),
            xyz_delta=xyz,
            duration_s=duration,
            preconditions=preconditions,
            success_state=str(step.get("success_state", "")),
        ))

    return normalized
