"""
csv_data_pipeline_builder/tui.py
Interactive Pipeline Builder TUI using rich layout panels.

Provides:
- PipelineBuilder: terminal UI with left (CSVs/columns), center (DAG graph),
  right (node config editor) panels.
- PipelineDiff: compare two ExecutionReport sets for schema/data drift.
"""
from __future__ import annotations

import json
import pathlib
import time
from dataclasses import dataclass, field, asdict
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree
from rich.layout import Layout
from rich.text import Text
from rich.live import Live

from .nodes import TransformNode, Row
from .pipeline import Pipeline, ExecutionReport


# ---------------------------------------------------------------------------
# PipelineDiff
# ---------------------------------------------------------------------------

@dataclass
class SchemaDrift:
    """Difference between two schemas."""
    added_columns: list[str] = field(default_factory=list)
    removed_columns: list[str] = field(default_factory=list)
    type_changes: list[str] = field(default_factory=list)


@dataclass
class DataDrift:
    """Difference between two row sets."""
    added_rows: int = 0
    removed_rows: int = 0
    changed_rows: int = 0


@dataclass
class PipelineDiff:
    """Compare two pipeline runs."""
    schema_drift: SchemaDrift = field(default_factory=SchemaDrift)
    data_drift: DataDrift = field(default_factory=DataDrift)
    timing_diff_ms: dict[str, float] = field(default_factory=dict)

    def has_drift(self) -> bool:
        return (
            bool(self.schema_drift.added_columns)
            or bool(self.schema_drift.removed_columns)
            or bool(self.schema_drift.type_changes)
            or self.data_drift.added_rows
            or self.data_drift.removed_rows
            or self.data_drift.changed_rows
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_drift": asdict(self.schema_drift),
            "data_drift": asdict(self.data_drift),
            "timing_diff_ms": self.timing_diff_ms,
        }


def compare_runs(
    old_reports: list[dict[str, Any]],
    new_reports: list[dict[str, Any]],
    old_rows: list[Row] | None = None,
    new_rows: list[Row] | None = None,
) -> PipelineDiff:
    """Compare two pipeline runs for schema or data drift."""
    diff = PipelineDiff()

    # Schema drift: compare last node output schemas
    old_schema: dict[str, str] = {}
    new_schema: dict[str, str] = {}
    for r in old_reports:
        if "schema" in r:
            old_schema = r["schema"]
    for r in new_reports:
        if "schema" in r:
            new_schema = r["schema"]

    old_cols = set(old_schema.keys())
    new_cols = set(new_schema.keys())
    diff.schema_drift.added_columns = sorted(new_cols - old_cols)
    diff.schema_drift.removed_columns = sorted(old_cols - new_cols)
    for col in old_cols & new_cols:
        if old_schema[col] != new_schema[col]:
            diff.schema_drift.type_changes.append(col)

    # Data drift
    if old_rows is not None and new_rows is not None:
        old_keys = {tuple(sorted(r.items())) for r in old_rows}
        new_keys = {tuple(sorted(r.items())) for r in new_rows}
        diff.data_drift.added_rows = len(new_keys - old_keys)
        diff.data_drift.removed_rows = len(old_keys - new_keys)
        diff.data_drift.changed_rows = len(old_keys ^ new_keys)

    # Timing diff
    old_map = {r["node_id"]: r.get("duration_ms", 0) for r in old_reports}
    new_map = {r["node_id"]: r.get("duration_ms", 0) for r in new_reports}
    all_ids = set(old_map.keys()) | set(new_map.keys())
    for nid in all_ids:
        diff.timing_diff_ms[nid] = new_map.get(nid, 0) - old_map.get(nid, 0)

    return diff


# ---------------------------------------------------------------------------
# PipelineBuilder TUI
# ---------------------------------------------------------------------------

