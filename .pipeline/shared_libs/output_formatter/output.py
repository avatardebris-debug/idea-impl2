"""Output formatters for URL Health Checker results.

Supports: table (default), json, csv, html.
"""

import csv
import io
import json
from typing import Dict, List


def format_table(results: List[Dict]) -> str:
    """Format results as an aligned text table."""
    if not results:
        return "(no results)"

    # Column widths
    url_w = max(len(r["url"]) for r in results)
    url_w = max(url_w, len("URL"))
    status_w = max(len(str(r["status_code"] or "N/A")) for r in results)
    status_w = max(status_w, len("Status"))
    time_w = max(len(f'{r["response_time_ms"] or "N/A"}') for r in results)
    time_w = max(time_w, len("Time (ms)"))
    health_w = max(len("UP" if r["is_up"] else "DOWN") for r in results)
    health_w = max(health_w, len("Status"))

    sep = "+" + "-" * (url_w + 2) + "+" + "-" * (status_w + 2) + "+" + "-" * (time_w + 2) + "+" + "-" * (health_w + 2) + "+"

    def _row(url: str, status: str, time: str, health: str) -> str:
        return (
            f"| {url:<{url_w}} | {status:>{status_w}} | {time:>{time_w}} | {health:^{health_w}} |"
        )

    lines = [
        sep,
        _row("URL", "Status", "Time (ms)", "Health"),
        sep,
    ]

    for r in results:
        url = r["url"]
        status = str(r["status_code"]) if r["status_code"] is not None else "N/A"
        time_val = f'{r["response_time_ms"]}' if r["response_time_ms"] is not None else "N/A"
        health = "UP" if r["is_up"] else "DOWN"
        lines.append(_row(url, status, time_val, health))

    lines.append(sep)
    return "\n".join(lines)


def format_json(results: List[Dict]) -> str:
    """Format results as a JSON array."""
    return json.dumps(results, indent=2)


def format_csv(results: List[Dict]) -> str:
    """Format results as RFC 4180-compatible CSV."""
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(["url", "status_code", "response_time_ms", "is_up"])
    for r in results:
        writer.writerow([
            r["url"],
            r["status_code"] if r["status_code"] is not None else "",
            r["response_time_ms"] if r["response_time_ms"] is not None else "",
            r["is_up"],
        ])
    return output.getvalue()


def format_html(results: List[Dict]) -> str:
    """Format results as a styled HTML document."""
    rows = ""
    for r in results:
        status = r["status_code"] if r["status_code"] is not None else "N/A"
        time_val = f'{r["response_time_ms"]}' if r["response_time_ms"] is not None else "N/A"
        health = "UP" if r["is_up"] else "DOWN"
        color = "#28a745" if r["is_up"] else "#dc3545"
        rows += f"""<tr>
<td>{r["url"]}</td>
<td>{status}</td>
<td>{time_val}</td>
<td style="color: {color}; font-weight: bold;">{health}</td>
</tr>
"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>URL Health Check Results</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 20px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
th {{ background-color: #4CAF50; color: white; }}
tr:nth-child(even) {{ background-color: #f2f2f2; }}
</style>
</head>
<body>
<h1>URL Health Check Results</h1>
<table>
<thead>
<tr><th>URL</th><th>Status</th><th>Time (ms)</th><th>Health</th></tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>
"""
    return html


# Map format names to functions
FORMATTERS = {
    "table": format_table,
    "json": format_json,
    "csv": format_csv,
    "html": format_html,
}


def format_results(results: List[Dict], fmt: str = "table") -> str:
    """Format results using the specified format.

    Args:
        results: List of result dicts.
        fmt: Format name ('table', 'json', 'csv', 'html').

    Returns:
        Formatted string output.
    """
    formatter = FORMATTERS.get(fmt, format_table)
    return formatter(results)
