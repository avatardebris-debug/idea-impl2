# VAST.ai Instance Initializer

A preset-driven CLI tool for launching and managing VAST.ai GPU instances.

## Overview

`vastai-init` simplifies launching GPU instances on VAST.ai by using YAML preset files to define instance configurations. It handles validation, authentication, instance creation, status polling, and session logging.

## Installation

```bash
pip install typer pyyaml requests
```

## Configuration

Set your VAST.ai API key via environment variable:

```bash
export VASTAI_API_KEY="your-api-key-here"
```

Or create a config file at `~/.vastai-init/config.ini`:

```ini
[api]
api_key = your-api-key-here
```

## Usage

### Launch an instance

```bash
vastai-init launch presets/default.yaml
```

### Validate a preset (without launching)

```bash
vastai-init validate presets/default.yaml
```

### Dry run (show config without launching)

```bash
vastai-init launch presets/default.yaml --dry-run
```

### Verbose output

```bash
vastai-init launch presets/default.yaml --verbose
```

## Preset Files

Preset files are YAML files that define the instance configuration. See the `presets/` directory for examples.

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Instance name (for your reference) |
| `gpu_type` | string | GPU type (e.g., "NVIDIA RTX 4090") |
| `price_cap` | string/number | Maximum price per hour in USD |
| `storage` | string | Storage size with unit (e.g., "100GB") |
| `image` | string | Docker image to use |

### Optional Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `ssh_commands` | list | `[]` | Commands to run after launch |
| `env_vars` | dict | `{}` | Environment variables |
| `disk_size` | int/string | `null` | Total disk size |
| `region` | string | `null` | Preferred region |
| `min_vram` | int/string | `null` | Minimum VRAM in GB |
| `uptime` | int/string | `null` | Maximum uptime |
| `ssh_public_key` | string | `null` | SSH public key |
| `docker_args` | dict | `{}` | Docker arguments |
| `ports` | list | `[]` | Ports to expose |
| `labels` | dict | `{}` | Instance labels |
| `timeout` | int | `300` | Polling timeout in seconds |
| `poll_interval` | int | `10` | Seconds between polls |

## Sample Presets

- `presets/default.yaml` — General-purpose GPU instance
- `presets/training-gpu.yaml` — High-memory GPU for deep learning training

## Session Logs

Session logs are stored in `~/.vastai-init/sessions/sessions.json` and contain:

- Timestamp
- Preset name and path
- Instance ID
- Final status
- SSH connection details
- GPU type, price cap, storage, and image

## Architecture

```
vastai_init/
├── __init__.py
├── cli.py              # CLI entry point
├── api/
│   ├── __init__.py
│   ├── adapter.py      # Instance creation logic
│   └── auth.py         # Authentication logic
├── monitor/
│   ├── __init__.py
│   └── status.py       # Status polling logic
├── launcher/
│   ├── __init__.py
│   └── session.py      # Session logging logic
└── utils/
    ├── __init__.py
    └── config.py       # Configuration utilities
presets/
├── default.yaml
└── training-gpu.yaml
```

## License

MIT
