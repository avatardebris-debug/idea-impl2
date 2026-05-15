# JSON Schema Profiler

A fast, lightweight CLI tool to scan JSON or Parquet datasets, infer schemas, detect anomalies, and output validation rules.

## Installation

```bash
pip install json-schema-profiler
```

To support Parquet files and YAML output:
```bash
pip install "json-schema-profiler[all]"
```

## Usage

### Infer Schema
Infer a basic JSON schema from a file:
```bash
json-schema-profiler infer data.json
```

### Analyze Datasets
Detect anomalies and infer schema with confidence scores:
```bash
json-schema-profiler analyze data.parquet --format pydantic
```

### Stream Large Files
Process gigabyte-scale datasets without running out of memory:
```bash
json-schema-profiler analyze large-file.jsonl --stream
```

### Compare Schemas
Detect schema drift between two schema files:
```bash
json-schema-profiler compare v1_schema.json v2_schema.json
```

## Output Formats
- **jsonschema**: Standard JSON Schema draft-07.
- **yaml**: Structured YAML including anomaly reports.
- **pydantic**: Auto-generated Python models for validation.
