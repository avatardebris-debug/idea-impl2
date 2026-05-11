"""Tests for the jurisdiction database module."""

import pytest

from nda_contract_generator.jurisdictions.jurisdiction_database import JurisdictionDatabase


@pytest.fixture
def jur_db():
    """Create a JurisdictionDatabase instance."""
    return JurisdictionDatabase()


# --- Loading tests ---


def test_load_all_jurisdictions(jur_db):
    """Test that all jurisdictions are loaded."""
    assert jur_db.get_config_count() == 3


def test_list_jurisdictions(jur_db):
    """Test listing all jurisdiction keys."""
    keys = jur_db.list_jurisdictions()
    assert isinstance(keys, list)
    assert len(keys) == 3
    assert "california" in keys
    assert "england_wales" in keys
    assert "gdpr_compliant" in keys


def test_get_config_returns_dict(jur_db):
    """Test that get_config returns a dict with expected keys."""
    config = jur_db.get_config("california")
    assert config is not None
    assert "key" in config
    assert "name" in config
    assert "display_name" in config
    assert "governing_law" in config
    assert "default_term" in config
    assert "required_clauses" in config
    assert "mandatory_fields" in config
    assert "special_notes" in config


def test_get_config_nonexistent(jur_db):
    """Test that nonexistent jurisdiction returns None."""
    assert jur_db.get_config("nonexistent") is None


def test_get_all_configs(jur_db):
    """Test that get_all_configs returns all jurisdictions."""
    all_configs = jur_db.get_all_configs()
    assert len(all_configs) == 3
    assert "california" in all_configs
    assert "england_wales" in all_configs
    assert "gdpr_compliant" in all_configs


# --- Display name tests ---


def test_get_display_name_california(jur_db):
    """Test display name for California."""
    assert jur_db.get_display_name("california") == "California, US"


def test_get_display_name_england_wales(jur_db):
    """Test display name for England & Wales."""
    assert jur_db.get_display_name("england_wales") == "England & Wales"


def test_get_display_name_gdpr(jur_db):
    """Test display name for GDPR."""
    assert jur_db.get_display_name("gdpr_compliant") == "EU (GDPR Compliant)"


def test_get_display_name_nonexistent(jur_db):
    """Test display name for nonexistent jurisdiction."""
    assert jur_db.get_display_name("nonexistent") is None


# --- Governing law tests ---


def test_get_governing_law_california(jur_db):
    """Test governing law for California."""
    assert jur_db.get_governing_law("california") == "California, US"


def test_get_governing_law_england_wales(jur_db):
    """Test governing law for England & Wales."""
    assert jur_db.get_governing_law("england_wales") == "England & Wales"


def test_get_governing_law_gdpr(jur_db):
    """Test governing law for GDPR."""
    assert jur_db.get_governing_law("gdpr_compliant") == "EU"


def test_get_governing_law_nonexistent(jur_db):
    """Test governing law for nonexistent jurisdiction."""
    assert jur_db.get_governing_law("nonexistent") is None


# --- Default term tests ---


def test_get_default_term_california(jur_db):
    """Test default term for California."""
    assert jur_db.get_default_term("california") == "2_years"


def test_get_default_term_england_wales(jur_db):
    """Test default term for England & Wales."""
    assert jur_db.get_default_term("england_wales") == "3_years"


def test_get_default_term_gdpr(jur_db):
    """Test default term for GDPR."""
    assert jur_db.get_default_term("gdpr_compliant") == "5_years"


def test_get_default_term_nonexistent(jur_db):
    """Test default term for nonexistent jurisdiction."""
    assert jur_db.get_default_term("nonexistent") is None


# --- Required clauses tests ---


def test_get_required_clauses_california(jur_db):
    """Test required clauses for California."""
    clauses = jur_db.get_required_clauses("california")
    assert isinstance(clauses, list)
    assert len(clauses) > 0
    assert "definition_of_confidential_info" in clauses
    assert "governing_law" in clauses


def test_get_required_clauses_england_wales(jur_db):
    """Test required clauses for England & Wales."""
    clauses = jur_db.get_required_clauses("england_wales")
    assert "non_circumvention" in clauses


def test_get_required_clauses_gdpr(jur_db):
    """Test required clauses for GDPR."""
    clauses = jur_db.get_required_clauses("gdpr_compliant")
    assert "data_protection" in clauses


def test_get_required_clauses_nonexistent(jur_db):
    """Test required clauses for nonexistent jurisdiction."""
    assert jur_db.get_required_clauses("nonexistent") == []


# --- Optional clauses tests ---


def test_get_optional_clauses_all_empty(jur_db):
    """Test that optional clauses are empty for all jurisdictions."""
    for key in jur_db.list_jurisdictions():
        assert jur_db.get_optional_clauses(key) == []


def test_get_optional_clauses_nonexistent(jur_db):
    """Test optional clauses for nonexistent jurisdiction."""
    assert jur_db.get_optional_clauses("nonexistent") == []


