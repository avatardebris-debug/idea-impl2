"""
csv_data_pipeline_builder/pipeline.py
DAG engine: wire nodes together, validate, and execute.
"""
from __future__ import annotations

import csv
import io
import json
import pathlib
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any

from .nodes import TransformNode, Row


@dataclass
class ExecutionReport:
    """Per-node execution metrics."""
    node_id: str
    input_rows: int
    output_rows: int
    duration_ms: float
    error: str = ""


@dataclass
class CsvSource:
    """Load rows from a CSV file."""
    path: str
    encoding: str = "utf-8"

    def load(self) -> list[Row]:
        with open(self.path, encoding=self.encoding, newline="") as f:
            return list(csv.DictReader(f))


@dataclass
class CsvSink:
    """Write rows to a CSV file."""
    path: str
    encoding: str = "utf-8"

    def write(self, rows: list[Row]) -> None:
        if not rows:
            return
        with open(self.path, "w", encoding=self.encoding, newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)


@dataclass
class JsonSink:
    """Write rows to a JSON file."""
    path: str

    def write(self, rows: list[Row]) -> None:
        pathlib.Path(self.path).write_text(json.dumps(rows, indent=2), encoding="utf-8")


@dataclass
class SqliteSink:
    """Write rows to a SQLite table."""
    path: str
    table: str = "pipeline_output"

    def write(self, rows: list[Row]) -> None:
        if not rows:
            return
        cols = list(rows[0].keys())
        conn = sqlite3.connect(self.path)
        conn.execute(f"DROP TABLE IF EXISTS {self.table}")
        col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
        conn.execute(f"CREATE TABLE {self.table} ({col_defs})")
        placeholders = ", ".join("?" * len(cols))
        conn.executemany(
            f"INSERT INTO {self.table} VALUES ({placeholders})",
            [[str(r.get(c, "")) for c in cols] for r in rows],
        )
        conn.commit()
        conn.close()


class Pipeline:
    """
    A linear sequence of TransformNodes.
    (Full DAG support with multiple inputs is Phase 2.)
    """

    def __init__(self, source: CsvSource | None = None) -> None:
        self.source = source
        self.nodes: list[TransformNode] = []
        self.sinks: list[CsvSink | JsonSink | SqliteSink] = []

    def add_node(self, node: TransformNode) -> "Pipeline":
        self.nodes.append(node)
        return self

    def add_sink(self, sink: CsvSink | JsonSink | SqliteSink) -> "Pipeline":
        self.sinks.append(sink)
        return self

    def execute(self, rows: list[Row] | None = None) -> tuple[list[Row], list[ExecutionReport]]:
        """Execute all nodes in sequence. Returns (final_rows, reports)."""
        if rows is None:
            if self.source is None:
                raise ValueError("No source or rows provided")
            rows = self.source.load()

        reports: list[ExecutionReport] = []
        for node in self.nodes:
            t0 = time.perf_counter()
            input_count = len(rows)
            error = ""
            try:
                rows = node.transform(rows)
            except Exception as e:
                error = str(e)
            duration_ms = (time.perf_counter() - t0) * 1000
            reports.append(ExecutionReport(
                node_id=node.node_id,
                input_rows=input_count,
                output_rows=len(rows),
                duration_ms=round(duration_ms, 2),
                error=error,
            ))

        for sink in self.sinks:
            sink.write(rows)

        return rows, reports

    def dry_run_schema(self, sample_rows: list[Row] | None = None) -> list[str]:
        """Infer output column names without writing to sinks."""
        rows = sample_rows or (self.source.load()[:5] if self.source else [])
        for node in self.nodes:
            try:
                rows = node.transform(rows)
            except Exception:
                pass
        return list(rows[0].keys()) if rows else []
