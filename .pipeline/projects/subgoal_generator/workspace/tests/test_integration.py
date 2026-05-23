"""Integration tests for the subgoal generator pipeline with mocked LLM."""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure workspace is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from subgoal_generator.models import Subgoal
from subgoal_generator.generator import SubgoalGenerator
from subgoal_generator.parser import parse_response
from subgoal_generator.prompt_builder import build_prompt


class TestSubgoalGeneratorIntegration(unittest.TestCase):
    """Integration tests for SubgoalGenerator with mocked LLM."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_llm_response = """title: Design the system
description: Create architecture diagrams
dependencies: []
priority: 3

title: Build the core
description: Implement core functionality
dependencies: [Design the system]
priority: 5

title: Test the app
description: Write unit tests
dependencies: [Build the core]
priority: 4"""

    @patch("subgoal_generator.generator.LLMClient")
    def test_full_pipeline(self, mock_llm_client_class):
        """Test the full pipeline: prompt -> LLM -> parse -> output."""
        # Mock the LLM client
        mock_client_instance = MagicMock()
        mock_client_instance.complete.return_value = self.mock_llm_response
        mock_llm_client_class.return_value = mock_client_instance

        # Create generator with mocked client
        generator = SubgoalGenerator(llm_client=mock_client_instance)

        # Run the pipeline
        subgoals = generator.generate("Build a web app")

        # Verify LLM was called with correct prompt
        mock_client_instance.complete.assert_called_once()
        call_args = mock_client_instance.complete.call_args
        prompt_arg = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        self.assertIn("Build a web app", prompt_arg)

        # Verify parsed subgoals
        self.assertEqual(len(subgoals), 3)
        self.assertEqual(subgoals[0].title, "Design the system")
        self.assertEqual(subgoals[1].title, "Build the core")
        self.assertEqual(subgoals[2].title, "Test the app")

        # Verify dependencies
        self.assertEqual(subgoals[1].dependencies, ["Design the system"])
        self.assertEqual(subgoals[2].dependencies, ["Build the core"])

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_with_output(self, mock_llm_client_class):
        """Test generate with output file writing."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = self.mock_llm_response
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(llm_client=mock_client_instance)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            output_path = f.name
        os.remove(output_path)

        try:
            subgoals = generator.generate(
                "Build a web app",
                output_path=output_path,
            )

            # Verify file was created
            self.assertTrue(os.path.exists(output_path))
            with open(output_path) as f:
                content = f.read()
            self.assertIn("title: Design the system", content)
            self.assertIn("title: Build the core", content)
            self.assertIn("title: Test the app", content)
        finally:
            os.remove(output_path)

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_empty_response(self, mock_llm_client_class):
        """Test generate handles empty LLM response."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = ""
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(llm_client=mock_client_instance)
        subgoals = generator.generate("Test goal")
        self.assertEqual(subgoals, [])

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_single_subgoal(self, mock_llm_client_class):
        """Test generate with single subgoal response."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = """title: Single task
description: Do one thing
priority: 1"""
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(llm_client=mock_client_instance)
        subgoals = generator.generate("Do one thing")
        self.assertEqual(len(subgoals), 1)
        self.assertEqual(subgoals[0].title, "Single task")

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_with_custom_model(self, mock_llm_client_class):
        """Test generate with custom model parameter."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = "title: A\ndescription: B\npriority: 1"
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(
            llm_client=mock_client_instance,
            model="custom-model",
        )
        generator.generate("Test")

        # Verify the client was initialized with the custom model
        mock_llm_client_class.assert_called_once()
        init_kwargs = mock_llm_client_class.call_args[1]
        self.assertEqual(init_kwargs.get("model"), "custom-model")

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_preserves_priority(self, mock_llm_client_class):
        """Test that priority values are preserved through the pipeline."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = """title: High priority
description: Important task
priority: 10"""
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(llm_client=mock_client_instance)
        subgoals = generator.generate("Test")
        self.assertEqual(subgoals[0].priority, 10)

    @patch("subgoal_generator.generator.LLMClient")
    def test_generate_preserves_dependencies(self, mock_llm_client_class):
        """Test that dependencies are preserved through the pipeline."""
        mock_client_instance = MagicMock()
        mock_client_instance.chat_completion.return_value = """title: Dependent task
description: Depends on others
dependencies: [Task A, Task B]
priority: 1"""
        mock_llm_client_class.return_value = mock_client_instance

        generator = SubgoalGenerator(llm_client=mock_client_instance)
        subgoals = generator.generate("Test")
        self.assertEqual(subgoals[0].dependencies, ["Task A", "Task B"])


class TestParseResponseIntegration(unittest.TestCase):
    """Integration tests for parse_response with realistic LLM outputs."""

    def test_parse_realistic_llm_output(self):
        """Parse a realistic LLM response with markdown formatting."""
        text = """Here are the subgoals:

title: Research competitors
description: Analyze top 5 competitors
dependencies: []
priority: 2

title: Define requirements
description: Write PRD document
dependencies: [Research competitors]
priority: 4

title: Design UI
description: Create wireframes and mockups
dependencies: [Define requirements]
priority: 3"""
        result = parse_response(text)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0].title, "Research competitors")
        self.assertEqual(result[1].title, "Define requirements")
        self.assertEqual(result[2].title, "Design UI")

    def test_parse_with_code_block(self):
        """Parse response that includes markdown code blocks."""
        text = """```
title: Write code
description: Implement features
priority: 5
```"""
        result = parse_response(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].title, "Write code")


if __name__ == "__main__":
    unittest.main()
