"""Report formatting for URL Health Checker."""


def format_report(results):
    """Format a list of result dicts into a readable text table.

    Args:
        results: List of dicts with keys url, status_code, response_time_ms, is_up.

    Returns:
        Formatted string table.
    """
    if not results:
        return "No results to display."

    # Determine column widths
    url_width = max(len(r["url"]) for r in results)
    url_width = max(url_width, len("URL"))
    status_width = max(len(str(r["status_code"] or "N/A")) for r in results)
    status_width = max(status_width, len("STATUS"))
    time_width = max(len(f"{r['response_time_ms'] or 'N/A'}") for r in results)
    time_width = max(time_width, len("TIME (ms)"))
    status_label_width = max(len("UP" if r["is_up"] else "DOWN") for r in results)
    status_label_width = max(status_label_width, len("STATUS"))

    header = (
        f"{'URL':<{url_width}}  "
        f"{'STATUS':<{status_width}}  "
        f"{'TIME (ms)':<{time_width}}  "
        f"{'STATUS':<{status_label_width}}"
    )
    separator = "-" * len(header)

    lines = [separator, header, separator]
    for r in results:
        status_code = r["status_code"] if r["status_code"] is not None else "N/A"
        resp_time = (
            f"{r['response_time_ms']}"
            if r["response_time_ms"] is not None
            else "N/A"
        )
        status_label = "UP" if r["is_up"] else "DOWN"
        line = (
            f"{r['url']:<{url_width}}  "
            f"{str(status_code):<{status_width}}  "
            f"{str(resp_time):<{time_width}}  "
            f"{status_label:<{status_label_width}}"
        )
        lines.append(line)
    lines.append(separator)
    return "\n".join(lines)
