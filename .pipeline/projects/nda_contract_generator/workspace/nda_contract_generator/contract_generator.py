"""Contract generator — orchestrates clause resolution, template rendering, and output."""

import logging
from typing import Any, Dict, List, Optional

from nda_contract_generator.core.clause_library import ClauseLibrary
from nda_contract_generator.jurisdictions.jurisdiction_database import JurisdictionDatabase
from nda_contract_generator.template_engine import TemplateEngine

logger = logging.getLogger(__name__)


class ContractGenerator:
    """Generates NDA contracts for a given jurisdiction.

    Combines clause library lookups, jurisdiction configurations,
    and template rendering to produce a complete NDA document.
    """

    def __init__(self, jurisdiction: str):
        """Initialize the contract generator.

        Args:
            jurisdiction: The jurisdiction key (e.g., 'california').
        """
        self.jurisdiction = jurisdiction
        self.clause_library = ClauseLibrary()
        self.jurisdiction_db = JurisdictionDatabase()
        self.template_engine = TemplateEngine()

        # Validate jurisdiction
        if not self.jurisdiction_db.validate_jurisdiction(jurisdiction):
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")

    def _resolve_clauses(self) -> Dict[str, str]:
        """Resolve all clause values for the jurisdiction.

        Returns:
            Dict mapping clause names to their resolved values.
        """
        effective = self.clause_library.apply_overrides(self.jurisdiction)
        return effective

    def _build_context(self, form_data: Dict) -> Dict[str, Any]:
        """Build the rendering context from resolved clauses and form data.

        Args:
            form_data: User-provided form data.

        Returns:
            The full rendering context dict.
        """
        clauses = self._resolve_clauses()
        config = self.jurisdiction_db.get_config(self.jurisdiction)

        # Merge form data with clause values
        context = dict(clauses)
        context.update(form_data)

        # Add jurisdiction-specific metadata
        if config:
            context["jurisdiction_display_name"] = config.get("display_name", self.jurisdiction)
            context["governing_law"] = config.get("governing_law", "N/A")

        return context

    def generate(self, form_data: Optional[Dict] = None) -> str:
        """Generate a complete NDA contract.

        Args:
            form_data: Optional dictionary of user-provided form data.

        Returns:
            The rendered NDA contract as a string.
        """
        if form_data is None:
            form_data = {}

        context = self._build_context(form_data)

        # Get the template path from jurisdiction config
        config = self.jurisdiction_db.get_config(self.jurisdiction)
        template_path = config.get("template_path") if config else None

        if template_path is None:
            raise ValueError(f"No template path configured for jurisdiction: {self.jurisdiction}")

        rendered = self.template_engine.render(template_path, context)
        logger.info("Contract generated for jurisdiction: %s", self.jurisdiction)
        return rendered

    def validate_contract(self, form_data: Optional[Dict] = None) -> Dict[str, Any]:
        """Validate that the contract will be complete for the jurisdiction.

        Args:
            form_data: Optional dictionary of user-provided form data.

        Returns:
            Validation result dict with 'valid', 'missing', and 'warnings'.
        """
        if form_data is None:
            form_data = {}

        config = self.jurisdiction_db.get_config(self.jurisdiction)
        if config is None:
            return {"valid": False, "missing": [], "warnings": ["Unknown jurisdiction"]}

        mandatory_fields = self.jurisdiction_db.get_mandatory_fields(self.jurisdiction)
        missing = [f for f in mandatory_fields if f not in form_data]

        required_clauses = self.jurisdiction_db.get_required_clauses(self.jurisdiction)
        clause_validation = self.jurisdiction_db.validate_clauses(
            self.jurisdiction, required_clauses
        )

        warnings = []
        special_notes = self.jurisdiction_db.get_special_notes(self.jurisdiction)
        warnings.extend(special_notes)

        return {
            "valid": len(missing) == 0 and clause_validation["valid"],
            "missing": missing,
            "warnings": warnings,
        }
