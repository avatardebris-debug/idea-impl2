"""CLI entry point for the Logistics CSV Optimizer."""

import argparse
import json
import sys

from logistics_csv_optimizer.importer import Importer
from logistics_csv_optimizer.calculator import CostCalculator
from logistics_csv_optimizer.scheduler import ScheduleGenerator


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        description="Logistics CSV Optimizer - Import manifests, calculate costs, and generate schedules."
    )
    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input CSV manifest file.",
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to the output JSON file.",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose output.",
    )
    return parser


def main(args: list[str] | None = None) -> int:
    """Run the CLI pipeline.

    Args:
        args: List of CLI arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for error).
    """
    parser = build_parser()
    parsed = parser.parse_args(args)

    try:
        # Step 1: Import CSV
        if parsed.verbose:
            print(f"Importing CSV from: {parsed.input}")

        shipments = Importer.import_csv(parsed.input)

        if parsed.verbose:
            print(f"Imported {len(shipments)} shipments.")

        # Step 2: Calculate costs
        if parsed.verbose:
            print("Calculating costs...")

        costed_shipments = CostCalculator.calculate_costs(shipments)
        total = CostCalculator.total_cost(costed_shipments)

        if parsed.verbose:
            print(f"Total cost: {total}")

        # Step 3: Generate schedule
        if parsed.verbose:
            print("Generating schedule...")

        schedule = ScheduleGenerator.generate(costed_shipments)

        if parsed.verbose:
            print(f"Generated schedule with {len(schedule)} entries.")

        # Step 4: Write output JSON
        output = {
            "shipments": costed_shipments,
            "total_cost": total,
            "schedule": schedule,
        }

        with open(parsed.output, "w", encoding="utf-8") as fh:
            json.dump(output, fh, indent=2, ensure_ascii=False)

        if parsed.verbose:
            print(f"Output written to: {parsed.output}")

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
