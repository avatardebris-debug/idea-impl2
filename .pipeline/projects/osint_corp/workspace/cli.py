"""CLI for OSINT Corp."""

from __future__ import annotations

import typer
from typing import Optional

app = typer.Typer(name="osint-corp", help="OSINT Corp — Corporate intelligence platform.")


@app.command("search")
def search(
    query: str = typer.Argument(..., help="Search query (company name or ticker)."),
    limit: int = typer.Option(10, "--limit", "-l", help="Maximum number of results."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path."),
):
    """Search for companies or filings."""
    from osint_corp.sources.corporate_registry import CorporateRegistry
    from osint_corp.sources.sec_importer import SECImporter

    registry = CorporateRegistry()
    importer = SECImporter()

    results = registry.search_by_name(query, limit=limit)
    if not results:
        # Fallback to SEC importer
        filings = importer.latest(query, limit=limit)
        typer.echo(f"Found {len(filings)} filings for '{query}'.")
        for f in filings:
            typer.echo(f"  {f.filing_type} ({f.filing_date}) — {f.company_name}")
    else:
        typer.echo(f"Found {len(results)} companies matching '{query}'.")
        for c in results:
            typer.echo(f"  {c.name} (ticker={c.ticker}, cik={c.cik})")

    if output:
        import json
        data = [c.to_dict() for c in results]
        with open(output, "w") as f:
            json.dump(data, f, indent=2, default=str)
        typer.echo(f"Results saved to {output}")


@app.command("correlate")
def correlate(
    companies_file: str = typer.Argument(..., help="Path to companies JSON file."),
    filings_file: str = typer.Argument(..., help="Path to filings JSON file."),
    threshold: float = typer.Option(0.8, "--threshold", "-t", help="Minimum confidence threshold."),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path."),
):
    """Correlate companies with filings."""
    import json
    from osint_corp.correlation import correlate as correlate_fn

    with open(companies_file) as f:
        companies_data = json.load(f)
    with open(filings_file) as f:
        filings_data = json.load(f)

    from osint_corp.models.entities import Company, Filing
    companies = [Company.from_dict(c) for c in companies_data]
    filings = [Filing.from_dict(f) for f in filings_data]

    relationships = correlate_fn(companies, filings, threshold=threshold)
    typer.echo(f"Found {len(relationships)} relationships.")

    if output:
        with open(output, "w") as f:
            json.dump(relationships, f, indent=2, default=str)
        typer.echo(f"Results saved to {output}")


@app.command("manifest")
def manifest(
    companies_file: str = typer.Argument(..., help="Path to companies JSON file."),
    filings_file: str = typer.Argument(..., help="Path to filings JSON file."),
    output: str = typer.Option("manifest.json", "--output", "-o", help="Output manifest file."),
):
    """Generate a manifest from companies and filings."""
    import json
    from osint_corp.correlation import correlate
    from osint_corp.models.entities import Company, Filing, Manifest

    with open(companies_file) as f:
        companies_data = json.load(f)
    with open(filings_file) as f:
        filings_data = json.load(f)

    companies = [Company.from_dict(c) for c in companies_data]
    filings = [Filing.from_dict(f) for f in filings_data]

    relationships = correlate(companies, filings, threshold=0.8)
    manifest = Manifest(entities=companies, filings=filings, relationships=relationships)

    with open(output, "w") as f:
        f.write(manifest.to_json())
    typer.echo(f"Manifest written to {output}")


@app.command("version")
def version():
    """Print the OSINT Corp version."""
    import osint_corp
    typer.echo(f"OSINT Corp v{osint_corp.__version__}")


if __name__ == "__main__":
    app()
