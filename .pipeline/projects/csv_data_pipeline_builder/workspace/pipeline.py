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

from .nodes import TransformNode, Row, CsvSink, JsonSink, SqliteSink


@dataclass
class ExecutionReport:
    """Per-node execution metrics."""
    node_id: str
    input_rows: int
    output_rows: int
    duration_ms: float
    error: str = ""


class Pipeline:
    """Orchestrates a sequence of TransformNodes."""

    def __init__(self) -> None:
        self._nodes: list[TransformNode] = []
        self._reports: list[dict[str, Any]] = []

    @property
    def reports(self) -> list[dict[str, Any]]:
        return self._reports

    def add_node(self, node: TransformNode) -> "Pipeline":
        self._nodes.append(node)
        return self

    def add_sink(self, sink: TransformNode) -> "Pipeline":
        self._nodes.append(sink)
        return self

    def execute(self, initial_rows: list[Row] | None = None) -> tuple[list[Row], list[dict[str, Any]]]:
        """Run the pipeline and return (final_rows, reports)."""
        rows = initial_rows if initial_rows is not None else []
        self._reports = []

        for node in self._nodes:
            rows = node.transform(rows)
            self._reports.append({
                "node_id": node.node_id,
                "rows": len(rows),
            })

        return rows, self._reports

    def dry_run_schema(self, sample_rows: list[Row]) -> list[str]:
        """Return the column names that would result from running the pipeline on sample data."""
        rows = sample_rows
        for node in self._nodes:
            rows = node.transform(rows)
            if not rows:
                return []
        return list(rows[0].keys())


__all__ = [
    "Pipeline",
]
