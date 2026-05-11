"""CLI entry point for OSINT Corp."""

from __future__ import annotations

import json
import logging
import sys
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from osint_corp.correlation import correlate, deduplicate_companies, find_companies_by_name
from osint_corp.models.entities import Company, Filing, Manifest
from osint_corp.sources.corporate_registry import CorporateRegistry
from osint_corp.sources.sec_importer import SECImporter

app = typer.Typer(
    name="osint-corp",
    help="OSINT Corp — Corporate intelligence gathering platform",
    rich_markup_mode="rich",
)

console = Console()
logger = logging.getLogger("osint-corp")


def _setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


@app.command()
def search(
    query: str = typer.Argument(..., help="Company name to search for"),
    source: str = typer.Option("all", "--source", "-s", help="Data source: sec, registry, or all"),
    jurisdiction: Optional[str] = typer.Option(None, "--jurisdiction", "-j", help="Jurisdiction filter (e.g., US-DE)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum results"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Search for a company across all data sources."""
    _setup_logging(verbose)
    console.print(f"[bold]Searching for:[/bold] {query}")

    companies: list[Company] = []

    if source in ("sec", "all"):
        console.print("[dim]Querying SEC EDGAR...[/dim]")
        with SECImporter() as importer:
            filings = importer.fetch_filings(ticker=query, limit=1)
            if filings:
                cik_company = Company(
                    name=filings[0].company_name,
                    ticker=filings[0].ticker,
                    cik=filings[0].cik,
                    source="sec",
                )
                companies.append(cik_company)
                console.print(f"  [green]✓[/green] SEC: {cik_company.name} (CIK: {cik_company.cik})")

    if source in ("registry", "all"):
        console.print("[dim]Querying corporate registries...[/dim]")
        with CorporateRegistry() as registry:
            reg_companies = registry.search_by_name(query, jurisdiction, limit)
            companies.extend(reg_companies)
            for comp in reg_companies:
                console.print(f"  [green]✓[/green] Registry: {comp.name} ({comp.jurisdiction})")

    if not companies:
        console.print("[yellow]No results found.[/yellow]")
        return

    # Deduplicate
    unique = deduplicate_companies(companies)
    console.print(f"\n[bold]Found {len(unique)} unique company(ies):[/bold]")

    table = Table(title="Search Results")
    table.add_column("Name", style="cyan")
    table.add_column("Ticker", style="green")
    table.add_column("Jurisdiction", style="yellow")
    table.add_column("Source", style="magenta")
    table.add_column("CIK", style="blue")

    for comp in unique:
        table.add_row(
            comp.name or "",
            comp.ticker or "",
            comp.jurisdiction or "",
            comp.source or "",
            comp.cik or "",
        )

    console.print(table)

    if output:
        data = [c.to_dict() for c in unique]
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"\n[bold]Results saved to {output}[/bold]")


@app.command()
def filings(
    ticker: str = typer.Argument(..., help="Company ticker symbol"),
    filing_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filing type (10-K, 10-Q, 8-K, etc.)"),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum filings"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file (JSON)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Fetch SEC filings for a company."""
    _setup_logging(verbose)
    console.print(f"[bold]Fetching filings for:[/bold] {ticker}")

    with SECImporter() as importer:
        if filing_type:
            filings = importer.fetch_filings(ticker, filing_types=[filing_type], limit=limit)
        else:
            filings = importer.fetch_filings(ticker, limit=limit)

    if not filings:
        console.print("[yellow]No filings found.[/yellow]")
        return

    console.print(f"\n[bold]Found {len(filings)} filing(s):[/bold]")

    table = Table(title="SEC Filings")
    table.add_column("Type", style="cyan")
    table.add_column("Date", style="green")
    table.add_column("Accession #", style="yellow")
    table.add_column("Company", style="magenta")

    for filing in filings:
        table.add_row(
            filing.filing_type,
            filing.filing_date or "",
            filing.accession_number,
            filing.company_name,
        )

    console.print(table)

    if output:
        data = [f.to_dict() for f in filings]
        with open(output, "w") as f:
            json.dump(data, f, indent=2)
        console.print(f"\n[bold]Results saved to {output}[/bold]")


@app.command()
def version() -> None:
    """Display the OSINT Corp version."""
    console.print("[bold]OSINT Corp[/bold] v1.0.0")


@app.command()
def manifest(
    companies_file: str = typer.Argument(..., help="JSON file with companies"),
    filings_file: str = typer.Argument(..., help="JSON file with filings"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output manifest file (JSON)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Generate a manifest from companies and filings data."""
    _setup_logging(verbose)
    console.print("[bold]Generating manifest...[/bold]")

    with open(companies_file) as f:
        company_data = json.load(f)
    with open(filings_file) as f:
        filing_data = json.load(f)

    companies = [Company(**c) for c in company_data]
    filings = [Filing(**f) for f in filing_data]

    relationships = correlate(companies, filings)
    manifest = Manifest(entities=companies, filings=filings, relationships=relationships)

    console.print(f"\n[bold]Manifest generated:[/bold]")
    console.print(f"  Entities: {len(manifest.entities)}")
    console.print(f"  Filings: {len(manifest.filings)}")
    console.print(f"  Relationships: {len(manifest.relationships)}")

    if output:
        with open(output, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        console.print(f"\n[bold]Manifest saved to {output}[/bold]")


@app.command()
def correlate(
    companies_file: str = typer.Argument(..., help="JSON file with companies"),
    filings_file: str = typer.Argument(..., help="JSON file with filings"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output manifest file (JSON)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Correlate companies and filings into a manifest."""
    _setup_logging(verbose)
    console.print("[bold]Correlating data...[/bold]")

    with open(companies_file) as f:
        company_data = json.load(f)
    with open(filings_file) as f:
        filing_data = json.load(f)

    companies = [Company(**c) for c in company_data]
    filings = [Filing(**f) for f in filing_data]

    manifest = correlate(companies, filings)

    console.print(f"\n[bold]Correlation complete:[/bold]")
    console.print(f"  Companies: {len(manifest.entities)}")
    console.print(f"  Filings: {len(manifest.filings)}")
    console.print(f"  Relationships: {len(manifest.relationships)}")

    if output:
        with open(output, "w") as f:
            json.dump(manifest.to_dict(), f, indent=2)
        console.print(f"\n[bold]Manifest saved to {output}[/bold]")


@app.command()
def match(
    name: str = typer.Argument(..., help="Name to match against"),
    companies_file: str = typer.Argument(..., help="JSON file with companies"),
    threshold: float = typer.Option(0.7, "--threshold", "-t", help="Minimum similarity (0.0-1.0)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
) -> None:
    """Find companies matching a name."""
    _setup_logging(verbose)

    with open(companies_file) as f:
        company_data = json.load(f)
    companies = [Company(**c) for c in company_data]

    matches = find_companies_by_name(name, companies, threshold)

    if not matches:
        console.print("[yellow]No matches found.[/yellow]")
        return

    console.print(f"\n[bold]Matches for '{name}':[/bold]")
    table = Table(title="Name Matches")
    table.add_column("Name", style="cyan")
    table.add_column("Ticker", style="green")
    table.add_column("Score", style="yellow")

    for comp, score in matches:
        table.add_row(comp.name or "", comp.ticker or "", f"{score:.2f}")

    console.print(table)


def main() -> None:
    """Entry point for the osint-corp CLI."""
    app()


if __name__ == "__main__":
    main()
