"""Tests for Template Library."""

import pytest
from pathlib import Path
import tempfile

from drop_servicing_tool.template_library import TemplateLibrary


class TestTemplateLibrary:
    """Tests for TemplateLibrary class."""

    def test_library_initialization(self, tmp_path):
        """Test library initialization."""
        library = TemplateLibrary(tmp_path)
        assert library is not None
        assert library._templates_dir.exists()
        assert library._builtin_dir.exists()

    def test_library_default_directory(self, tmp_path):
        """Test library uses default directory."""
        library = TemplateLibrary(tmp_path)
        assert library._base == tmp_path
        assert library._templates_dir == tmp_path / "templates"

    def test_register_template(self, tmp_path):
        """Test registering a template."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content")

        assert "test_template" in library._store
        assert library._store["test_template"] == "Test content"
        assert library._categories["test_template"] == "default"

    def test_register_template_with_category(self, tmp_path):
        """Test registering template with category."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content", category="test_category")

        assert library._categories["test_template"] == "test_category"

    def test_register_template_persists_to_disk(self, tmp_path):
        """Test that registered template is persisted to disk."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content")

        template_file = tmp_path / "templates" / "test_template.md"
        assert template_file.exists()

        content = template_file.read_text(encoding="utf-8")
        assert content == "Test content"

    def test_register_template_in_category(self, tmp_path):
        """Test registering template in category directory."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content", category="test_category")

        template_file = tmp_path / "templates" / "test_category" / "test_template.md"
        assert template_file.exists()

    def test_get_template(self, tmp_path):
        """Test getting a registered template."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content")

        content = library.get_template("test_template")
        assert content == "Test content"

    def test_get_template_not_found(self, tmp_path):
        """Test getting non-existent template."""
        library = TemplateLibrary(tmp_path)

        with pytest.raises(FileNotFoundError, match="Template 'nonexistent' not found"):
            library.get_template("nonexistent")

    def test_get_template_from_disk(self, tmp_path):
        """Test getting template from disk."""
        library = TemplateLibrary(tmp_path)

        # Create template file manually
        template_file = tmp_path / "templates" / "disk_template.md"
        template_file.write_text("Disk content", encoding="utf-8")

        content = library.get_template("disk_template")
        assert content == "Disk content"

    def test_list_templates(self, tmp_path):
        """Test listing templates."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1")
        library.register_template("template2", "Content 2")
        library.register_template("template3", "Content 3")

        templates = library.list_templates()
        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates

    def test_list_templates_by_category(self, tmp_path):
        """Test listing templates by category."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1", category="cat1")
        library.register_template("template2", "Content 2", category="cat1")
        library.register_template("template3", "Content 3", category="cat2")

        templates_cat1 = library.list_templates(category="cat1")
        assert len(templates_cat1) == 2
        assert "template1" in templates_cat1
        assert "template2" in templates_cat1
        assert "template3" not in templates_cat1

    def test_delete_template(self, tmp_path):
        """Test deleting a template."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content")

        result = library.delete_template("test_template")
        assert result is True
        assert "test_template" not in library._store

    def test_delete_template_not_found(self, tmp_path):
        """Test deleting non-existent template."""
        library = TemplateLibrary(tmp_path)

        result = library.delete_template("nonexistent")
        assert result is False

    def test_delete_template_removes_from_disk(self, tmp_path):
        """Test that deleting template removes from disk."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content")

        template_file = tmp_path / "templates" / "test_template.md"
        assert template_file.exists()

        library.delete_template("test_template")
        assert not template_file.exists()

    def test_delete_template_from_category(self, tmp_path):
        """Test deleting template from category directory."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Test content", category="test_category")

        template_file = tmp_path / "templates" / "test_category" / "test_template.md"
        assert template_file.exists()

        library.delete_template("test_template")
        assert not template_file.exists()

    def test_get_template_categories(self, tmp_path):
        """Test getting template categories."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1", category="cat1")
        library.register_template("template2", "Content 2", category="cat2")
        library.register_template("template3", "Content 3", category="cat1")

        categories = library.get_template_categories()
        assert "cat1" in categories
        assert "cat2" in categories
        assert len(categories) == 2

    def test_load_existing_templates(self, tmp_path):
        """Test loading existing templates from disk."""
        # Create template files manually
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        template_file = templates_dir / "existing_template.md"
        template_file.write_text("Existing content", encoding="utf-8")

        library = TemplateLibrary(tmp_path)

        assert "existing_template" in library._store
        assert library._store["existing_template"] == "Existing content"

    def test_load_existing_templates_from_category(self, tmp_path):
        """Test loading existing templates from category directory."""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        category_dir = templates_dir / "test_category"
        category_dir.mkdir()

        template_file = category_dir / "existing_template.md"
        template_file.write_text("Existing content", encoding="utf-8")

        library = TemplateLibrary(tmp_path)

        assert "existing_template" in library._store
        assert library._store["existing_template"] == "Existing content"
        assert library._categories["existing_template"] == "test_category"


class TestTemplateLibraryPersistence:
    """Tests for TemplateLibrary persistence."""

    def test_persistence_across_instances(self, tmp_path):
        """Test that templates persist across library instances."""
        # Create first library and register template
        library1 = TemplateLibrary(tmp_path)
        library1.register_template("test_template", "Test content")

        # Create second library instance
        library2 = TemplateLibrary(tmp_path)

        # Template should still be registered
        assert "test_template" in library2._store
        assert library2.get_template("test_template") == "Test content"

    def test_multiple_templates_persistence(self, tmp_path):
        """Test persistence of multiple templates."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1", category="cat1")
        library.register_template("template2", "Content 2", category="cat2")
        library.register_template("template3", "Content 3", category="cat1")

        # Create new instance
        library2 = TemplateLibrary(tmp_path)

        assert len(library2.list_templates()) == 3
        assert library2.get_template("template1") == "Content 1"
        assert library2.get_template("template2") == "Content 2"
        assert library2.get_template("template3") == "Content 3"


