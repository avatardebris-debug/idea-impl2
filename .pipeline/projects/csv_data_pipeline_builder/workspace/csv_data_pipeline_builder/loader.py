"""
csv_data_pipeline_builder/loader.py
YAML DSL parser — converts a pipeline.yaml into a Pipeline object.

pipeline.yaml format:
---
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
      id: count

sinks:
  - id: output_csv
    type: csv
    path: output/result.csv
"""
from __future__ import annotations

import pathlib
from typing import Any

from .nodes import (
    FilterNode, SelectNode, AggregateNode, JoinNode, PivotNode,
    CsvSource, CsvSink, JsonSink, SqliteSink,
)
from .pipeline import Pipeline


class PipelineLoader:
    """Parse and validate a pipeline.yaml into a Pipeline object."""

    def __init__(self):
        try:
            import yaml
            self.yaml = yaml
        except ImportError:
            raise ImportError("pyyaml is required for PipelineLoader")

    def load(self, path: str | pathlib.Path) -> Pipeline:
        """Load a pipeline from a YAML file."""
        path = pathlib.Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {path}")

        with open(path) as f:
            data = self.yaml.safe_load(f)

        if not data or not isinstance(data, dict):
            raise ValueError("Invalid pipeline YAML: must be a mapping")

        pipeline = Pipeline()

        # Load sources
        sources = data.get("sources", {}) or {}
        for name, src_path in sources.items():
            node = CsvSource(path=str(src_path), node_id=f"source_{name}")
            pipeline.add_node(node)
            pipeline.sources[name] = str(src_path)

        # Load steps
        steps = data.get("steps", []) or []
        for step in steps:
            node = self._build_node(step, pipeline)
            pipeline.add_node(node)

        # Load sinks
        sinks = data.get("sinks", []) or []
        for sink in sinks:
            node = self._build_sink(sink)
            pipeline.add_node(node)

        # Wire edges: source -> first step, step -> next step, last step -> sink
        all_nodes = [n for n in pipeline.nodes]
        for i in range(len(all_nodes) - 1):
            pipeline.add_edge(all_nodes[i].node_id, all_nodes[i + 1].node_id)

        return pipeline

    def _build_node(self, step: dict[str, Any], pipeline: Pipeline) -> Any:
        """Build a transform node from a step definition."""
        node_id = step.get("id", "unnamed")
        node_type = step.get("type", "")

        if node_type == "filter":
            return FilterNode(
                predicate_expr=step.get("predicate", "True"),
                node_id=node_id,
            )
        elif node_type == "select":
            columns = step.get("columns", [])
            rename = step.get("rename", None)
            return SelectNode(
                columns=columns,
                rename=rename,
                node_id=node_id,
            )
        elif node_type == "aggregate":
            group_by = step.get("group_by", [])
            aggregations = step.get("aggregations", {})
            return AggregateNode(
                group_by=group_by,
                aggregations=aggregations,
                node_id=node_id,
            )
        elif node_type == "join":
            left_key = step.get("left_key", "")
            right_key = step.get("right_key", "")
            how = step.get("how", "inner")
            right_source = step.get("right_source", None)
            # Resolve right source rows from pipeline sources
            right_rows: list = []
            if right_source and right_source in pipeline.sources:
                src_path = pipeline.sources[right_source]
                import csv
                with open(src_path, newline="") as f:
                    right_rows = list(csv.DictReader(f))
            return JoinNode(
                left_key=left_key,
                right_key=right_key,
                how=how,
                right_rows=right_rows,
                node_id=node_id,
            )
        elif node_type == "pivot":
            index = step.get("index", [])
            columns = step.get("columns", "")
            values = step.get("values", "")
            agg = step.get("agg", "first")
            return PivotNode(
                index=index,
                columns=columns,
                values=values,
                agg=agg,
                node_id=node_id,
            )
        else:
            raise ValueError(f"Unknown node type: {node_type}")

    def _build_sink(self, sink: dict[str, Any]) -> Any:
        """Build a sink node from a sink definition."""
        node_id = sink.get("id", "sink")
        sink_type = sink.get("type", "")

        if sink_type == "csv":
            return CsvSink(path=sink.get("path", "output.csv"), node_id=node_id)
        elif sink_type == "json":
            return JsonSink(path=sink.get("path", "output.json"), node_id=node_id)
        elif sink_type == "sqlite":
            return SqliteSink(
                path=sink.get("path", "output.db"),
                table=sink.get("table", "output"),
                node_id=node_id,
            )
        else:
            raise ValueError(f"Unknown sink type: {sink_type}")
