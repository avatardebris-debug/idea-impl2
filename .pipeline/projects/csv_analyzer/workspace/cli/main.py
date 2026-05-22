"""CLI module for csv_analyzer — command-line interface."""

from __future__ import annotations

import click
from pathlib import Path
from typing import Any

from csv_analyzer.core.analyzer import AnalysisEngine
from csv_analyzer.io.csv_reader import CsvReader


@click.group(invoke_without_command=True)
@click.version_option(version="0.1.0", prog_name="csv-analyzer")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """csv-analyzer — A CSV analysis tool.

    This tool provides commands for analyzing CSV files, including:
    - info: Display basic information about a CSV file
    - stats: Show summary statistics for numeric columns
    - head: Display the first few rows of a CSV file
    """
    # If no subcommand was provided, show help
    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))


@cli.command()
@click.argument("filepath", type=click.Path())
@click.option("--n", default=5, help="Number of rows to display (default: 5)")
def head(filepath: str, n: int) -> None:
    """Display the first n rows of a CSV file.

    FILEPATH is the path to the CSV file to display.
    """
    try:
        reader = CsvReader()
        df = reader.read(filepath)

        if len(df) == 0:
            click.echo("Empty CSV file")
            return

        head_df = df.head(n)
        click.echo(head_df.to_string())

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def info(filepath: str) -> None:
    """Display basic information about a CSV file.

    FILEPATH is the path to the CSV file to analyze.
    """
    try:
        reader = CsvReader()
        df = reader.read(filepath)
        engine = AnalysisEngine(df)
        profile = engine.profile()

        click.echo(f"File: {filepath}")
        click.echo(f"Rows: {profile['row_count']}")
        click.echo(f"Columns: {profile['column_count']}")
        click.echo("")

        # Column types
        click.echo("Column Types:")
        for col, col_type in profile["column_types"].items():
            click.echo(f"  {col}: {col_type}")
        click.echo("")

        # Numeric statistics
        if profile["numeric_stats"]:
            click.echo("Numeric Statistics:")
            for col, stats in profile["numeric_stats"].items():
                click.echo(f"  {col}:")
                click.echo(f"    Count: {stats['count']}")
                if stats['mean'] is not None:
                    click.echo(f"    Mean: {stats['mean']:.2f}")
                if stats['std'] is not None:
                    click.echo(f"    Std: {stats['std']:.2f}")
                if stats['min'] is not None:
                    click.echo(f"    Min: {stats['min']}")
                if stats['max'] is not None:
                    click.echo(f"    Max: {stats['max']}")
                if stats['median'] is not None:
                    click.echo(f"    Median: {stats['median']}")
            click.echo("")

        # Categorical statistics
        if profile["categorical_stats"]:
            click.echo("Categorical Statistics:")
            for col, stats in profile["categorical_stats"].items():
                click.echo(f"  {col}:")
                click.echo(f"    Unique values: {stats['unique_count']}")
                click.echo(f"    Value counts: {stats['value_counts']}")
            click.echo("")

        # Missing values
        if any(mv["count"] > 0 for mv in profile["missing_values"].values()):
            click.echo("Missing Values:")
            for col, mv in profile["missing_values"].items():
                if mv["count"] > 0:
                    click.echo(f"  {col}: {mv['count']} ({mv['percentage']}%)")
            click.echo("")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
def stats(filepath: str) -> None:
    """Display summary statistics for numeric columns.

    FILEPATH is the path to the CSV file to analyze.
    """
    try:
        reader = CsvReader()
        df = reader.read(filepath)
        engine = AnalysisEngine(df)
        summary = engine.get_summary_stats()

        if summary.empty:
            click.echo("No numeric columns found in the CSV file.")
            return

        click.echo("Summary Statistics:")
        click.echo(summary.to_string())

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    try:
        cli()
    except SystemExit:
        # Click raises SystemExit when no command is provided or on error
        # This is expected behavior, so we handle it gracefully
        pass
