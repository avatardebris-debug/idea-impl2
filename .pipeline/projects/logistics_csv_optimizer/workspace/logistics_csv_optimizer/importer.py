"""CSV shipment manifest importer.

Reads CSV files containing shipment data and validates required fields.

Required columns (case-insensitive):
    - origin:        departure city or location
    - destination:   arrival city or location
    - weight:        weight in kg (positive number)
    - priority:      one of 'standard', 'express', 'overnight'

Optional columns:
    - length:        length in cm (default 0)
    - width:         width in cm (default 0)
    - height:        height in cm (default 0)
    - description:   free-text description
"""

import csv
import os
from typing import Any, Dict, List


REQUIRED_COLUMNS = {"origin", "destination", "weight", "priority"}
OPTIONAL_COLUMNS = {"length", "width", "height", "description"}
VALID_PRIORITIES = {"standard", "express", "overnight"}


class Importer:
    """Load and validate CSV shipment manifests."""

    @staticmethod
    def load_manifest(filepath: str) -> List[Dict[str, Any]]:
        """Load a CSV manifest and return a list of validated shipment dicts.

        Args:
            filepath: Path to the CSV file.

        Returns:
            List of shipment dicts with keys: origin, destination, weight,
            priority, length, width, height, description.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If required columns are missing or data is invalid.
        """
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Manifest file not found: {filepath}")

        with open(filepath, newline="", encoding="utf-8") as fh:
            content = fh.read()

        if not content.strip():
            return []

        # Re-use content via StringIO to avoid opening file twice
        from io import StringIO
        reader = csv.DictReader(StringIO(content))

        if reader.fieldnames is None:
            return []

        # Normalize column names to lowercase
        normalized = {name.strip().lower(): name for name in reader.fieldnames}

        missing = REQUIRED_COLUMNS - set(normalized.keys())
        if missing:
            raise ValueError(
                f"Missing required columns: {', '.join(sorted(missing))}"
            )

        shipments: List[Dict[str, Any]] = []
        for row_num, row in enumerate(reader, start=2):
            shipment = _parse_row(row, normalized, row_num)
            shipments.append(shipment)

        return shipments


def _parse_row(
    row: Dict[str, str], normalized: Dict[str, str], row_num: int
) -> Dict[str, Any]:
    """Parse and validate a single CSV row into a shipment dict."""
    def get_field(key: str) -> str:
        raw = row.get(normalized.get(key, key), "")
        return raw.strip() if raw else ""

    origin = get_field("origin")
    destination = get_field("destination")
    weight_str = get_field("weight")
    priority = get_field("priority").lower()

    # Validate required fields
    if not origin:
        raise ValueError(f"Row {row_num}: 'origin' is empty")
    if not destination:
        raise ValueError(f"Row {row_num}: 'destination' is empty")
    if not weight_str:
        raise ValueError(f"Row {row_num}: 'weight' is empty")

    try:
        weight = float(weight_str)
    except ValueError:
        raise ValueError(f"Row {row_num}: 'weight' must be a number, got '{weight_str}'")

    if weight <= 0:
        raise ValueError(f"Row {row_num}: 'weight' must be positive, got {weight}")

    if priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Row {row_num}: 'priority' must be one of {VALID_PRIORITIES}, got '{priority}'"
        )

    # Optional fields with defaults
    length = float(get_field("length") or 0)
    width = float(get_field("width") or 0)
    height = float(get_field("height") or 0)
    description = get_field("description")

    return {
        "origin": origin,
        "destination": destination,
        "weight": weight,
        "priority": priority,
        "length": length,
        "width": width,
        "height": height,
        "description": description,
    }
