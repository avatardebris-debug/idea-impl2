"""CLI entry point for PodcastSEO Metadata Optimizer."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

from podcastseo.transcript_parser import TranscriptParser
from podcastseo.keyword_extractor import KeywordExtractor
from podcastseo.show_notes_generator import ShowNotesGenerator

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


@app.command("notes")
def notes(
    input: str = typer.Argument(..., help="Path to the transcript file (SRT, VTT, TXT, or DOCX)."),
    format: str = typer.Option("markdown", "--format", "-f", help="Output format: markdown, html, or txt."),
    output: str = typer.Option(None, "--output", "-o", help="Path to write the output file. Defaults to stdout."),
    keywords: str = typer.Option(None, "--keywords", "-k", help="Path to a keywords JSON file from Phase 1. Auto-generated if omitted."),
    config: str = typer.Option(None, "--config", "-c", help="Path to config.yaml for template customization."),
    top: int = typer.Option(10, "--top", "-t", help="Number of top keywords to use. Overrides config if provided."),
) -> None:
    """Generate show notes from a transcript file.

    This command runs the full pipeline:
    1. Parse the transcript
    2. Extract keywords (if no --keywords file is provided)
    3. Generate show notes using templates
    4. Write output to file or stdout
    """
    input_path = Path(input)
    if not input_path.exists():
        typer.echo(f"Error: Input file '{input}' not found.", err=True)
        raise typer.Exit(1)

    # Step 1: Parse transcript
    parser = TranscriptParser()
    transcript_text = parser.parse(input_path)
    if not transcript_text or not transcript_text.strip():
        typer.echo("Warning: Transcript is empty. Generating show notes with no content.", err=True)

    # Step 2: Extract keywords if not provided
    if keywords:
        kw_path = Path(keywords)
        if not kw_path.exists():
            typer.echo(f"Error: Keywords file '{keywords}' not found.", err=True)
            raise typer.Exit(1)
        with open(kw_path, "r", encoding="utf-8") as f:
            keywords_data = json.load(f)
    else:
        # Auto-generate keywords
        extractor = KeywordExtractor(top_n=top)
        transcript_text_for_kw = parser.parse(input_path)
        keywords_data = extractor.extract(transcript_text_for_kw, top_n=top)
        typer.echo(f"Auto-generated {len(keywords_data)} keywords.", err=True)

    if not keywords_data:
        typer.echo("Warning: No keywords extracted. Show notes will be minimal.", err=True)

    # Step 3: Generate show notes
    generator = ShowNotesGenerator(config_path=config)
    show_notes = generator.generate(
        keywords=keywords_data,
        transcript_text=transcript_text,
        transcript_path=input,
        output_format=format,
    )

    # Step 4: Write output
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(show_notes)
        typer.echo(f"Show notes written to '{output}'.", err=True)
    else:
        typer.echo(show_notes)


if __name__ == "__main__":
    app()
