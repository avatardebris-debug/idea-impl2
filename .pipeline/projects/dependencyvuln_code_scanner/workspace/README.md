# depvuln — Dependency Vulnerability Scanner

A CLI tool that scans npm and pip dependency manifests for known CVEs using the OSV API.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Scan a project directory (auto-detects npm or pip)
depvuln scan ./path/to/project

# Specify output format
depvuln scan ./path/to/project --format json
depvuln scan ./path/to/project --format text

# Enable/disable caching (default: enabled)
depvuln scan ./path/to/project --cache
depvuln scan ./path/to/project --no-cache
```

## Flags

| Flag | Description |
|------|-------------|
| `--format` | Output format: `text` (default) or `json` |
| `--cache` | Enable SQLite-based caching of CVE lookups (default) |
| `--no-cache` | Disable caching |
| `--help` | Show help message |

## Output Examples

### Text Format

```
[CRITICAL] lodash==4.17.20 — CVE-2021-23337 — CVSS: 9.8
  Description: Command injection via template strings
  Fix: Upgrade to lodash >= 4.17.21

[HIGH] express==4.17.1 — CVE-2022-24999 — CVSS: 7.5
  Description: Open redirect vulnerability
  Fix: Upgrade to express >= 4.18.2
```

### JSON Format

```json
[
  {
    "severity": "CRITICAL",
    "package": "lodash",
    "version": "4.17.20",
    "cve_id": "CVE-2021-23337",
    "cvss": 9.8,
    "description": "Command injection via template strings",
    "fix": "Upgrade to lodash >= 4.17.21"
  }
]
```

## Supported Ecosystems

- **npm**: Reads `package-lock.json` and `yarn.lock`
- **pip**: Reads `requirements.txt` and `Pipfile.lock`

## Architecture

```
depvuln/
├── cli.py          # Click-based CLI entry point
├── parsers/        # Dependency manifest parsers
│   ├── base.py
│   ├── npm_parser.py
│   └── pip_parser.py
├── cve/            # CVE data fetching and caching
│   ├── fetcher.py
│   └── cache.py
├── reports/        # Report generators
│   ├── json_report.py
│   └── text_report.py
├── scorer.py       # CVSS severity scoring
└── __main__.py     # Entry point
```
