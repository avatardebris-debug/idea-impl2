# Phase 3 Specification: Production Polish and Distribution

## 1. Overview
In Phase 3, we transition `json-schema-profiler` from a functional library to a production-ready, distributable CLI tool capable of handling large datasets, detecting schema drift, and integrating into automated data pipelines.

## 2. Core Features

### 2.1 Schema Drift Detection
- Introduce a `compare` command that takes two inferred schema objects (or saved files) and identifies added, removed, or changed fields. This is critical for data engineers to monitor if upstream data sources have silently altered their format.

### 2.2 Streaming Mode for Large Files
- Introduce a `--stream` flag for processing massive JSON/JSONL datasets without OOM (Out-Of-Memory) issues.
- Read files in chunks (e.g., via `ijson` for JSON, or line-by-line for JSONL) rather than loading the entire file into memory.

### 2.3 Progress Indicators
- Integrate `rich.progress` to display real-time progress bars when scanning large directories or streaming heavy files.

### 2.4 Caching
- Avoid re-analyzing large datasets if their content (mtime + file hash) hasn't changed.
- Use `xxhash` for fast file hashing and store a local cache manifest.

### 2.5 Config File Support
- Load defaults from `~/.json-schema-profiler.yaml` (e.g., default anomaly thresholds, preferred output formats).

### 2.6 Packaging & Distribution
- Set up `pyproject.toml` correctly to build wheels and source distributions.
- Write a comprehensive `README.md` containing install instructions and example workflows.

## 3. Success Criteria
- [ ] `compare` command correctly identifies added/removed/changed fields.
- [ ] Large files (e.g., 5GB JSONL) can be processed with `< 100MB` memory usage.
- [ ] Re-running analysis on unchanged files completes instantly due to caching.
- [ ] Package is installable and publishable to PyPI.
