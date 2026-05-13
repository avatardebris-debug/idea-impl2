"""CSV Importer for logistics manifests."""

import csv
import os


class Importer:
    """Import shipment data from a CSV file."""

    REQUIRED_COLUMNS = {"origin", "destination", "priority", "weight"}
    DIMENSION_COLUMNS = {"length", "width", "height"}

    @classmethod
    def import_csv(cls, filepath: str) -> list[dict]:
        """Read a CSV manifest file and return a list of shipment dicts.

        Args:
            filepath: Path to the CSV file.

        Returns:
            List of dicts with shipment data.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the CSV is missing required columns.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Input file not found: {filepath}")

        shipments = []
        with open(filepath, "r", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)

            if reader.fieldnames is None:
                return []

            header_set = set(reader.fieldnames)
            missing = cls.REQUIRED_COLUMNS - header_set
            if missing:
                raise ValueError(f"CSV is missing required columns: {missing}")

            for row in reader:
                shipment = {
                    "origin": row["origin"].strip(),
                    "destination": row["destination"].strip(),
                    "priority": row["priority"].strip(),
                    "weight": float(row["weight"]),
                }
                # Add optional dimension fields, defaulting to 0 if missing
                for col in cls.DIMENSION_COLUMNS:
                    val = row.get(col)
                    if val is not None and val.strip():
                        shipment[col] = int(float(val))
                    else:
                        shipment[col] = 0
                shipments.append(shipment)

        return shipments
