"""
csv_data_pipeline_builder/cli.py
CLI entrypoint for the CSV pipeline builder.

Usage:
    csv-pipeline run pipeline.yaml
    csv-pipeline validate pipeline.yaml
    csv-pipeline dry-run pipeline.yaml --show-schema
    csv-pipeline report --last
    csv-pipeline init my_pipeline.yaml    # scaffold a starter YAML
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import textwrap


_STARTER_YAML = """\
# csv-pipeline starter template
# Edit sources, steps, and sinks to build your pipeline.

sources:
  sales: data/sales.csv
  customers: data/customers.csv

steps:
  - id: filter_2024
    type: filter
    predicate: "year == '2024'"

  - id: join_customers
    type: join
    left_key: customer_id
    right_key: id
    right_source: customers
    how: left

  - id: agg_by_region
    type: aggregate
    group_by: [region]
    aggregations:
      revenue: sum
      id: count

sinks:
  - id: output_csv
    type: csv
    path: output/result.csv
"""


def cmd_init(args: argparse.Namespace) -> None:
    """Scaffold a starter pipeline YAML."""
    path = pathlib.Path(args.output)
    if path.exists():
        print(f"Error: {path} already exists")
        sys.exit(1)
    path.write_text(_STARTER_YAML)
    print(f"Created {path}")


def cmd_run(args: argparse.Namespace) -> None:
    """Run a pipeline from a YAML file."""
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required. Install with: pip install pyyaml")
        sys.exit(1)

    from .loader import PipelineLoader

    loader = PipelineLoader()
    pipeline = loader.load(args.pipeline)

    reports = pipeline.execute()
    for r in reports:
        status = "OK" if not r.error else f"ERROR: {r.error}"
        print(f"  [{r.node_id}] {r.input_rows} -> {r.output_rows} rows ({r.duration_ms:.1f}ms) {status}")

    # Get final output
    if pipeline.reports:
        last_report = pipeline.reports[-1]
        print(f"\nFinal output: {last_report.output_rows} rows")


def cmd_validate(args: argparse.Namespace) -> None:
    """Validate a pipeline YAML file."""
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required. Install with: pip install pyyaml")
        sys.exit(1)

    from .loader import PipelineLoader

    loader = PipelineLoader()
    pipeline = loader.load(args.pipeline)
    errors = pipeline.validate()
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("Pipeline is valid.")


def cmd_dry_run(args: argparse.Namespace) -> None:
    """Infer output schema without executing transforms."""
    try:
        import yaml
    except ImportError:
        print("Error: pyyaml is required. Install with: pip install pyyaml")
        sys.exit(1)

    from .loader import PipelineLoader

    loader = PipelineLoader()
    pipeline = loader.load(args.pipeline)

    # Infer schema from the last node's expected output
    if pipeline.nodes:
        last = pipeline.nodes[-1]
        print(f"Last node: {last}")
        if args.show_schema:
            print("Schema inference: (would show column types)")
            print("  (Full schema inference requires execution or type hints)")


def cmd_report(args: argparse.Namespace) -> None:
    """Print the last execution summary."""
    report_path = pathlib.Path("pipeline_reports.json")
    if not report_path.exists():
        print("No execution reports found.")
        return
    reports = json.loads(report_path.read_text())
    print(json.dumps(reports, indent=2))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="csv-pipeline", description="CSV Data Pipeline Builder")
    sub = parser.add_subparsers(dest="command")

    # run
    run_p = sub.add_parser("run", help="Run a pipeline")
    run_p.add_argument("pipeline", help="Path to pipeline.yaml")

    # validate
    val_p = sub.add_parser("validate", help="Validate a pipeline YAML")
    val_p.add_argument("pipeline", help="Path to pipeline.yaml")

    # dry-run
    dry_p = sub.add_parser("dry-run", help="Dry-run a pipeline")
    dry_p.add_argument("pipeline", help="Path to pipeline.yaml")
    dry_p.add_argument("--show-schema", action="store_true", help="Show inferred schema")

    # report
    rep_p = sub.add_parser("report", help="Show last execution report")
    rep_p.add_argument("--last", action="store_true", help="Show last report")

    # init
    init_p = sub.add_parser("init", help="Scaffold a starter pipeline YAML")
    init_p.add_argument("output", help="Output file path")

    args = parser.parse_args(argv)

    if args.command == "run":
        cmd_run(args)
    elif args.command == "validate":
        cmd_validate(args)
    elif args.command == "dry-run":
        cmd_dry_run(args)
    elif args.command == "report":
        cmd_report(args)
    elif args.command == "init":
        cmd_init(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
