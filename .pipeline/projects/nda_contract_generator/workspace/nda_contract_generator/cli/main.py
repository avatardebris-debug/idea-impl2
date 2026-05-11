"""Main CLI entry point for the NDA Contract Generator."""

import argparse
import json
import logging
import sys
from typing import Optional

from nda_contract_generator.core.clause_library import ClauseLibrary
from nda_contract_generator.core.template_engine import TemplateEngine
from nda_contract_generator.jurisdictions.jurisdiction_database import JurisdictionDatabase

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Configure logging for the CLI.

    Args:
        verbose: If True, set log level to DEBUG.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def cmd_draft(args: argparse.Namespace) -> int:
    """Handle the 'draft' subcommand.

    Generates a new NDA contract based on jurisdiction and clauses.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        clause_lib = ClauseLibrary()
        jur_db = JurisdictionDatabase()
        engine = TemplateEngine()

        jurisdiction = args.jurisdiction
        if not jur_db.validate_jurisdiction(jurisdiction):
            print(f"Error: Unknown jurisdiction '{jurisdiction}'.")
            print(f"Available jurisdictions: {', '.join(jur_db.list_jurisdictions())}")
            return 1

        config = jur_db.get_config(jurisdiction)
        effective_values = clause_lib.apply_overrides(jurisdiction)

        # Build context from args and effective values
        context = {
            "disclosing_party_name": args.disclosing_party or "Disclosing Party",
            "receiving_party_name": args.receiving_party or "Receiving Party",
            "effective_date": args.effective_date or "TBD",
            "purpose": args.purpose or "Evaluation of potential business relationship",
            "jurisdiction_name": jur_db.get_display_name(jurisdiction) or jurisdiction,
            "governing_law": jur_db.get_governing_law(jurisdiction) or "TBD",
            "default_term": jur_db.get_default_term(jurisdiction) or "TBD",
        }
        context.update(effective_values)

        # Use the template from the jurisdiction config
        template_name = config.get("template_path", f"nda_{jurisdiction}.txt")

        rendered = engine.render_contract(template_name, context)
        print(rendered)
        return 0

    except ValueError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error generating contract: {e}")
        logger.exception("Contract generation failed")
        return 1


def cmd_customize(args: argparse.Namespace) -> int:
    """Handle the 'customize' subcommand.

    Overrides clause defaults for a jurisdiction.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        clause_lib = ClauseLibrary()

        if args.list:
            print("Available clauses:")
            for name in clause_lib.list_clause_names():
                clause = clause_lib.get_clause(name)
                print(f"  {name}: default={clause['default']}, allowed={clause['allowed_values']}")
            return 0

        if args.show:
            clause = clause_lib.get_clause(args.show)
            if clause is None:
                print(f"Error: Clause '{args.show}' not found.")
                return 1
            print(f"Clause: {clause['name']}")
            print(f"  Description: {clause['description']}")
            print(f"  Default: {clause['default']}")
            print(f"  Allowed values: {', '.join(clause['allowed_values'])}")
            return 0

        if args.set:
            clause_name, value = args.set
            if clause_lib.override_clause(clause_name, value):
                clause_lib.save_overrides()
                print(f"Override set: {clause_name} = {value}")
                return 0
            else:
                clause = clause_lib.get_clause(clause_name)
                if clause is None:
                    print(f"Error: Clause '{clause_name}' not found.")
                else:
                    print(f"Error: Invalid value '{value}' for clause '{clause_name}'.")
                    print(f"Allowed values: {', '.join(clause['allowed_values'])}")
                return 1

        if args.remove:
            if clause_lib.remove_override(args.remove):
                clause_lib.save_overrides()
                print(f"Override removed: {args.remove}")
                return 0
            else:
                print(f"No override to remove for clause '{args.remove}'.")
                return 1

        print("Usage: nda customize --list | --show <clause> | --set <clause>=<value> | --remove <clause>")
        return 0

    except Exception as e:
        print(f"Error customizing clauses: {e}")
        return 1


def cmd_validate(args: argparse.Namespace) -> int:
    """Handle the 'validate' subcommand.

    Validates a contract against jurisdiction requirements.

    Args:
        args: Parsed CLI arguments.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    try:
        jur_db = JurisdictionDatabase()

        jurisdiction = args.jurisdiction
        if not jur_db.validate_jurisdiction(jurisdiction):
            print(f"Error: Unknown jurisdiction '{jurisdiction}'.")
            return 1

        # Read the contract file
        with open(args.contract, "r", encoding="utf-8") as f:
            contract_text = f.read()

        # Extract clause names from the contract (simple heuristic: look for clause names)
        clause_lib = ClauseLibrary()
        all_clause_names = clause_lib.list_clause_names()
        present_clauses = [name for name in all_clause_names if name in contract_text]

        result = jur_db.validate_clauses(jurisdiction, present_clauses)

        if result["valid"]:
            print(f"Contract is valid for {jurisdiction}.")
        else:
            print(f"Contract is INVALID for {jurisdiction}.")
            if result.get("missing"):
                print(f"Missing required clauses: {', '.join(result['missing'])}")
            if result.get("extra"):
                print(f"Extra clauses: {', '.join(result['extra'])}")

        # Print as JSON for programmatic use
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1

    except FileNotFoundError:
        print(f"Error: Contract file not found: {args.contract}")
        return 1
    except Exception as e:
        print(f"Error validating contract: {e}")
        return 1


def main() -> int:
    """Main entry point for the CLI.

    Returns:
        Exit code.
    """
    parser = argparse.ArgumentParser(
        prog="nda",
        description="NDA Contract Generator — draft, customize, and validate jurisdiction-specific NDAs.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging.")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # draft subcommand
    draft_parser = subparsers.add_parser("draft", help="Generate a new NDA contract")
    draft_parser.add_argument("--jurisdiction", "-j", required=True, help="Jurisdiction key")
    draft_parser.add_argument("--disclosing-party", "-d", help="Disclosing party name")
    draft_parser.add_argument("--receiving-party", "-r", help="Receiving party name")
    draft_parser.add_argument("--effective-date", "-e", help="Effective date")
    draft_parser.add_argument("--purpose", "-p", help="Purpose of disclosure")

    # customize subcommand
    customize_parser = subparsers.add_parser("customize", help="Manage clause overrides")
    customize_parser.add_argument("--list", action="store_true", help="List all clauses")
    customize_parser.add_argument("--show", help="Show details for a clause")
    customize_parser.add_argument("--set", help="Set a clause override (clause=value)")
    customize_parser.add_argument("--remove", help="Remove a clause override")

    # validate subcommand
    validate_parser = subparsers.add_parser("validate", help="Validate a contract against jurisdiction rules")
    validate_parser.add_argument("--jurisdiction", "-j", required=True, help="Jurisdiction key")
    validate_parser.add_argument("--contract", "-c", required=True, help="Path to the contract file")

    args = parser.parse_args()

    setup_logging(args.verbose)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "draft":
        return cmd_draft(args)
    elif args.command == "customize":
        return cmd_customize(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
