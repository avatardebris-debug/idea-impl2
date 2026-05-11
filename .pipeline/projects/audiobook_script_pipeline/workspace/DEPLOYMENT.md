# Audiobook Script Pipeline — Deployment Guide

## Table of Contents
- [Quick Start](#quick-start)
- [pip Install](#pip-install)
- [Docker](#docker)
- [Docker Compose](#docker-compose)
- [Environment Variables](#environment-variables)
- [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# Install from source
pip install -e .

# Run the CLI
audiobook-pipeline --version
audiobook-pipeline manuscript.txt
audiobook-pipeline manuscript.txt --format json
```

---

## pip Install

### From PyPI (once published)
```bash
pip install audiobook-script-pipeline
```

### From Source
```bash
cd audiobook_script_pipeline/workspace
pip install -e .
```

### From a Git Repository
```bash
pip install git+https://github.com/your-org/audiobook-script-pipeline.git
```

### Uninstall
```bash
pip uninstall audiobook-script-pipeline
```

---

## Docker

### Build the Image
```bash
docker build -t audiobook-pipeline .
```

### Run the Container
```bash
# Mount your manuscript file into the container
docker run --rm -v $(pwd):/data audiobook-pipeline /data/manuscript.txt

# With JSON output
docker run --rm -v $(pwd):/data audiobook-pipeline /data/manuscript.txt --format json

# With custom pause duration
docker run --rm -v $(pwd):/data audiobook-pipeline /data/manuscript.txt --pause 2.5

# With config file
docker run --rm -v $(pwd):/data audiobook-pipeline /data/manuscript.txt --config /data/config.json
```

### Dockerfile Reference
```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

ENTRYPOINT ["audiobook-pipeline"]
```

---

## Docker Compose

### docker-compose.yml
```yaml
version: '3.8'

services:
  audiobook-pipeline:
    build: .
    volumes:
      - ./manuscripts:/data/manuscripts
      - ./output:/data/output
      - ./config:/data/config
    environment:
      - DEFAULT_PAUSE=1.5
    command: /data/manuscripts/manuscript.txt --format json --output /data/output/result.json
```

### Run with Compose
```bash
docker compose up --build
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `DEFAULT_PAUSE` | Default pause duration in seconds | `1.0` |
| `MANUSCRIPT_PATH` | Path to the manuscript file (if not passed as CLI arg) | — |
| `OUTPUT_PATH` | Path to write the output file | stdout |
| `OUTPUT_FORMAT` | Output format: `text` or `json` | `text` |

### Example with Environment Variables
```bash
export DEFAULT_PAUSE=2.0
export OUTPUT_FORMAT=json
audiobook-pipeline manuscript.txt
```

---

## Troubleshooting

### "File not found" error
- Ensure the manuscript file path is correct and the file exists.
- When using Docker, ensure the file is mounted into the container:
  ```bash
  docker run --rm -v $(pwd):/data audiobook-pipeline /data/manuscript.txt
  ```

### "Manuscript is empty" error
- The manuscript file is empty or contains only whitespace.
- Provide a valid manuscript file with text content.

### "No module named 'audiobook_script_pipeline'"
- The package is not installed in the current Python environment.
- Run `pip install -e .` from the workspace directory.

### JSON output is not valid
- Ensure you are using `--format json` flag.
- Verify the output is being captured correctly (not mixed with CLI messages).

### Import errors when using as a library
- Ensure the package is installed: `pip install -e .`
- Use the public API:
  ```python
  from audiobook_script_pipeline import ScriptPipeline
  pipeline = ScriptPipeline(default_pause=1.5)
  result = pipeline.run("manuscript.txt")
  ```

### Docker build fails
- Ensure Docker is installed and running.
- Check that `pyproject.toml` and `requirements.txt` are in the build context.
- Try building with `--no-cache`:
  ```bash
  docker build --no-cache -t audiobook-pipeline .
  ```
