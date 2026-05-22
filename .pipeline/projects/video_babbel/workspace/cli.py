"""CLI entry point for VideoBabbel — a Click-based command-line interface.

This module exposes the full VideoBabbel pipeline via the ``video-babbel``
console script and the ``python -m video_babbel`` invocation.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from video_babbel.core import (
    IngestionError,
    QAError,
    SummarizationError,
    TranslationError,
    TranscriptionError,
    VideoBabbelError,
    get_logger,
)
from video_babbel.pipeline import VideoBabbel

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.group(context_settings=CONTEXT_SETTINGS)
@click.version_option(version="0.1.0", prog_name="VideoBabbel")
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    help="Enable verbose (DEBUG) logging.",
)
def cli(verbose: bool) -> None:
    """VideoBabbel — translate, transcribe, summarize, and answer questions on video content.

    VideoBabbel is a modular pipeline that extracts audio from video files,
    transcribes the audio to text, translates the text to a target language,
    generates a summary, and answers questions about the content.

    Examples
    --------
    Process a video and translate to Spanish::

        video-babbel process --video /path/to/video.mp4 --lang es

    Process a video and output JSON::

        video-babbel process --video /path/to/video.mp4 --lang fr --output result.json

    List available languages::

        video-babbel languages
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        for handler in logging.getLogger().handlers:
            handler.setLevel(logging.DEBUG)
    logger.debug("VideoBabbel CLI started (verbose=%s)", verbose)


# ---------------------------------------------------------------------------
# Supported languages
# ---------------------------------------------------------------------------

SUPPORTED_LANGUAGES: Dict[str, str] = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese",
    "ru": "Russian",
}


# ---------------------------------------------------------------------------
# process sub-command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("video_path", required=False, type=click.Path(dir_okay=False))
@click.option(
    "--target-lang",
    "-l",
    "target_lang",
    default="es",
    type=click.Choice(list(SUPPORTED_LANGUAGES.keys())),
    help="Target language ISO 639-1 code (default: es).",
)
@click.option(
    "--whisper-model",
    "-m",
    "whisper_model",
    default="base",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    help="Whisper model size (default: base).",
)
@click.option(
    "--max-sentences",
    "-s",
    "max_sentences",
    default=5,
    type=int,
    help="Maximum number of sentences in the summary (default: 5).",
)
@click.option(
    "--backend",
    "-b",
    "backend",
    default="google",
    type=click.Choice(["google", "deepL"]),
    help="Translation backend (default: google).",
)
@click.option(
    "--output-json",
    "output_json",
    is_flag=True,
    default=False,
    help="Print results as JSON to stdout.",
)
@click.option(
    "--output-file",
    "-o",
    "output_file",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Path to write JSON output file.",
)
@click.option(
    "--question",
    "-q",
    "question",
    default=None,
    type=str,
    help="Optional question to answer from the transcript.",
)
@click.pass_context
def process(
    ctx: click.Context,
    video_path: Optional[str],
    target_lang: str,
    whisper_model: str,
    max_sentences: int,
    backend: str,
    output_json: bool,
    output_file: Optional[str],
    question: Optional[str],
) -> None:
    """Process a video file through the full pipeline.

    This command runs the complete VideoBabbel pipeline:
    ingestion → transcription → translation → summarization → Q&A.
    """
    # Require video_path as a positional argument
    if video_path is None:
        click.echo("Error: Missing argument 'VIDEO_PATH'.", err=True)
        ctx.fail("Missing argument")

    if not output_json:
        click.echo(f"Processing video: {video_path}")
        click.echo(f"Target language: {target_lang} ({SUPPORTED_LANGUAGES[target_lang]})")
        click.echo(f"Whisper model: {whisper_model}")
        click.echo(f"Backend: {backend}")
        click.echo("-" * 60)

    pipeline = VideoBabbel(
        target_lang=target_lang,
        whisper_model=whisper_model,
        max_sentences=max_sentences,
        backend=backend,
    )

    try:
        result: Dict[str, Any] = pipeline.process(video_path)
    except VideoBabbelError as exc:
        click.echo(f"Error: {exc}", err=True)
        click.echo(str(exc), err=True)
        ctx.fail(str(exc))

    # Build output dict
    output: Dict[str, Any] = {
        "video_path": video_path,
        "target_lang": target_lang,
        "transcript": result.get("transcript", []),
        "translation": result.get("translation", ""),
        "summary": result.get("summary", ""),
    }

    if question:
        output["question"] = question
        output["answer"] = result.get("qa", "")

    # Write output
    json_output = json.dumps(output, indent=2, ensure_ascii=False)

    if output_file:
        Path(output_file).write_text(json_output, encoding="utf-8")
        click.echo(f"Results written to: {output_file}")
    elif output_json:
        click.echo(json_output)
    else:
        click.echo(json_output)


