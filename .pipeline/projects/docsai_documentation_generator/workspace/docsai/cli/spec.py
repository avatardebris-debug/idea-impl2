"""The `docsai spec` subcommand — ties config, discovery, parsing, and generation together."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import typer

from docsai.core.config import load_config
from docsai.parsers.python_parser import PythonParser
from docsai.parsers.typescript_parser import TypeScriptParser
from docsai.generators.api_spec import ApiSpecGenerator

spec_app = typer.Typer()


def _resolve_option(value, default):
    """Resolve a typer.Option value — handles both CLI (OptionInfo) and direct call (None) cases."""
    if value is None or (hasattr(value, '__class__') and value.__class__.__name__ == 'OptionInfo'):
        return default
    return value


@spec_app.command()
def spec(
    source_dir: str = typer.Argument(..., help="Directory containing source files to document."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path for the API spec."),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="Output format: yaml or json."),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to docsai.yaml config file."),
):
    """Generate an API specification from source code files."""
    # Resolve typer.Option defaults (which are OptionInfo objects when called directly)
    output_path = _resolve_option(output, None)
    output_format = _resolve_option(format, None)
    config_path = _resolve_option(config, None)

    # Load config
    cfg = load_config(config_path)

    # Override config with CLI flags if provided
    output_path = output_path or cfg.get("output_path", "./docsai_output/api_spec.yaml")
    output_format = output_format or cfg.get("output_format", "yaml")
    languages = cfg.get("languages", ["python", "typescript"])

    # Discover source files
    src = Path(source_dir)
    if not src.is_dir():
        typer.echo(f"Error: '{source_dir}' is not a directory.", err=True)
        raise typer.Exit(1)

    extensions_map = {
        "python": [".py"],
        "typescript": [".ts", ".tsx"],
    }

    extensions: List[str] = []
    for lang in languages:
        extensions.extend(extensions_map.get(lang, []))

    source_files: List[Path] = []
    for ext in extensions:
        source_files.extend(src.rglob(f"*{ext}"))

    if not source_files:
        typer.echo(f"No source files found with extensions {extensions} in '{source_dir}'.", err=True)
        raise typer.Exit(1)

    # Parse files
    parser_map = {
        ".py": PythonParser(),
        ".ts": TypeScriptParser(),
        ".tsx": TypeScriptParser(),
    }

    all_symbols: List[Dict[str, Any]] = []
    for file_path in source_files:
        ext = file_path.suffix
        parser = parser_map.get(ext)
        if parser is None:
            continue
        symbols = parser.parse(str(file_path))
        # Tag each symbol with its source file
        for sym in symbols:
            sym["file"] = str(file_path)
        all_symbols.extend(symbols)

    if not all_symbols:
        typer.echo("No public symbols found in the source files.", err=True)
        raise typer.Exit(1)

    # Determine project name and language
    project_name = src.name
    primary_language = languages[0] if languages else "unknown"

    # Generate spec
    generator = ApiSpecGenerator()
    spec_content = generator.generate(
        symbols=all_symbols,
        output_format=output_format,
        project_name=project_name,
        language=primary_language,
    )

    # Write output
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(spec_content)

    typer.echo(f"API spec written to {output_path} ({len(all_symbols)} symbols, format={output_format})")
