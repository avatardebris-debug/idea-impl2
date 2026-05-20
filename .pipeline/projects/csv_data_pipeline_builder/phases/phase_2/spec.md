## Phase 2 — Pipeline YAML DSL & Validation
- Design `pipeline.yaml` schema (sources, steps, sinks)
- Implement `PipelineLoader`: parse + validate YAML against JSON Schema
- Implement dry-run mode: infer output schema without executing transforms
- Add `JsonSink` and `SqliteSink` export backends
- CLI: `csv-pipeline validate pipeline.yaml`
- CLI: `csv-pipeline dry-run pipeline.yaml --show-schema`
- Tests: YAML round-trip, schema inference accuracy

