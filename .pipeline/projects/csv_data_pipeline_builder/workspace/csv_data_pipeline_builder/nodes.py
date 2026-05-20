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
        """Apply the transform and return the resulting rows."""
        ...

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.node_id}>"


class FilterNode(TransformNode):
    """Row-level predicate filtering using a simple expression DSL.

    Supported operators: ==, !=, >, <, >=, <=, and, or, not
    Column names are looked up in the row dict.
    String literals are wrapped in quotes: 'value'
    Numeric literals are bare: 42
    """

    def __init__(self, predicate_expr: str, node_id: str = "filter"):
        self.node_id = node_id
        self.predicate_expr = predicate_expr

    def _eval_expr(self, row: Row, expr: str) -> bool:
        """Evaluate a simple boolean expression against a row."""
        expr = expr.strip()

        # Handle 'and'
        if " and " in expr:
            parts = expr.split(" and ", 1)
            return self._eval_expr(row, parts[0]) and self._eval_expr(row, parts[1])

        # Handle 'or'
        if " or " in expr:
            parts = expr.split(" or ", 1)
            return self._eval_expr(row, parts[0]) or self._eval_expr(row, parts[1])

        # Handle 'not'
        if expr.startswith("not "):
            return not self._eval_expr(row, expr[4:])

        # Handle comparison operators (order matters: >= before >)
        for op in [">=", "<=", "!=", "==", ">", "<"]:
            if op in expr:
                parts = expr.split(op, 1)
                if len(parts) == 2:
                    left = self._parse_value(parts[0].strip(), row)
                    right = self._parse_value(parts[1].strip(), row)
                    if op == "==":
                        return left == right
                    elif op == "!=":
                        return left != right
                    elif op == ">":
                        return left > right
                    elif op == "<":
                        return left < right
                    elif op == ">=":
                        return left >= right
                    elif op == "<=":
                        return left <= right

        # Bare column name — truthy check
        val = self._parse_value(expr, row)
        return bool(val)

    def _parse_value(self, val: str, row: Row) -> Any:
        """Parse a literal or column reference."""
        val = val.strip()
        # String literal
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            return val[1:-1]
        # Numeric literal
        try:
            if "." in val:
                return float(val)
            return int(val)
        except ValueError:
            pass
        # Column reference
        if val in row:
            return row[val]
        return val

    def transform(self, rows: list[Row]) -> list[Row]:
        return [r for r in rows if self._eval_expr(r, self.predicate_expr)]


class SelectNode(TransformNode):
    """Column projection and optional rename."""

    def __init__(self, columns: list[str], rename: dict[str, str] | None = None, node_id: str = "select"):
        self.node_id = node_id
        self.columns = columns
        self.rename = rename or {}

    def transform(self, rows: list[Row]) -> list[Row]:
        result = []
        for r in rows:
            new_row = {}
            for col in self.columns:
                # If col is in rename keys, use it as the new key name
                new_key = col
                if col in self.rename:
                    new_key = self.rename[col]
                new_row[new_key] = r.get(col, "")
            result.append(new_row)
        return result


class AggregateNode(TransformNode):
    """Group-by + aggregation (sum, mean, count, min, max)."""

    def __init__(self, group_by: list[str], aggregations: dict[str, str], node_id: str = "aggregate"):
        self.node_id = node_id
        self.group_by = group_by
        self.aggregations = aggregations  # {column: "sum"|"mean"|"count"|"min"|"max"}

    def transform(self, rows: list[Row]) -> list[Row]:
        groups: dict[tuple, list[Row]] = {}
        for r in rows:
            key = tuple(r.get(c, "") for c in self.group_by)
            groups.setdefault(key, []).append(r)

        result = []
        for key, group_rows in groups.items():
            out: dict[str, Any] = {}
            for i, col in enumerate(self.group_by):
                out[col] = key[i]
            for agg_col, agg_fn in self.aggregations.items():
                values = []
                for gr in group_rows:
                    v = gr.get(agg_col, 0)
                    try:
                        values.append(float(v))
                    except (ValueError, TypeError):
                        values.append(v)
                if agg_fn == "sum":
                    out[agg_col] = sum(values) if values else 0
                elif agg_fn == "mean":
                    out[agg_col] = sum(values) / len(values) if values else 0
                elif agg_fn == "count":
                    out[agg_col] = len(group_rows)
                elif agg_fn == "min":
                    out[agg_col] = min(values) if values else 0
                elif agg_fn == "max":
                    out[agg_col] = max(values) if values else 0
            result.append(out)
        return result


