"""Tests for sacbot package."""

from sacbot import generate


def test_package_import():
    """Verify that the package-level import works and exports generate."""
    assert callable(generate)


def test_package_all_exports_generate():
    """Verify that __all__ includes 'generate'."""
    import sacbot
    assert "generate" in sacbot.__all__
