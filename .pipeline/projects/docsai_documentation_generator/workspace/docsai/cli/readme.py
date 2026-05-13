"""CLI subcommand: `docsai readme` — generate README.md for a project."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from docsai.parsers import get_parser
from docsai.generators.readme_generator import ReadmeGenerator

readme_app = typer.Typer(
    name="readme",
    help="Generate a complete README.md for a project",
)


@readme_app.command()
def generate(
    project_path: str = typer.Argument(
        ..., help="Path to the project directory to document"
    ),
    output: Optional[str] = typer.Option(
        None, "--output", "-o", help="Output file path (default: ./README.md)"
    ),
    template: Optional[str] = typer.Option(
        None, "--template", "-t", help="Path to a custom Jinja2 template directory"
    ),
    template_file: str = typer.Option(
        "readme.md.j2", "--template-file", help="Template filename to use"
    ),
    language: Optional[str] = typer.Option(
        None, "--language", "-l", help="Override detected language"
    ),
    llm_provider: str = typer.Option(
        "openai", "--provider", "-p", help="LLM provider (openai, claude, gemini, ollama, grok)"
    ),
    llm_model: Optional[str] = typer.Option(
        None, "--model", "-m", help="LLM model override"
    ),
    llm_temperature: float = typer.Option(
        0.7, "--temperature", help="LLM sampling temperature (0.0–1.0)"
    ),
    dry_run: bool = typer.Option(
        False, "--dry-run", help="Print generated README to stdout instead of writing"
    ),
):
    """Generate a complete README.md for the project at PROJECT_PATH.

    This command:
    1. Parses the project source files to extract public symbols.
    2. Uses an LLM to generate project description, usage examples, and architecture notes.
    3. Renders a Jinja2 template with all content to produce the final README.md.
    """
    project = Path(project_path)
    if not project.is_dir():
        typer.echo(f"Error: '{project_path}' is not a directory.", err=True)
        raise typer.Exit(1)

    # Detect language
    detected_language = language
    if not detected_language:
        # Auto-detect from file extensions
        py_files = list(project.rglob("*.py"))
        ts_files = list(project.rglob("*.ts"))
        if py_files:
            detected_language = "python"
        elif ts_files:
            detected_language = "typescript"
        else:
            detected_language = "unknown"

    # Parse source files
    typer.echo(f"Parsing project files in '{project_path}'...")
    parser = get_parser(detected_language)
    source_files = list(project.rglob("*"))
    source_files = [
        f for f in source_files
        if f.is_file() and f.suffix in parser.LANGUAGES
    ]
    if not source_files:
        typer.echo(f"Error: No supported source files found in '{project_path}'.", err=True)
        raise typer.Exit(1)

    all_symbols = []
    for sf in source_files:
        symbols = parser.parse(str(sf))
        for sym in symbols:
            sym["file"] = str(sf.relative_to(project))
        all_symbols.extend(symbols)

    typer.echo(f"Found {len(all_symbols)} public symbols across {len(source_files)} files.")

    # Determine project name from directory
    project_name = project.name

    # Generate README
    typer.echo("Generating README.md with LLM-powered content...")
    readme_gen = ReadmeGenerator(
        template_dir=template,
        template_file=template_file,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
    )

    readme_content = readme_gen.generate(
        symbols=all_symbols,
        output_format="markdown",
        project_name=project_name,
        language=detected_language,
    )

    if dry_run:
        typer.echo("\n" + "=" * 60)
        typer.echo("Generated README.md (dry run):")
        typer.echo("=" * 60)
        typer.echo(readme_content)
    else:
        out_path = Path(output) if output else project / "README.md"
        readme_gen.generate_to_file(
            symbols=all_symbols,
            output_path=out_path,
            project_name=project_name,
            language=detected_language,
        )
        typer.echo(f"README.md written to: {out_path}")


def register_readme_app(app: typer.Typer) -> None:
    """Register the readme subcommand with the main CLI app."""
    app.add_typer(readme_app, name="readme")


def readme(
    project_path: str,
    output: Optional[str] = None,
    template: Optional[str] = None,
    template_file: str = "readme.md.j2",
    language: Optional[str] = None,
    llm_provider: str = "openai",
    llm_model: Optional[str] = None,
    llm_temperature: float = 0.7,
) -> Path:
    """Generate a README.md for the project at PROJECT_PATH.

    This is the programmatic entry point used by tests and other callers.

    Args:
        project_path: Path to the project directory.
        output: Output file path. Defaults to ./README.md in the project dir.
        template: Optional custom Jinja2 template directory.
        template_file: Template filename.
        language: Override detected language.
        llm_provider: LLM provider name.
        llm_model: Optional model override.
        llm_temperature: LLM sampling temperature.

    Returns:
        Path to the generated README.md file.
    """
    project = Path(project_path)
    if not project.is_dir():
        raise ValueError(f"'{project_path}' is not a directory.")

    # Detect language
    detected_language = language
    if not detected_language:
        py_files = list(project.rglob("*.py"))
        ts_files = list(project.rglob("*.ts"))
        if py_files:
            detected_language = "python"
        elif ts_files:
            detected_language = "typescript"
        else:
            detected_language = "unknown"

    # Parse source files
    parser = get_parser(detected_language)
    
    # Map file extensions to supported languages for this parser
    _EXT_MAP = {
        "python": {".py"},
        "typescript": {".ts", ".tsx"},
        "tsx": {".tsx"},
    }
    supported_exts = _EXT_MAP.get(detected_language, set())
    
    source_files = [
        f for f in project.rglob("*")
        if f.is_file() and f.suffix in supported_exts
    ]
    if not source_files:
        raise ValueError(f"No supported source files found in '{project_path}'.")

    all_symbols = []
    for sf in source_files:
        symbols = parser.parse(str(sf))
        for sym in symbols:
            sym["file"] = str(sf.relative_to(project))
        all_symbols.extend(symbols)

    project_name = project.name

    # Generate README
    readme_gen = ReadmeGenerator(
        template_dir=template,
        template_file=template_file,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
    )

    out_path = Path(output) if output else project / "README.md"
    readme_gen.generate_to_file(
        symbols=all_symbols,
        output_path=out_path,
        project_name=project_name,
        language=detected_language,
    )
    return out_path
