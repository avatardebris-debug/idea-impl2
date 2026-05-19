"""
csv_data_pipeline_builder/nodes.py
Transform node implementations for the DAG-based CSV pipeline engine.
"""
from __future__ import annotations

import csv
import io
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


Row = dict[str, Any]


class TransformNode(ABC):
    """Base class for all pipeline nodes."""
    node_id: str = ""

    @abstractmethod
    def transform(self, rows: list[Row]) -> list[Row]:
        """Apply the transform and return the result rows."""


@dataclass
class FilterNode(TransformNode):
    """Keep only rows matching a predicate.

    predicate_expr: a Python expression string evaluated with the row dict
    as local variables. E.g. "int(age) > 30 and city == 'Austin'"
    """
    node_id: str = "filter"
    predicate_expr: str = "True"

    def transform(self, rows: list[Row]) -> list[Row]:
        result = []
        for row in rows:
            try:
                if eval(self.predicate_expr, {"__builtins__": {}}, row):  # noqa: S307
                    result.append(row)
            except Exception:
                pass  # skip rows that fail evaluation
        return result


@dataclass
class SelectNode(TransformNode):
    """Project and optionally rename columns."""
    node_id: str = "select"
    columns: list[str] = field(default_factory=list)         # output column names
    rename: dict[str, str] = field(default_factory=dict)     # old -> new

    def transform(self, rows: list[Row]) -> list[Row]:
        result = []
        for row in rows:
            new_row: Row = {}
            for col in self.columns:
                src = self.rename.get(col, col)
                if src in row:
                    new_row[col] = row[src]
            result.append(new_row)
        return result


@dataclass
class AggregateNode(TransformNode):
    """Group rows and compute aggregations."""
    node_id: str = "aggregate"
    group_by: list[str] = field(default_factory=list)
    aggregations: dict[str, str] = field(default_factory=dict)  # col -> op (sum/mean/count/min/max)

    def transform(self, rows: list[Row]) -> list[Row]:
        from collections import defaultdict
        groups: dict[tuple, list[Row]] = defaultdict(list)
        for row in rows:
            key = tuple(row.get(k, "") for k in self.group_by)
            groups[key].append(row)

        result = []
        for key, group_rows in groups.items():
            out: Row = dict(zip(self.group_by, key))
            for col, op in self.aggregations.items():
                vals = []
                for r in group_rows:
                    try:
                        vals.append(float(r[col]))
                    except (KeyError, ValueError, TypeError):
                        pass
                if op == "sum":
                    out[col] = sum(vals)
                elif op == "mean":
                    out[col] = sum(vals) / len(vals) if vals else 0.0
                elif op == "count":
                    out[col] = len(group_rows)
                elif op == "min":
                    out[col] = min(vals) if vals else None
                elif op == "max":
                    out[col] = max(vals) if vals else None
            result.append(out)
        return result


@dataclass
class JoinNode(TransformNode):
    """Join two Row streams on a key column."""
    node_id: str = "join"
    left_key: str = "id"
    right_key: str = "id"
    how: str = "inner"   # inner | left | right
    right_rows: list[Row] = field(default_factory=list)

    def transform(self, rows: list[Row]) -> list[Row]:
        index: dict[Any, list[Row]] = {}
        for r in self.right_rows:
            k = r.get(self.right_key)
            index.setdefault(k, []).append(r)

        result = []
        for left in rows:
            k = left.get(self.left_key)
            matches = index.get(k, [])
            if matches:
                for right in matches:
                    merged = {**left, **right}
                    result.append(merged)
            elif self.how in ("left",):
                result.append(dict(left))
        return result


@dataclass
class PivotNode(TransformNode):
    """Pivot a long table to wide format."""
    node_id: str = "pivot"
    index: list[str] = field(default_factory=list)    # columns to keep as row identity
    columns: str = ""                                   # column whose unique values become new columns
    values: str = ""                                    # column to fill the cells with
    agg: str = "first"                                  # first | sum | mean

    def transform(self, rows: list[Row]) -> list[Row]:
        from collections import defaultdict
        groups: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
        for row in rows:
            key = tuple(row.get(k, "") for k in self.index)
            col_val = str(row.get(self.columns, ""))
            val = row.get(self.values)
            groups[key][col_val].append(val)

        result = []
        for key, col_map in groups.items():
            out: Row = dict(zip(self.index, key))
            for col_val, vals in col_map.items():
                if self.agg == "first":
                    out[col_val] = vals[0] if vals else None
                elif self.agg == "sum":
                    try:
                        out[col_val] = sum(float(v) for v in vals if v is not None)
                    except (TypeError, ValueError):
                        out[col_val] = vals[0]
                elif self.agg == "mean":
                    try:
                        nums = [float(v) for v in vals if v is not None]
                        out[col_val] = sum(nums) / len(nums) if nums else None
                    except (TypeError, ValueError):
                        out[col_val] = None
            result.append(out)
        return result