# ---------------------------------------------------------------------------
# list-languages sub-command
# ---------------------------------------------------------------------------

@cli.command(name="list-languages")
@click.option(
    "--json",
    "as_json",
    is_flag=True,
    default=False,
    help="Output as JSON.",
)
def list_languages(as_json: bool) -> None:
    """List all supported target languages."""
    if as_json:
        click.echo(json.dumps(list(SUPPORTED_LANGUAGES.keys())))
    else:
        click.echo("Supported languages:")
        for code, name in sorted(SUPPORTED_LANGUAGES.items()):
            click.echo(f"  {code:4s} — {name}")


# ---------------------------------------------------------------------------
# validate sub-command
# ---------------------------------------------------------------------------

@cli.command()
@click.argument("video_path", required=False, type=click.Path(dir_okay=False))
@click.option(
    "--target-lang",
    "-l",
    "target_lang",
    default="es",
    type=click.Choice(list(SUPPORTED_LANGUAGES.keys())),
    help="Target language ISO 639-1 code (default: es).",
)
@click.option(
    "--whisper-model",
    "-m",
    "whisper_model",
    default="base",
    type=click.Choice(["tiny", "base", "small", "medium", "large"]),
    help="Whisper model size (default: base).",
)
@click.option(
    "--max-sentences",
    "-s",
    "max_sentences",
    default=5,
    type=int,
    help="Maximum number of sentences in the summary (default: 5).",
)
@click.option(
    "--backend",
    "-b",
    "backend",
    default="google",
    type=click.Choice(["google", "deepL"]),
    help="Translation backend (default: google).",
)
@click.pass_context
def validate(
    ctx: click.Context,
    video_path: Optional[str],
    target_lang: str,
    whisper_model: str,
    max_sentences: int,
    backend: str,
) -> None:
    """Validate the pipeline by processing a video and checking all steps."""
    if video_path is None:
        click.echo("Error: Missing argument 'VIDEO_PATH'.", err=True)
        ctx.fail("Missing argument")

    click.echo(f"Validating video: {video_path}")

    pipeline = VideoBabbel(
        target_lang=target_lang,
        whisper_model=whisper_model,
        max_sentences=max_sentences,
        backend=backend,
    )

    try:
        result: Dict[str, Any] = pipeline.process(video_path)
        click.echo("All checks passed")
        click.echo(f"  Transcript: {len(result.get('transcript', []))} segments")
        click.echo(f"  Translation: {result.get('translation', '')[:50]}")
        click.echo(f"  Summary: {result.get('summary', '')[:50]}")
    except VideoBabbelError as exc:
        click.echo(f"Validation failed: {exc}", err=True)
        ctx.fail(str(exc))


# ---------------------------------------------------------------------------
# info sub-command
# ---------------------------------------------------------------------------

@cli.command(context_settings=CONTEXT_SETTINGS)
def info() -> None:
    """Display VideoBabbel version and configuration info."""
    click.echo("VideoBabbel CLI")
    click.echo(f"  Version: 0.1.0")
    click.echo(f"  Python:  {sys.version.split()[0]}")
    click.echo(f"  Platform: {sys.platform}")
    click.echo(f"  Executable: {sys.executable}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
