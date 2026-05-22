"""Form handler — validates and processes user input for NDA generation."""

import logging
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class FormHandler:
    """Handles validation and processing of form data for NDA generation."""

    def __init__(self):
        """Initialize the form handler."""
        self.required_fields = [
            "disclosing_party_name",
            "receiving_party_name",
            "effective_date",
            "purpose",
        ]
        self.optional_fields = [
            "non_solicitation_clause",
            "non_circumvention_clause",
            "data_protection_clause",
            "third_party_disclosure_clause",
            "liquidated_damages_clause",
            "carve_outs_clause",
            "publication_restrictions_clause",
            "agent_disclosure_clause",
            "audit_rights_clause",
        ]

    def validate_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate form data against required fields.

        Args:
            form_data: The form data to validate.

        Returns:
            Validation result with 'valid', 'missing', and 'warnings'.
        """
        missing = [f for f in self.required_fields if f not in form_data]
        valid = len(missing) == 0

        warnings = []
        if not valid:
            warnings.append(f"Missing required fields: {missing}")

        # Check for unknown fields
        known_fields = set(self.required_fields + self.optional_fields)
        unknown_fields = set(form_data.keys()) - known_fields
        if unknown_fields:
            warnings.append(f"Unknown fields: {unknown_fields}")

        return {
            "valid": valid,
            "missing": missing,
            "warnings": warnings,
        }

    def process_form_data(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process and normalize form data.

        Args:
            form_data: The raw form data.

        Returns:
            Processed form data with normalized values.
        """
        processed = {}
        for key, value in form_data.items():
            if isinstance(value, str):
                processed[key] = value.strip()
            else:
                processed[key] = value
        return processed

    def get_required_fields(self) -> List[str]:
        """Get the list of required fields.

        Returns:
            List of required field names.
        """
        return list(self.required_fields)

    def get_optional_fields(self) -> List[str]:
        """Get the list of optional fields.

        Returns:
            List of optional field names.
        """
        return list(self.optional_fields)
