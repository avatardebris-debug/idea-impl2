"""CLI entry point for sacbot."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from sacbot.generator import generate, GenerationResult
from sacbot.types import ContentType


@click.group()
def main():
    """sacbot — Generate content in Scott Adams' writing style."""
    pass


@main.command()
@click.option("--topic", required=True, help="Topic to write about.")
@click.option("--type", "content_type", default="blog", type=click.Choice(["blog", "tweet", "linkedin"]),
              help="Content type to generate.")
@click.option("--corpus", default=None, help="Path to corpus.jsonl for few-shot examples.")
@click.option("--n-few-shot", default=3, type=int, help="Number of few-shot examples.")
@click.option("--model", default="gpt-4o", help="OpenAI model to use.")
@click.option("--api-key", default=None, help="OpenAI API key (or set OPENAI_API_KEY env var).")
@click.option("--temperature", default=0.7, type=float, help="Sampling temperature.")
@click.option("--seed", default=None, type=int, help="Random seed for reproducibility.")
@click.option("--output", default=None, type=click.Path(), help="Output file path.")
@click.option("--format", "output_format", default="text", type=click.Choice(["text", "json"]),
              help="Output format.")
def generate_content(topic: str, content_type: ContentType, corpus: str | None,
                     n_few_shot: int, model: str, api_key: str | None,
                     temperature: float, seed: int | None, output: str | None,
                     output_format: str) -> None:
    """Generate content in Scott Adams' style."""
    try:
        result = generate(
            topic=topic,
            content_type=content_type,
            corpus_path=corpus,
            n_few_shot=n_few_shot,
            model=model,
            api_key=api_key,
            temperature=temperature,
            seed=seed,
            output_format=output_format,
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    # Format output
    if output_format == "json":
        output_data = {
            "content": result.content,
            "model": result.model,
            "tokens_used": result.tokens_used,
            "latency_seconds": round(result.latency_seconds, 2),
            "prompt_tokens": result.prompt_tokens,
            "few_shot_count": result.few_shot_count,
            "content_type": result.content_type,
            "topic": result.topic,
        }
        output_str = json.dumps(output_data, indent=2)
    else:
        output_str = result.content

    # Write output
    if output:
        Path(output).write_text(output_str, encoding="utf-8")
        click.echo(f"Content written to {output}")
    else:
        click.echo(output_str)


@main.command()
def version():
    """Print version information."""
    try:
        from sacbot import __version__
        click.echo(f"sacbot {__version__}")
    except ImportError:
        click.echo("sacbot (version unknown)")


if __name__ == "__main__":
    main()
