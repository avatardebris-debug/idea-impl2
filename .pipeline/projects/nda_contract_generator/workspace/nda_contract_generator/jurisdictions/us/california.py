"""California jurisdiction configuration."""


def get_config():
    """Return the California jurisdiction configuration."""
    return {
        "key": "california",
        "name": "California",
        "display_name": "California, US",
        "governing_law": "California, US",
        "default_term": "2_years",
        "required_clauses": [
            "definition_of_confidential_info",
            "exclusions_from_confidential_info",
            "term_length",
            "permitted_use",
            "return_of_materials",
            "remedies",
            "governing_law",
            "dispute_resolution",
            "non_solicitation",
            "no_license_granted",
            "survival_period",
            "notice_period",
            "confidentiality_obligations",
            "data_protection",
            "third_party_disclosure",
            "injunctive_relief",
            "liquidated_damages",
            "mutual_vs_unilateral",
            "carve_outs",
            "standard_of_care",
            "publication_restrictions",
            "agent_disclosure",
            "audit_rights",
        ],
        "optional_clauses": [],
        "mandatory_fields": [
            "disclosing_party_name",
            "receiving_party_name",
            "effective_date",
            "purpose",
        ],
        "special_notes": [
            "California law restricts non-solicitation clauses in employment contexts.",
            "CCPA compliance may be required for personal data handling.",
            "Consider arbitration clauses for dispute resolution.",
        ],
        "template_path": "templates/nda_california.docx",
    }
