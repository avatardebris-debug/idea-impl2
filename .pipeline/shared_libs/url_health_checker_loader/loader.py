"""Load URLs from a text file."""

from pathlib import Path


def load_urls(filepath: str) -> list[str]:
    """Read URLs from a text file.

    One URL per line. Blank lines and lines starting with '#' are skipped.
    Returns a list of stripped, non-empty strings.

    Args:
        filepath: Path to the text file.

    Returns:
        List of URL strings.
    """
    path = Path(filepath)
    if not path.exists():
        return []

    urls = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                urls.append(stripped)
    return urls
