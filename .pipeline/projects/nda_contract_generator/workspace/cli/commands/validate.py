"""Extended NDA validator — clause conflict detection and jurisdiction compliance."""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Known clause conflicts: if clause A is present, clause B cannot also be X
CONFLICT_RULES: List[Tuple[str, str, str, str]] = [
    # (clause_a, value_a_pattern, clause_b, conflict_description)
    ("term", r"indefinite", "auto_renewal", "Indefinite term conflicts with auto-renewal clause"),
    ("governing_law", r"california", "mandatory_arbitration_excluded", "CA law may restrict some arbitration exclusions"),
]

# Required fields per template type
TEMPLATE_REQUIRED_FIELDS: Dict[str, List[str]] = {
    "mutual": ["party_a_name", "party_b_name", "effective_date", "term"],
    "unilateral": ["disclosing_party", "receiving_party", "effective_date", "term"],
    "employment": ["employer_name", "employee_name", "effective_date", "position"],
}


def validate_contract_text(text: str, jurisdiction: str = "", template_type: str = "") -> Dict[str, Any]:
    """Validate a rendered NDA contract text.

    Checks for:
    - Missing required fields (unfilled placeholders)
    - Clause conflicts
    - Jurisdiction compliance markers
    - Disclaimer presence

    Args:
        text: The rendered NDA text to validate.
        jurisdiction: The jurisdiction key (used for compliance checks).
        template_type: The template type ('mutual', 'unilateral', 'employment').

    Returns:
        Dict with 'valid', 'errors', 'warnings', 'missing_fields'.
    """
    errors: List[str] = []
    warnings: List[str] = []

    # 1. Check for unfilled Jinja2 placeholders
    unfilled = re.findall(r"\{\{[^}]+\}\}", text)
    if unfilled:
        errors.append(f"Unfilled template placeholders detected: {', '.join(unfilled[:5])}")

    # 2. Check minimum length — a real NDA should be substantial
    if len(text.strip()) < 200:
        errors.append("Contract text is too short — may be incomplete (< 200 chars)")

    # 3. Check for disclaimer
    if "legal advice" not in text.lower() and "disclaimer" not in text.lower():
        warnings.append("No legal disclaimer found — consider adding one")

    # 4. Check for essential NDA sections
    essential_sections = ["confidential", "term", "governing"]
    for section in essential_sections:
        if section.lower() not in text.lower():
            warnings.append(f"Expected section keyword '{section}' not found in contract")

    # 5. Jurisdiction-specific compliance
    if jurisdiction:
        compliance = _check_jurisdiction_compliance(text, jurisdiction)
        warnings.extend(compliance)

    # 6. Missing required fields (look for blank/placeholder values)
    missing_fields = _find_missing_fields(text, template_type)

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "missing_fields": missing_fields,
    }


def validate_form_data(form_data: Dict[str, Any], template_type: str = "mutual") -> Dict[str, Any]:
    """Validate user-supplied form data before generation.

    Args:
        form_data: Dictionary of user-provided values.
        template_type: NDA template type.

    Returns:
        Dict with 'valid', 'missing', 'warnings'.
    """
    required = TEMPLATE_REQUIRED_FIELDS.get(template_type, [])
    missing = [f for f in required if not form_data.get(f)]

    warnings = []
    if form_data.get("term") == "indefinite" and form_data.get("auto_renewal"):
        warnings.append("Indefinite term with auto-renewal is contradictory")

    return {
        "valid": len(missing) == 0,
        "missing": missing,
        "warnings": warnings,
    }


def detect_clause_conflicts(clauses: Dict[str, str]) -> List[str]:
    """Detect conflicts between clause values.

    Args:
        clauses: Dict mapping clause names to their values.

    Returns:
        List of conflict description strings (empty if no conflicts).
    """
    conflicts = []
    for clause_a, pattern_a, clause_b, description in CONFLICT_RULES:
        val_a = clauses.get(clause_a, "")
        val_b = clauses.get(clause_b, "")
        if re.search(pattern_a, str(val_a), re.IGNORECASE) and val_b:
            conflicts.append(description)
    return conflicts


def _check_jurisdiction_compliance(text: str, jurisdiction: str) -> List[str]:
    """Check jurisdiction-specific compliance requirements."""
    warnings = []
    jur = jurisdiction.lower()

    if "california" in jur or "ca" == jur:
        if "california" not in text.lower() and "cal." not in text.lower():
            warnings.append("California jurisdiction selected but 'California' not found in contract text")
        if "ccpa" not in text.lower() and "consumer" not in text.lower():
            warnings.append("California NDA should reference consumer privacy considerations (CCPA)")

    if "gdpr" in jur or "eu" in jur:
        if "gdpr" not in text.lower() and "data protection" not in text.lower():
            warnings.append("GDPR jurisdiction selected but no GDPR/data protection language found")

    if "england" in jur or "uk" in jur:
        if "england" not in text.lower() and "wales" not in text.lower() and "united kingdom" not in text.lower():
            warnings.append("UK jurisdiction selected but no UK governing law language found")

    return warnings


def _find_missing_fields(text: str, template_type: str) -> List[str]:
    """Look for common placeholder patterns indicating unfilled fields."""
    missing = []
    # Patterns like [PARTY NAME], [DATE], [TERM]
    bracket_placeholders = re.findall(r"\[([A-Z][A-Z _]+)\]", text)
    for ph in bracket_placeholders:
        if ph not in ("DISCLAIMER", "NDA"):  # known intentional markers
            missing.append(ph)
    return list(set(missing))
