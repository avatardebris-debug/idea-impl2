"""Tests for the Design Template Manager."""

import pytest
import sys
import pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))
from design.template_manager import TemplateManager, DesignTemplate, DesignStyle, ColorScheme, TypographyStyle


class TestTemplateManager:
    """Test suite for TemplateManager."""

    @pytest.fixture
    def manager(self):
        """Create a fresh TemplateManager instance for each test."""
        return TemplateManager()

    @pytest.fixture
    def sample_templates(self):
        """Provide sample templates for testing."""
        return [
            DesignTemplate(
                template_id="t001",
                template_name="Modern Minimalist",
                genre="fiction",
                style=DesignStyle.MODERN,
                description="Clean, modern design with minimal elements",
                color_scheme=ColorScheme.MONOCHROMATIC,
                typography_style=TypographyStyle.SANS_SERIF,
                layout_type="centered",
                image_style="generated",
                recommended_for=["fiction", "non-fiction", "business"],
                usage_examples=["Use for contemporary fiction", "Good for business books"]
            ),
            DesignTemplate(
                template_id="t002",
                template_name="Classic Elegant",
                genre="fiction",
                style=DesignStyle.CLASSIC,
                description="Traditional elegant design with serif fonts",
                color_scheme=ColorScheme.COMPLEMENTARY,
                typography_style=TypographyStyle.SERIF,
                layout_type="centered",
                image_style="generated",
                recommended_for=["fiction", "romance", "literary"],
                usage_examples=["Use for romance novels", "Good for literary fiction"]
            ),
            DesignTemplate(
                template_id="t003",
                template_name="Vibrant Fantasy",
                genre="fantasy",
                style=DesignStyle.FANTASY,
                description="Colorful, imaginative design for fantasy books",
                color_scheme=ColorScheme.TRIADIC,
                typography_style=TypographyStyle.DISPLAY,
                layout_type="dynamic",
                image_style="generated",
                recommended_for=["fantasy", "sci-fi", "adventure"],
                usage_examples=["Use for fantasy novels", "Good for adventure stories"]
            ),
            DesignTemplate(
                template_id="t004",
                template_name="Professional Business",
                genre="business",
                style=DesignStyle.PROFESSIONAL,
                description="Clean, professional design for business books",
                color_scheme=ColorScheme.ANALOGOUS,
                typography_style=TypographyStyle.SANS_SERIF,
                layout_type="centered",
                image_style="generated",
                recommended_for=["business", "self-help", "non-fiction"],
                usage_examples=["Use for business books", "Good for self-help"]
            ),
        ]

    # == Initialization Tests ==

    def test_manager_initialization(self, manager):
        """Test that manager initializes correctly."""
        assert manager is not None
        assert isinstance(manager.templates, dict)
        assert len(manager.templates) == 0

    def test_manager_with_initial_templates(self, sample_templates):
        """Test manager initialization with templates."""
        manager = TemplateManager(initial_templates=sample_templates)
        
        assert len(manager.templates) == 4
        assert "t001" in manager.templates
        assert "t002" in manager.templates
        assert "t003" in manager.templates
        assert "t004" in manager.templates

    # == Template Addition Tests ==

    def test_add_template(self, manager):
        """Test adding a single template."""
        template = DesignTemplate(
            template_id="t005",
            template_name="Test Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="Test description",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.add_template(template)
        
        assert result is True
        assert "t005" in manager.templates
        assert manager.templates["t005"].template_name == "Test Template"

    def test_add_template_duplicate_id(self, manager):
        """Test adding a template with duplicate ID."""
        template1 = DesignTemplate(
            template_id="t001",
            template_name="Template 1",
            genre="fiction",
            style=DesignStyle.MODERN,
            description="Description 1",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        template2 = DesignTemplate(
            template_id="t001",
            template_name="Template 2",
            genre="fiction",
            style=DesignStyle.CLASSIC,
            description="Description 2",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        # Add first template
        result1 = manager.add_template(template1)
        assert result1 is True
        
        # Try to add second template with same ID
        result2 = manager.add_template(template2)
        assert result2 is False
        assert manager.templates["t001"].template_name == "Template 1"

    def test_add_multiple_templates(self, manager, sample_templates):
        """Test adding multiple templates at once."""
        result = manager.add_templates(sample_templates)
        
        assert result is True
        assert len(manager.templates) == 4
        assert all(tid in manager.templates for tid in ["t001", "t002", "t003", "t004"])

    # == Template Retrieval Tests ==

    def test_get_template_by_id(self, manager, sample_templates):
        """Test retrieving a template by ID."""
        manager.add_templates(sample_templates)
        
        template = manager.get_template("t001")
        
        assert template is not None
        assert template.template_id == "t001"
        assert template.template_name == "Modern Minimalist"

    def test_get_template_not_found(self, manager):
        """Test retrieving a non-existent template."""
        template = manager.get_template("nonexistent")
        
        assert template is None

    def test_get_all_templates(self, manager, sample_templates):
        """Test retrieving all templates."""
        manager.add_templates(sample_templates)
        
        templates = manager.get_all_templates()
        
        assert len(templates) == 4
        assert all(isinstance(t, DesignTemplate) for t in templates)

    def test_get_template_as_dict(self, manager, sample_templates):
        """Test retrieving template as dictionary."""
        manager.add_templates(sample_templates)
        
        template_dict = manager.get_template_as_dict("t001")
        
        assert template_dict is not None
        assert template_dict["template_id"] == "t001"
        assert template_dict["template_name"] == "Modern Minimalist"

    # == Template Filtering Tests ==

    def test_filter_by_genre(self, manager, sample_templates):
        """Test filtering templates by genre."""
        manager.add_templates(sample_templates)
        
        fiction_templates = manager.filter_by_genre("fiction")
        
        assert len(fiction_templates) == 2
        assert all(t.genre == "fiction" for t in fiction_templates)
        assert all(t.template_id in ["t001", "t002"] for t in fiction_templates)

    def test_filter_by_style(self, manager, sample_templates):
        """Test filtering templates by design style."""
        manager.add_templates(sample_templates)
        
        modern_templates = manager.filter_by_style(DesignStyle.MODERN)
        
        assert len(modern_templates) == 1
        assert modern_templates[0].template_id == "t001"

    def test_filter_by_color_scheme(self, manager, sample_templates):
        """Test filtering templates by color scheme."""
        manager.add_templates(sample_templates)
        
        mono_templates = manager.filter_by_color_scheme(ColorScheme.MONOCHROMATIC)
        
        assert len(mono_templates) == 1
        assert mono_templates[0].template_id == "t001"

    def test_filter_by_layout_type(self, manager, sample_templates):
        """Test filtering templates by layout type."""
        manager.add_templates(sample_templates)
        
        centered_templates = manager.filter_by_layout_type("centered")
        
        assert len(centered_templates) == 3
        assert all(t.layout_type == "centered" for t in centered_templates)

    def test_filter_multiple_criteria(self, manager, sample_templates):
        """Test filtering by multiple criteria."""
        manager.add_templates(sample_templates)
        
        filtered = manager.filter_templates(
            genre="fiction",
            style=DesignStyle.CLASSIC
        )
        
        assert len(filtered) == 1
        assert filtered[0].template_id == "t002"

    def test_filter_no_results(self, manager, sample_templates):
        """Test filtering with no matching results."""
        manager.add_templates(sample_templates)
        
        filtered = manager.filter_by_genre("nonexistent_genre")
        
        assert len(filtered) == 0

    # == Template Modification Tests ==

    def test_update_template(self, manager, sample_templates):
        """Test updating an existing template."""
        manager.add_templates(sample_templates)
        
        updated_template = DesignTemplate(
            template_id="t001",
            template_name="Updated Modern Minimalist",
            genre="fiction",
            style=DesignStyle.MODERN,
            description="Updated description",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.update_template(updated_template)
        
        assert result is True
        assert manager.templates["t001"].template_name == "Updated Modern Minimalist"
        assert manager.templates["t001"].description == "Updated description"

    def test_update_template_not_found(self, manager):
        """Test updating a non-existent template."""
        updated_template = DesignTemplate(
            template_id="t999",
            template_name="New Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="Description",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.update_template(updated_template)
        
        assert result is False

    def test_update_template_preserves_other_fields(self, manager, sample_templates):
        """Test that updating a template preserves unchanged fields."""
        manager.add_templates(sample_templates)
        
        original_template = manager.templates["t001"]
        
        updated_template = DesignTemplate(
            template_id="t001",
            template_name="Updated Name",
            genre=original_template.genre,
            style=original_template.style,
            description=original_template.description,
            color_scheme=original_template.color_scheme,
            typography_style=original_template.typography_style,
            layout_type=original_template.layout_type,
            image_style=original_template.image_style,
            recommended_for=original_template.recommended_for,
            usage_examples=original_template.usage_examples
        )
        
        manager.update_template(updated_template)
        
        # Verify unchanged fields
        assert manager.templates["t001"].genre == original_template.genre
        assert manager.templates["t001"].style == original_template.style
        assert manager.templates["t001"].recommended_for == original_template.recommended_for

    # == Template Deletion Tests ==

    def test_delete_template(self, manager, sample_templates):
        """Test deleting a template."""
        manager.add_templates(sample_templates)
        
        result = manager.delete_template("t001")
        
        assert result is True
        assert "t001" not in manager.templates
        assert len(manager.templates) == 3

    def test_delete_template_not_found(self, manager):
        """Test deleting a non-existent template."""
        result = manager.delete_template("nonexistent")
        
        assert result is False
        assert len(manager.templates) == 0

    def test_delete_all_templates(self, manager, sample_templates):
        """Test deleting all templates."""
        manager.add_templates(sample_templates)
        
        result = manager.delete_template("t001")
        assert result is True
        
        result = manager.delete_template("t002")
        assert result is True
        
        result = manager.delete_template("t003")
        assert result is True
        
        result = manager.delete_template("t004")
        assert result is True
        
        assert len(manager.templates) == 0

    # == Template Count Tests ==

    def test_get_template_count(self, manager, sample_templates):
        """Test getting the total number of templates."""
        manager.add_templates(sample_templates)
        
        count = manager.get_template_count()
        
        assert count == 4

    def test_get_template_count_empty(self, manager):
        """Test getting template count when empty."""
        count = manager.get_template_count()
        
        assert count == 0

    # == Template Existence Tests ==

    def test_template_exists_true(self, manager, sample_templates):
        """Test checking if a template exists."""
        manager.add_templates(sample_templates)
        
        exists = manager.template_exists("t001")
        
        assert exists is True

    def test_template_exists_false(self, manager):
        """Test checking if a template exists when it doesn't."""
        exists = manager.template_exists("nonexistent")
        
        assert exists is False

    # == Template Export/Import Tests ==

    def test_export_templates_to_dict(self, manager, sample_templates):
        """Test exporting templates to dictionary format."""
        manager.add_templates(sample_templates)
        
        exported = manager.export_templates()
        
        assert isinstance(exported, dict)
        assert len(exported) == 4
        assert "t001" in exported
        assert exported["t001"]["template_id"] == "t001"

    def test_import_templates_from_dict(self, manager, sample_templates):
        """Test importing templates from dictionary format."""
        exported = manager.export_templates()
        
        # Clear templates
        manager.templates = {}
        
        # Import back
        manager.import_templates(exported)
        
        assert len(manager.templates) == 4
        assert manager.templates["t001"].template_name == "Modern Minimalist"

    def test_import_templates_overwrites_existing(self, manager, sample_templates):
        """Test that importing templates overwrites existing ones."""
        manager.add_templates(sample_templates)
        
        # Create different templates
        different_templates = [
            DesignTemplate(
                template_id="t001",
                template_name="Different Name",
                genre="different",
                style=DesignStyle.CLASSIC,
                description="Different description",
                color_scheme=ColorScheme.CUSTOM,
                typography_style=TypographyStyle.SERIF,
                layout_type="centered",
                image_style="generated"
            )
        ]
        
        exported = manager.export_templates()
        
        # Import different templates
        manager.import_templates(exported)
        
        # Should have original templates, not the different ones
        assert manager.templates["t001"].template_name == "Modern Minimalist"

    # == Template Recommendation Tests ==

    def test_get_recommended_templates(self, manager, sample_templates):
        """Test getting templates recommended for a genre."""
        manager.add_templates(sample_templates)
        
        recommended = manager.get_recommended_templates("fiction")
        
        assert len(recommended) >= 1
        assert all("fiction" in t.recommended_for for t in recommended)

    def test_get_recommended_templates_multiple(self, manager, sample_templates):
        """Test getting templates recommended for multiple genres."""
        manager.add_templates(sample_templates)
        
        recommended = manager.get_recommended_templates(["fiction", "business"])
        
        assert len(recommended) >= 2
        # Should include templates recommended for either genre

    def test_get_recommended_templates_none(self, manager):
        """Test getting recommended templates when none match."""
        recommended = manager.get_recommended_templates("nonexistent_genre")
        
        assert len(recommended) == 0

    # == Template Search Tests ==

    def test_search_templates_by_name(self, manager, sample_templates):
        """Test searching templates by name."""
        manager.add_templates(sample_templates)
        
        results = manager.search_templates("Modern")
        
        assert len(results) >= 1
        assert any("Modern" in r.template_name for r in results)

    def test_search_templates_case_insensitive(self, manager, sample_templates):
        """Test that search is case-insensitive."""
        manager.add_templates(sample_templates)
        
        results = manager.search_templates("modern")
        
        assert len(results) >= 1
        assert any("Modern" in r.template_name for r in results)

    def test_search_templates_by_description(self, manager, sample_templates):
        """Test searching templates by description."""
        manager.add_templates(sample_templates)
        
        results = manager.search_templates("minimalist")
        
        assert len(results) >= 1
        assert any("minimalist" in r.description.lower() for r in results)

    def test_search_templates_no_results(self, manager, sample_templates):
        """Test searching with no matching results."""
        manager.add_templates(sample_templates)
        
        results = manager.search_templates("nonexistent")
        
        assert len(results) == 0

    # == Edge Cases and Error Handling ==

    def test_manager_with_empty_templates_list(self):
        """Test manager initialization with empty templates list."""
        manager = TemplateManager(initial_templates=[])
        
        assert len(manager.templates) == 0

    def test_manager_with_none_templates_list(self):
        """Test manager initialization with None templates list."""
        manager = TemplateManager(initial_templates=None)
        
        assert len(manager.templates) == 0

    def test_template_with_all_optional_fields(self, manager):
        """Test template with all optional fields populated."""
        template = DesignTemplate(
            template_id="t006",
            template_name="Complete Template",
            genre="fiction",
            style=DesignStyle.MODERN,
            description="Complete template with all fields",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated",
            recommended_for=["fiction", "non-fiction"],
            usage_examples=["Example 1", "Example 2"]
        )
        
        manager.add_template(template)
        
        assert template.template_id in manager.templates
        assert manager.templates[template.template_id].recommended_for == ["fiction", "non-fiction"]
        assert len(manager.templates[template.template_id].usage_examples) == 2

    def test_template_with_minimal_fields(self, manager):
        """Test template with minimal required fields."""
        template = DesignTemplate(
            template_id="t007",
            template_name="Minimal Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="Minimal template",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        manager.add_template(template)
        
        assert template.template_id in manager.templates

    # == Integration Tests ==

    def test_full_workflow(self, manager, sample_templates):
        """Test a complete workflow of template operations."""
        # Add templates
        manager.add_templates(sample_templates)
        assert len(manager.templates) == 4
        
        # Retrieve a template
        template = manager.get_template("t001")
        assert template is not None
        assert template.template_name == "Modern Minimalist"
        
        # Filter templates
        fiction_templates = manager.filter_by_genre("fiction")
        assert len(fiction_templates) == 2
        
        # Update a template
        updated = DesignTemplate(
            template_id="t001",
            template_name="Updated Modern",
            genre="fiction",
            style=DesignStyle.MODERN,
            description="Updated description",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        manager.update_template(updated)
        assert manager.templates["t001"].template_name == "Updated Modern"
        
        # Export and import
        exported = manager.export_templates()
        assert len(exported) == 4
        
        # Delete a template
        manager.delete_template("t001")
        assert len(manager.templates) == 3
        
        # Search
        results = manager.search_templates("Updated")
        assert len(results) == 1

    def test_template_persistence(self, manager, sample_templates):
        """Test that templates can be persisted and restored."""
        # Add templates
        manager.add_templates(sample_templates)
        
        # Export
        exported = manager.export_templates()
        
        # Create new manager
        new_manager = TemplateManager()
        
        # Import
        new_manager.import_templates(exported)
        
        # Verify
        assert len(new_manager.templates) == 4
        assert new_manager.templates["t001"].template_name == "Modern Minimalist"
        assert new_manager.templates["t003"].style == DesignStyle.FANTASY


class TestTemplateManagerEdgeCases:
    """Edge case tests for TemplateManager."""

    def test_manager_with_special_characters_in_template_id(self):
        """Test template with special characters in ID."""
        manager = TemplateManager()
        
        template = DesignTemplate(
            template_id="t-001_special",
            template_name="Special ID Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="Template with special ID",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.add_template(template)
        
        assert result is True
        assert "t-001_special" in manager.templates

    def test_manager_with_very_long_template_name(self):
        """Test template with very long name."""
        manager = TemplateManager()
        
        long_name = "A" * 500
        template = DesignTemplate(
            template_id="t001",
            template_name=long_name,
            genre="test",
            style=DesignStyle.MODERN,
            description="Template with long name",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.add_template(template)
        
        assert result is True
        assert len(manager.templates["t001"].template_name) == 500

    def test_manager_with_empty_description(self):
        """Test template with empty description."""
        manager = TemplateManager()
        
        template = DesignTemplate(
            template_id="t001",
            template_name="Empty Description Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.add_template(template)
        
        assert result is True
        assert manager.templates["t001"].description == ""

    def test_manager_with_unicode_characters(self):
        """Test template with unicode characters."""
        manager = TemplateManager()
        
        template = DesignTemplate(
            template_id="t001",
            template_name="模板 - テンプレート - 模板",
            genre="测试 - テスト - 测试",
            style=DesignStyle.MODERN,
            description="描述 - 説明 - 描述",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated"
        )
        
        result = manager.add_template(template)
        
        assert result is True
        assert "模板" in manager.templates["t001"].template_name

    def test_manager_with_duplicate_recommended_genres(self):
        """Test template with duplicate recommended genres."""
        manager = TemplateManager()
        
        template = DesignTemplate(
            template_id="t001",
            template_name="Duplicate Genres Template",
            genre="test",
            style=DesignStyle.MODERN,
            description="Template with duplicate genres",
            color_scheme=ColorScheme.CUSTOM,
            typography_style=TypographyStyle.SANS_SERIF,
            layout_type="centered",
            image_style="generated",
            recommended_for=["fiction", "fiction", "non-fiction"]
        )
        
        result = manager.add_template(template)
        
        assert result is True
        # Manager should preserve the duplicates as provided
        assert manager.templates["t001"].recommended_for == ["fiction", "fiction", "non-fiction"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])