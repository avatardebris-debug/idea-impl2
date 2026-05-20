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

