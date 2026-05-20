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