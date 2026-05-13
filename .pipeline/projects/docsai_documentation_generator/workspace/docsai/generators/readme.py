"""README generator module — provides load_template, render_readme, and READMEGenerator."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from docsai.generators.base import BaseGenerator
from docsai.generators.readme_templates import TemplateEngine

# Default template directory (relative to this file)
_DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "readme_templates" / "default"


def load_template() -> str:
    """Load the default README.md.j2 template as a string.

    Returns:
        The raw Jinja2 template source.
    """
    template_path = _DEFAULT_TEMPLATE_DIR / "readme.md.j2"
    return template_path.read_text(encoding="utf-8")


def render_readme(
    symbols: List[Dict[str, Any]],
    language: str,
    project_name: str,
) -> str:
    """Render a README.md from parsed symbols using the default template.

    Args:
        symbols: List of parsed symbol dicts.
        language: Primary programming language.
        project_name: Name of the project.

    Returns:
        A rendered README.md string.
    """
    engine = TemplateEngine(template_dir=_DEFAULT_TEMPLATE_DIR)

    # Build a simple project description from symbols
    project_description = (
        f"{project_name} is a {language} project."
    )
    usage_examples = "No usage examples available."
    architecture_notes = "No architecture notes available."

    metadata = {
        "file_count": len(set(s.get("file", "") for s in symbols)),
        "total_symbols": len(symbols),
    }

    return engine.render(
        project_name=project_name,
        project_description=project_description,
        usage_examples=usage_examples,
        architecture_notes=architecture_notes,
        symbols=symbols,
        language=language.capitalize(),
        metadata=metadata,
    )


class READMEGenerator(BaseGenerator):
    """Generate a README.md document from parsed symbols.

    This class implements the BaseGenerator interface and produces
    markdown-formatted README output.
    """

    def generate(
        self,
        symbols: List[Dict[str, Any]],
        output_format: str = "markdown",
        project_name: str = "unknown",
        language: str = "unknown",
    ) -> str:
        """Generate a README.md document.

        Args:
            symbols: List of parsed symbol dicts.
            output_format: Must be 'markdown'.
            project_name: Name of the project.
            language: Primary programming language.

        Returns:
            A rendered README.md string.
        """
        if output_format != "markdown":
            raise ValueError(
                f"READMEGenerator only supports 'markdown' format, got '{output_format}'"
            )

        return render_readme(symbols, language, project_name)
