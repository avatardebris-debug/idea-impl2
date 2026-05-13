"""CLI entry point for json-schema-profiler using typer."""

import json
import sys
from pathlib import Path

import typer

from json_schema_profiler.inference import infer_schema

app = typer.Typer(
    name="json-schema-profiler",
    help="Scan JSON datasets, infer schemas, and output validation rules.",
)


@app.callback()
def main():
    """json-schema-profiler: Scan JSON datasets, infer schemas, and output validation rules."""
    pass


@app.command("infer")
def infer_cmd(
    input_file: str = typer.Argument(
        ...,
        help="Path to a JSON file (single object or array of objects) to analyze.",
    ),
    output: str | None = typer.Option(
        None,
        "--output",
        "-o",
        help="Write the inferred schema to a file instead of stdout.",
    ),
    format: str = typer.Option(
        "jsonschema",
        "--format",
        "-f",
        help="Output format (currently only 'jsonschema' is supported).",
    ),
) -> None:
    """Infer a JSON Schema from a JSON file."""
    if format != "jsonschema":
        typer.echo(f"Error: unsupported format '{format}'. Only 'jsonschema' is supported in Phase 1.", err=True)
        raise typer.Exit(1)

    path = Path(input_file)
    if not path.exists():
        typer.echo(f"Error: file not found: {input_file}", err=True)
        raise typer.Exit(1)

    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        typer.echo(f"Error: invalid JSON in {input_file}: {e}", err=True)
        raise typer.Exit(1)

    schema = infer_schema(data)

    schema_json = json.dumps(schema, indent=2, ensure_ascii=False)

    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(schema_json, encoding="utf-8")
        typer.echo(f"Schema written to {output}", err=True)
    else:
        typer.echo(schema_json)


if __name__ == "__main__":
    app()
