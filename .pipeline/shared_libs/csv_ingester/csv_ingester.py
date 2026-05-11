"""Generic CSV ingestion and parsing.

Accepts a CSV file path (or file-like object) and parses it into a list
of row dictionaries keyed by header names.
"""

import csv
import io
from typing import Dict, List, Optional, TextIO, Union


def read_csv(
    source: Union[str, TextIO],
    encoding: str = "utf-8-sig",
) -> List[Dict[str, str]]:
    """Parse a CSV file into a list of row dictionaries.

    Parameters
    ----------
    source : str or TextIO
        Either a file path (str) or an already-open file-like object.
    encoding : str
        Encoding to use when opening a file path. Defaults to utf-8-sig
        (handles BOM).

    Returns
    -------
    list[dict[str, str]]
        One dict per row, keyed by the CSV header names.

    Raises
    ------
    ValueError
        If the CSV is empty, has no headers, or is otherwise malformed.
    FileNotFoundError
        If *source* is a path that does not exist.
    """
    if isinstance(source, str):
        try:
            fh = open(source, newline="", encoding=encoding)
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file not found: {source}")
        owned = True
    else:
        fh = source
        owned = False

    try:
        reader = csv.reader(fh)

        # Read headers
        try:
            headers = next(reader)
        except StopIteration:
            raise ValueError("CSV file is empty — no headers found.")

        # Strip whitespace from headers
        headers = [h.strip() for h in headers]

        if not headers or all(h == "" for h in headers):
            raise ValueError("CSV file has no valid headers.")

        # Build a header-to-index map for O(1) lookups
        header_index = {col: i for i, col in enumerate(headers)}

        rows: List[Dict[str, str]] = []
        for line_num, row in enumerate(reader, start=2):
            # Skip completely blank rows
            if not any(cell.strip() for cell in row):
                continue
            record: Dict[str, str] = {}
            for col in headers:
                idx = header_index[col]
                if idx < len(row):
                    record[col] = row[idx].strip()
                else:
                    record[col] = ""
            rows.append(record)

        return rows

    finally:
        if owned:
            fh.close()


def read_csv_from_string(csv_text: str) -> List[Dict[str, str]]:
    """Parse CSV text (e.g. from a string or StringIO) into row dicts."""
    return read_csv(io.StringIO(csv_text))