# --- Mandatory fields tests ---


def test_get_mandatory_fields_california(jur_db):
    """Test mandatory fields for California."""
    fields = jur_db.get_mandatory_fields("california")
    assert isinstance(fields, list)
    assert "disclosing_party_name" in fields
    assert "receiving_party_name" in fields
    assert "effective_date" in fields
    assert "purpose" in fields


def test_get_mandatory_fields_gdpr(jur_db):
    """Test mandatory fields for GDPR include data-specific fields."""
    fields = jur_db.get_mandatory_fields("gdpr_compliant")
    assert "data_processing_purpose" in fields
    assert "data_subject_categories" in fields


def test_get_mandatory_fields_nonexistent(jur_db):
    """Test mandatory fields for nonexistent jurisdiction."""
    assert jur_db.get_mandatory_fields("nonexistent") == []


# --- Special notes tests ---


def test_get_special_notes_california(jur_db):
    """Test special notes for California."""
    notes = jur_db.get_special_notes("california")
    assert isinstance(notes, list)
    assert len(notes) > 0
    assert any("non-solicitation" in note.lower() for note in notes)


def test_get_special_notes_gdpr(jur_db):
    """Test special notes for GDPR include GDPR-specific notes."""
    notes = jur_db.get_special_notes("gdpr_compliant")
    assert any("gdpr" in note.lower() for note in notes)


def test_get_special_notes_nonexistent(jur_db):
    """Test special notes for nonexistent jurisdiction."""
    assert jur_db.get_special_notes("nonexistent") == []


# --- Template path tests ---


def test_get_template_path_california(jur_db):
    """Test template path for California."""
    assert jur_db.get_template_path("california") == "templates/nda_california.docx"


def test_get_template_path_england_wales(jur_db):
    """Test template path for England & Wales."""
    assert jur_db.get_template_path("england_wales") == "templates/nda_england_wales.docx"


def test_get_template_path_gdpr(jur_db):
    """Test template path for GDPR."""
    assert jur_db.get_template_path("gdpr_compliant") == "templates/nda_eu_gdpr.docx"


def test_get_template_path_nonexistent(jur_db):
    """Test template path for nonexistent jurisdiction."""
    assert jur_db.get_template_path("nonexistent") is None


# --- Validation tests ---


def test_validate_jurisdiction_valid(jur_db):
    """Test validating a valid jurisdiction."""
    assert jur_db.validate_jurisdiction("california") is True
    assert jur_db.validate_jurisdiction("england_wales") is True
    assert jur_db.validate_jurisdiction("gdpr_compliant") is True


def test_validate_jurisdiction_invalid(jur_db):
    """Test validating an invalid jurisdiction."""
    assert jur_db.validate_jurisdiction("nonexistent") is False
    assert jur_db.validate_jurisdiction("") is False


# --- Bulk retrieval tests ---


def test_get_all_special_notes(jur_db):
    """Test getting all special notes."""
    all_notes = jur_db.get_all_special_notes()
    assert len(all_notes) == 3
    for key in jur_db.list_jurisdictions():
        assert key in all_notes
        assert isinstance(all_notes[key], list)


def test_get_all_mandatory_fields(jur_db):
    """Test getting all mandatory fields."""
    all_fields = jur_db.get_all_mandatory_fields()
    assert len(all_fields) == 3
    for key in jur_db.list_jurisdictions():
        assert key in all_fields
        assert isinstance(all_fields[key], list)


# --- Edge cases ---


def test_config_count_matches_list(jur_db):
    """Test that config count matches list length."""
    assert jur_db.get_config_count() == len(jur_db.list_jurisdictions())


def test_all_configs_have_required_keys(jur_db):
    """Test that all configs have the required keys."""
    required_keys = {
        "key",
        "name",
        "display_name",
        "governing_law",
        "default_term",
        "required_clauses",
        "optional_clauses",
        "mandatory_fields",
        "special_notes",
        "template_path",
    }
    for key, config in jur_db.get_all_configs().items():
        assert required_keys.issubset(set(config.keys())), f"Missing keys in {key}"


def test_all_required_clauses_are_strings(jur_db):
    """Test that all required clauses are strings."""
    for key in jur_db.list_jurisdictions():
        clauses = jur_db.get_required_clauses(key)
        assert all(isinstance(c, str) for c in clauses)


def test_all_mandatory_fields_are_strings(jur_db):
    """Test that all mandatory fields are strings."""
    for key in jur_db.list_jurisdictions():
        fields = jur_db.get_mandatory_fields(key)
        assert all(isinstance(f, str) for f in fields)


def test_all_special_notes_are_strings(jur_db):
    """Test that all special notes are strings."""
    for key in jur_db.list_jurisdictions():
        notes = jur_db.get_special_notes(key)
        assert all(isinstance(n, str) for n in notes)
