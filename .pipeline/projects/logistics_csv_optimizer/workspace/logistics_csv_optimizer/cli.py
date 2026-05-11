"""CLI entry point for the Logistics CSV Optimizer."""

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser."""
    parser = argparse.ArgumentParser(
        prog="logistics_csv_optimizer",
        description="Import shipment manifests, calculate routing costs, "
                    "and generate optimized delivery schedules.",
    )
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to the input CSV shipment manifest file.",
    )
    parser.add_argument(
        "--output", "-o",
        required=True,
        help="Path to the output JSON schedule file.",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print progress information to stdout.",
    )
    return parser


def main(argv=None) -> int:
    """Run the CLI workflow. Returns exit code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        from logistics_csv_optimizer.importer import Importer
        from logistics_csv_optimizer.calculator import CostCalculator
        from logistics_csv_optimizer.scheduler import ScheduleGenerator
        import json

        if args.verbose:
            print(f"[1/3] Loading manifest from {args.input} ...")

        shipments = Importer.load_manifest(args.input)
        if not shipments:
            print("Warning: No shipments found in the manifest.", file=sys.stderr)

        if args.verbose:
            print(f"[2/3] Calculating costs for {len(shipments)} shipments ...")

        cost_results = CostCalculator.calculate(shipments)

        if args.verbose:
            print("[3/3] Generating optimized delivery schedule ...")

        schedule = ScheduleGenerator.generate(shipments)

        output = {
            "shipments": cost_results["per_shipment"],
            "total_cost": cost_results["total_cost"],
            "schedule": schedule,
        }

        with open(args.output, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2)

        if args.verbose:
            print(f"Schedule written to {args.output}")

        return 0

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
