"""Batch configuration schema and loader.

Defines the YAML batch config format that supports multiple preset references
with instance counts, global timing settings, concurrency limits, and a
batch-level name.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class BatchPresetRef:
    """A reference to a preset file within a batch config."""

    preset_path: str
    count: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {"preset_path": self.preset_path, "count": self.count}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BatchPresetRef:
        return cls(
            preset_path=data["preset_path"],
            count=data.get("count", 1),
        )


@dataclass
class TimingConfig:
    """Timing configuration for batch launches."""

    delay_seconds: float = 0.0
    stagger_percent: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "delay_seconds": self.delay_seconds,
            "stagger_percent": self.stagger_percent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> TimingConfig:
        return cls(
            delay_seconds=data.get("delay_seconds", 0.0),
            stagger_percent=data.get("stagger_percent", 0.0),
        )


@dataclass
class BatchConfig:
    """Full batch configuration loaded from a YAML file."""

    name: str
    presets: list[BatchPresetRef]
    timing: TimingConfig = field(default_factory=TimingConfig)
    concurrency: int = 1
    timeout: int = 3600
    _source_path: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "presets": [p.to_dict() for p in self.presets],
            "timing": self.timing.to_dict(),
            "concurrency": self.concurrency,
            "timeout": self.timeout,
            "_source_path": self._source_path,
        }


# Schema constants for batch config fields
BATCH_REQUIRED_FIELDS = ["name", "presets"]
BATCH_PRESET_REF_REQUIRED = ["preset_path"]

BATCH_OPTIONAL_FIELDS: dict[str, Any] = {
    "timing": {
        "default": {"delay_seconds": 0.0, "stagger_percent": 0.0},
        "type": dict,
    },
    "concurrency": {"default": 1, "type": int},
    "timeout": {"default": 3600, "type": int},
}


def load_batch_config(batch_path: str | Path) -> BatchConfig:
    """Load a batch configuration from a YAML file.

    Args:
        batch_path: Path to the batch config YAML file.

    Returns:
        A validated BatchConfig instance.

    Raises:
        FileNotFoundError: If the batch config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(batch_path)
    if not path.exists():
        raise FileNotFoundError(f"Batch config file not found: {path}")
    if not path.is_file():
        raise FileNotFoundError(f"Batch config path is not a file: {path}")

    with open(path, "r") as f:
        raw = yaml.safe_load(f)

    if not isinstance(raw, dict):
        raise yaml.YAMLError("Batch config must contain a YAML mapping")

    return _parse_batch_config(raw, str(path))


def _parse_batch_config(raw: dict[str, Any], source_path: str) -> BatchConfig:
    """Parse raw dict into a BatchConfig (no validation — use validate_batch_config)."""
    name = raw.get("name", "unnamed-batch")

    presets_raw = raw.get("presets", [])
    presets = []
    for p in presets_raw:
        if isinstance(p, dict):
            presets.append(BatchPresetRef.from_dict(p))
        elif isinstance(p, str):
            presets.append(BatchPresetRef(preset_path=p))

    timing_raw = raw.get("timing", {})
    if isinstance(timing_raw, dict):
        timing = TimingConfig.from_dict(timing_raw)
    else:
        timing = TimingConfig()

    concurrency = raw.get("concurrency", 1)
    timeout = raw.get("timeout", 3600)

    return BatchConfig(
        name=name,
        presets=presets,
        timing=timing,
        concurrency=int(concurrency),
        timeout=int(timeout),
        _source_path=source_path,
    )


def find_batch_configs(directory: str | Path | None = None) -> list[Path]:
    """Find all batch config YAML files in a directory.

    Args:
        directory: Directory to search. Defaults to presets/batch/ relative to
                   the project root (parent of vastai_init/).

    Returns:
        List of paths to batch config files.
    """
    if directory is None:
        # Default: presets/batch/ relative to the project root
        project_root = Path(__file__).resolve().parent.parent.parent
        directory = project_root / "presets" / "batch"

    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    return sorted(dir_path.glob("*.yaml")) + sorted(dir_path.glob("*.yml"))
