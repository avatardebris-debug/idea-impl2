"""
Transcript Extractor CLI.

Command-line interface for the transcript extractor tool.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

import click

from transcript_extractor import (
    TranscriptionPipeline,
    Config,
    TranscriptionOutput,
    SUPPORTED_FORMATS,
    MODEL_SIZES,
    OUTPUT_FORMATS,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="transcript-extractor")
def cli():
    """Transcript Extractor - Extract transcripts from video/audio files using Whisper."""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option(
    '--model', '-m',
    default='small',
    type=click.Choice(MODEL_SIZES),
    help='Whisper model size to use'
)
@click.option(
    '--language', '-l',
    default='en',
    help='Language code for transcription (e.g., en, es, fr)'
)
@click.option(
    '--output-format', '-o',
    default='txt',
    type=click.Choice(OUTPUT_FORMATS),
    help='Output format for transcript'
)
@click.option(
    '--summary-length', '-s',
    default='medium',
    type=click.Choice(['short', 'medium', 'long']),
    help='Length of generated summary'
)
@click.option(
    '--summary-strategy',
    default='extractive',
    type=click.Choice(['extractive', 'abstractive', 'simple']),
    help='Summarization strategy'
)
@click.option(
    '--output-dir', '-d',
    default=None,
    type=click.Path(),
    help='Output directory for files'
)
@click.option(
    '--no-timestamps',
    is_flag=True,
    help='Exclude timestamps from transcript'
)
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
def transcribe(
    input_file: str,
    model: str,
    language: str,
    output_format: str,
    summary_length: str,
    summary_strategy: str,
    output_dir: Optional[str],
    no_timestamps: bool,
    verbose: bool,
):
    """
    Extract transcript from a video/audio file.
    
    Example:
        transcript-extractor transcribe video.mp4 --model small --language en
    
    Supported formats: mp4, avi, mov, mkv
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create pipeline
    pipeline = TranscriptionPipeline(
        model_size=model,
        language=language,
        output_format=output_format,
        summary_length=summary_length,
        summary_strategy=summary_strategy,
    )
    
    logger.info(f"Processing: {input_file}")
    logger.info(f"Model: {model}, Language: {language}, Format: {output_format}")
    
    # Process
    try:
        output = pipeline.process(
            input_file,
            output_dir=output_dir,
            include_timestamps=not no_timestamps,
        )
        
        # Display results
        if output.success:
            click.echo("\n" + "="*60)
            click.echo(f"TRANSCRIPT: {output.input_file}")
            click.echo("="*60)
            click.echo(f"Language: {output.language}")
            click.echo(f"Duration: {output.duration:.2f} seconds")
            click.echo(f"Word count: {output.word_count}")
            click.echo(f"Segments: {output.segments_count}")
            click.echo("\n" + "-"*60)
            click.echo("TRANSCRIPT TEXT:")
            click.echo("-"*60)
            click.echo(output.transcript)
            click.echo("\n" + "-"*60)
            click.echo("SUMMARY:")
            click.echo("-"*60)
            click.echo(output.summary)
            click.echo("\n" + "="*60)
            
            if output_dir:
                click.echo(f"\n✓ Output saved to: {output.input_file}")
            
            click.echo(f"\n✓ Transcription completed successfully!")
        else:
            click.echo(f"\n✗ Transcription failed: {output.error_message}", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"\n✗ Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    '--model', '-m',
    default='small',
    type=click.Choice(MODEL_SIZES),
    help='Whisper model size to use'
)
@click.option(
    '--language', '-l',
    default='en',
    help='Language code for transcription'
)
@click.option(
    '--output-format', '-o',
    default='txt',
    type=click.Choice(OUTPUT_FORMATS),
    help='Output format for transcript'
)
@click.option(
    '--summary-length', '-s',
    default='medium',
    type=click.Choice(['short', 'medium', 'long']),
    help='Length of generated summary'
)
@click.option(
    '--summary-strategy',
    default='extractive',
    type=click.Choice(['extractive', 'abstractive', 'simple']),
    help='Summarization strategy'
)
@click.option(
    '--output-dir', '-d',
    default=None,
    type=click.Path(),
    help='Output directory for files'
)
@click.argument('input_files', nargs=-1, required=True, type=click.Path(exists=True))
def batch(
    input_files: tuple,
    model: str,
    language: str,
    output_format: str,
    summary_length: str,
    summary_strategy: str,
    output_dir: Optional[str],
):
    """
    Process multiple files in batch mode.
    
    Example:
        transcript-extractor batch video1.mp4 video2.mp4 video3.mp4
    
    Supported formats: mp4, avi, mov, mkv
    """
    # Create pipeline
    pipeline = TranscriptionPipeline(
        model_size=model,
        language=language,
        output_format=output_format,
        summary_length=summary_length,
        summary_strategy=summary_strategy,
    )
    
    logger.info(f"Processing {len(input_files)} files")
    
    # Process all files
    results = pipeline.process_batch(
        list(input_files),
        output_dir=output_dir,
    )
    
    # Display results
    success_count = 0
    fail_count = 0
    
    for output in results:
        if output.success:
            success_count += 1
            click.echo(f"\n✓ {Path(output.input_file).name}: {output.word_count} words")
        else:
            fail_count += 1
            click.echo(f"\n✗ {Path(output.input_file).name}: {output.error_message}", err=True)
    
    # Summary
    click.echo("\n" + "="*60)
    click.echo("BATCH PROCESSING SUMMARY")
    click.echo("="*60)
    click.echo(f"Total files: {len(input_files)}")
    click.echo(f"Successful: {success_count}")
    click.echo(f"Failed: {fail_count}")
    
    if fail_count > 0:
        sys.exit(1)


@cli.command()
def info():
    """Display system information and supported formats."""
    click.echo("\n" + "="*60)
    click.echo("TRANSCRIPT EXTRACTOR - SYSTEM INFORMATION")
    click.echo("="*60)
    
    click.echo("\nSupported input formats:")
    for fmt in SUPPORTED_FORMATS:
        click.echo(f"  - {fmt}")
    
    click.echo("\nSupported output formats:")
    for fmt in OUTPUT_FORMATS:
        click.echo(f"  - {fmt}")
    
    click.echo("\nAvailable Whisper models:")
    for model in MODEL_SIZES:
        click.echo(f"  - {model}")
    
    click.echo("\nSummary lengths:")
    click.echo("  - short")
    click.echo("  - medium")
    click.echo("  - long")
    
    click.echo("\nSummarization strategies:")
    click.echo("  - extractive (default)")
    click.echo("  - abstractive")
    click.echo("  - simple")
    
    click.echo("\n" + "="*60)


@cli.command()
def version():
    """Display version information."""
    click.echo("transcript-extractor version 1.0.0")


def main():
    """Entry point for CLI."""
    cli()


if __name__ == '__main__':
    main()
