"""CLI interface for config validator."""

import sys
from pathlib import Path
from typing import Optional

import typer
import yaml
from pydantic import ValidationError

from config_validator.schemas import get_schema_for_type

app = typer.Typer(help="Validate pipeline YAML definitions against typed schemas.")


@app.command()
def validate(
    config_file: Path = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        help="Path to the YAML config file to validate.",
    ),
    schema_type: str = typer.Option(
        "constitution",
        "--type",
        "-t",
        help="The type of schema to validate against (e.g., constitution).",
    ),
):
    """Validate a YAML configuration file against its corresponding schema."""
    try:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        typer.secho(f"Error parsing YAML file: {e}", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)
    
    if data is None:
        typer.secho("YAML file is empty.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    SchemaModel = get_schema_for_type(schema_type)
    if SchemaModel is None:
        typer.secho(f"Unknown schema type: '{schema_type}'.", fg=typer.colors.RED, err=True)
        raise typer.Exit(1)

    try:
        SchemaModel.model_validate(data)
        typer.secho(f"Successfully validated '{config_file}' against '{schema_type}' schema.", fg=typer.colors.GREEN)
    except ValidationError as e:
        typer.secho(f"Validation failed for '{config_file}':", fg=typer.colors.RED, err=True)
        for err in e.errors():
            loc = " -> ".join(str(l) for l in err["loc"])
            typer.secho(f"  - {loc}: {err['msg']}", fg=typer.colors.YELLOW, err=True)
        raise typer.Exit(1)


def main():
    app()


if __name__ == "__main__":
    main()
