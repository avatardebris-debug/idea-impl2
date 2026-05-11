"""Format URL check results as a human-readable table."""

from typing import Sequence


def format_report(results: Sequence[dict]) -> str:
    """Format a list of result dicts into a table string.

    Columns: URL | Status Code | Response Time | Status

    Args:
        results: Sequence of result dicts (as returned by checker.check_url).

    Returns:
        A formatted table string.
    """
    # Determine column widths
    header = ["URL", "Status Code", "Response Time", "Status"]
    rows: list[list[str]] = []
    for r in results:
        status_label = "UP" if r.get("is_up") else "DOWN"
        sc = str(r.get("status_code", "N/A"))
        rt = f"{r.get('response_time_ms', 0.0):.2f} ms"
        rows.append([r["url"], sc, rt, status_label])

    widths = [len(h) for h in header]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def _sep() -> str:
        return "+-" + "-+-".join("-" * w for w in widths) + "-+"

    def _row(cells: list[str]) -> str:
        return "| " + " | ".join(c.ljust(widths[i]) for i, c in enumerate(cells)) + " |"

    lines = [_sep(), _row(header), _sep()]
    for row in rows:
        lines.append(_row(row))
    lines.append(_sep())

    return "\n".join(lines)
