"""Tests for ai_movie_gen_suite templates module."""

from pathlib import Path

import pytest

from ai_movie_gen_suite.templates import (
    load_template,
    render_template,
    get_template_path,
    get_all_template_names,
)


class TestGetTemplatePath:
    def test_get_template_path_returns_path(self):
        path = get_template_path("beats")
        assert isinstance(path, Path)
        assert path.exists()

    def test_get_template_path_invalid_name(self):
        with pytest.raises(ValueError, match="Unknown template"):
            get_template_path("nonexistent")

    def test_get_template_path_all_templates(self):
        """All known templates should have valid paths."""
        templates = get_all_template_names()
        for template_name in templates:
            path = get_template_path(template_name)
            assert path.exists()
            assert path.name.endswith(".j2")


class TestLoadTemplate:
    def test_load_template_returns_string(self):
        template_str = load_template("beats")
        assert isinstance(template_str, str)
        assert len(template_str) > 0

    def test_load_template_all_templates(self):
        """All templates should load without error."""
        templates = get_all_template_names()
        for template_name in templates:
            template_str = load_template(template_name)
            assert isinstance(template_str, str)
            assert len(template_str) > 0

    def test_load_template_invalid_name(self):
        with pytest.raises(ValueError, match="Unknown template"):
            load_template("nonexistent")


class TestRenderTemplate:
    def test_render_template_basic(self):
        template_str = load_template("beats")
        rendered = render_template(template_str, logline="A test logline")
        assert isinstance(rendered, str)
        assert "A test logline" in rendered

    def test_render_template_with_multiple_variables(self):
        template_str = load_template("beats")
        rendered = render_template(
            template_str,
            logline="A test logline",
            genre="drama",
            tone="dark",
        )
        assert isinstance(rendered, str)
        assert "A test logline" in rendered
        assert "drama" in rendered
        assert "dark" in rendered

    def test_render_template_with_project(self):
        from ai_movie_gen_suite.models import Project

        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
        )
        template_str = load_template("beats")
        rendered = render_template(template_str, project=project)
        assert isinstance(rendered, str)
        assert "A test logline" in rendered

    def test_render_template_with_both(self):
        from ai_movie_gen_suite.models import Project

        project = Project(
            title="Test Movie",
            logline="A test logline",
            genre="drama",
            tone="dark",
        )
        template_str = load_template("beats")
        rendered = render_template(
            template_str,
            project=project,
            genre="comedy",
        )
        assert isinstance(rendered, str)
        assert "A test logline" in rendered
        assert "comedy" in rendered

    def test_render_template_empty_template(self):
        with pytest.raises(ValueError, match="Template cannot be empty"):
            render_template("", logline="test")

    def test_render_template_with_none_values(self):
        template_str = load_template("beats")
        rendered = render_template(template_str, logline=None, genre=None)
        assert isinstance(rendered, str)
        assert "None" in rendered

    def test_render_template_all_templates(self):
        """All templates should render without error."""
        templates = get_all_template_names()
        for template_name in templates:
            template_str = load_template(template_name)
            rendered = render_template(template_str, logline="A test logline")
            assert isinstance(rendered, str)


class TestGetAllTemplateNames:
    def test_get_all_template_names_returns_list(self):
        template_names = get_all_template_names()
        assert isinstance(template_names, list)

    def test_get_all_template_names_contains_expected(self):
        template_names = get_all_template_names()
        expected_templates = [
            "beats",
            "characters",
            "script",
            "scenes",
        ]
        for template in expected_templates:
            assert template in template_names

    def test_get_all_template_names_not_empty(self):
        template_names = get_all_template_names()
        assert len(template_names) > 0
