"""pipeline.py — Pipeline orchestration and sink nodes."""

from __future__ import annotations

import csv
import json
import sqlite3
from typing import Any

from .nodes import (
    AggregateNode,
    CsvSink,
    CsvSource,
    FilterNode,
    JoinNode,
    JsonSink,
    PivotNode,
    SelectNode,
    SqliteSink,
    TransformNode,
)

Row = dict[str, Any]


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
    "CsvSource",
    "CsvSink",
    "JsonSink",
    "SqliteSink",
    "FilterNode",
    "SelectNode",
    "AggregateNode",
    "JoinNode",
    "PivotNode",
]
