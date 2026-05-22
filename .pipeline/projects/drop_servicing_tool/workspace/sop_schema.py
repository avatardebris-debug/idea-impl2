"""SOP Schema Definition & Validation.

Pydantic models that define the structure of Standard Operating Procedures
and a loader that validates YAML SOP files on load.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List, Optional

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Input field model
# ---------------------------------------------------------------------------

SUPPORTED_INPUT_TYPES = {"string", "number", "boolean", "array", "object"}


class SOPInput(BaseModel):
    """A single input field for an SOP.

    Attributes:
        name:  Field name (used as the key in the input JSON).
        type:  One of string / number / boolean / array / object.
        required:  Whether the field must be present.
        description:  Human-readable description of the input.
    """

    name: str
    type: str = Field(description="Type of the input field.")
    required: bool = False
    description: str = ""

    @field_validator("type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        v = v.lower()
        if v not in SUPPORTED_INPUT_TYPES:
            raise ValueError(
                f"Unsupported input type '{v}'. Must be one of {SUPPORTED_INPUT_TYPES}"
            )
        return v


# ---------------------------------------------------------------------------
# Step model
# ---------------------------------------------------------------------------

class SOPStep(BaseModel):
    """A single step in an SOP execution.

    Attributes:
        name:          Unique step identifier.
        description:   What this step is supposed to do.
        prompt_template:  Name of the prompt template file (without extension).
                          Defaults to ``default_step``.
        llm_required:  Whether this step needs an LLM call.
        output_key:    Key under which the step's output is stored.
                       Defaults to the step name.
    """

    name: str
    description: str
    prompt_template: str = "default_step"
    llm_required: bool = True
    output_key: Optional[str] = None

    @model_validator(mode="after")
    def _set_default_output_key(self) -> "SOPStep":
        if self.output_key is None:
            self.output_key = self.name
        return self


# ---------------------------------------------------------------------------
# Top-level SOP model
# ---------------------------------------------------------------------------

class SOP(BaseModel):
    """A validated Standard Operating Procedure.

    Attributes:
        name:          SOP identifier.
        description:   Human-readable description.
        inputs:        List of input field definitions.
        steps:         Ordered list of execution steps.
        output_format:  Description of the expected final output.
        metadata:      Optional free-form metadata dict.
    """

    name: str
    description: str
    inputs: List[SOPInput] = Field(default_factory=list)
    steps: List[SOPStep] = Field(default_factory=list)
    output_format: str = ""
    metadata: Optional[dict[str, Any]] = None

    @model_validator(mode="after")
    def _validate_steps(self) -> "SOP":
        if not self.steps:
            raise ValueError("SOP must define at least one step.")
        step_names = [s.name for s in self.steps]
        if len(step_names) != len(set(step_names)):
            raise ValueError(f"Step names must be unique. Duplicates: {[n for n in step_names if step_names.count(n) > 1]}")
        return self


# ---------------------------------------------------------------------------
# Loader
# ---------------------------------------------------------------------------

def load_sop(path: str | Path) -> SOP:
    """Load and validate an SOP from a YAML file.

    Args:
        path:  Path to the YAML file.

    Returns:
        A validated :class:`SOP` model.

    Raises:
        FileNotFoundError:  If the file does not exist.
        ValueError:         If the YAML is malformed or fails validation.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"SOP file not found: {path}")

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"SOP YAML must resolve to a mapping, got {type(raw).__name__}")

    try:
        sop = SOP(**raw)
    except Exception as exc:
        raise ValueError(f"Invalid SOP '{path}': {exc}") from exc

    return sop


# ---------------------------------------------------------------------------
# Input validation helper
# ---------------------------------------------------------------------------

def validate_input(sop: SOP, input_data: dict[str, Any]) -> dict[str, Any]:
    """Validate *input_data* against the SOP's declared inputs.

    Returns the validated (and possibly type-coerced) input dict.

    Raises:
        ValueError:  If required fields are missing or types don't match.
    """
    result: dict[str, Any] = {}
    for inp in sop.inputs:
        if inp.name not in input_data:
            if inp.required:
                raise ValueError(f"Required input field '{inp.name}' is missing.")
            continue  # optional, absent → skip
        value = input_data[inp.name]
        result[inp.name] = _coerce(value, inp.type)
    return result


def _coerce(value: Any, target_type: str) -> Any:
    """Coerce *value* to *target_type* (best-effort)."""
    type_map = {
        "string": str,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
    }
    expected = type_map.get(target_type, type)
    if not isinstance(value, expected):
        raise ValueError(
            f"Input '{value}' expected type '{target_type}' (got {type(value).__name__})."
        )
    return value


# Export Step class for convenience
Step = SOPStep
