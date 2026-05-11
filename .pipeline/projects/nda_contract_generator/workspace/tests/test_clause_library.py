"""Tests for the clause library module."""

import json
import os
import tempfile
import pytest

from nda_contract_generator.core.clause_library import ClauseLibrary


@pytest.fixture
def clause_lib():
    """Create a ClauseLibrary instance using the real data file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(
        base_dir, "nda_contract_generator", "core", "clause_data.json"
    )
    return ClauseLibrary(data_path=data_path)


@pytest.fixture
def custom_lib():
    """Create a ClauseLibrary from a temporary JSON file."""
    data = {
        "clauses": [
            {
                "name": "test_clause",
                "default": "option_a",
                "allowed_values": ["option_a", "option_b", "option_c"],
                "description": "A test clause",
                "jurisdiction_overrides": {"jur_a": "option_b", "jur_b": "option_c"},
            },
            {
                "name": "another_clause",
                "default": "x",
                "allowed_values": ["x", "y"],
                "description": "Another test clause",
                "jurisdiction_overrides": {},
            },
        ]
    }
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        tmp_path = f.name
    try:
        return ClauseLibrary(data_path=tmp_path)
    finally:
        os.unlink(tmp_path)


# --- Loading tests ---


def test_load_clauses(clause_lib):
    """Test that clauses are loaded from the JSON file."""
    assert clause_lib.get_clause_count() >= 20


def test_list_clause_names(clause_lib):
    """Test listing all clause names."""
    names = clause_lib.list_clause_names()
    assert isinstance(names, list)
    assert "definition_of_confidential_info" in names
    assert "governing_law" in names
    assert "audit_rights" in names


def test_get_clause_returns_dict(clause_lib):
    """Test that get_clause returns a dict with expected keys."""
    clause = clause_lib.get_clause("term_length")
    assert clause is not None
    assert "name" in clause
    assert "default" in clause
    assert "allowed_values" in clause
    assert "description" in clause
    assert "jurisdiction_overrides" in clause


def test_get_clause_default_value(clause_lib):
    """Test that the default value is correctly reported."""
    clause = clause_lib.get_clause("term_length")
    assert clause["default"] == "2_years"
    assert clause["current_value"] == "2_years"


def test_get_clause_allowed_values(clause_lib):
    """Test that allowed values are correctly reported."""
    allowed = clause_lib.get_allowed_values("term_length")
    assert "1_year" in allowed
    assert "2_years" in allowed
    assert "3_years" in allowed
    assert "5_years" in allowed
    assert "indefinite" in allowed


def test_get_clause_nonexistent(clause_lib):
    """Test that nonexistent clauses return None."""
    assert clause_lib.get_clause("nonexistent_clause") is None


def test_get_allowed_values_nonexistent(clause_lib):
    """Test that allowed values for nonexistent clause returns empty list."""
    assert clause_lib.get_allowed_values("nonexistent_clause") == []


# --- Override tests ---


def test_override_clause_success(custom_lib):
    """Test overriding a clause value."""
    result = custom_lib.override_clause("test_clause", "option_b")
    assert result is True
    clause = custom_lib.get_clause("test_clause")
    assert clause["current_value"] == "option_b"


def test_override_clause_invalid_value(custom_lib):
    """Test that overriding with an invalid value fails."""
    result = custom_lib.override_clause("test_clause", "invalid_option")
    assert result is False


def test_override_clause_nonexistent(custom_lib):
    """Test that overriding a nonexistent clause fails."""
    result = custom_lib.override_clause("nonexistent", "option_a")
    assert result is False


def test_remove_override(custom_lib):
    """Test removing an override reverts to default."""
    custom_lib.override_clause("test_clause", "option_b")
    result = custom_lib.remove_override("test_clause")
    assert result is True
    clause = custom_lib.get_clause("test_clause")
    assert clause["current_value"] == "option_a"


def test_remove_override_nonexistent(custom_lib):
    """Test removing a nonexistent override returns False."""
    result = custom_lib.remove_override("nonexistent")
    assert result is False


# --- Jurisdiction override tests ---


def test_apply_overrides_jurisdiction_a(custom_lib):
    """Test applying jurisdiction-specific overrides."""
    effective = custom_lib.apply_overrides("jur_a")
    assert effective["test_clause"] == "option_b"
    assert effective["another_clause"] == "x"  # no override, use default


def test_apply_overrides_jurisdiction_b(custom_lib):
    """Test applying different jurisdiction overrides."""
    effective = custom_lib.apply_overrides("jur_b")
    assert effective["test_clause"] == "option_c"
    assert effective["another_clause"] == "x"


def test_apply_overrides_unknown_jurisdiction(custom_lib):
    """Test applying an unknown jurisdiction uses defaults."""
    effective = custom_lib.apply_overrides("unknown_jur")
    assert effective["test_clause"] == "option_a"
    assert effective["another_clause"] == "x"


def test_apply_overrides_returns_all_clauses(custom_lib):
    """Test that apply_overrides returns all clauses."""
    effective = custom_lib.apply_overrides("jur_a")
    assert len(effective) == 2
    assert "test_clause" in effective
    assert "another_clause" in effective


# --- get_all_clauses tests ---


def test_get_all_clauses_returns_all(clause_lib):
    """Test that get_all_clauses returns all loaded clauses."""
    all_clauses = clause_lib.get_all_clauses()
    assert len(all_clauses) == clause_lib.get_clause_count()


def test_get_all_clauses_with_overrides(custom_lib):
    """Test that get_all_clauses reflects current overrides."""
    custom_lib.override_clause("test_clause", "option_b")
    all_clauses = custom_lib.get_all_clauses()
    assert all_clauses["test_clause"]["current_value"] == "option_b"
    assert all_clauses["another_clause"]["current_value"] == "x"


# --- Edge cases ---


def test_empty_clause_library():
    """Test loading an empty clause library."""
    data = {"clauses": []}
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(data, f)
        tmp_path = f.name
    try:
        lib = ClauseLibrary(data_path=tmp_path)
        assert lib.get_clause_count() == 0
        assert lib.list_clause_names() == []
        assert lib.get_all_clauses() == {}
    finally:
        os.unlink(tmp_path)


def test_clause_with_no_overrides(custom_lib):
    """Test a clause with no jurisdiction overrides uses default."""
    effective = custom_lib.apply_overrides("jur_a")
    assert effective["another_clause"] == "x"


def test_multiple_overrides(custom_lib):
    """Test applying multiple overrides."""
    custom_lib.override_clause("test_clause", "option_c")
    custom_lib.override_clause("another_clause", "y")
    assert custom_lib.get_clause("test_clause")["current_value"] == "option_c"
    assert custom_lib.get_clause("another_clause")["current_value"] == "y"


def test_override_then_remove(custom_lib):
    """Test overriding and then removing an override."""
    custom_lib.override_clause("test_clause", "option_b")
    assert custom_lib.get_clause("test_clause")["current_value"] == "option_b"
    custom_lib.remove_override("test_clause")
    assert custom_lib.get_clause("test_clause")["current_value"] == "option_a"


def test_get_all_clauses_reflects_overrides(clause_lib):
    """Test that get_all_clauses reflects overrides applied."""
    clause_lib.override_clause("term_length", "5_years")
    all_clauses = clause_lib.get_all_clauses()
    assert all_clauses["term_length"]["current_value"] == "5_years"
    # Other clauses should still have defaults
    assert all_clauses["definition_of_confidential_info"]["current_value"] == "broad"
