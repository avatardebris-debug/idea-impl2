# Deployment Guide

## Prerequisites

- Python 3.7+
- pip

## Installation

```bash
cd .pipeline/projects/robot_primitive_vocabulary_schema/workspace
pip install -e .
```

## Running Tests

```bash
pytest tests/
python verify.py
```

## CLI Usage

After installation, the `primitives` command is available:

```bash
primitives create grasp --json data.json
primitives validate data.json
primitives schema
```

## Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["primitives", "schema"]
```

## CI/CD

Add to your CI pipeline:

```yaml
test:
  script:
    - pytest tests/
    - python verify.py
```
