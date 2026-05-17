"""Preset validation module.

Validates YAML preset files against the schema defined in schema.py.
Provides functions to check required fields, validate types, and load presets.
"""

import os
from pathlib import Path
from typing import Any

import yaml

from .schema import (
    PRESET_OPTIONAL_FIELDS,
    PRESET_REQUIRED_FIELDS,
    PRESET_SCHEMA,
    get_field_default,
    is_required_field,
)


class PresetValidationError(Exception):
    """Raised when a preset fails validation."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


def _validate_field_type(field_name: str, value: Any, expected_type: type | tuple[type, ...]) -> str | None:
    """Validate that a field value matches the expected type.

    Args:
        field_name: The name of the field being validated.
        value: The value to validate.
        expected_type: The expected type or tuple of types.

    Returns:
        An error message string if validation fails, None if it passes.
    """
    if value is None:
        return None

    if not isinstance(value, expected_type):
        return f"Field '{field_name}' has invalid type: expected {expected_type}, got {type(value).__name__}"
    return None


def validate_preset(preset: dict[str, Any]) -> dict[str, Any]:
    """Validate a preset dictionary against the schema.

    Args:
        preset: The preset dictionary to validate.

    Returns:
        The validated preset with defaults filled in for missing optional fields.

    Raises:
        PresetValidationError: If the preset fails validation.
    """
    if not isinstance(preset, dict):
        raise PresetValidationError(
            f"Preset must be a dictionary, got {type(preset).__name__}"
        )

    errors: list[str] = []

    # Check required fields
    for field in PRESET_REQUIRED_FIELDS:
        if field not in preset:
            errors.append(f"Missing required field: '{field}'")
        elif field in ("price_cap", "storage"):
            # price_cap and storage can be str, int, or float
            value = preset[field]
            if isinstance(value, str):
                if not value.strip():
                    errors.append(f"Field '{field}' must be a non-empty string")
            elif not isinstance(value, (int, float)):
                errors.append(f"Field '{field}' has invalid type: expected str/int/float, got {type(value).__name__}")
        elif field in ("name", "gpu_type", "image"):
            value = preset[field]
            if not isinstance(value, str) or not value.strip():
                errors.append(f"Field '{field}' must be a non-empty string")

    # Validate optional fields that are present
    for field, value in preset.items():
        if field in PRESET_REQUIRED_FIELDS:
            continue

        if field not in PRESET_SCHEMA:
            # Unknown field - allow it through
            continue

        field_info = PRESET_SCHEMA[field]
        expected_type = field_info.get("type")

        if expected_type and value is not None:
            type_error = _validate_field_type(field, value, expected_type)
            if type_error:
                errors.append(type_error)

    # Additional validation for specific fields
    if "price_cap" in preset and preset["price_cap"] is not None:
        try:
            price = float(preset["price_cap"])
            if price < 0:
                errors.append("Field 'price_cap' must be a non-negative number")
        except (ValueError, TypeError):
            errors.append("Field 'price_cap' must be a valid number")

    if "storage" in preset and preset["storage"] is not None:
        storage = preset["storage"]
        if isinstance(storage, str):
            if not any(unit in storage.upper() for unit in ["GB", "TB", "KB"]):
                errors.append("Field 'storage' must include a unit (e.g., '100GB')")
        elif not isinstance(storage, (int, float)):
            errors.append("Field 'storage' must be a string with unit or a number")

    if errors:
        raise PresetValidationError("; ".join(errors))

    # Fill in defaults for missing optional fields
    result = dict(preset)
    for field in PRESET_OPTIONAL_FIELDS:
        if field not in result:
            result[field] = get_field_default(field)

    return result


def load_preset(path: str | Path) -> dict[str, Any]:
    """Load and validate a preset from a YAML file.

    Args:
        path: Path to the YAML preset file.

    Returns:
        The validated preset dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        PresetValidationError: If the file is invalid or preset fails validation.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Preset file not found: {path}")

    if path.is_dir():
        raise PresetValidationError(f"Path is a directory, not a file: {path}")

    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PresetValidationError(f"Invalid YAML: {e}")

    if data is None or not isinstance(data, dict):
        raise PresetValidationError("YAML file must contain a YAML mapping, not a scalar or sequence")

    return validate_preset(data)
