"""CLI changelog subcommand for DocsAI."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

app = typer.Typer(help="Generate changelog from git history")


@app.command()
def changelog(
    input_dir: str = typer.Option(
        ".",
        "--input-dir",
        "-i",
        help="Path to the git repository to analyze.",
    ),
    output: str = typer.Option(
        "CHANGELOG.md",
        "--output",
        "-o",
        help="Output file path for the changelog.",
    ),
    version: Optional[str] = typer.Option(
        None,
        "--version",
        "-v",
        help="Version string for the changelog entry (e.g., '1.0.0').",
    ),
    template: Optional[str] = typer.Option(
        None,
        "--template",
        "-t",
        help="Custom changelog template filename.",
    ),
    template_dir: Optional[str] = typer.Option(
        None,
        "--template-dir",
        "-d",
        help="Directory containing the changelog template.",
    ),
    llm_provider: str = typer.Option(
        "openai",
        "--llm-provider",
        help="LLM provider to use for generating summaries (e.g., 'openai', 'anthropic').",
    ),
    llm_model: str = typer.Option(
        "gpt-4o-mini",
        "--llm-model",
        help="LLM model to use for generating summaries.",
    ),
    llm_temperature: float = typer.Option(
        0.3,
        "--llm-temperature",
        help="LLM temperature for generation (0.0 to 1.0).",
    ),
    commit_count: int = typer.Option(
        10,
        "--commit-count",
        "-c",
        help="Number of recent commits to analyze.",
    ),
) -> None:
    """Generate a changelog from git history.

    Analyzes the last N commits in the specified repository and generates
    a versioned changelog with categorized entries (Added, Changed, Fixed,
    Removed, Deprecated). Uses the LLM to produce human-readable summaries
    of each commit's changes.
    """
    from docsai.generators.changelog import ChangelogGenerator

    generator = ChangelogGenerator(
        repo_path=input_dir,
        llm_provider=llm_provider,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        commit_count=commit_count,
    )

    rendered = generator.generate(
        version=version,
        output_path=output,
        template_dir=template_dir,
        template_file=template or "changelog_default.md",
    )

    typer.echo(f"Changelog generated successfully: {output}")
    typer.echo(f"Version: {version or 'auto-detected'}")
    typer.echo(f"Commits analyzed: {commit_count}")
