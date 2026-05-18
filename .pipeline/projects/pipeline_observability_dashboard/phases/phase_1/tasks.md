# Phase 1 Tasks: Metrics Aggregation Engine

[x] **Task 1: Setup project structure and core dataclasses.**
    - Define Pydantic models (or dataclasses) for `ProjectState`, `PhaseStatus`, and `GlobalMetrics`.
    - Setup `pyproject.toml` with `pytest` and `pydantic`.
    - Write unit tests verifying model initialization.

[x] **Task 2: Build the Directory Scanner.**
    - Implement a `PipelineScanner` class that takes the pipeline root directory.
    - Discover all active projects in `.pipeline/projects/`.
    - Extract basic project names.
    - Write test asserting it finds existing mock project directories.

[x] **Task 3: State Extractor.**
    - Implement logic to read `state/current_phase.json`, `state/phase_retries.json`, and `state/current_idea.json` for each project.
    - Handle missing files safely (defaulting to "unstarted" or "unknown").
    - Write tests mocking the file system and validating correct state inference.

[x] **Task 4: Aggregation Service.**
    - Combine scanner and extractor into an `AggregationService`.
    - Expose a `get_all_projects_status()` method returning a list of `ProjectState`.
    - Validate with an integration test against a temporary file tree.
