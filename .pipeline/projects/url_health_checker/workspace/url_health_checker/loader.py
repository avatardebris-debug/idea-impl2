"""URL loader module — reads and validates URLs from a text file."""

import re
from urllib.parse import urlparse


def load_urls(path: str) -> list[str]:
    """Load URLs from a text file, one per line.

    - Blank lines and lines starting with '#' are skipped.
    - Each URL must have a scheme of 'http' or 'https'.
    - Raises ValueError for any line that is not blank, not a comment,
      and not a valid http/https URL.

    Args:
        path: Path to the text file.

    Returns:
        A list of validated URL strings.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If a non-comment, non-blank line is not a valid URL.
    """
    url_pattern = re.compile(r"^https?://", re.IGNORECASE)
    urls: list[str] = []

    with open(path, "r", encoding="utf-8") as fh:
        for line_num, raw_line in enumerate(fh, start=1):
            line = raw_line.strip()

            # Skip blank lines and comments
            if not line or line.startswith("#"):
                continue

            # Validate URL
            if not url_pattern.match(line):
                raise ValueError(
                    f"Line {line_num}: invalid URL '{line}' — "
                    "must start with http:// or https://"
                )

            # Additional validation: parse and check scheme
            parsed = urlparse(line)
            if parsed.scheme not in ("http", "https"):
                raise ValueError(
                    f"Line {line_num}: URL '{line}' has unsupported scheme "
                    f"'{parsed.scheme}' — only http and https are allowed"
                )
            if not parsed.netloc:
                raise ValueError(
                    f"Line {line_num}: URL '{line}' is missing a host"
                )

            urls.append(line)

    return urls