class JoinNode(TransformNode):
    """Inner / left / right join between two CSV sources on key columns."""

    def __init__(self, left_key: str, right_key: str, how: str = "inner",
                 right_rows: list[Row] | None = None, node_id: str = "join"):
        self.node_id = node_id
        self.left_key = left_key
        self.right_key = right_key
        self.how = how
        self.right_rows = right_rows or []

    def transform(self, rows: list[Row]) -> list[Row]:
        # Build index of right rows by key
        right_index: dict[str, list[Row]] = {}
        for r in self.right_rows:
            key = str(r.get(self.right_key, ""))
            right_index.setdefault(key, []).append(r)

        result = []
        for left_row in rows:
            left_val = str(left_row.get(self.left_key, ""))
            matches = right_index.get(left_val, [])
            if self.how == "inner":
                if matches:
                    for m in matches:
                        merged = {**left_row, **{k: v for k, v in m.items() if k != self.right_key}}
                        result.append(merged)
                # inner: skip if no match
            elif self.how == "left":
                if matches:
                    for m in matches:
                        merged = {**left_row, **{k: v for k, v in m.items() if k != self.right_key}}
                        result.append(merged)
                else:
                    result.append(left_row)
            elif self.how == "right":
                # For right join, we need to also include unmatched right rows
                matched_keys = set()
                for m in matches:
                    merged = {**left_row, **{k: v for k, v in m.items() if k != self.right_key}}
                    result.append(merged)
                    matched_keys.add(str(m.get(self.right_key, "")))
                # Add unmatched right rows
                for m in self.right_rows:
                    rv = str(m.get(self.right_key, ""))
                    if rv not in matched_keys:
                        # Check if this right row was already added via another left row
                        already = any(
                            str(r.get(self.right_key, "")) == rv for r in result
                        )
                        if not already:
                            result.append(m)
            else:
                raise ValueError(f"Unknown join type: {self.how}")
        return result


class PivotNode(TransformNode):
    """Wide ↔ long reshaping.

    Converts long-form data (index, columns, values) into wide-form.
    """

    def __init__(self, index: list[str], columns: str, values: str,
                 agg: str = "first", node_id: str = "pivot"):
        self.node_id = node_id
        self.index = index
        self.columns = columns
        self.values = values
        self.agg = agg

    def transform(self, rows: list[Row]) -> list[Row]:
        # Collect all unique column values
        col_values: set[str] = set()
        # data[(index_tuple, col_val)] = list of values
        data: dict[tuple, dict[str, list]] = {}
        for r in rows:
            idx = tuple(r.get(c, "") for c in self.index)
            col = r.get(self.columns, "")
            val = r.get(self.values, "")
            col_values.add(col)
            data.setdefault(idx, {}).setdefault(col, []).append(val)

        col_values = sorted(col_values)
        result = []
        for idx, col_vals in data.items():
            out: dict[str, Any] = {}
            for i, c in enumerate(self.index):
                out[c] = idx[i]
            for col in col_values:
                vals = col_vals.get(col, [])
                if self.agg == "first" and vals:
                    out[col] = vals[0]
                elif self.agg == "sum":
                    try:
                        out[col] = sum(float(v) for v in vals)
                    except (ValueError, TypeError):
                        out[col] = 0
                elif self.agg == "count":
                    out[col] = len(vals)
                elif self.agg == "mean":
                    try:
                        out[col] = sum(float(v) for v in vals) / len(vals) if vals else 0
                    except (ValueError, TypeError):
                        out[col] = 0
                else:
                    out[col] = vals[0] if vals else ""
            result.append(out)
        return result


class CsvSource(TransformNode):
    """Reads rows from a CSV file."""

    def __init__(self, path: str, node_id: str = "csv_source"):
        self.node_id = node_id
        self.path = path

    def transform(self, rows: list[Row] | None = None) -> list[Row]:
        with open(self.path, newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)


class CsvSink(TransformNode):
    """Writes rows to a CSV file."""

    def __init__(self, path: str, node_id: str = "csv_sink"):
        self.node_id = node_id
        self.path = path

    def transform(self, rows: list[Row]) -> list[Row]:
        if not rows:
            return rows
        fieldnames = list(rows[0].keys())
        with open(self.path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return rows


class JsonSink(TransformNode):
    """Writes rows to a JSON file."""

    def __init__(self, path: str, node_id: str = "json_sink"):
        self.node_id = node_id
        self.path = path

    def transform(self, rows: list[Row]) -> list[Row]:
        import json
        with open(self.path, "w") as f:
            json.dump(rows, f, indent=2)
        return rows


class SqliteSink(TransformNode):
    """Writes rows to a SQLite table."""

    def __init__(self, path: str, table: str, node_id: str = "sqlite_sink"):
        self.node_id = node_id
        self.path = path
        self.table = table

    def transform(self, rows: list[Row]) -> list[Row]:
        import sqlite3
        conn = sqlite3.connect(self.path)
        cursor = conn.cursor()
        if rows:
            fieldnames = list(rows[0].keys())
            placeholders = ", ".join(["?"] * len(fieldnames))
            col_names = ", ".join(fieldnames)
            cursor.execute(f"DROP TABLE IF EXISTS {self.table}")
            cursor.execute(f"CREATE TABLE {self.table} ({', '.join(f'{c} TEXT' for c in fieldnames)})")
            for r in rows:
                vals = [str(r.get(c, "")) for c in fieldnames]
                cursor.execute(f"INSERT INTO {self.table} ({col_names}) VALUES ({placeholders})", vals)
        conn.commit()
        conn.close()
        return rows
