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

@app.command("analyze")
def analyze_cmd(
    input_path: str = typer.Argument(
        ...,
        help="Path to a JSON/Parquet file or directory to analyze.",
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
        help="Output format: jsonschema, yaml, or pydantic.",
    ),
    stream: bool = typer.Option(
        False,
        "--stream",
        help="Use chunked streaming for very large JSON/JSONL files.",
    ),
) -> None:
    """Analyze datasets, detect anomalies, and output validation rules."""
    from json_schema_profiler.anomaly import detect_anomalies
    from json_schema_profiler.formatters import to_jsonschema, to_yaml, to_pydantic
    from json_schema_profiler.inference import infer_schema_stream
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    path = Path(input_path)
    if not path.exists():
        typer.echo(f"Error: path not found: {input_path}", err=True)
        raise typer.Exit(1)
        
    data = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        task = progress.add_task(description="Reading and analyzing data...", total=None)
        
        from json_schema_profiler.cache import get_cached_result, save_cached_result
        
        cached = None
        if not stream and not path.is_dir():
            cached = get_cached_result(str(path))
            
        if cached:
            schema = cached["schema"]
            anomalies = cached["anomalies"]
        else:
            if stream and path.suffix not in ['.parquet']:
                # Use stream inference
                with open(path, "rb") as f:
                    schema = infer_schema_stream(f)
                # For anomalies we can't easily stream the entire dataset without 
                # more complex accumulators, so we return empty anomalies for stream MVP
                anomalies = {}
            else:
                if path.is_dir():
                    from json_schema_profiler.parquet_loader import scan_parquet_directory
                    data = scan_parquet_directory(str(path))
                elif path.suffix == '.parquet':
                    from json_schema_profiler.parquet_loader import read_parquet
                    data = read_parquet(str(path))
                else:
                    try:
                        raw = path.read_text(encoding="utf-8")
                        data = json.loads(raw)
                    except json.JSONDecodeError as e:
                        typer.echo(f"Error: invalid JSON in {input_path}: {e}", err=True)
                        raise typer.Exit(1)
                        
                if not isinstance(data, list):
                    data = [data]
                    
                schema = infer_schema(data)
                anomalies = detect_anomalies(data)
                
            if not stream and not path.is_dir():
                save_cached_result(str(path), {"schema": schema, "anomalies": anomalies})
    
    if format == "jsonschema":
        result = to_jsonschema(schema, anomalies)
    elif format == "yaml":
        result = to_yaml(schema, anomalies)
    elif format == "pydantic":
        result = to_pydantic(schema, anomalies)
    else:
        typer.echo(f"Error: unsupported format '{format}'.", err=True)
        raise typer.Exit(1)
        
    if output:
        out_path = Path(output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(result, encoding="utf-8")
        typer.echo(f"Output written to {output}", err=True)
    else:
        typer.echo(result)

@app.command("compare")
def compare_cmd(
    schema_a_path: str = typer.Argument(..., help="Path to the first (baseline) JSON Schema."),
    schema_b_path: str = typer.Argument(..., help="Path to the second (new) JSON Schema.")
) -> None:
    """Compare two JSON schemas to detect drift (added, removed, or changed fields)."""
    from json_schema_profiler.drift import compare_schemas
    
    path_a = Path(schema_a_path)
    path_b = Path(schema_b_path)
    
    if not path_a.exists():
        typer.echo(f"Error: {schema_a_path} not found.", err=True)
        raise typer.Exit(1)
    if not path_b.exists():
        typer.echo(f"Error: {schema_b_path} not found.", err=True)
        raise typer.Exit(1)
        
    try:
        schema_a = json.loads(path_a.read_text(encoding="utf-8"))
        schema_b = json.loads(path_b.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        typer.echo(f"Error parsing schemas: {e}", err=True)
        raise typer.Exit(1)
        
    diff = compare_schemas(schema_a, schema_b)
    
    if not diff["added"] and not diff["removed"] and not diff["changed"]:
        typer.echo("No schema drift detected. Schemas are identical.")
        return
        
    typer.echo("Schema Drift Detected:\n")
    if diff["added"]:
        typer.echo("Added fields:")
        for f in diff["added"]:
            typer.echo(f"  + {f}")
            
    if diff["removed"]:
        typer.echo("\nRemoved fields:")
        for f in diff["removed"]:
            typer.echo(f"  - {f}")
            
    if diff["changed"]:
        typer.echo("\nChanged fields:")
        for change in diff["changed"]:
            typer.echo(f"  ~ {change['field']}:")
            typer.echo(f"    Old: {change['old']}")
            typer.echo(f"    New: {change['new']}")

if __name__ == "__main__":
    app()
