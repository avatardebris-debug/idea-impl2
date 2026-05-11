"""SOP Loader — loads, validates, and manages SOP definitions.

Wraps the shared sopinput schema with project-specific SOP directory
management and YAML loading.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

# Reuse shared SOP schema models
import sys
_shared_libs = Path(__file__).resolve().parent.parent.parent.parent.parent / "shared_libs"
if str(_shared_libs) not in sys.path:
    sys.path.insert(0, str(_shared_libs))

from sopinput.sop_schema import SOP, SOPInput, SOPStep, load_sop as _shared_load_sop, validate_input as _shared_validate_input


class AgencySOP(BaseModel):
    """Project-level SOP wrapper with metadata."""

    name: str
    description: str
    inputs: List[SOPInput] = Field(default_factory=list)
    steps: List[SOPStep] = Field(default_factory=list)
    output_format: str = ""
    metadata: Optional[Dict[str, Any]] = None
    source_path: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any], source_path: Optional[str] = None) -> "AgencySOP":
        """Create an AgencySOP from a dict (e.g. parsed YAML)."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            inputs=[SOPInput(**i) for i in data.get("inputs", [])],
            steps=[SOPStep(**s) for s in data.get("steps", [])],
            output_format=data.get("output_format", ""),
            metadata=data.get("metadata"),
            source_path=source_path,
        )

    def to_sop(self) -> SOP:
        """Convert to the shared SOP model for executor compatibility."""
        return SOP(
            name=self.name,
            description=self.description,
            inputs=self.inputs,
            steps=self.steps,
            output_format=self.output_format,
        )


class SOPLoader:
    """Load SOPs from YAML files in the SOPs directory."""

    def __init__(self, sops_dir: Optional[Path] = None) -> None:
        self.sops_dir = sops_dir or self._default_sops_dir()

    @staticmethod
    def _default_sops_dir() -> Path:
        """Return the default SOPs directory, respecting DST_SOPS_DIR env var."""
        env_dir = os.environ.get("DST_SOPS_DIR")
        if env_dir:
            return Path(env_dir)
        return Path(__file__).resolve().parent.parent / "sops"

    def list_sops(self) -> List[str]:
        """List all available SOP names (without extension)."""
        if not self.sops_dir.exists():
            return []
        return [
            f.stem
            for f in self.sops_dir.glob("*.yaml")
            if f.is_file()
        ] + [
            f.stem
            for f in self.sops_dir.glob("*.yml")
            if f.is_file()
        ]

    def load_sop(self, name: str) -> AgencySOP:
        """Load a specific SOP by name.

        Args:
            name: SOP name (without extension).

        Returns:
            AgencySOP instance.

        Raises:
            FileNotFoundError: If the SOP file does not exist.
            ValueError: If the SOP is invalid.
        """
        # Try both extensions
        for ext in (".yaml", ".yml"):
            path = self.sops_dir / f"{name}{ext}"
            if path.exists():
                break
        else:
            raise FileNotFoundError(
                f"SOP '{name}' not found in {self.sops_dir}. "
                f"Available: {', '.join(self.list_sops())}"
            )

        import yaml
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(f"SOP file '{path}' contains invalid YAML: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError(f"SOP file '{path}' does not contain a valid YAML mapping")

        return AgencySOP.from_dict(data, source_path=str(path))

    def validate_input(self, sop: AgencySOP, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data against the SOP's input schema.

        Args:
            sop: The SOP to validate against.
            input_data: User-provided input data.

        Returns:
            Validated input data.

        Raises:
            ValueError: If validation fails.
        """
        try:
            return _shared_validate_input(sop.to_sop(), input_data)
        except ValueError as exc:
            msg = str(exc)
            # Normalize error messages to match expected test patterns
            if "Missing required" not in msg and "required" in msg.lower():
                raise ValueError(f"Missing required input: {msg}") from exc
            if "Invalid type for input" not in msg and ("type" in msg.lower() or "expected" in msg.lower()):
                raise ValueError(f"Invalid type for input: {msg}") from exc
            raise

    def get_sop(self, name: str) -> AgencySOP:
        """Alias for load_sop for convenience."""
        return self.load_sop(name)
