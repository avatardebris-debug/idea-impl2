"""Orchestrator that ties template engine and content generator together."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from docsai.generators.base import BaseGenerator
from docsai.generators.readme_content import ReadmeContentGenerator
from docsai.generators.readme_templates import TemplateEngine


class ReadmeGenerator(BaseGenerator):
    """Generate a complete README.md using templates and LLM content."""

    def __init__(
        self,
        template_dir: Optional[str | Path] = None,
        template_file: str = "readme.md.j2",
        llm_provider: str = "openai",
        llm_model: Optional[str] = None,
        llm_temperature: float = 0.7,
    ):
        """Initialize the README generator.

        Args:
            template_dir: Directory containing Jinja2 templates.
            template_file: Template filename to use.
            llm_provider: LLM provider for content generation.
            llm_model: Optional LLM model override.
            llm_temperature: LLM sampling temperature.
        """
        self._template_engine = TemplateEngine(
            template_dir=template_dir,
            template_file=template_file,
        )
        self._content_generator = ReadmeContentGenerator(
            provider=llm_provider,
            model=llm_model,
            temperature=llm_temperature,
        )

    def generate(
        self,
        symbols: List[Dict[str, Any]],
        output_format: str = "markdown",
        project_name: str = "unknown",
        language: str = "unknown",
    ) -> str:
        """Generate a complete README.md document.

        Args:
            symbols: List of parsed symbol dicts.
            output_format: Must be 'markdown' (default).
            project_name: Name of the project.
            language: Primary language of the project.

        Returns:
            A string containing the rendered README.md content.
        """
        if output_format != "markdown":
            raise ValueError(f"ReadmeGenerator only supports 'markdown' format, got '{output_format}'")

        # Generate LLM-powered content sections
        project_description = self._content_generator.generate_project_description(
            symbols, project_name, language
        )
        usage_examples = self._content_generator.generate_usage_examples(
            symbols, language
        )
        architecture_notes = self._content_generator.generate_architecture_notes(
            symbols, language
        )

        # Build metadata
        metadata = {
            "file_count": len(set(s.get("file", "") for s in symbols)),
            "total_symbols": len(symbols),
        }

        # Render the template
        readme_content = self._template_engine.render(
            project_name=project_name,
            project_description=project_description,
            usage_examples=usage_examples,
            architecture_notes=architecture_notes,
            symbols=symbols,
            language=language,
            metadata=metadata,
        )

        return readme_content

    def generate_to_file(
        self,
        symbols: List[Dict[str, Any]],
        output_path: str | Path,
        project_name: str = "unknown",
        language: str = "unknown",
    ) -> Path:
        """Generate README.md and write it to a file.

        Args:
            symbols: List of parsed symbol dicts.
            output_path: Path to write the README.md file.
            project_name: Name of the project.
            language: Primary language of the project.

        Returns:
            The path to the written file.
        """
        content = self.generate(
            symbols=symbols,
            output_format="markdown",
            project_name=project_name,
            language=language,
        )
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        return output_path
