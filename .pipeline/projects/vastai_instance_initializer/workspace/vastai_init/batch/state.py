"""Batch state serialization for pause/resume persistence."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class InstanceState:
    """State of a single instance within a batch."""

    instance_id: str
    preset_path: str
    count_index: int
    status: str = "pending"  # pending | launching | running | failed | stopped | skipped
    error: str = ""
    started_at: float = 0.0
    stopped_at: float = 0.0
    timing_offset: float = 0.0


@dataclass
class BatchState:
    """Persistable state of a batch launch."""

    batch_name: str
    source_path: str
    presets: list[dict[str, Any]]
    timing: dict[str, float]
    concurrency: int
    timeout: int
    instances: list[InstanceState] = field(default_factory=list)
    started_at: float = 0.0
    completed_at: float = 0.0
    status: str = "pending"  # pending | running | completed | failed | paused


def save_batch_state(state: BatchState, path: str | Path) -> None:
    """Save batch state to a JSON file for pause/resume."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = asdict(state)
    path.write_text(json.dumps(data, indent=2))


def load_batch_state(path: str | Path) -> BatchState:
    """Load batch state from a JSON file."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Batch state file not found: {path}")

    data = json.loads(path.read_text())
    return BatchState(
        batch_name=data["batch_name"],
        source_path=data["source_path"],
        presets=data["presets"],
        timing=data["timing"],
        concurrency=data["concurrency"],
        timeout=data["timeout"],
        instances=[InstanceState(**inst) for inst in data.get("instances", [])],
        started_at=data.get("started_at", 0.0),
        completed_at=data.get("completed_at", 0.0),
        status=data.get("status", "pending"),
    )
