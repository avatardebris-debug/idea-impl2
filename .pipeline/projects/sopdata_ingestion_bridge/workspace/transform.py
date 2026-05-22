"""CSV-to-SOP transformation logic.

Takes parsed CSV row dicts and transforms them into structured SOP input
objects using configurable column mappings.
"""

from typing import Dict, List, Optional

from .core import DEFAULT_MAPPING, get_default_mapping, merge_mappings
from .models import SOPInputRow


def transform(
    rows: List[Dict[str, str]],
    mapping: Optional[Dict[str, str]] = None,
) -> List[SOPInputRow]:
    """Transform raw CSV rows into SOPInputRow instances.

    Args:
        rows: List of CSV row dicts (each key is a column name).
        mapping: Optional custom column mapping. If None, uses the default.

    Returns:
        List of SOPInputRow instances.
    """
    if mapping is not None and len(mapping) == 0:
        # Empty mapping means no columns are mapped — all fields are empty
        return [SOPInputRow(raw=row) for row in rows]
    effective_mapping = merge_mappings(get_default_mapping(), mapping)
    return [SOPInputRow.from_dict(row, mapping=effective_mapping) for row in rows]
