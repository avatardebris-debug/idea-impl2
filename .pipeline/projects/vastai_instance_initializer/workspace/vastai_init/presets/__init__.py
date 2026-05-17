"""Preset management module.

Provides schema definitions, validation, and loading of YAML preset files
that describe VAST.ai instance configurations.
"""

from .schema import PRESET_SCHEMA, PRESET_REQUIRED_FIELDS, PRESET_OPTIONAL_FIELDS
from .validator import PresetValidationError, validate_preset, load_preset

__all__ = [
    "PRESET_SCHEMA",
    "PRESET_REQUIRED_FIELDS",
    "PRESET_OPTIONAL_FIELDS",
    "PresetValidationError",
    "validate_preset",
    "load_preset",
]
