# CSV Data Pipeline Builder — Master Plan

## Overview
Extends csv_analyzer with a visual DAG-based pipeline builder that chains
transformations (filter, join, pivot, aggregate) between multiple CSV files
and exports results to SQL or JSON.

## Phase 1 — Transform Node Engine
- Implement `TransformNode` base class and concrete node types:
  - `FilterNode`: row-level predicate filtering (expression DSL)
  - `SelectNode`: column projection / rename
  - `AggregateNode`: group-by + aggregation (sum, mean, count, min, max)
  - `JoinNode`: inner/left/right join between two CSV sources on key columns
  - `PivotNode`: wide ↔ long reshaping
- Implement `Pipeline` DAG: nodes + directed edges, cycle detection
- Implement `CsvSource` and `CsvSink` I/O nodes
- CLI: `csv-pipeline run pipeline.yaml`
- Tests: each node type with sample CSV data

## Phase 2 — Pipeline YAML DSL & Validation
- Design `pipeline.yaml` schema (sources, steps, sinks)
- Implement `PipelineLoader`: parse + validate YAML against JSON Schema
- Implement dry-run mode: infer output schema without executing transforms
- Add `JsonSink` and `SqliteSink` export backends
- CLI: `csv-pipeline validate pipeline.yaml`
- CLI: `csv-pipeline dry-run pipeline.yaml --show-schema`
- Tests: YAML round-trip, schema inference accuracy

## Phase 3 — Interactive Builder TUI & Reporting
- Implement `PipelineBuilder` terminal UI (using `rich` layout panels):
  - Left panel: available CSVs and columns
  - Center: DAG node graph (ASCII art via `rich.tree`)
  - Right: node config editor
- Implement `ExecutionReport`: per-node row counts, timing, memory delta
- Add pipeline diff: compare two runs for schema or data drift
- CLI: `csv-pipeline build` (launches TUI)
- CLI: `csv-pipeline report --last` (prints last execution summary)
- Tests: TUI smoke test, execution report golden file
