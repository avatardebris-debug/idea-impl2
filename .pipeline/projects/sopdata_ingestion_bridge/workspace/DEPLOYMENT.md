# Deployment Guide — SOPData Ingestion Bridge

## Installation

### pip (from PyPI, once published)

```bash
pip install sopdata-ingestion-bridge
```

### Editable install (development)

```bash
cd sopdata_ingestion_bridge/workspace
pip install -e .
```

### From source

```bash
git clone <repo-url>
cd <repo>/sopdata_ingestion_bridge/workspace
pip install -e .
```

---

## CLI Usage

The package ships a console script `sopdata-ingestion-bridge`.

### Basic usage (JSON output)

```bash
sopdata-ingestion-bridge --csv sample_data.csv
```

### Table output

```bash
sopdata-ingestion-bridge --csv sample_data.csv --format table
```

### Custom column mapping

```bash
sopdata-ingestion-bridge --csv data.csv --mapping custom_mapping.json
```

### Help

```bash
sopdata-ingestion-bridge --help
```

---

## Docker Deployment

### Build the image

```bash
docker build -t sopdata-ingestion-bridge:latest .
```

### Run as a container

```bash
docker run --rm \
  -v $(pwd)/sample_data.csv:/app/sample_data.csv \
  sopdata-ingestion-bridge:latest \
  --csv /app/sample_data.csv
```

### Docker Compose (optional)

```yaml
version: "3.8"
services:
  bridge:
    build: .
    volumes:
      - ./data:/app/data
    command: --csv /app/data/input.csv --format table
```

---

## CI/CD Integration

### GitHub Actions (example)

```yaml
name: Test & Deploy
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest -v
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install build twine
      - run: python -m build
      - run: twine upload dist/*
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
```

---

## PyPI Release Checklist

- [ ] Bump version in `pyproject.toml`
- [ ] Update `CHANGELOG.md`
- [ ] Run full test suite: `pytest -v`
- [ ] Run type checks: `mypy sopdata_ingestion_bridge/`
- [ ] Build wheel/sdist: `python -m build`
- [ ] Dry-run upload: `twine check dist/*`
- [ ] Upload to PyPI: `twine upload dist/*`
- [ ] Verify install: `pip install sopdata-ingestion-bridge`
- [ ] Tag release in Git
