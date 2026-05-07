# Forensic Suite

A fraud detection analysis tool for SEC EDGAR filings.

## Features

- Fetches latest 10-K filings via SEC EDGAR
- Parses filing text into structured sections
- Detects fraud red flags (5+ checks)
- Computes composite fraud scores (0–100)
- Outputs JSON analysis reports

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python -m forensic analyze AAPL
```

## Configuration

Edit `config.yaml` to customize database path, rate limiting, and logging settings.
