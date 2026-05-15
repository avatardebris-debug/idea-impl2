"""CSV parser with auto-detection for three manuscript data types."""

import csv
from typing import Any

# ── Column definitions ──────────────────────────────────────────────

SALES_COLUMNS = {"date", "book title", "units sold", "revenue", "platform"}
DEMOGRAPHICS_COLUMNS = {"age group", "gender", "country", "rating", "review count"}
CONTENT_COLUMNS = {"chapter", "word count", "read-through rate", "completion rate"}

# Normalised column name → canonical column name
COLUMN_ALIASES = {
    # Sales
    "date": "date",
    "book title": "book_title",
    "booktitle": "book_title",
    "book": "book_title",
    "title": "book_title",
    "units sold": "units_sold",
    "units_sold": "units_sold",
    "units": "units_sold",
    "revenue": "revenue",
    "platform": "platform",
    # Demographics
    "age group": "age_group",
    "age_group": "age_group",
    "age": "age_group",
    "gender": "gender",
    "country": "country",
    "rating": "rating",
    "review count": "review_count",
    "review_count": "review_count",
    "reviews": "review_count",
    # Content
    "chapter": "chapter",
    "word count": "word_count",
    "word_count": "word_count",
    "words": "word_count",
    "read-through rate": "read_through_rate",
    "read_through_rate": "read_through_rate",
    "readthrough": "read_through_rate",
    "completion rate": "completion_rate",
    "completion_rate": "completion_rate",
    "completion": "completion_rate",
}


def _normalise_header(headers: list[str]) -> list[str]:
    """Lowercase and strip whitespace from header names."""
    return [h.strip().lower() for h in headers]


def _match_columns(normalised: list[str], required: set[str]) -> bool:
    """Check whether *required* columns are all present in *normalised*."""
    return required.issubset(set(normalised))


def detect_data_type(headers: list[str]) -> str:
    """Auto-detect the data type from CSV header columns.

    Returns one of ``'sales_data'``, ``'demographics_data'``, ``'content_metrics'``.

    Raises
    ------
    ValueError
        If the headers do not match any known type.
    """
    normalised = [h.strip().lower().replace(" ", "_").replace("-", "_") for h in headers]
    def _norm_set(cols: set[str]) -> set[str]:
        return {c.strip().lower().replace(" ", "_").replace("-", "_") for c in cols}

    norm_sales = _norm_set(SALES_COLUMNS)
    norm_demo = _norm_set(DEMOGRAPHICS_COLUMNS)
    norm_content = _norm_set(CONTENT_COLUMNS)

    if norm_sales.issubset(set(normalised)):
        return "sales_data"
    if norm_demo.issubset(set(normalised)):
        return "demographics_data"
    if norm_content.issubset(set(normalised)):
        return "content_metrics"

    raise ValueError(
        f"Unrecognised CSV format. Headers: {headers}. "
        f"Expected one of: sales, demographics, or content metrics."
    )


def _normalise_value(col: str, value: str) -> Any:
    """Convert a CSV string value to the appropriate Python type."""
    if value is None or value.strip() == "":
        return None

    col_lower = col.strip().lower()

    # Integer columns
    if col_lower in ("units_sold", "review_count", "chapter", "word_count"):
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    # Float columns
    if col_lower in ("revenue", "rating", "read_through_rate", "completion_rate"):
        try:
            return float(value.replace(",", "").replace("$", "").replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    # Everything else stays as string
    return value.strip()


def _canonical_column(header: str) -> str:
    """Map a raw header name to its canonical column name."""
    key = header.strip().lower()
    return COLUMN_ALIASES.get(key, key)


def parse_csv(filepath: str) -> tuple[str, list[dict[str, Any]]]:
    """Read a CSV file, auto-detect its type, and return structured records.

    Parameters
    ----------
    filepath : str
        Path to the CSV file.

    Returns
    -------
    tuple[str, list[dict]]
        (data_type, records) where each record is a dict with canonical keys.

    Raises
    ------
    ValueError
        If the file cannot be read or the format is unrecognised.
    """
    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.reader(fh)
        headers = next(reader)
        normalised = _normalise_header(headers)

        data_type = detect_data_type(headers)

        # Build mapping from raw header → canonical column
        header_map = {}
        for h in headers:
            header_map[h] = _canonical_column(h)

        records: list[dict[str, Any]] = []
        for row in reader:
            if not any(cell.strip() for cell in row):
                continue  # skip blank rows
            record: dict[str, Any] = {}
            for raw_col, val in zip(headers, row):
                canon = header_map[raw_col]
                record[canon] = _normalise_value(canon, val)
            records.append(record)

    return data_type, records


def detect_and_parse(filepath: str) -> tuple[str, list[dict[str, Any]]]:
    """Convenience wrapper: detect type and parse in one call."""
    return parse_csv(filepath)