class TestTemplateLibraryValidation:
    """Tests for TemplateLibrary validation."""

    def test_register_template_with_empty_name(self, tmp_path):
        """Test registering template with empty name."""
        library = TemplateLibrary(tmp_path)

        with pytest.raises(ValueError, match="Template name cannot be empty"):
            library.register_template("", "Content")

    def test_register_template_with_special_chars(self, tmp_path):
        """Test registering template with special characters."""
        library = TemplateLibrary(tmp_path)

        # Should work with special characters
        library.register_template("test-template_123", "Content")
        assert "test-template_123" in library._store

    def test_delete_template_with_special_chars(self, tmp_path):
        """Test deleting template with special characters."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test-template_123", "Content")
        result = library.delete_template("test-template_123")
        assert result is True

    def test_get_template_with_special_chars(self, tmp_path):
        """Test getting template with special characters."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test-template_123", "Content")
        content = library.get_template("test-template_123")
        assert content == "Content"


class TestTemplateLibraryCategories:
    """Tests for template categories."""

    def test_default_category(self, tmp_path):
        """Test default category for templates."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Content")

        assert library._categories["test_template"] == "default"

    def test_custom_category(self, tmp_path):
        """Test custom category for templates."""
        library = TemplateLibrary(tmp_path)

        library.register_template("test_template", "Content", category="custom")

        assert library._categories["test_template"] == "custom"

    def test_list_templates_by_default_category(self, tmp_path):
        """Test listing templates in default category."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1")
        library.register_template("template2", "Content 2", category="custom")

        templates = library.list_templates(category="default")
        assert len(templates) == 1
        assert "template1" in templates

    def test_list_templates_by_custom_category(self, tmp_path):
        """Test listing templates in custom category."""
        library = TemplateLibrary(tmp_path)

        library.register_template("template1", "Content 1", category="custom")
        library.register_template("template2", "Content 2", category="custom")
        library.register_template("template3", "Content 3")

        templates = library.list_templates(category="custom")
        assert len(templates) == 2
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" not in templates
