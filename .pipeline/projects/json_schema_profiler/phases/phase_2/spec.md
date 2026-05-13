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

