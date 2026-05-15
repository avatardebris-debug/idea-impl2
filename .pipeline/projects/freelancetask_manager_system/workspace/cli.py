"""CLI entry point for the FreelanceTask Manager System.

Usage:
    ftm sop create --file service.json
    ftm sop list
    ftm sop edit <name> --field title "New Title"
    ftm proposal generate --sop <name> --client <name> --format markdown|html
    ftm opportunity create --sop <name> --client <name>
    ftm opportunity list [--pipeline <id>]
    ftm pipeline create --name <name>
    ftm pipeline list
    ftm pipeline stats <id>
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
from opportunity.models import OpportunityStage
from opportunity.opportunity_engine import OpportunityEngine
from opportunity.pipeline_manager import PipelineManager
from opportunity.matching import OpportunityMatcher


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
        print("Error: Provide --field and --value to update.")
        sys.exit(1)

    sop = manager.get(name)
    if not sop:
        print(f"Error: SOP '{name}' not found.")
        sys.exit(1)

    # Apply updates
    if "title" in updates:
        sop.title = updates["title"]
    if "description" in updates:
        sop.description = updates["description"]
    if "deliverables" in updates:
        sop.deliverables = json.loads(updates["deliverables"])
    if "features" in updates:
        sop.features = json.loads(updates["features"])
    if "pricing" in updates:
        sop.pricing = [
            ServiceOffering.PricingTier(**t)
            for t in json.loads(updates["pricing"])
        ]

    sop.version += 1
    manager.save(name, sop)
    print(f"SOP '{name}' updated to version {sop.version}")


def cmd_sop_show(args: argparse.Namespace) -> None:
    """Handle 'ftm sop show' command."""
    manager = TemplateManager()
    sop = manager.get(args.name)
    if not sop:
        print(f"Error: SOP '{args.name}' not found.")
        sys.exit(1)

    print(json.dumps(sop.to_dict(), indent=2))


def cmd_proposal_generate(args: argparse.Namespace) -> None:
    """Handle 'ftm proposal generate' command."""
    # Load SOP
    sop_manager = TemplateManager()
    sop = sop_manager.get(args.sop)
    if not sop:
        print(f"Error: SOP '{args.sop}' not found.")
        sys.exit(1)

    # Load client
    client_manager = TemplateManager()
    client = client_manager.get(args.client)
    if not client:
        print(f"Error: Client '{args.client}' not found.")
        sys.exit(1)

    # Generate proposal
    builder = ProposalBuilder()
    proposal = builder.build(sop, client)

    # Render
    renderer = TemplateRenderer()
    fmt = args.format or "markdown"
    output = renderer.render(proposal, fmt)

    if args.output:
        with open(args.output, "w") as f:
            f.write(output)
        print(f"Proposal saved to {args.output}")
    else:
        print(output)


def cmd_opportunity_create(args: argparse.Namespace) -> None:
    """Handle 'ftm opportunity create' command."""
    # Load SOP
    sop_manager = TemplateManager()
    sop = sop_manager.get(args.sop)
    if not sop:
        print(f"Error: SOP '{args.sop}' not found.")
        sys.exit(1)

    # Load client
    client_manager = TemplateManager()
    client = client_manager.get(args.client)
    if not client:
        print(f"Error: Client '{args.client}' not found.")
        sys.exit(1)

    # Create opportunity
    engine = OpportunityEngine()
    stage = getattr(OpportunityStage, args.stage.upper(), OpportunityStage.NEW)
    opp = engine.create_opportunity(
        offering=sop,
        client=client,
        stage=stage,
        notes=args.notes or "",
    )

    # Save to pipeline
    pipeline_mgr = PipelineManager()
    pipeline = pipeline_mgr.create_pipeline(f"{client.name} - {sop.title}")
    pipeline_mgr.add_opportunity(pipeline.pipeline_id, opp)

    print(f"Opportunity created: {opp.opportunity_id}")
    print(f"  Client: {opp.client_name}")
    print(f"  Service: {opp.service_title}")
    print(f"  Score: {opp.score:.2f}")
    print(f"  Stage: {opp.stage.value}")
    print(f"  Pipeline ID: {pipeline.pipeline_id}")


def cmd_opportunity_list(args: argparse.Namespace) -> None:
    """Handle 'ftm opportunity list' command."""
    pipeline_mgr = PipelineManager()
    pipelines = pipeline_mgr.list_pipelines()

    if not pipelines:
        print("No pipelines found.")
        return

    for pipeline in pipelines:
        print(f"\nPipeline: {pipeline.name} (ID: {pipeline.pipeline_id})")
        print(f"  Total Opportunities: {len(pipeline.opportunities)}")
        
        if args.pipeline and pipeline.pipeline_id != args.pipeline:
            continue

        if pipeline.opportunities:
            print(f"  {'ID':<12} {'Client':<20} {'Service':<25} {'Score':<8} {'Stage':<12}")
            print(f"  {'-'*12} {'-'*20} {'-'*25} {'-'*8} {'-'*12}")
            for opp in pipeline.opportunities:
                print(f"  {opp.opportunity_id:<12} {opp.client_name:<20} "
                      f"{opp.service_title:<25} {opp.score:<8.2f} {opp.stage.value:<12}")


def cmd_pipeline_create(args: argparse.Namespace) -> None:
    """Handle 'ftm pipeline create' command."""
    pipeline_mgr = PipelineManager()
    pipeline = pipeline_mgr.create_pipeline(args.name)
    print(f"Pipeline created: {pipeline.name} (ID: {pipeline.pipeline_id})")


def cmd_pipeline_list(args: argparse.Namespace) -> None:
    """Handle 'ftm pipeline list' command."""
    pipeline_mgr = PipelineManager()
    pipelines = pipeline_mgr.list_pipelines()

    if not pipelines:
        print("No pipelines found.")
        return

    print(f"{'Name':<30} {'ID':<20} {'Opportunities':<15}")
    print("-" * 65)
    for p in pipelines:
        print(f"{p.name:<30} {p.pipeline_id:<20} {len(p.opportunities):<15}")


def cmd_pipeline_stats(args: argparse.Namespace) -> None:
    """Handle 'ftm pipeline stats' command."""
    pipeline_mgr = PipelineManager()
    stats = pipeline_mgr.get_pipeline_stats(args.id)

    print(f"Pipeline Stats: {stats['name']}")
    print(f"  Total Opportunities: {stats['total_opportunities']}")
    print(f"  Average Score: {stats['avg_score']:.2f}")
    print(f"  By Stage: {stats['by_stage']}")
    
    if stats['top_opportunities']:
        print("\n  Top Opportunities:")
        for opp in stats['top_opportunities']:
            print(f"    - {opp['client']} ({opp['service']}): {opp['score']:.2f} [{opp['stage']}]")


def cmd_match(args: argparse.Namespace) -> None:
    """Handle 'ftm match' command - advanced matching."""
    # Load SOP
    sop_manager = TemplateManager()
    sop = sop_manager.get(args.sop)
    if not sop:
        print(f"Error: SOP '{args.sop}' not found.")
        sys.exit(1)

    # Load all clients
    client_manager = TemplateManager()
    clients = client_manager.list_all()
    
    if not clients:
        print("No clients found.")
        return

    # Run matching
    matcher = OpportunityMatcher()
    matches = matcher.rank_matches(sop, clients)

    print(f"\nMatching Results for: {sop.title}")
    print(f"{'Rank':<6} {'Client':<20} {'Industry':<15} {'Score':<8} {'Keywords':<30}")
    print("-" * 80)
    for i, match in enumerate(matches, 1):
        keywords = ", ".join(match['matched_keywords'][:5])
        print(f"{i:<6} {match['client_name']:<20} {match['client_industry']:<15} "
              f"{match['score']:<8.2f} {keywords:<30}")


def cmd_contract_generate(args: argparse.Namespace) -> None:
    """Handle 'ftm contract generate' command."""
    try:
        from contract_engine.contract_generator import ContractGenerator
    except ImportError:
        print("Error: Contract Engine not installed/found.")
        sys.exit(1)
        
    generator = ContractGenerator()
    contract = generator.generate_from_proposal(
        client_id="client-auto",
        proposal_id=args.match,
        amount=1500.0,
        deliverables=["Custom Deliverable 1", "Custom Deliverable 2"]
    )
    
    if args.format == "pdf":
        print(f"Contract generated for match {args.match} in PDF format (mock).")
    else:
        md = generator.format_as_markdown(contract)
        print(md)


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="FreelanceTask Manager System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # SOP commands
    sop_parser = subparsers.add_parser("sop", help="SOP management")
    sop_sub = sop_parser.add_subparsers(dest="sop_command")

    sop_create = sop_sub.add_parser("create", help="Create a new SOP")
    sop_create.add_argument("--file", required=True, help="Path to SOP JSON file")

    sop_list = sop_sub.add_parser("list", help="List all SOPs")

    sop_edit = sop_sub.add_parser("edit", help="Edit an SOP")
    sop_edit.add_argument("name", help="SOP name")
    sop_edit.add_argument("--field", help="Field to update")
    sop_edit.add_argument("--value", help="New value")

    sop_show = sop_sub.add_parser("show", help="Show SOP details")
    sop_show.add_argument("name", help="SOP name")

    # Proposal commands
    prop_parser = subparsers.add_parser("proposal", help="Proposal generation")
    prop_sub = prop_parser.add_subparsers(dest="prop_command")

    prop_gen = prop_sub.add_parser("generate", help="Generate a proposal")
    prop_gen.add_argument("--sop", required=True, help="SOP name")
    prop_gen.add_argument("--client", required=True, help="Client name")
    prop_gen.add_argument("--format", choices=["markdown", "html"], default="markdown")
    prop_gen.add_argument("--output", help="Output file path")

    # Opportunity commands
    opp_parser = subparsers.add_parser("opportunity", help="Opportunity management")
    opp_sub = opp_parser.add_subparsers(dest="opp_command")

    opp_create = opp_sub.add_parser("create", help="Create an opportunity")
    opp_create.add_argument("--sop", required=True, help="SOP name")
    opp_create.add_argument("--client", required=True, help="Client name")
    opp_create.add_argument("--stage", default="new", help="Initial stage")
    opp_create.add_argument("--notes", default="", help="Notes")

    opp_list = opp_sub.add_parser("list", help="List opportunities")
    opp_list.add_argument("--pipeline", help="Filter by pipeline ID")

    # Pipeline commands
    pipe_parser = subparsers.add_parser("pipeline", help="Pipeline management")
    pipe_sub = pipe_parser.add_subparsers(dest="pipe_command")

    pipe_create = pipe_sub.add_parser("create", help="Create a pipeline")
    pipe_create.add_argument("--name", required=True, help="Pipeline name")

    pipe_list = pipe_sub.add_parser("list", help="List pipelines")

    pipe_stats = pipe_sub.add_parser("stats", help="Show pipeline stats")
    pipe_stats.add_argument("id", help="Pipeline ID")

    # Match command
    match_parser = subparsers.add_parser("match", help="Advanced client-offering matching")
    match_parser.add_argument("--sop", required=True, help="SOP name")

    # Contract command
    contract_parser = subparsers.add_parser("contract", help="Contract management")
    contract_sub = contract_parser.add_subparsers(dest="contract_command")
    
    contract_gen = contract_sub.add_parser("generate", help="Generate a contract")
    contract_gen.add_argument("--match", required=True, help="Match/Proposal ID")
    contract_gen.add_argument("--format", choices=["md", "pdf"], default="md", help="Output format")

    args = parser.parse_args()

    if args.command == "sop":
        if args.sop_command == "create":
            cmd_sop_create(args)
        elif args.sop_command == "list":
            cmd_sop_list(args)
        elif args.sop_command == "edit":
            cmd_sop_edit(args)
        elif args.sop_command == "show":
            cmd_sop_show(args)
        else:
            sop_parser.print_help()

    elif args.command == "proposal":
        if args.prop_command == "generate":
            cmd_proposal_generate(args)
        else:
            prop_parser.print_help()

    elif args.command == "opportunity":
        if args.opp_command == "create":
            cmd_opportunity_create(args)
        elif args.opp_command == "list":
            cmd_opportunity_list(args)
        else:
            opp_parser.print_help()

    elif args.command == "pipeline":
        if args.pipe_command == "create":
            cmd_pipeline_create(args)
        elif args.pipe_command == "list":
            cmd_pipeline_list(args)
        elif args.pipe_command == "stats":
            cmd_pipeline_stats(args)
        else:
            pipe_parser.print_help()

    elif args.command == "match":
        cmd_match(args)

    elif args.command == "contract":
        if args.contract_command == "generate":
            cmd_contract_generate(args)
        else:
            contract_parser.print_help()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
