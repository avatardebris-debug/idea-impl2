# Phase 2 Tasks: Cost & Telemetry Integration

[x] **Task 1: Log Parser.**
    - Scan the workspace of each project for `SOPExecutor` execution log JSON files (e.g. `execution_log.json` if available).
    - Aggregate step execution duration, success/error rates, and `tokens_used`.

[x] **Task 2: Cost Calculator.**
    - Implement a `CostCalculator` class using token usage and model pricing.
    - Compute estimated total cost per project and across the entire pipeline.
    
[x] **Task 3: Integration with Aggregation Service.**
    - Augment `ProjectState` with `cost_estimate`, `error_rate`, and `avg_step_duration`.
    - Update integration tests.
