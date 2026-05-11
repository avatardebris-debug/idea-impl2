"""EU GDPR jurisdiction configuration."""


def get_config():
    """Return the EU GDPR jurisdiction configuration."""
    return {
        "key": "gdpr_compliant",
        "name": "EU GDPR",
        "display_name": "EU (GDPR Compliant)",
        "governing_law": "EU",
        "default_term": "5_years",
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
            "non_circumvention",
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
            "data_processing_purpose",
            "data_subject_categories",
        ],
        "special_notes": [
            "GDPR requires explicit consent for personal data processing.",
            "Data Protection Impact Assessment may be required.",
            "Cross-border data transfers need appropriate safeguards.",
            "Include Data Processing Agreement (DPA) annex if applicable.",
        ],
        "template_path": "templates/nda_eu_gdpr.docx",
    }
