# FFO Deployment Guide

## Prerequisites

- Python 3.10+
- pip
- Git

## Development Setup

```bash
# Clone the repository
git clone <repo-url>
cd ffo

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Run linting
ruff check .
ruff format --check .
```

## Building the Package

```bash
# Build the package
pip install build
python -m build

# The built wheel will be in dist/
ls dist/
```

## Publishing to PyPI

### Option 1: Manual Publishing

```bash
# Install twine
pip install twine

# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Verify installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple ffo

# If everything works, upload to PyPI
twine upload dist/*
```

### Option 2: Automated Publishing (GitHub Actions)

See `.github/workflows/publish.yml` for the CI/CD pipeline.

## Docker Deployment

### Build the Docker image

```bash
docker build -t ffo:latest .
```

### Run in a container

```bash
docker run --rm ffo:latest python -m ffo.cli optimize \
    --roster /data/roster.json \
    --pool /data/pool.json \
    --cap 100000000
```

### Docker Compose

```yaml
version: '3.8'
services:
  ffo:
    build: .
    volumes:
      - ./data:/data
    command: >
      python -m ffo.cli optimize
      --roster /data/roster.json
      --pool /data/pool.json
      --cap 100000000
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `FFO_LOG_LEVEL` | Logging level (DEBUG, INFO, WARNING, ERROR) | `INFO` |
| `FFO_OUTPUT_DIR` | Default output directory for reports | `./output` |

## Configuration

FFO can be configured via a YAML config file:

```yaml
# ffo_config.yaml
salary_cap: 100000000
age_weight: 1.0
contract_weight: 1.0
roster_path: roster.json
pool_path: pool.json
output_dir: ./output
```

Usage:

```bash
python -m ffo.cli optimize --config ffo_config.yaml
```

## Production Considerations

1. **Salary Cap Limits**: Ensure the salary cap is set appropriately for the league/season.
2. **Data Validation**: Always validate input data before running optimization.
3. **Logging**: Configure logging to capture optimization decisions for audit trails.
4. **Backup**: Keep backups of original roster data before running optimization.
5. **Review**: Always review optimization results before making roster changes.

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure you're in the correct virtual environment and the package is installed.
2. **File not found**: Check that roster and pool JSON files exist at the specified paths.
3. **Salary cap exceeded**: The optimizer will raise an error if no valid roster can be formed within the cap.

### Debug Mode

```bash
# Enable debug logging
FFO_LOG_LEVEL=DEBUG python -m ffo.cli optimize --roster roster.json --pool pool.json --cap 100000000
```

## Support

For issues and questions, please open a GitHub issue or contact the maintainers.
