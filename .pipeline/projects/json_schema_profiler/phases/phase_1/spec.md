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