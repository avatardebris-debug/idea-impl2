# SOP Data Ingestion Bridge

## Overview

The **SOP Data Ingestion Bridge** is a Python library that reads Standard Operating Procedure (SOP) data from CSV files and transforms it into structured `SOPInputRow` objects. It supports custom column mappings, multiple encodings, and provides both a class-based API (`SOPBridge`) and a convenience function (`ingest()`).

## Installation

```bash
pip install -e .
```

Or simply ensure the package is importable:

```python
from sopdata_ingestion_bridge.bridge import SOPBridge, ingest
```

## Quick Start

### Using the convenience function

```python
from sopdata_ingestion_bridge import ingest

rows = ingest("sample_data.csv")
for row in rows:
    print(row.task_name, row.description)
```

### Using the class-based API

```python
from sopdata_ingestion_bridge.bridge import SOPBridge

bridge = SOPBridge()
rows = bridge.ingest("sample_data.csv")
```

### Custom column mapping

```python
custom_mapping = {
    "title": "task_name",
    "desc": "description",
    "step": "steps",
    "assigned_to": "assignee",
    "due_date": "deadline",
    "level": "priority",
}

rows = ingest("sample_data.csv", mapping=custom_mapping)
```

### Reading from a string

```python
from sopdata_ingestion_bridge.ingest import read_csv_from_string

csv_text = "task_name,description\nTask A,Desc A"
rows = read_csv_from_string(csv_text)
```

## API Reference

### `SOPBridge`

| Method | Description |
|---|---|
| `ingest(path, mapping=None)` | Reads a CSV file and returns a list of `SOPInputRow` instances. |

### `ingest()` (convenience function)

Identical to `SOPBridge().ingest()` but callable as a standalone function.

### `SOPInputRow`

| Attribute | Type | Description |
|---|---|---|
| `task_name` | `str` | Name of the SOP task |
| `description` | `str` | Description of the task |
| `steps` | `str` | Step-by-step instructions |
| `assignee` | `str` | Person responsible |
| `deadline` | `str` | Due date |
| `priority` | `str` | Priority level |

| Method | Description |
|---|---|
| `from_dict(data, mapping=None)` | Create an instance from a dict |
| `to_dict()` | Serialize to a dict (excludes raw CSV data) |

### `core.py` utilities

| Function | Description |
|---|---|
| `get_default_mapping()` | Returns the default column alias mapping (a copy) |
| `merge_mappings(default, custom)` | Merges custom mapping over default |

### `ingest.py` utilities

| Function | Description |
|---|---|
| `read_csv(path, encoding='utf-8')` | Read and parse a CSV file |
| `read_csv_from_string(csv_text)` | Parse CSV from a raw string |

### `transform.py` utilities

| Function | Description |
|---|---|
| `transform(rows, mapping=None)` | Transform raw CSV rows into `SOPInputRow` instances |

## Development

### Running tests

```bash
pytest -v
```

### Test coverage

```bash
pytest --cov=sopdata_ingestion_bridge --cov-report=term-missing
```

### Project structure

```
sopdata_ingestion_bridge/
├── __init__.py
├── bridge.py        # SOPBridge class and ingest() convenience function
├── core.py          # get_default_mapping, merge_mappings
├── ingest.py        # read_csv, read_csv_from_string
├── models.py        # SOPInputRow dataclass
├── transform.py     # transform() function
tests/
├── __init__.py
├── test_bridge.py   # Integration tests
├── test_core.py     # Core utility tests
├── test_edge_cases.py  # Edge case coverage
├── test_ingest.py   # CSV ingestion tests
├── test_models.py   # Model tests
└── test_transform.py  # Transform tests
```
