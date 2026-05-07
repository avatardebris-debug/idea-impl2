"""CLI entry point for PodcastSEO Metadata Optimizer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from podcastseo.transcript_parser import TranscriptParser
from podcastseo.keyword_extractor import KeywordExtractor

app = typer.Typer(
    name="podcastseo",
    help="PodcastSEO Metadata Optimizer — extract keywords from podcast transcripts.",
    add_completion=False,
)


def _validate_input_file(input_path: str) -> Path:
    """Validate that the input file exists and has a supported extension."""
    p = Path(input_path)
    if not p.exists():
        typer.echo(f"Error: File not found: {input_path}", err=True)
        raise typer.Exit(code=1)
    if not p.is_file():
        typer.echo(f"Error: Not a file: {input_path}", err=True)
        raise typer.Exit(code=1)
    supported = {".srt", ".vtt", ".txt", ".docx"}
    ext = p.suffix.lower()
    if ext not in supported:
        typer.echo(
            f"Error: Unsupported format '{ext}'. Supported formats: {', '.join(sorted(supported))}",
            err=True,
        )
        raise typer.Exit(code=1)
    return p


@app.command()
def keywords(
    input: str = typer.Argument(..., help="Path to the transcript file (SRT, VTT, TXT, or DOCX)"),
    top: int = typer.Option(20, "--top", "-t", help="Number of top keywords to extract"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path for JSON results"),
):
    """Extract keywords from a podcast transcript."""
    # Validate input
    input_path = _validate_input_file(input)

    # Parse transcript
    try:
        parser = TranscriptParser()
        raw = parser.parse_raw(input)
    except FileNotFoundError:
        typer.echo(f"Error: File not found: {input}", err=True)
        raise typer.Exit(code=1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)
    except RuntimeError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"Detected format: {raw['format']}", err=True)
    typer.echo(f"Word count: {raw['word_count']}", err=True)

    # Extract keywords
    try:
        extractor = KeywordExtractor(top_n=top)
        keywords = extractor.extract(raw["text"], top_n=top)
    except Exception as e:
        typer.echo(f"Error extracting keywords: {e}", err=True)
        raise typer.Exit(code=1)

    if not keywords:
        typer.echo("No keywords extracted.", err=True)
        typer.echo("[]")
        raise typer.Exit(code=0)

    # Output results
    json_output = json.dumps(keywords, indent=2)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_output, encoding="utf-8")
        typer.echo(f"Keywords written to: {out_path}", err=True)
    else:
        typer.echo(json_output)

    typer.echo(f"Extracted {len(keywords)} keywords.", err=True)


@app.callback()
def version() -> None:
    """Show version information."""
    pass


if __name__ == "__main__":
    app()
