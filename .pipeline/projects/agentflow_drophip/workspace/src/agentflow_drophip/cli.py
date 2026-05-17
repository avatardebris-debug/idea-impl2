"""CLI module for AgentFlow."""

from __future__ import annotations

import click
from agentflow_drophip.orchestrator import Orchestrator


@click.group()
@click.version_option(version="0.1.0")
def main():
    """AgentFlow - AI-powered dropshipping automation system."""
    pass


@main.command()
@click.argument("description")
@click.option("--output", "-o", type=click.Path(), help="Output file for results")
def setup(description: str, output: str | None):
    """Set up a new dropshipping business."""
    orchestrator = Orchestrator()
    spec = orchestrator.setup_business(description)

    click.echo(f"Business spec created:")
    click.echo(f"  Niche: {spec.niche}")
    click.echo(f"  Supplier: {spec.supplier_type.value}")
    click.echo(f"  Storefront: {spec.storefront_type.value}")
    click.echo(f"  Fulfillment: {spec.fulfillment_type.value}")
    click.echo(f"  Pricing: {spec.pricing_strategy.value}")

    if output:
        import json
        with open(output, "w") as f:
            json.dump(spec.to_dict(), f, indent=2)
        click.echo(f"\nSpec saved to {output}")


@main.command()
@click.option("--spec", "-s", type=click.Path(), help="Path to business spec file")
def run(spec: str | None):
    """Run the full dropshipping workflow."""
    orchestrator = Orchestrator()

    if spec:
        import json
        with open(spec) as f:
            spec_dict = json.load(f)
        from agentflow_drophip.models.business_spec import BusinessSpec
        business_spec = BusinessSpec.from_dict(spec_dict)
    else:
        business_spec = None

    result = orchestrator.run_full_workflow(business_spec)

    if result.is_success:
        click.echo("Workflow completed successfully!")
        click.echo(f"  Tasks: {len(result.data)}")
    else:
        click.echo(f"Workflow failed: {result.error}")
        raise click.Abort()


@main.command()
@click.option("--spec", "-s", type=click.Path(), help="Path to business spec file")
def source(spec: str | None):
    """Source products for the business."""
    from agentflow_drophip.agents.sourcing_agent import SourcingAgent

    agent = SourcingAgent()

    if spec:
        import json
        with open(spec) as f:
            spec_dict = json.load(f)
        from agentflow_drophip.models.business_spec import BusinessSpec
        business_spec = BusinessSpec.from_dict(spec_dict)
        result = agent.execute(spec=business_spec)
    else:
        result = agent.execute()

    if result.is_success:
        click.echo(f"Found {len(result.products)} products:")
        for product in result.products[:5]:
            click.echo(f"  - {product['name']}: ${product['price']}")
    else:
        click.echo(f"Sourcing failed: {result.error}")
        raise click.Abort()


if __name__ == "__main__":
    main()
