# JSON Schema Profiler — Master Implementation Plan

## Overview

A CLI tool that scans JSON or Parquet datasets, infers schemas, detects anomalies, and outputs standardized validation rules.

### Core Deliverable
A Python CLI application (`json-schema-profiler`) that accepts input files/directories, performs schema inference and anomaly detection, and emits machine-readable validation rules (JSON Schema / custom format) for downstream use in data pipelines, APIs, or quality gates.

---

## Architecture Notes

```
┌─────────────────────────────────────────────────────────┐
│                    CLI Entry Point                      │
│              (click / typer argument parsing)            │
├──────────┬──────────┬──────────────┬───────────────────┤
│  Source   │  Schema  │  Anomaly     │   Output          │
│  Loader   │  Inference│  Detector    │  Formatter        │
│           │          │              │                   │
│ JSON      │  Type    │  Statistical │  JSON Schema      │
│ Parquet   │  Inference│  + Rule-based│  (jsonschema)     │
│           │  (min/max│  (null rates,│  Custom YAML      │
│           │  outliers│   cardinality│  (pydantic rules) │
│           │  skew)  │  checks)      │                   │
└──────────┴──────────┴──────────────┴───────────────────┘
         │           │              │
         ▼           ▼              ▼
   ┌─────────────────────────────────────┐
   │         Rule Aggregator             │
   │   (unifies per-field rules)         │
   └─────────────────────────────────────┘
```

### Key Design Decisions
- **Language**: Python 3.10+ (rich ecosystem for JSON/Parquet/schema libraries)
- **CLI Framework**: `typer` (clean, fast, auto-docs)
- **JSON Schema Output**: `jsonschema` library for validation
- **Parquet Support**: `pyarrow` / `pandas`
- **Schema Inference**: Custom logic (no heavy ML dependency — keep it lightweight)
- **Anomaly Detection**: Statistical (z-score, IQR) + rule-based (null %, cardinality, pattern match)
- **No external API calls** — fully offline, deterministic

### Risk Register

| Risk | Impact | Mitigation |
|------|--------|------------|
| Large files cause OOM | High | Stream processing with chunked reads; configurable sample size |
| Parquet schema inference is lossy | Medium | Use pyarrow's native schema as baseline; augment with data stats |
| Schema inference ambiguity (e.g. mixed types) | Medium | Report ambiguity as warnings; use most-likely type with confidence score |
| Anomaly detection false positives | Medium | Configurable thresholds; output confidence levels |
| CLI dependency bloat | Low | Pin minimal deps; use optional extras for parquet |

---

## Phase 1: JSON Schema Inference (MVP)

> **Goal**: A working CLI that reads a JSON file and outputs an inferred JSON Schema.

### Description
Build the core schema inference engine for JSON data. The tool reads a JSON file (or array of objects), analyzes field types, value distributions, and structural patterns, then emits a JSON Schema document. This is the smallest useful thing — a developer can immediately validate data against the inferred schema.

### Deliverable
- CLI command: `json-schema-profiler infer <input.json>`
- Output: A valid JSON Schema (`draft-07`) written to stdout or `--output <file>`
- Per-field metadata: type, required/optional, min/max (for numbers), length (for strings), enum candidates (for low-cardinality fields)
- Unit tests covering: simple objects, nested objects, arrays, mixed types, empty arrays

### Dependencies
- None (pure Python core; `json` stdlib only)

### Success Criteria
- [ ] Given a JSON file of 100 objects with 5 fields (string, int, float, bool, nested), the tool produces a valid JSON Schema with correct type annotations
- [ ] Nested objects are recursively inferred
- [ ] Arrays of objects infer the item schema
- [ ] Low-cardinality string fields are flagged as potential enums
- [ ] CLI exits with code 0 on success, non-zero on error
- [ ] `--help` displays usage
- [ ] All unit tests pass (≥ 15 test cases)

---

## Phase 2: Anomaly Detection + Parquet Support + Validation Rule Output

> **Goal**: Extend the tool to detect data anomalies, support Parquet files, and output richer validation rules.

### Description
Add three capabilities:
1. **Anomaly detection**: Statistical analysis (null rates, value distribution outliers, cardinality anomalies, numeric skew) with configurable thresholds.
2. **Parquet support**: Read `.parquet` files using pyarrow, infer schemas from both schema metadata and sampled data.
3. **Validation rule output**: Emit structured validation rules beyond JSON Schema — including custom YAML format with anomaly metadata, confidence scores, and suggested fixes.

### Deliverable
- CLI command: `json-schema-profiler analyze <input.{json,parquet}>`
- Anomaly report embedded in output with per-field stats
- Parquet file support (single file and directory of files)
- Output formats: `--format jsonschema | yaml | pydantic`
- Integration tests with sample Parquet datasets

### Dependencies
- Phase 1 complete
- New deps: `pyarrow`, `pandas`, `pyyaml` (optional extras)

### Success Criteria
- [ ] Tool reads a Parquet file and infers schema correctly (matching pyarrow schema)
- [ ] Anomaly detection identifies: null rates > threshold, numeric outliers (IQR method), cardinality anomalies, pattern mismatches
- [ ] Output includes confidence scores for each anomaly
- [ ] All three output formats produce valid, parseable output
- [ ] Directory scanning works (processes all `.json` / `.parquet` files)
- [ ] Integration tests pass with sample datasets (≥ 10 test scenarios)
- [ ] CLI `analyze` command is a superset of `infer` (backwards compatible)

---

## Phase 3: CLI Polish, Production Readiness, and Distribution

> **Goal**: Ship a production-quality, distributable CLI tool.

### Description
Finalize the tool with production features: streaming/large-file support, progress reporting, caching, and packaging. Add a `compare` subcommand to diff schemas across runs (useful for detecting schema drift). Publish to PyPI.

### Deliverable
- `json-schema-profiler compare <schema-a> <schema-b>` — schema drift detection
- Streaming mode: `--stream --chunk-size 10000` for large files (memory-bounded)
- Progress bar (`rich.progress`) for long-running operations
- Config file support: `~/.json-schema-profiler.yaml` for defaults
- Caching: skip re-analysis if input hasn't changed (mtime + hash)
- Packaging: `pyproject.toml`, entry point, PyPI publishable
- Documentation: README, CLI help, example workflows

### Dependencies
- Phase 2 complete
- New deps: `rich`, `click` (if not using typer), `xxhash`

### Success Criteria
- [ ] `compare` command identifies added, removed, and changed fields with diff summary
- [ ] Streaming mode processes a 1GB+ JSON file with < 100MB RSS memory
- [ ] Tool is installable via `pip install json-schema-profiler`
- [ ] PyPI package metadata is correct (description, classifiers, license)
- [ ] README includes: install, usage examples, output format docs
- [ ] `--version` displays version string
- [ ] All previous tests still pass (regression check)

---

## Summary of Phases

| Phase | Scope | Key Output | Est. Effort |
|-------|-------|------------|-------------|
| 1 | JSON schema inference | `infer` command, JSON Schema output | 2-3 days |
| 2 | Anomalies + Parquet + rule output | `analyze` command, multi-format output | 3-4 days |
| 3 | Production polish + distribution | `compare`, streaming, PyPI package | 2-3 days |

**Total estimated effort: 7-10 days**
