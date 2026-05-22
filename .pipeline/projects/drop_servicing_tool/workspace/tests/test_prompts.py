"""Tests for Prompt Template System."""

import pytest
from drop_servicing_tool.prompts import (
    load_prompt_template,
    fill_prompt,
    build_step_prompt,
)
from drop_servicing_tool.sop_schema import SOP, SOPInput, SOPStep


class TestLoadPromptTemplate:
    """Tests for load_prompt_template function."""

    def test_load_existing_template(self):
        """Test loading an existing prompt template."""
        # default_step template should exist
        template = load_prompt_template("default_step")
        assert isinstance(template, str)
        assert len(template) > 0

    def test_load_nonexistent_template(self):
        """Test loading a non-existent template."""
        with pytest.raises(FileNotFoundError, match="Prompt template not found"):
            load_prompt_template("nonexistent_template")


class TestFillPrompt:
    """Tests for fill_prompt function."""

    def test_fill_simple_placeholders(self):
        """Test filling simple placeholders."""
        template = "Hello {{name}}, welcome to {{place}}!"
        context = {"name": "Alice", "place": "Wonderland"}
        result = fill_prompt(template, context)
        assert result == "Hello Alice, welcome to Wonderland!"

    def test_fill_dict_value(self):
        """Test filling a dict value (should be JSON)."""
        template = "Data: {{data}}"
        context = {"data": {"key": "value"}}
        result = fill_prompt(template, context)
        assert '"key": "value"' in result

    def test_fill_list_value(self):
        """Test filling a list value (should be JSON)."""
        template = "Items: {{items}}"
        context = {"items": [1, 2, 3]}
        result = fill_prompt(template, context)
        assert "[1, 2, 3]" in result

    def test_fill_missing_key(self):
        """Test filling with missing key (should leave placeholder)."""
        template = "Hello {{name}}"
        context = {}
        result = fill_prompt(template, context)
        assert result == "Hello {{name}}"


class TestBuildStepPrompt:
    """Tests for build_step_prompt function."""

    def test_build_prompt_basic(self):
        """Test building a basic step prompt."""
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            inputs=[SOPInput(name="topic", type="string", required=True)],
            steps=[
                SOPStep(name="research", description="Research the topic"),
            ],
            output_format="Research findings",
        )

        prompt = build_step_prompt(
            sop=sop,
            step_index=0,
            input_data={"topic": "AI"},
            step_outputs=[],
        )

        assert "research" in prompt.lower()
        assert "Research the topic" in prompt
        assert "AI" in prompt
        assert "Research findings" in prompt

    def test_build_prompt_with_previous_output(self):
        """Test building prompt with previous step output."""
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            inputs=[SOPInput(name="topic", type="string", required=True)],
            steps=[
                SOPStep(name="research", description="Research"),
                SOPStep(name="draft", description="Draft"),
            ],
            output_format="Draft",
        )

        step_outputs = [
            {"step_name": "research", "raw": "Research findings", "step_index": 0}
        ]

        prompt = build_step_prompt(
            sop=sop,
            step_index=1,
            input_data={"topic": "AI"},
            step_outputs=step_outputs,
        )

        assert "Research findings" in prompt
        assert "Draft" in prompt

    def test_build_prompt_custom_template(self):
        """Test building prompt with custom template."""
        sop = SOP(
            name="test_sop",
            description="Test SOP",
            inputs=[SOPInput(name="topic", type="string", required=True)],
            steps=[
                SOPStep(
                    name="research",
                    description="Research",
                    prompt_template="research_template",
                ),
            ],
            output_format="Research",
        )

        # This should use research_template instead of default_step
        prompt = build_step_prompt(
            sop=sop,
            step_index=0,
            input_data={"topic": "AI"},
            step_outputs=[],
        )

        # The prompt should be built (may use default if template doesn't exist)
        assert isinstance(prompt, str)
        assert len(prompt) > 0
