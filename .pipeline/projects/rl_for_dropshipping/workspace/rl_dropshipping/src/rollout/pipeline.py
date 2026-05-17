"""Rollout pipeline — manages gradual deployment of RL policies."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RolloutStatus(Enum):
    """Status of a rollout phase."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ROLLED_BACK = "rolled_back"


@dataclass
class RolloutPhase:
    """A single phase in the rollout."""
    phase_id: str
    name: str
    status: RolloutStatus = RolloutStatus.PENDING
    traffic_fraction: float = 0.0
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    metrics: Dict[str, Any] = field(default_factory=dict)

    def activate(self, traffic_fraction: float) -> None:
        """Activate this phase with a given traffic fraction."""
        self.status = RolloutStatus.ACTIVE
        self.traffic_fraction = traffic_fraction
        self.start_time = time.time()
        logger.info(
            f"Rollout phase '{self.name}' activated with "
            f"{traffic_fraction*100:.1f}% traffic"
        )

    def pause(self) -> None:
        """Pause this phase."""
        if self.status == RolloutStatus.ACTIVE:
            self.status = RolloutStatus.PAUSED
            self.end_time = time.time()
            logger.info(f"Rollout phase '{self.name}' paused")

    def complete(self) -> None:
        """Mark this phase as completed."""
        if self.status == RolloutStatus.ACTIVE:
            self.status = RolloutStatus.COMPLETED
            self.end_time = time.time()
            logger.info(f"Rollout phase '{self.name}' completed")

    def rollback(self) -> None:
        """Roll back this phase."""
        self.status = RolloutStatus.ROLLED_BACK
        self.end_time = time.time()
        logger.warning(f"Rollout phase '{self.name}' rolled back")


class RolloutPipeline:
    """Manages gradual rollout of RL policies across phases.

    Supports traffic fraction management, metrics tracking,
    and rollback capabilities.
    """

    def __init__(self, name: str = "default_rollout"):
        self.name = name
        self._phases: Dict[str, RolloutPhase] = {}
        self._current_phase_id: Optional[str] = None
        self._history: List[Dict[str, Any]] = []

    def add_phase(
        self,
        phase_id: str,
        name: str,
        traffic_fraction: float = 0.0,
    ) -> RolloutPhase:
        """Add a new rollout phase."""
        phase = RolloutPhase(phase_id=phase_id, name=name)
        self._phases[phase_id] = phase
        logger.info(f"Added rollout phase '{name}' (id={phase_id})")
        return phase

    def activate_phase(
        self,
        phase_id: str,
        traffic_fraction: float = 0.1,
    ) -> bool:
        """Activate a phase with a given traffic fraction."""
        if phase_id not in self._phases:
            logger.error(f"Phase '{phase_id}' not found")
            return False

        phase = self._phases[phase_id]
        if phase.status == RolloutStatus.ACTIVE:
            logger.warning(f"Phase '{phase_id}' already active")
            return False

        phase.activate(traffic_fraction)
        self._current_phase_id = phase_id
        self._history.append({
            "event": "activate",
            "phase_id": phase_id,
            "traffic_fraction": traffic_fraction,
            "timestamp": time.time(),
        })
        return True

    def pause_phase(self, phase_id: str) -> bool:
        """Pause a phase."""
        if phase_id not in self._phases:
            return False
        self._phases[phase_id].pause()
        if self._current_phase_id == phase_id:
            self._current_phase_id = None
        self._history.append({
            "event": "pause",
            "phase_id": phase_id,
            "timestamp": time.time(),
        })
        return True

    def complete_phase(self, phase_id: str) -> bool:
        """Complete a phase."""
        if phase_id not in self._phases:
            return False
        self._phases[phase_id].complete()
        self._history.append({
            "event": "complete",
            "phase_id": phase_id,
            "timestamp": time.time(),
        })
        return True

    def rollback_phase(self, phase_id: str) -> bool:
        """Roll back a phase."""
        if phase_id not in self._phases:
            return False
        self._phases[phase_id].rollback()
        if self._current_phase_id == phase_id:
            self._current_phase_id = None
        self._history.append({
            "event": "rollback",
            "phase_id": phase_id,
            "timestamp": time.time(),
        })
        return True

    def get_phase(self, phase_id: str) -> Optional[RolloutPhase]:
        """Get a phase by ID."""
        return self._phases.get(phase_id)

    def get_current_phase(self) -> Optional[RolloutPhase]:
        """Get the currently active phase."""
        if self._current_phase_id:
            return self._phases.get(self._current_phase_id)
        return None

    def should_use_rl(self, phase_id: str) -> bool:
        """Check if RL should be used for a given phase."""
        phase = self._phases.get(phase_id)
        if phase is None:
            return False
        return phase.status == RolloutStatus.ACTIVE

    def get_traffic_fraction(self, phase_id: str) -> float:
        """Get the traffic fraction for a phase."""
        phase = self._phases.get(phase_id)
        if phase is None:
            return 0.0
        return phase.traffic_fraction

    def get_history(self) -> List[Dict[str, Any]]:
        """Get rollout history."""
        return list(self._history)

    def get_all_phases(self) -> Dict[str, RolloutPhase]:
        """Get all phases."""
        return dict(self._phases)

    @property
    def phases(self) -> Dict[str, RolloutPhase]:
        """Expose phases dict."""
        return self._phases

    @property
    def current_phase(self) -> Optional[RolloutPhase]:
        """Expose current phase."""
        return self.get_current_phase()

    def get_current_traffic_fraction(self) -> float:
        """Get the sum of traffic fractions across all active phases."""
        total = 0.0
        for phase in self._phases.values():
            if phase.status == RolloutStatus.ACTIVE:
                total += phase.traffic_fraction
        return total

    def get_status(self) -> Dict[str, Any]:
        """Get pipeline status summary."""
        return {
            "name": self.name,
            "phases": {pid: phase.status.value for pid, phase in self._phases.items()},
            "current_phase": self._current_phase_id,
            "current_traffic_fraction": self.get_current_traffic_fraction(),
        }
