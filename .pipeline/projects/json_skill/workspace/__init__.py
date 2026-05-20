"""
json_skill - Enable local AI to run Claude skills as JSON files.

This package provides a loader, dispatcher, and runtime for executing
Claude skills defined in JSON format.
"""

from .loader import load_skill, validate_skill_schema
from .dispatcher import FunctionDispatcher
from .runtime import SkillRuntime

__all__ = [
    "load_skill",
    "validate_skill_schema",
    "FunctionDispatcher",
    "SkillRuntime",
]
