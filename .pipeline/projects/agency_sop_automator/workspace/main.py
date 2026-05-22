"""Main entry point for the Agency SOP Automator.

Usage:
    python -m agency_sop_automator.main --sop client_onboarding --input-file input.json
    python -m agency_sop_automator.main --sop client_onboarding --input '{"client_name": "Acme", "service_type": "web_design", "budget": 5000}'
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from .config import get_output_dir
from .executor import SOPExecutor, execute_sop, MockLLMClient
from .output_formatter import format_output
from .sop_loader import SOPLoader


def run_sop(
    sop_name: str,
    input_data: Dict[str, Any],
    output_format: str = "yaml",
    output_path: Optional[str] = None,
    use_mock: bool = True,
) -> Dict[str, Any]:
    """Run an SOP with the given input data.

    Args:
        sop_name:      Name of the SOP to run.
        input_data:    Input data dict.
        output_format: Output format ('yaml', 'json', 'csv', 'text').
        output_path:   Optional file path to write output to.
        use_mock:      If True, use mock LLM client (for testing).

    Returns:
        The final output dict from SOP execution.
    """
    loader = SOPLoader()
    sop = loader.get_sop(sop_name)

    llm_client = MockLLMClient() if use_mock else None
    executor = SOPExecutor(sop, llm_client)
    result = executor.run(input_data)

    # Format and optionally write output
    formatted = format_output(
        result,
        output_format=output_format,
        output_path=output_path,
    )
    print(formatted)

    return result


def main(argv: Optional[list[str]] = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Agency SOP Automator — run SOPs step-by-step"
    )
    parser.add_argument(
        "--sop",
        required=False,
        default=None,
        help="Name of the SOP to execute",
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Input data as a JSON string (e.g., '{\"client_name\": \"Acme\"}')",
    )
    parser.add_argument(
        "--input-file",
        type=str,
        default=None,
        help="Path to a JSON file containing input data",
    )
    parser.add_argument(
        "--output-format",
        type=str,
        default="yaml",
        choices=["yaml", "json", "csv", "text"],
        help="Output format (default: yaml)",
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default=None,
        help="Path to write output file (default: stdout)",
    )
    parser.add_argument(
        "--no-mock",
        action="store_true",
        help="Use real LLM client instead of mock",
    )
    parser.add_argument(
        "--list-sops",
        action="store_true",
        help="List available SOPs and exit",
    )

    args = parser.parse_args(argv)

    if args.list_sops:
        loader = SOPLoader()
        sops = loader.list_sops()
        if sops:
            print("Available SOPs:")
            for sop in sops:
                print(f"  - {sop}")
        else:
            print("No SOPs found.")
        return 0

    # Get input data
    if args.input:
        try:
            input_data = json.loads(args.input)
        except json.JSONDecodeError as exc:
            print(f"Error: Invalid JSON input: {exc}", file=sys.stderr)
            return 1
    elif args.input_file:
        try:
            with open(args.input_file, "r") as f:
                input_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as exc:
            print(f"Error: Could not read input file: {exc}", file=sys.stderr)
            return 1
    else:
        print("Error: Either --input or --input-file is required", file=sys.stderr)
        return 2

    # Run the SOP
    output_path = args.output_path or str(get_output_dir() / f"{args.sop}_output.{args.output_format}")
    try:
        run_sop(
            sop_name=args.sop,
            input_data=input_data,
            output_format=args.output_format,
            output_path=output_path,
            use_mock=not args.no_mock,
        )
        return 0
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
