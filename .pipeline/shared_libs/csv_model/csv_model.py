"""Generic CSV-to-model dataclass with configurable column mapping.

Provides a reusable dataclass pattern that maps arbitrary CSV row dicts
to structured fields using a configurable column alias mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CSVRowModel:
    """A structured dataclass that maps CSV row dicts to typed fields.

    Subclasses should define class-level ``FIELD_MAP`` as a dict of
    ``csv_column_name -> field_name`` and ``FIELD_NAMES`` as a list of
    field names to use during ``from_dict`` resolution.

    Usage
    -----
    >>> class MyModel(CSVRowModel):
    ...     FIELD_MAP = {"name": "name", "title": "name", "desc": "description"}
    ...     FIELD_NAMES = ["name", "description"]
    ...     name: str = ""
    ...     description: str = ""
    ...
    >>> row = MyModel.from_dict({"title": "Hello", "desc": "World"})
    >>> row.name
    'Hello'
    """

    raw: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, str],
        mapping: Optional[Dict[str, str]] = None,
    ) -> "CSVRowModel":
        """Instantiate from a CSV row dict.

        Parameters
        ----------
        data : dict
            Raw CSV row keyed by column names.
        mapping : dict, optional
            Mapping from CSV column names to model field names.
            If None, uses the class-level FIELD_MAP.

        Returns
        -------
        CSVRowModel
            A populated instance.
        """
        if mapping is None:
            mapping = getattr(cls, "FIELD_MAP", {})

        # Build reverse mapping: field_name → list of CSV columns (in order)
        reverse: Dict[str, List[str]] = {}
        for csv_col, field_name in mapping.items():
            if field_name not in reverse:
                reverse[field_name] = []
            reverse[field_name].append(csv_col)

        def _get(field_name: str) -> str:
            csv_cols = reverse.get(field_name, [])
            for csv_col in csv_cols:
                val = data.get(csv_col, "")
                if val:
                    return val
            return ""

        # Collect field names to populate
        field_names = getattr(cls, "FIELD_NAMES", [])
        kwargs: Dict[str, Any] = {}
        for fn in field_names:
            kwargs[fn] = _get(fn)

        kwargs["raw"] = dict(data)
        return cls(**kwargs)

    def to_dict(self) -> Dict[str, str]:
        """Serialize to a dict, excluding the ``raw`` field."""
        d = {k: v for k, v in self.__dict__.items() if k != "raw"}
        return d
