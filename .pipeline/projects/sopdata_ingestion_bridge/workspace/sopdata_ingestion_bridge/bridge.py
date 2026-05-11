"""Bridge API entry point.

Wires ingestion, parsing, and transformation together into a clean public API.
"""

from typing import Dict, List, Optional

from .ingest import read_csv
from .models import SOPInputRow
from .transform import transform


class SOPBridge:
    """Main bridge class that orchestrates CSV ingestion → SOP transformation.

    Usage:
        >>> bridge = SOPBridge()
        >>> results = bridge.ingest("data.csv")
        >>> for row in results:
        ...     print(row.task_name)
    """

    def ingest(
        self,
        csv_path: str,
        mapping: Optional[Dict[str, str]] = None,
    ) -> List[SOPInputRow]:
        """Ingest a CSV file and return structured SOP input rows.

        Args:
            csv_path: Path to the CSV file.
            mapping: Custom column mapping from CSV headers to SOP fields.
                     If None, uses the default mapping.

        Returns:
            Structured SOP input objects, one per CSV row.
        """
        raw_rows = read_csv(csv_path)
        return transform(raw_rows, mapping=mapping)


def ingest(
    csv_path: str,
    mapping: Optional[Dict[str, str]] = None,
) -> List[SOPInputRow]:
    """Convenience function to ingest a CSV file and return SOP rows.

    Args:
        csv_path: Path to the CSV file.
        mapping: Custom column mapping from CSV headers to SOP fields.
                 If None, uses the default mapping.

    Returns:
        Structured SOP input objects, one per CSV row.
    """
    bridge = SOPBridge()
    return bridge.ingest(csv_path, mapping=mapping)