class PipelineBuilder:
    """Interactive terminal UI for building CSV pipelines."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.pipeline = Pipeline()
        self.available_csvs: dict[str, list[str]] = {}  # name -> columns
        self.selected_node_id: str | None = None
        self.node_configs: dict[str, dict[str, Any]] = {}
        self._running = False

    # -- CSV discovery -------------------------------------------------------

    def discover_csvs(self, directory: str | pathlib.Path = ".") -> None:
        """Scan a directory for CSV files and extract column names."""
        d = pathlib.Path(directory)
        for csv_file in sorted(d.glob("*.csv")):
            name = csv_file.stem
            try:
                with open(csv_file, newline="") as f:
                    reader = csv.reader(f)
                    header = next(reader, [])
                    self.available_csvs[name] = header
            except Exception:
                self.available_csvs[name] = []

    # -- DAG rendering -------------------------------------------------------

    def render_dag(self) -> Tree:
        """Render the current pipeline DAG as a rich.tree.Tree."""
        tree = Tree("📊 Pipeline DAG")
        for node in self.pipeline._nodes:
            child = tree.add(f"[bold]{node.node_id}[/] ({type(node).__name__})")
            # Add config details
            config = self.node_configs.get(node.node_id, {})
            for k, v in config.items():
                child.add(f"[dim]{k}: {v}[/]")
        return tree

    # -- Layout construction -------------------------------------------------

    def _build_layout(self) -> Layout:
        """Build the three-panel layout."""
        layout = Layout()
        layout.split_row(
            Layout(name="left", ratio=1),
            Layout(name="center", ratio=2),
            Layout(name="right", ratio=1),
        )
        return layout

    def _render_left(self) -> Panel:
        """Left panel: available CSVs and columns."""
        lines = [Text("[bold]Available CSVs[/]", style="cyan")]
        lines.append(Text("─" * 30))
        for name, cols in self.available_csvs.items():
            lines.append(Text(f"  📁 {name}.csv", style="green"))
            for col in cols:
                lines.append(Text(f"    └─ {col}", style="dim"))
        return Panel(
            *lines,
            title="📂 Data Sources",
            border_style="blue",
        )

    def _render_center(self) -> Panel:
        """Center panel: DAG node graph."""
        tree = self.render_dag()
        # Capture tree to text
        from io import StringIO
        buf = StringIO()
        sub_console = Console(file=buf, force_terminal=True)
        sub_console.print(tree)
        return Panel(
            Text(buf.getvalue(), style="white"),
            title="🔗 Pipeline DAG",
            border_style="magenta",
        )

    def _render_right(self) -> Panel:
        """Right panel: node config editor."""
        lines = [Text("[bold]Node Config[/]", style="cyan")]
        lines.append(Text("─" * 30))
        if self.selected_node_id:
            config = self.node_configs.get(self.selected_node_id, {})
            if config:
                for k, v in config.items():
                    lines.append(Text(f"  {k}: {v}", style="yellow"))
            else:
                lines.append(Text("  (no config)", style="dim"))
        else:
            lines.append(Text("  Select a node to edit", style="dim"))
        lines.append(Text(""))
        lines.append(Text("  [q] Quit  [s] Save  [h] Help", style="dim"))
        return Panel(
            *lines,
            title="⚙️ Node Config",
            border_style="green",
        )

    # -- Main loop -----------------------------------------------------------

    def run(self) -> None:
        """Launch the interactive TUI."""
        self._running = True
        layout = self._build_layout()

        with Live(layout, console=self.console, refresh_per_second=4) as live:
            while self._running:
                layout["left"].update(self._render_left())
                layout["center"].update(self._render_center())
                layout["right"].update(self._render_right())
                live.refresh()
                # Simple key input (non-blocking via timeout)
                try:
                    import sys
                    import msvcrt  # type: ignore
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode()
                        if key == "q":
                            self._running = False
                except ImportError:
                    # Unix: use select for non-blocking input
                    import select
                    if select.select([sys.stdin], [], [], 0.5)[0]:
                        key = sys.stdin.read(1)
                        if key == "q":
                            self._running = False

    def stop(self) -> None:
        """Stop the TUI loop."""
        self._running = False


# ---------------------------------------------------------------------------
# ExecutionReport helpers
# ---------------------------------------------------------------------------

def format_report(report: ExecutionReport) -> str:
    """Format an ExecutionReport as a human-readable string."""
    lines = [
        f"  Node: {report.node_id}",
        f"  Input rows:  {report.input_rows}",
        f"  Output rows: {report.output_rows}",
        f"  Duration:    {report.duration_ms:.2f} ms",
    ]
    if report.error:
        lines.append(f"  Error:       {report.error}")
    return "\n".join(lines)


def format_execution_summary(reports: list[ExecutionReport]) -> str:
    """Format a list of ExecutionReports as a summary table."""
    lines = [
        "",
        "╔══════════════════════════════════════════════════════╗",
        "║           PIPELINE EXECUTION SUMMARY                 ║",
        "╠══════════════════════════════════════════════════════╣",
    ]
    total_input = 0
    total_output = 0
    total_time = 0.0
    for r in reports:
        lines.append(f"║  {r.node_id:<28s} │ {r.input_rows:>6d} in │ {r.output_rows:>6d} out │ {r.duration_ms:>8.2f} ms  ║")
        total_input += r.input_rows
        total_output += r.output_rows
        total_time += r.duration_ms
    lines.append("╠══════════════════════════════════════════════════════╣")
    lines.append(f"║  {'TOTAL':<28s} │ {total_input:>6d} in │ {total_output:>6d} out │ {total_time:>8.2f} ms  ║")
    lines.append("╚══════════════════════════════════════════════════════╝")
    lines.append("")
    return "\n".join(lines)


def save_report_last(reports: list[ExecutionReport], output_dir: str | pathlib.Path = ".") -> pathlib.Path:
    """Save the last execution report to disk for later retrieval."""
    out = pathlib.Path(output_dir) / "last_execution_report.json"
    data = [asdict(r) for r in reports]
    out.write_text(json.dumps(data, indent=2))
    return out


def load_last_report(output_dir: str | pathlib.Path = ".") -> list[ExecutionReport] | None:
    """Load the last saved execution report, or None if not found."""
    path = pathlib.Path(output_dir) / "last_execution_report.json"
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [ExecutionReport(**r) for r in data]


__all__ = [
    "PipelineBuilder",
    "PipelineDiff",
    "SchemaDrift",
    "DataDrift",
    "compare_runs",
    "format_report",
    "format_execution_summary",
    "save_report_last",
    "load_last_report",
]
