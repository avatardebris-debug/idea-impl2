"""Batch completion report generation.

Produces a text summary after a batch finishes, including total instances,
count by status, per-instance failure details, total elapsed time, and
SSH connection details for running instances.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .state import BatchState, InstanceState


@dataclass
class BatchReport:
    """Holds the data needed to render a batch completion report."""

    batch_state: BatchState
    total_elapsed: float = 0.0

    # ── summary helpers ─────────────────────────────────────────

    @property
    def total_instances(self) -> int:
        return len(self.batch_state.instances)

    def count_by_status(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for inst in self.batch_state.instances:
            counts[inst.status] = counts.get(inst.status, 0) + 1
        return counts

    @property
    def failed_instances(self) -> List[InstanceState]:
        return [i for i in self.batch_state.instances if i.status == "failed"]

    @property
    def running_instances(self) -> List[InstanceState]:
        return [i for i in self.batch_state.instances if i.status == "running"]

    @property
    def stopped_instances(self) -> List[InstanceState]:
        return [i for i in self.batch_state.instances if i.status == "stopped"]

    # ── report rendering ────────────────────────────────────────

    def render(self) -> str:
        lines: List[str] = []
        lines.append("=" * 60)
        lines.append(f"  Batch Complete: {self.batch_state.name}")
        lines.append("=" * 60)
        lines.append("")

        # Summary counts
        counts = self.count_by_status()
        lines.append("Summary:")
        lines.append(f"  Total instances : {self.total_instances}")
        for status in ("running", "failed", "stopped", "pending", "launching", "skipped"):
            c = counts.get(status, 0)
            if c > 0:
                lines.append(f"  {status:<12s}: {c}")
        lines.append(f"  Total elapsed   : {self._format_elapsed(self.total_elapsed)}")
        lines.append("")

        # Failed instances
        if self.failed_instances:
            lines.append("Failed Instances:")
            for inst in self.failed_instances:
                lines.append(f"  [{inst.instance_id}] preset={inst.preset_path}  error={inst.error}")
            lines.append("")

        # Running instances — SSH details
        if self.running_instances:
            lines.append("Running Instances — SSH Connection Details:")
            for inst in self.running_instances:
                lines.append(f"  [{inst.instance_id}] preset={inst.preset_path}")
                if inst.ssh_command:
                    lines.append(f"    SSH: {inst.ssh_command}")
                if inst.ip_address:
                    lines.append(f"    IP:  {inst.ip_address}")
                if inst.port:
                    lines.append(f"    Port: {inst.port}")
            lines.append("")

        # Stopped instances
        if self.stopped_instances:
            lines.append("Stopped Instances:")
            for inst in self.stopped_instances:
                lines.append(f"  [{inst.instance_id}] preset={inst.preset_path}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
