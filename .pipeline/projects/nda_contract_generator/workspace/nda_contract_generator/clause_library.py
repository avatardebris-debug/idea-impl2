"""Clause library — manages default clause values and jurisdiction overrides."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ClauseLibrary:
    """Manages default clause values and jurisdiction-specific overrides."""

    # Default clause values
    DEFAULTS = {
        "definition_of_confidential_info": "broad",
        "exclusions_from_confidential_info": "standard",
        "term_length": "2_years",
        "permitted_use": "evaluation_only",
        "return_of_materials": "upon_request",
        "remedies": "injunctive",
        "governing_law": "California, US",
        "dispute_resolution": "arbitration",
        "non_solicitation": "standard",
        "non_circumvention": "standard",
        "no_license_granted": "yes",
        "survival_period": "2_years",
        "notice_period": "10_days",
        "confidentiality_obligations": "standard",
        "data_protection": "standard",
        "third_party_disclosure": "prohibited",
        "injunctive_relief": "available",
        "liquidated_damages": "none",
        "mutual_vs_unilateral": "mutual",
        "carve_outs": "standard",
        "standard_of_care": "reasonable",
        "publication_restrictions": "prohibited",
        "agent_disclosure": "prohibited",
        "audit_rights": "none",
    }

    # Jurisdiction overrides
    JURISDICTION_OVERRIDES = {
        "california": {
            "definition_of_confidential_info": "broad",
            "exclusions_from_confidential_info": "standard",
            "term_length": "2_years",
            "permitted_use": "evaluation_only",
            "return_of_materials": "upon_termination",
            "remedies": "both",
            "governing_law": "California, US",
            "dispute_resolution": "arbitration",
            "non_solicitation": "none",
            "non_circumvention": "standard",
            "no_license_granted": "yes",
            "survival_period": "2_years",
            "notice_period": "10_days",
            "confidentiality_obligations": "standard",
            "data_protection": "ccpa_compliant",
            "third_party_disclosure": "with_consent",
            "injunctive_relief": "available",
            "liquidated_damages": "none",
            "mutual_vs_unilateral": "mutual",
            "carve_outs": "standard",
            "standard_of_care": "reasonable",
            "publication_restrictions": "with_notice",
            "agent_disclosure": "with_consent",
            "audit_rights": "none",
        },
        "england_wales": {
            "definition_of_confidential_info": "broad",
            "exclusions_from_confidential_info": "standard",
            "term_length": "3_years",
            "permitted_use": "business_purpose",
            "return_of_materials": "upon_termination",
            "remedies": "equitable",
            "governing_law": "England & Wales",
            "dispute_resolution": "court_litigation",
            "non_solicitation": "standard",
            "non_circumvention": "standard",
            "no_license_granted": "yes",
            "survival_period": "3_years",
            "notice_period": "15_days",
            "confidentiality_obligations": "enhanced",
            "data_protection": "gdpr_compliant",
            "third_party_disclosure": "prohibited",
            "injunctive_relief": "available",
            "liquidated_damages": "none",
            "mutual_vs_unilateral": "mutual",
            "carve_outs": "standard",
            "standard_of_care": "reasonable",
            "publication_restrictions": "prohibited",
            "agent_disclosure": "with_consent",
            "audit_rights": "none",
        },
        "gdpr_compliant": {
            "definition_of_confidential_info": "broad",
            "exclusions_from_confidential_info": "standard",
            "term_length": "3_years",
            "permitted_use": "business_purpose",
            "return_of_materials": "upon_termination",
            "remedies": "both",
            "governing_law": "EU Member State",
            "dispute_resolution": "court_litigation",
            "non_solicitation": "standard",
            "non_circumvention": "standard",
            "no_license_granted": "yes",
            "survival_period": "3_years",
            "notice_period": "15_days",
            "confidentiality_obligations": "enhanced",
            "data_protection": "gdpr_compliant",
            "third_party_disclosure": "prohibited",
            "injunctive_relief": "available",
            "liquidated_damages": "none",
            "mutual_vs_unilateral": "mutual",
            "carve_outs": "standard",
            "standard_of_care": "reasonable",
            "publication_restrictions": "prohibited",
            "agent_disclosure": "with_consent",
            "audit_rights": "gdpr_audit",
        },
    }

    def get_default(self, clause_name: str) -> str:
        """Get the default value for a clause.

        Args:
            clause_name: The clause name.

        Returns:
            The default value as a string.
        """
        return self.DEFAULTS.get(clause_name, "")

    def get_overrides(self, jurisdiction: str) -> Dict[str, str]:
        """Get jurisdiction-specific overrides.

        Args:
            jurisdiction: The jurisdiction key.

        Returns:
            Dictionary of clause overrides.
        """
        return self.JURISDICTION_OVERRIDES.get(jurisdiction, {})

    def apply_overrides(self, jurisdiction: str) -> Dict[str, str]:
        """Apply jurisdiction overrides to defaults.

        Args:
            jurisdiction: The jurisdiction key.

        Returns:
            Merged dictionary of clause values.
        """
        merged = dict(self.DEFAULTS)
        overrides = self.get_overrides(jurisdiction)
        merged.update(overrides)
        return merged

    def get_all_clauses(self) -> Dict[str, str]:
        """Get all available clauses with their defaults.

        Returns:
            Dictionary of all clause names to default values.
        """
        return dict(self.DEFAULTS)
