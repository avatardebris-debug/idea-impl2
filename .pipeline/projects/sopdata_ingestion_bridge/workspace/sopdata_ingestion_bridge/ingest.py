"""CSV ingestion and parsing utilities.

Provides functions to read CSV files (from disk or strings) and return
parsed row dictionaries ready for transformation.
"""

import csv
import io
from typing import Dict, List, Optional


def read_csv(
    path: str,
    encoding: str = "utf-8",
) -> List[Dict[str, str]]:
    """Read and parse a CSV file into a list of row dicts.

    Args:
        path: Filesystem path to the CSV file.
        encoding: Character encoding of the CSV file (default UTF-8).

    Returns:
        List of dicts, one per data row, keyed by column header.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the CSV is empty or has no valid headers.
    """
    try:
        with open(path, "r", encoding=encoding) as fh:
            content = fh.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found: {path}")

    return parse_csv_string(content)


def parse_csv_string(
    content: str,
    delimiter: str = ",",
) -> List[Dict[str, str]]:
    """Parse a CSV string into a list of row dicts.

    Args:
        content: Raw CSV string content.
        delimiter: Column delimiter character (default comma).

    Returns:
        List of dicts, one per data row, keyed by column header.

    Raises:
        ValueError: If the CSV is empty, has no valid headers, or has no data rows.
    """
    # Handle truly empty content (no bytes at all)
    if not content:
        raise ValueError("CSV file is empty")

    # Strip UTF-8 BOM if present
    if content.startswith("\ufeff"):
        content = content[1:]

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)

    if reader.fieldnames is None or all(f is None or f.strip() == "" for f in reader.fieldnames):
        raise ValueError("CSV file has no valid headers")

    rows = []
    for row in reader:
        # Fill in missing columns with empty strings
        if row is not None:
            normalized = {}
            for key in reader.fieldnames:
                normalized[key] = row.get(key) if row.get(key) is not None else ""
            rows.append(normalized)

    return rows


def read_csv_from_string(
    content: str,
    delimiter: str = ",",
) -> List[Dict[str, str]]:
    """Convenience alias for parse_csv_string.

    Args:
        content: Raw CSV string content.
        delimiter: Column delimiter character (default comma).

    Returns:
        List of dicts, one per data row, keyed by column header.
    """
    return parse_csv_string(content, delimiter=delimiter)
