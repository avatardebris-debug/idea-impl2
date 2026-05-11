"""CLI interface for NDA Contract Generator."""

import argparse
import json
import logging
import sys
from typing import Dict, List, Optional

from nda_contract_generator.contract_generator import ContractGenerator
from nda_contract_generator.jurisdictions.jurisdiction_database import JurisdictionDatabase

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s: %(message)s")


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser for the CLI."""
    parser = argparse.ArgumentParser(
        prog="nda-contract-generator",
        description="Generate jurisdiction-specific Non-Disclosure Agreements.",
    )
    parser.add_argument(
        "--jurisdiction",
        "-j",
        choices=["california", "england_wales", "gdpr_compliant"],
        default="california",
        help="Target jurisdiction for the NDA.",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="nda_output.txt",
        help="Output file path for the generated NDA.",
    )
    parser.add_argument(
        "--input",
        "-i",
        default=None,
        help="Path to a JSON file with form data.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging.",
    )
    parser.add_argument(
        "--list-jurisdictions",
        action="store_true",
        help="List all available jurisdictions and exit.",
    )
    return parser


def list_jurisdictions() -> None:
    """List all available jurisdictions."""
    db = JurisdictionDatabase()
    jurisdictions = db.list_jurisdictions()
    print("Available jurisdictions:")
    for key in jurisdictions:
        display_name = db.get_display_name(key) or key
        print(f"  - {key}: {display_name}")
    sys.exit(0)


def load_form_data(input_path: Optional[str] = None) -> Dict:
    """Load form data from a JSON file or return empty dict."""
    if input_path:
        with open(input_path, "r") as f:
            return json.load(f)
    return {}


def generate_nda(
    jurisdiction: str,
    output_path: str,
    form_data: Dict,
) -> str:
    """Generate an NDA contract.

    Args:
        jurisdiction: The target jurisdiction.
        output_path: The output file path.
        form_data: Dictionary of form data.

    Returns:
        The generated contract text.
    """
    generator = ContractGenerator(jurisdiction)
    contract_text = generator.generate(form_data)

    with open(output_path, "w") as f:
        f.write(contract_text)

    logger.info("NDA generated successfully: %s", output_path)
    return contract_text


def main() -> None:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.list_jurisdictions:
        list_jurisdictions()

    db = JurisdictionDatabase()
    if not db.validate_jurisdiction(args.jurisdiction):
        logger.error("Unknown jurisdiction: %s", args.jurisdiction)
        sys.exit(1)

    form_data = load_form_data(args.input)

    try:
        generate_nda(args.jurisdiction, args.output, form_data)
    except Exception as e:
        logger.error("Failed to generate NDA: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
