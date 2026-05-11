"""Tests for the AI Movie Generation Suite prompt library."""

import pytest
from ai_movie_gen_suite.prompts.prompt_library import (
    PromptTemplate,
    PromptLibrary,
    prompt_library,
)


class TestPromptTemplate:
    """Tests for the PromptTemplate class."""

    def test_create_prompt_template(self):
        """Test creating a prompt template."""
        template = PromptTemplate(
            name="test_template",
            prompt="Test prompt",
            description="Test description",
            category="test",
            parameters=["param1", "param2"],
        )
        assert template.name == "test_template"
        assert template.prompt == "Test prompt"
        assert template.description == "Test description"
        assert template.category == "test"
        assert template.parameters == ["param1", "param2"]

    def test_render_prompt_template(self):
        """Test rendering a prompt template."""
        template = PromptTemplate(
            name="test_template",
            prompt="Hello {name}!",
            description="Test description",
            category="test",
            parameters=["name"],
        )
        rendered = template.render(name="World")
        assert rendered == "Hello World!"

    def test_render_prompt_template_missing_parameter(self):
        """Test rendering a prompt template with missing parameter."""
        template = PromptTemplate(
            name="test_template",
            prompt="Hello {name}!",
            description="Test description",
            category="test",
            parameters=["name"],
        )
        with pytest.raises(KeyError):
            template.render()


class TestPromptLibrary:
    """Tests for the PromptLibrary class."""

    def test_add_prompt_template(self):
        """Test adding a prompt template."""
        library = PromptLibrary()
        template = PromptTemplate(
            name="test_template",
            prompt="Test prompt",
            description="Test description",
            category="test",
            parameters=["param1"],
        )
        library.add_template(template)
        assert library.get_template("test_template") == template

    def test_get_template_not_found(self):
        """Test getting a non-existent template."""
        library = PromptLibrary()
        with pytest.raises(KeyError):
            library.get_template("non_existent")

    def test_get_templates_by_category(self):
        """Test getting templates by category."""
        library = PromptLibrary()
        template1 = PromptTemplate(
            name="test_template1",
            prompt="Test prompt 1",
            description="Test description",
            category="test",
            parameters=[],
        )
        template2 = PromptTemplate(
            name="test_template2",
            prompt="Test prompt 2",
            description="Test description",
            category="test",
            parameters=[],
        )
        library.add_template(template1)
        library.add_template(template2)
        templates = library.get_templates_by_category("test")
        assert len(templates) == 2
        assert template1 in templates
        assert template2 in templates

    def test_get_templates_by_category_not_found(self):
        """Test getting templates by non-existent category."""
        library = PromptLibrary()
        templates = library.get_templates_by_category("non_existent")
        assert templates == []


class TestPromptLibrarySingleton:
    """Tests for the prompt_library singleton."""

    def test_prompt_library_singleton(self):
        """Test that prompt_library is a singleton."""
        library1 = prompt_library
        library2 = prompt_library
        assert library1 is library2

    def test_prompt_library_has_templates(self):
        """Test that prompt_library has templates."""
        assert len(prompt_library.templates) > 0

    def test_prompt_library_has_concept_generation_templates(self):
        """Test that prompt_library has concept generation templates."""
        templates = prompt_library.get_templates_by_category("concept_generation")
        assert len(templates) > 0

    def test_prompt_library_has_character_development_templates(self):
        """Test that prompt_library has character development templates."""
        templates = prompt_library.get_templates_by_category("character_development")
        assert len(templates) > 0

    def test_prompt_library_has_scene_writing_templates(self):
        """Test that prompt_library has scene writing templates."""
        templates = prompt_library.get_templates_by_category("scene_writing")
        assert len(templates) > 0

    def test_prompt_library_has_script_formatting_templates(self):
        """Test that prompt_library has script formatting templates."""
        templates = prompt_library.get_templates_by_category("script_formatting")
        assert len(templates) > 0

    def test_prompt_library_has_visual_development_templates(self):
        """Test that prompt_library has visual development templates."""
        templates = prompt_library.get_templates_by_category("visual_development")
        assert len(templates) > 0

    def test_prompt_library_has_audio_production_templates(self):
        """Test that prompt_library has audio production templates."""
        templates = prompt_library.get_templates_by_category("audio_production")
        assert len(templates) > 0

    def test_prompt_library_has_post_production_templates(self):
        """Test that prompt_library has post-production templates."""
        templates = prompt_library.get_templates_by_category("post_production")
        assert len(templates) > 0

    def test_prompt_library_has_marketing_templates(self):
        """Test that prompt_library has marketing templates."""
        templates = prompt_library.get_templates_by_category("marketing")
        assert len(templates) > 0

    def test_prompt_library_has_distribution_templates(self):
        """Test that prompt_library has distribution templates."""
        templates = prompt_library.get_templates_by_category("distribution")
        assert len(templates) > 0
