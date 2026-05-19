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
# Edit sources, steps, and sinks as needed.

sources:
  main: data/input.csv
  # secondary: data/other.csv

steps:
  - id: drop_blanks
    type: filter
    predicate: "id != '' and id != 'None'"

  - id: select_cols
    type: select
    columns: [id, name, value, category]

  - id: agg_by_category
    type: aggregate
    group_by: [category]
    aggregations:
      value: sum
      id: count

sinks:
  - type: csv
    path: output/result.csv
  - type: json
    path: output/result.json
"""


def _cmd_init(args: argparse.Namespace) -> None:
    target = pathlib.Path(args.file)
    if target.exists():
        print(f"  {target} already exists — use --force to overwrite")
        sys.exit(1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(_STARTER_YAML, encoding="utf-8")
    print(f"  ✓ Created {target}")
    print("  Edit the sources, steps, and sinks, then run:")
    print(f"    csv-pipeline validate {target}")
    print(f"    csv-pipeline run {target}")


def _cmd_validate(args: argparse.Namespace) -> None:
    from .loader import load_pipeline
    print(f"  Validating {args.file}...")
    try:
        pipeline, rows = load_pipeline(args.file)
        print(f"  ✓ Valid — {len(pipeline.nodes)} step(s), {len(pipeline.sinks)} sink(s)")
        print(f"  Source rows: {len(rows)}")
    except Exception as e:
        print(f"  ✗ Validation failed: {e}")
        sys.exit(1)


def _cmd_dry_run(args: argparse.Namespace) -> None:
    from .loader import load_pipeline
    print(f"  Dry-run {args.file}...")
    try:
        pipeline, seed_rows = load_pipeline(args.file)
        schema = pipeline.dry_run_schema(seed_rows[:10])
        print(f"  ✓ Output schema ({len(schema)} columns):")
        for col in schema:
            print(f"    - {col}")
    except Exception as e:
        print(f"  ✗ Dry-run failed: {e}")
        sys.exit(1)


def _cmd_run(args: argparse.Namespace) -> None:
    from .loader import execute_yaml
    print(f"  Running pipeline: {args.file}")
    try:
        rows, reports = execute_yaml(args.file)
        print(f"\n  ✓ Pipeline complete — {len(rows)} output rows\n")
        print(f"  {'Node':<25} {'In':>6} {'Out':>6} {'ms':>8}  Status")
        print(f"  {'-'*55}")
        for r in reports:
            status = "✓" if not r.error else f"✗ {r.error[:30]}"
            print(f"  {r.node_id:<25} {r.input_rows:>6} {r.output_rows:>6} {r.duration_ms:>7.1f}ms  {status}")

        if args.show_sample and rows:
            print(f"\n  Sample output (first 3 rows):")
            for row in rows[:3]:
                print(f"    {json.dumps(row)}")
    except Exception as e:
        print(f"  ✗ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def _cmd_report(args: argparse.Namespace) -> None:
    """Print the last execution report from .pipeline_last_run.json if it exists."""
    report_file = pathlib.Path(".pipeline_last_run.json")
    if not report_file.exists():
        print("  No previous run report found (.pipeline_last_run.json)")
        return
    try:
        data = json.loads(report_file.read_text(encoding="utf-8"))
        print(f"\n  Last run: {data.get('timestamp', '?')}")
        print(f"  Pipeline: {data.get('file', '?')}")
        print(f"  Output rows: {data.get('output_rows', '?')}")
        for r in data.get("reports", []):
            print(f"    {r['node_id']:<25} {r['input_rows']:>6}→{r['output_rows']:<6} {r['duration_ms']:.1f}ms")
    except Exception as e:
        print(f"  Could not read report: {e}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CSV Data Pipeline Builder",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              csv-pipeline init my_pipeline.yaml
              csv-pipeline validate my_pipeline.yaml
              csv-pipeline dry-run my_pipeline.yaml --show-schema
              csv-pipeline run my_pipeline.yaml
              csv-pipeline run my_pipeline.yaml --show-sample
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Scaffold a starter pipeline.yaml")
    p_init.add_argument("file", nargs="?", default="pipeline.yaml")

    p_val = sub.add_parser("validate", help="Validate a pipeline YAML without running it")
    p_val.add_argument("file")

    p_dry = sub.add_parser("dry-run", help="Infer output schema without writing sinks")
    p_dry.add_argument("file")
    p_dry.add_argument("--show-schema", action="store_true")

    p_run = sub.add_parser("run", help="Execute a pipeline YAML")
    p_run.add_argument("file")
    p_run.add_argument("--show-sample", action="store_true", help="Print first 3 output rows")

    p_rep = sub.add_parser("report", help="Show last execution report")
    p_rep.add_argument("--last", action="store_true")

    args = parser.parse_args()
    {
        "init":     _cmd_init,
        "validate": _cmd_validate,
        "dry-run":  _cmd_dry_run,
        "run":      _cmd_run,
        "report":   _cmd_report,
    }[args.command](args)


if __name__ == "__main__":
    main()
