# Master Plan: Pipeline Observability Dashboard

## 1. Architectural Vision
Build a lightweight, fast, local web dashboard (using FastAPI + vanilla HTML/JS/CSS for minimal dependencies and maximum aesthetic control) that monitors the multi-agent pipeline in real-time. It aggregates data from three primary sources:
1. **Pipeline State**: The `.pipeline/projects/*/state/` directories (current phases, tasks, retries, validation status).
2. **Execution Logs**: The `shared_libs/llmclient/executor.py` step logs and duration metrics.
3. **LLM Cost/Metrics**: The `UniversalRouter` metrics (requests, failures, latency, and token costs across providers).

## 2. Phase Deconstruction

**Phase 1: Metrics Aggregation Engine (Data Layer)**
- **Goal**: Build a data aggregator that scans the `.pipeline/projects/` directory and parses the dispersed `.json` and `.md` state files into a unified memory model.

**Phase 2: Cost & Telemetry Integration (Analytics Layer)**
- **Goal**: Integrate token cost calculations and error rate telemetry.

**Phase 3: Web Dashboard UI (Presentation Layer)**
- **Goal**: Stand up a fast, visually stunning, local dashboard to render the aggregated data.
