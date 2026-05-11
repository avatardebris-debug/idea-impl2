"""England & Wales jurisdiction configuration."""


def get_config():
    """Return the England & Wales jurisdiction configuration."""
    return {
        "key": "england_wales",
        "name": "England & Wales",
        "display_name": "England & Wales",
        "governing_law": "England & Wales",
        "default_term": "3_years",
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
        ],
        "special_notes": [
            "Equitable remedies are preferred over monetary damages in UK law.",
            "GDPR compliance is mandatory for personal data processing.",
            "Consider including a severability clause.",
        ],
        "template_path": "templates/nda_england_wales.docx",
    }
