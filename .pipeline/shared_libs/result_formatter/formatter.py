"""Report formatter — formats URL check results as text or JSON."""

import json
from typing import Any


def format_results(results: list[dict[str, Any]], fmt: str = "text") -> str:
    """Format check results into a human-readable string.

    Args:
        results: List of result dicts from checker.check_urls.
        fmt: Output format — 'text' (default) or 'json'.

    Returns:
        Formatted string.
    """
    if fmt == "json":
        return json.dumps(results, indent=2, default=str)

    return _format_text(results)


def _format_text(results: list[dict[str, Any]]) -> str:
    """Format results as an ASCII table."""
    if not results:
        return "No URLs to report."

    # Determine column widths
    url_w = max(len(str(r["url"])) for r in results)
    url_w = max(url_w, len("URL"))
    code_w = max(len(str(r.get("status_code") or "None")) for r in results)
    code_w = max(code_w, len("Status"))
    time_w = max(len(_format_time(r.get("response_time_ms"))) for r in results)
    time_w = max(time_w, len("Time"))
    up_w = max(len(str(r.get("up", False))) for r in results)
    up_w = max(up_w, len("Up"))

    # Build separator line
    sep = "+-" + "-+-".join("-" * w for w in (url_w, code_w, time_w, up_w)) + "-+"

    # Build header
    header = (
        "| "
        + " | ".join(
            f"{{:<{w}}}".format(h)
            for h, w in [("URL", url_w), ("Status", code_w), ("Time", time_w), ("Up", up_w)]
        )
        + " |"
    )

    lines = [header, sep]

    for r in results:
        url = str(r.get("url", ""))
        code = str(r.get("status_code") or "None")
        t = _format_time(r.get("response_time_ms"))
        up = str(r.get("up", False))
        row = (
            "| "
            + " | ".join(
                f"{{:<{w}}}".format(v)
                for v, w in [(url, url_w), (code, code_w), (t, time_w), (up, up_w)]
            )
            + " |"
        )
        lines.append(row)

    lines.append(sep)
    return "\n".join(lines)


def _format_time(ms: Any) -> str:
    """Format response time in milliseconds."""
    if ms is None:
        return "None"
    return f"{ms:.2f}"
