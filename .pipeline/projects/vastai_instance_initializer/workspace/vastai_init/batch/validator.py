"""Batch configuration validation.

Validates batch config YAML files against the schema defined in config.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import (
    BATCH_OPTIONAL_FIELDS,
    BATCH_PRESET_REF_REQUIRED,
    BATCH_REQUIRED_FIELDS,
    BatchConfig,
    BatchPresetRef,
    TimingConfig,
)


class BatchConfigValidationError(Exception):
    """Raised when a batch config fails validation."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


def validate_batch_config(config: BatchConfig) -> BatchConfig:
    """Validate a batch configuration.

    Args:
        config: The BatchConfig to validate.

    Returns:
        The validated BatchConfig (same object, possibly with defaults filled).

    Raises:
        BatchConfigValidationError: If validation fails.
    """
    errors: list[str] = []

    # Check required top-level fields
    if not config.name or not config.name.strip():
        errors.append("Field 'name' must be a non-empty string")

    if not config.presets:
        errors.append("Field 'presets' must contain at least one preset reference")

    # Validate each preset reference
    for i, preset_ref in enumerate(config.presets):
        prefix = f"presets[{i}]"

        if not preset_ref.preset_path or not preset_ref.preset_path.strip():
            errors.append(f"{prefix}: 'preset_path' is required")
        else:
            # Check preset file exists
            preset_path = Path(preset_ref.preset_path)
            if not preset_path.exists():
                errors.append(
                    f"{prefix}: preset file not found: {preset_ref.preset_path}"
                )

        if preset_ref.count < 1:
            errors.append(f"{prefix}: 'count' must be a positive integer, got {preset_ref.count}")

    # Validate timing
    if config.timing.delay_seconds < 0:
        errors.append(f"timing.delay_seconds must be >= 0, got {config.timing.delay_seconds}")

    if not (0 <= config.timing.stagger_percent <= 100):
        errors.append(
            f"timing.stagger_percent must be between 0 and 100, got {config.timing.stagger_percent}"
        )

    # Validate concurrency
    if config.concurrency < 1:
        errors.append(f"concurrency must be >= 1, got {config.concurrency}")

    # Validate timeout
    if config.timeout < 1:
        errors.append(f"timeout must be >= 1, got {config.timeout}")

    if errors:
        raise BatchConfigValidationError("; ".join(errors))

    return config


def validate_batch_config_raw(raw: dict[str, Any]) -> list[str]:
    """Validate raw batch config dict and return list of error messages.

    Args:
        raw: The raw dict loaded from YAML.

    Returns:
        List of error message strings (empty if valid).
    """
    errors: list[str] = []

    # Check required fields
    for field in BATCH_REQUIRED_FIELDS:
        if field not in raw:
            errors.append(f"Missing required field: '{field}'")

    if errors:
        return errors

    # Validate presets
    presets = raw.get("presets", [])
    if not isinstance(presets, list):
        errors.append("'presets' must be a list")
    else:
        for i, p in enumerate(presets):
            prefix = f"presets[{i}]"
            if not isinstance(p, dict):
                errors.append(f"{prefix}: must be a mapping")
                continue

            for req_field in BATCH_PRESET_REF_REQUIRED:
                if req_field not in p:
                    errors.append(f"{prefix}: missing required field '{req_field}'")

            count = p.get("count", 1)
            if not isinstance(count, int) or count < 1:
                errors.append(f"{prefix}: 'count' must be a positive integer, got {count}")

    # Validate timing
    timing = raw.get("timing", {})
    if isinstance(timing, dict):
        delay = timing.get("delay_seconds", 0)
        if not isinstance(delay, (int, float)) or delay < 0:
            errors.append("timing.delay_seconds must be >= 0")

        stagger = timing.get("stagger_percent", 0)
        if not isinstance(stagger, (int, float)) or not (0 <= stagger <= 100):
            errors.append("timing.stagger_percent must be between 0 and 100")

    # Validate concurrency
    concurrency = raw.get("concurrency", 1)
    if not isinstance(concurrency, int) or concurrency < 1:
        errors.append("concurrency must be a positive integer")

    # Validate timeout
    timeout = raw.get("timeout", 3600)
    if not isinstance(timeout, int) or timeout < 1:
        errors.append("timeout must be a positive integer")

    return errors
