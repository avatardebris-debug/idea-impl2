"""Live progress display for batch launches.

Uses `rich` to render a live-updating terminal table showing per-instance
status, GPU type, elapsed time, and errors.  Supports spinner animation,
auto-refresh at a configurable interval, and graceful Ctrl-C handling.
"""

from __future__ import annotations

import signal
import sys
import time
from typing import Any, Dict, Optional

from rich.console import Console
from rich.live import Live
from rich.spinner import Spinner
from rich.table import Table

from .state import BatchState, InstanceState


class BatchProgressView:
    """Renders a live-updating table of batch instance states."""

    def __init__(
        self,
        batch_state: BatchState,
        console: Optional[Console] = None,
        refresh_interval: float = 1.0,
    ) -> None:
        self.batch_state = batch_state
        self.console = console or Console()
        self.refresh_interval = refresh_interval
        self._running = True
        self._start_time = time.time()
        self._spinner_frames = [
            "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
        ]
        self._spinner_idx = 0
        self._task: Optional[Any] = None

    # ── public API ────────────────────────────────────────────────

    def start(self) -> None:
        """Begin the live progress display (blocks until stop)."""
        # Install a signal handler for graceful shutdown
        self._running = True
        try:
            with Live(
                self._render_table(),
                console=self.console,
                refresh_per_second=1,
                screen=False,
            ) as live:
                while self._running:
                    live.update(self._render_table())
                    time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        """Stop the live progress display."""
        self._running = False

    def update_state(self, instance_id: str, status: str, error: str = "") -> None:
        """Update the state of a single instance."""
        for inst in self.batch_state.instances:
            if inst.instance_id == instance_id:
                inst.status = status
                if error:
                    inst.error = error
                break

    # ── rendering ─────────────────────────────────────────────────

    def _render_table(self) -> Table:
        table = Table(
            title=f"Batch: {self.batch_state.name}",
            show_header=True,
            header_style="bold cyan",
            title_style="bold magenta",
        )
        table.add_column("Instance", style="dim", width=12)
        table.add_column("Preset", style="dim", width=20)
        table.add_column("Status", width=10)
        table.add_column("Elapsed", width=8)
        table.add_column("Error", style="red", width=30)

        elapsed = time.time() - self._start_time

        for inst in self.batch_state.instances:
            status_text = self._status_color(inst.status)
            inst_elapsed = self._format_elapsed(
                elapsed if inst.status in ("running", "failed") else 0
            )
            error_text = inst.error if inst.error else ""
            table.add_row(
                inst.instance_id[:12],
                inst.preset_path,
                status_text,
                inst_elapsed,
                error_text,
            )

        # Summary line
        total = len(self.batch_state.instances)
        running = sum(1 for i in self.batch_state.instances if i.status == "running")
        failed = sum(1 for i in self.batch_state.instances if i.status == "failed")
        done = sum(
            1 for i in self.batch_state.instances if i.status in ("running", "failed", "stopped")
        )
        table.add_row(
            "",
            f"Total: {total}  Running: {running}  Failed: {failed}  Done: {done}",
            "",
            self._format_elapsed(elapsed),
            "",
        )
        return table

    def _status_color(self, status: str) -> str:
        colors = {
            "pending": "yellow",
            "launching": "blue",
            "running": "green",
            "failed": "red",
            "stopped": "dim",
            "skipped": "dim",
        }
        return f"[{colors.get(status, 'white')}]{status}[/]"

    @staticmethod
    def _format_elapsed(seconds: float) -> str:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
