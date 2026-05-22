"""CLI entry point for YouTube Workflow Tool.

Provides click commands for metadata generation, optimization,
and analysis.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click

from .config import Config
from .metadata_generator import MetadataGenerator
from .optimizer import evaluate_metadata, keyword_density_report


# ── Helper: load config ───────────────────────────────────────────────

def _load_config(ctx: click.Context, config_path: Optional[str]) -> Config:
    """Load config from file or use defaults."""
    if config_path:
        p = Path(config_path)
        if p.exists():
            return Config.from_file(p)
    return Config()


# ── CLI group ───────────────────────────────────────────────

@click.group()
@click.option(
    "--config",
    "-c",
    default=None,
    help="Path to config YAML file.",
)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str]):
    """YouTube Workflow Tool — metadata generation, optimization, and analysis."""
    ctx.ensure_object(dict)
    ctx.obj["config"] = _load_config(ctx, config)


# ── generate command ───────────────────────────────────────────────

@cli.command()
@click.argument("topic")
@click.option(
    "--num-titles",
    "-n",
    default=10,
    type=int,
    help="Number of title variants to generate.",
)
@click.option(
    "--num-tags",
    default=15,
    type=int,
    help="Number of tags to generate.",
)
@click.option(
    "--num-hashtags",
    default=10,
    type=int,
    help="Number of hashtags to generate.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (JSON). Defaults to stdout.",
)
@click.option(
    "--format",
    "-f",
    default="json",
    type=click.Choice(["json", "yaml", "text"]),
    help="Output format.",
)
@click.option(
    "--style",
    "-s",
    default=None,
    multiple=True,
    help="Title styles to use (repeatable). Choices: educational, entertainment, news, listicle, howto, review, comparison, personal, controversial, curiosity.",
)
@click.pass_context
def generate(
    ctx: click.Context,
    topic: str,
    num_titles: int,
    num_tags: int,
    num_hashtags: int,
    output: Optional[str],
    format: str,
    style: tuple[str, ...],
):
    """Generate metadata for a YouTube video topic.

    Generates titles, description, tags, and hashtags for the given TOPIC.
    """
    config: Config = ctx.obj["config"]

    # Override styles if provided
    styles = list(style) if style else None

    generator = MetadataGenerator(config=config)
    metadata = generator.generate(
        topic=topic,
        num_titles=num_titles,
        num_tags=num_tags,
        num_hashtags=num_hashtags,
        styles=styles,
    )

    # Evaluate
    score = evaluate_metadata(metadata, config)

    # Build output
    result = {
        "metadata": metadata.to_dict(),
        "score": score.to_dict(),
    }

    # Format output
    if format == "json":
        output_text = json.dumps(result, indent=2)
    elif format == "yaml":
        try:
            import yaml
            output_text = yaml.dump(result, default_flow_style=False, sort_keys=False)
        except ImportError:
            click.echo("PyYAML not installed. Install with: pip install pyyaml", err=True)
            sys.exit(1)
    elif format == "text":
        lines = []
        lines.append(f"Topic: {topic}")
        lines.append(f"Overall Score: {score.overall_score}/100")
        lines.append("")
        lines.append("Titles:")
        for i, t in enumerate(metadata.titles[:5]):
            lines.append(f"  {i+1}. {t}")
        lines.append("")
        lines.append("Description:")
        lines.append(metadata.description[:200] + "...")
        lines.append("")
        lines.append("Tags:")
        lines.append(", ".join(metadata.tags[:10]))
        lines.append("")
        lines.append("Hashtags:")
        lines.append(" ".join(metadata.hashtags[:10]))
        lines.append("")
        lines.append("Recommendations:")
        for r in score.recommendations:
            lines.append(f"  • {r}")
        output_text = "\n".join(lines)
    else:
        output_text = json.dumps(result, indent=2)

    if output:
        Path(output).write_text(output_text)
        click.echo(f"Output written to {output}")
    else:
        click.echo(output_text)


# ── analyze command ───────────────────────────────────────────────

@cli.command()
@click.argument("topic")
@click.pass_context
def analyze(ctx: click.Context, topic: str):
    """Analyze keyword density for a topic."""
    report = keyword_density_report(topic)
    click.echo(json.dumps(report.to_dict(), indent=2))


# ── optimize command ───────────────────────────────────────────────

@cli.command()
@click.argument("topic")
@click.option(
    "--num-titles",
    "-n",
    default=10,
    type=int,
    help="Number of title variants to generate.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, writable=True),
    help="Output file path (JSON).",
)
@click.pass_context
def optimize(ctx: click.Context, topic: str, num_titles: int, output: Optional[str]):
    """Generate metadata and return the best-scoring variant."""
    config: Config = ctx.obj["config"]
    generator = MetadataGenerator(config=config)

    # Generate multiple variants
    best_score = -1
    best_metadata = None

    for _ in range(3):  # Generate 3 variants
        metadata = generator.generate(
            topic=topic,
            num_titles=num_titles,
            num_tags=config.min_tags,
            num_hashtags=config.min_hashtags,
        )
        score = evaluate_metadata(metadata, config)
        if score.overall_score > best_score:
            best_score = score.overall_score
            best_metadata = metadata
            best_score_result = score

    result = {
        "metadata": best_metadata.to_dict(),
        "score": best_score_result.to_dict(),
    }

    if output:
        Path(output).write_text(json.dumps(result, indent=2))
        click.echo(f"Best variant (score: {best_score:.1f}/100) written to {output}")
    else:
        click.echo(json.dumps(result, indent=2))


# ── Entry point ───────────────────────────────────────────────

if __name__ == "__main__":
    cli()
