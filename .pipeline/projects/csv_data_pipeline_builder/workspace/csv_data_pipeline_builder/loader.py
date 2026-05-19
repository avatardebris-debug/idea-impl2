"""
csv_data_pipeline_builder/loader.py
YAML DSL parser — converts a pipeline.yaml into a Pipeline object.

pipeline.yaml format:
-----------------------
sources:
  sales: data/sales.csv
  customers: data/customers.csv

steps:
  - id: filter_2024
    type: filter
    predicate: "year == '2024'"

  - id: join_customers
    type: join
    left_key: customer_id
    right_key: id
    right_source: customers
    how: left

  - id: agg_by_region
    type: aggregate
    group_by: [region]
    aggregations:
      revenue: sum
      order_count: count

  - id: select_cols
    type: select
    columns: [region, revenue, order_count]

sinks:
  - type: csv
    path: output/report.csv
  - type: sqlite
    path: output/report.db
    table: sales_summary
"""
from __future__ import annotations

import pathlib
from typing import Any

from .nodes import FilterNode, SelectNode, AggregateNode, JoinNode, PivotNode
from .pipeline import Pipeline, CsvSource, CsvSink, JsonSink, SqliteSink


def load_pipeline(yaml_path: str | pathlib.Path, base_dir: str | pathlib.Path | None = None) -> Pipeline:
    """Parse a pipeline YAML file and return a configured Pipeline."""
    try:
        import yaml  # type: ignore[import]
    except ImportError:
        raise ImportError("pip install pyyaml  # required for pipeline YAML loading")

    yaml_path = pathlib.Path(yaml_path)
    base = pathlib.Path(base_dir) if base_dir else yaml_path.parent

    with open(yaml_path, encoding="utf-8") as f:
        spec: dict[str, Any] = yaml.safe_load(f)

    # --- Sources ---
    sources: dict[str, list] = {}
    for name, path in (spec.get("sources") or {}).items():
        src = CsvSource(path=str(base / path))
        sources[name] = src.load()

    # Primary source = first declared source
    primary_name = next(iter(spec.get("sources", {})), None)
    primary_rows = sources.get(primary_name, []) if primary_name else []

    pipeline = Pipeline()

    # --- Steps ---
    for step in spec.get("steps") or []:
        step_type = step.get("type", "").lower()
        step_id   = step.get("id", step_type)

        if step_type == "filter":
            node = FilterNode(node_id=step_id, predicate_expr=step.get("predicate", "True"))

        elif step_type == "select":
            rename = step.get("rename", {})
            node = SelectNode(node_id=step_id, columns=step.get("columns", []), rename=rename)

        elif step_type == "aggregate":
            node = AggregateNode(
                node_id=step_id,
                group_by=step.get("group_by", []),
                aggregations=step.get("aggregations", {}),
            )

        elif step_type == "join":
            right_src = step.get("right_source", "")
            right_rows = sources.get(right_src, [])
            node = JoinNode(
                node_id=step_id,
                left_key=step.get("left_key", "id"),
                right_key=step.get("right_key", "id"),
                how=step.get("how", "inner"),
                right_rows=right_rows,
            )

        elif step_type == "pivot":
            node = PivotNode(
                node_id=step_id,
                index=step.get("index", []),
                columns=step.get("columns", ""),
                values=step.get("values", ""),
                agg=step.get("agg", "first"),
            )

        else:
            raise ValueError(f"Unknown step type: '{step_type}' in step '{step_id}'")

        pipeline.add_node(node)

    # Pre-load primary source rows so pipeline.execute() doesn't need a CsvSource
    pipeline._preloaded_rows = primary_rows  # type: ignore[attr-defined]

    # --- Sinks ---
    for sink_spec in spec.get("sinks") or []:
        sink_type = sink_spec.get("type", "").lower()
        sink_path = str(base / sink_spec["path"]) if "path" in sink_spec else ""
        if sink_type == "csv":
            pipeline.add_sink(CsvSink(path=sink_path))
        elif sink_type == "json":
            pipeline.add_sink(JsonSink(path=sink_path))
        elif sink_type == "sqlite":
            pipeline.add_sink(SqliteSink(path=sink_path, table=sink_spec.get("table", "output")))

    return pipeline, primary_rows


def execute_yaml(yaml_path: str | pathlib.Path, base_dir: str | pathlib.Path | None = None):
    """Load and execute a pipeline YAML. Returns (rows, reports)."""
    pipeline, seed_rows = load_pipeline(yaml_path, base_dir)
    return pipeline.execute(seed_rows)
