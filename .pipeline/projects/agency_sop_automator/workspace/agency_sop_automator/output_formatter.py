"""Output formatter for SOP results.

Formats the final output of SOP execution into various formats
(YAML, JSON, CSV, etc.).
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


def format_output(
    data: Dict[str, Any],
    output_format: str = "yaml",
    output_path: Optional[str] = None,
) -> str:
    """Format SOP output data into the specified format.

    Args:
        data:          The output data dict from SOP execution.
        output_format: Output format ('yaml', 'json', 'csv', 'text').
        output_path:   Optional file path to write the output to.

    Returns:
        The formatted output string.

    Raises:
        ValueError: If the output format is unsupported.
    """
    formatters = {
        "yaml": _format_yaml,
        "json": _format_json,
        "csv": _format_csv,
        "text": _format_text,
    }

    formatter = formatters.get(output_format.lower())
    if formatter is None:
        raise ValueError(
            f"Unsupported output format '{output_format}'. "
            f"Supported: {', '.join(formatters.keys())}"
        )

    result = formatter(data)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(result, encoding="utf-8")

    return result


def _format_yaml(data: Dict[str, Any]) -> str:
    """Format data as YAML."""
    import yaml
    return yaml.dump(data, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _format_json(data: Dict[str, Any]) -> str:
    """Format data as JSON."""
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _format_csv(data: Dict[str, Any]) -> str:
    """Format data as CSV (flattened)."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(["key", "value"])

    # Flatten the data
    for key, value in _flatten_dict(data).items():
        writer.writerow([key, value])

    return output.getvalue()


def _format_text(data: Dict[str, Any]) -> str:
    """Format data as human-readable text."""
    lines = []
    lines.append(f"SOP: {data.get('_sop_name', 'N/A')}")
    lines.append("=" * 50)

    for key, value in data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict):
            lines.append(f"\n{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        else:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


def _flatten_dict(d: Dict[str, Any], parent_key: str = "", sep: str = ".") -> Dict[str, Any]:
    """Flatten a nested dict for CSV output."""
    items: List[tuple] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
