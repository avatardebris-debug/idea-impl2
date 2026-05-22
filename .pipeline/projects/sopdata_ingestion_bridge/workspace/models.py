"""SOP data model definition.

Defines structured SOP input data classes that map CSV columns to SOP fields
(task_name, description, steps, assignee, deadline, priority).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .core import DEFAULT_MAPPING


@dataclass
class SOPInputRow:
    """A single structured SOP input row derived from a CSV row.

    Attributes:
        task_name: Name or title of the SOP task.
        description: Human-readable description of the task.
        steps: Step-by-step instructions (may be multi-line).
        assignee: Person or role assigned to the task.
        deadline: Due date / deadline string.
        priority: Priority level (e.g. "low", "medium", "high").
        raw: Original CSV row data for reference.
    """

    task_name: str = ""
    description: str = ""
    steps: str = ""
    assignee: str = ""
    deadline: str = ""
    priority: str = ""
    raw: Dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, str],
        mapping: Optional[Dict[str, str]] = None,
    ) -> SOPInputRow:
        """Instantiate an SOPInputRow from a CSV row dict.

        Args:
            data: Raw CSV row keyed by column names.
            mapping: Mapping from CSV column names to SOP field names.
                     If None, uses the default mapping.

        Returns:
            A populated SOPInputRow instance.
        """
        effective_mapping = mapping if mapping is not None else DEFAULT_MAPPING

        # Build reverse mapping: SOP field → list of CSV columns
        reverse: Dict[str, List[str]] = {}
        for csv_col, sop_field in effective_mapping.items():
            if sop_field not in reverse:
                reverse[sop_field] = []
            reverse[sop_field].append(csv_col)

        def _get(field_name: str) -> str:
            csv_cols = reverse.get(field_name, [])
            for csv_col in csv_cols:
                if csv_col in data:
                    return data[csv_col]
            return ""

        return cls(
            task_name=_get("task_name"),
            description=_get("description"),
            steps=_get("steps"),
            assignee=_get("assignee"),
            deadline=_get("deadline"),
            priority=_get("priority"),
            raw=data,
        )

    def to_dict(self) -> Dict[str, str]:
        """Export the row as a plain dict (excluding raw)."""
        return {
            "task_name": self.task_name,
            "description": self.description,
            "steps": self.steps,
            "assignee": self.assignee,
            "deadline": self.deadline,
            "priority": self.priority,
        }
