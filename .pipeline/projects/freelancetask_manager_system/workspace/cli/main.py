"""CLI entry point for the FreelanceTask Manager System.

Usage:
    ftm sop create --file service.json
    ftm sop list
    ftm sop edit <name> --field title "New Title"
    ftm proposal generate --sop <name> --client <name> --format markdown|html
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# Ensure the workspace directory is on the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.service_offering import ServiceOffering
from core.client_profile import ClientProfile
from sop_engine.template_manager import TemplateManager
from sop_engine.scope_extractor import ScopeExtractor
from sop_engine.pricing_calculator import PricingCalculator
from proposal_engine.proposal_builder import ProposalBuilder
from proposal_engine.template_renderer import TemplateRenderer


def cmd_sop_create(args: argparse.Namespace) -> None:
    """Handle 'ftm sop create' command."""
    filepath = args.file
    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    with open(filepath, "r") as f:
        data = json.load(f)

    errors = ServiceOffering.validate(data)
    if errors:
        print("Validation errors:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    offering = ServiceOffering.from_dict(data)
    manager = TemplateManager()
    name = manager.create(offering)
    print(f"SOP created successfully: {name} (v{offering.version})")


def cmd_sop_list(args: argparse.Namespace) -> None:
    """Handle 'ftm sop list' command."""
    manager = TemplateManager()
    sops = manager.list_all()
    if not sops:
        print("No SOPs found.")
        return

    print(f"{'Name':<30} {'Version':<10} {'Deliverables':<12} {'Min Price':<12} {'Max Price':<12}")
    print("-" * 76)
    for sop in sops:
        prices = [t.price for t in sop.pricing]
        print(f"{sop.title:<30} {sop.version:<10} {len(sop.deliverables):<12} "
              f"${min(prices):<11.2f} ${max(prices):<11.2f}")


def cmd_sop_edit(args: argparse.Namespace) -> None:
    """Handle 'ftm sop edit' command."""
    manager = TemplateManager()
    name = args.name

    updates = {}
    if args.field and args.value:
        updates[args.field] = args.value

    if not updates:
        print("Error: Provide at least one --field <value> pair.")
        sys.exit(1)

    try:
        updated = manager.edit(name, updates)
        print(f"SOP updated: {updated.title} (v{updated.version})")
    except FileNotFoundError:
        print(f"Error: SOP not found: {name}")
        sys.exit(1)


def cmd_proposal_generate(args: argparse.Namespace) -> None:
    """Handle 'ftm proposal generate' command."""
    manager = TemplateManager()
    client_manager = ClientStore()

    try:
        offering = manager.get(args.sop)
    except FileNotFoundError:
        print(f"Error: SOP not found: {args.sop}")
        sys.exit(1)

    try:
        client = client_manager.get(args.client)
    except FileNotFoundError:
        print(f"Error: Client not found: {args.client}")
        sys.exit(1)

    builder = ProposalBuilder()
    proposal = builder.build(offering, client, budget=args.budget)

    renderer = TemplateRenderer()
    output = renderer.render(proposal, fmt=args.format)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Proposal saved to: {args.output}")
    else:
        print(output)


class ClientStore:
    """Simple in-memory client store for CLI lookups."""

    def __init__(self):
        self._clients: dict[str, ClientProfile] = {}
        self._load_benchmarks()

    def _load_benchmarks(self) -> None:
        benchmarks_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "benchmarks"
        )
        client_file = os.path.join(benchmarks_dir, "sample_clients.json")
        if os.path.exists(client_file):
            with open(client_file, "r") as f:
                data = json.load(f)
            for c in data:
                client = ClientProfile.from_dict(c)
                self._clients[client.name] = client

    def get(self, name: str) -> ClientProfile:
        if name in self._clients:
            return self._clients[name]
        # Also try case-insensitive
        for k, v in self._clients.items():
            if k.lower() == name.lower():
                return v
        raise FileNotFoundError(f"Client not found: {name}")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="ftm",
        description="FreelanceTask Manager — SOP engine, proposal generator, and job automation.",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # sop create
    sop_parser = subparsers.add_parser("sop", help="SOP management commands")
    sop_sub = sop_parser.add_subparsers(dest="sop_command")

    sop_create = sop_sub.add_parser("create", help="Create a new SOP from a JSON file")
    sop_create.add_argument("--file", required=True, help="Path to SOP JSON file")

    sop_sub.add_parser("list", help="List all SOPs")

    sop_edit = sop_sub.add_parser("edit", help="Edit an existing SOP")
    sop_edit.add_argument("name", help="SOP name to edit")
    sop_edit.add_argument("--field", help="Field to update")
    sop_edit.add_argument("--value", help="New value for the field")

    # proposal generate
    prop_parser = subparsers.add_parser("proposal", help="Proposal commands")
    prop_sub = prop_parser.add_subparsers(dest="prop_command")

    prop_gen = prop_sub.add_parser("generate", help="Generate a proposal")
    prop_gen.add_argument("--sop", required=True, help="SOP name")
    prop_gen.add_argument("--client", required=True, help="Client name")
    prop_gen.add_argument("--format", choices=["markdown", "html"], default="markdown",
                          help="Output format (default: markdown)")
    prop_gen.add_argument("--budget", type=float, default=None, help="Client budget for tier recommendation")
    prop_gen.add_argument("--output", "-o", help="Output file path (default: stdout)")

    args = parser.parse_args()

    if args.command == "sop":
        if not hasattr(args, "sop_command") or not args.sop_command:
            sop_parser.print_help()
            sys.exit(1)
        if args.sop_command == "create":
            cmd_sop_create(args)
        elif args.sop_command == "list":
            cmd_sop_list(args)
        elif args.sop_command == "edit":
            cmd_sop_edit(args)
        else:
            sop_parser.print_help()
    elif args.command == "proposal":
        if not hasattr(args, "prop_command") or not args.prop_command:
            prop_parser.print_help()
            sys.exit(1)
        if args.prop_command == "generate":
            cmd_proposal_generate(args)
        else:
            prop_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
