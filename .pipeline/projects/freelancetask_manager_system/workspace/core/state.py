"""Pipeline state serialization for the FreelanceTask Manager System."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any


@dataclass
class PipelineState:
    """
    Serializable pipeline state that captures the current position
    of a service offering through the pipeline stages.
    """
    pipeline_id: str
    current_stage: str  # "sop_created", "proposal_generated", "matched", "contract_generated", "signed"
    service_offering_id: str = ""
    client_profile_id: str = ""
    proposal_id: str = ""
    opportunity_id: str = ""
    contract_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PipelineState:
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> PipelineState:
        return cls.from_dict(json.loads(json_str))

    def advance_stage(self, new_stage: str) -> None:
        self.current_stage = new_stage
        self.updated_at = datetime.utcnow().isoformat()


# ---- Storage helpers ----

class StateStore:
    """In-memory + file-backed store for PipelineState objects."""

    def __init__(self, storage_path: str = "pipeline_state.json"):
        self.storage_path = storage_path
        self._states: dict[str, PipelineState] = {}
        self._load()

    def _load(self) -> None:
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
                for pid, sdata in data.items():
                    self._states[pid] = PipelineState.from_dict(sdata)
        except (FileNotFoundError, json.JSONDecodeError):
            self._states = {}

    def _save(self) -> None:
        with open(self.storage_path, "w") as f:
            json.dump({pid: s.to_dict() for pid, s in self._states.items()}, f, indent=2)

    def save(self, state: PipelineState) -> None:
        self._states[state.pipeline_id] = state
        self._save()

    def get(self, pipeline_id: str) -> PipelineState | None:
        return self._states.get(pipeline_id)

    def list_all(self) -> list[PipelineState]:
        return list(self._states.values())

    def delete(self, pipeline_id: str) -> bool:
        if pipeline_id in self._states:
            del self._states[pipeline_id]
            self._save()
            return True
        return False
