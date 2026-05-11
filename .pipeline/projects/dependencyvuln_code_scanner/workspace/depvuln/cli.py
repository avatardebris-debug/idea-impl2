"""CLI entry point for depvuln."""
import sys
import os
import json
import click
from typing import Any

from depvuln.parsers import NpmParser, PipParser, MavenParser, CargoParser, GoParser, PodfileParser
from depvuln.cve import CveFetcher, NvdFetcher, CveDataMerger
from depvuln.scorer import VulnScorer
from depvuln.reports import JsonReportGenerator, TextReportGenerator, HtmlReportGenerator
from depvuln.config import ConfigManager


@click.group()
@click.version_option("0.1.0", prog_name="depvuln")
def cli():
    """depvuln - Dependency vulnerability scanner."""
    pass


def _scan_file(path: str, osv_fetcher: CveFetcher, nvd_fetcher: NvdFetcher, merger: CveDataMerger, scorer: VulnScorer, config: ConfigManager) -> list[dict]:
    """Scan a single file for vulnerabilities."""
    path = os.path.abspath(path)
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    # Determine parser
    if path.endswith("requirements.txt") or path.endswith("Pipfile") or path.endswith("setup.py"):
        parser = PipParser()
    elif path.endswith("package-lock.json") or path.endswith("yarn.lock") or path.endswith("package.json"):
        parser = NpmParser()
    elif path.endswith("pom.xml") or path.endswith("build.gradle") or path.endswith("build.gradle.kts"):
        parser = MavenParser()
    elif path.endswith("Cargo.toml"):
        parser = CargoParser()
    elif path.endswith("go.mod"):
        parser = GoParser()
    elif path.endswith("Podfile"):
        parser = PodfileParser()
    else:
        raise ValueError(f"Unsupported file type: {path}")

    # Parse dependencies
    deps = parser.parse(path)

    # Fetch CVE data
    findings = []
    for dep in deps:
        # Fetch from OSV
        osv_data = osv_fetcher.fetch(dep["name"], dep["version"], dep["ecosystem"])
        # Fetch from NVD
        nvd_data = nvd_fetcher.fetch(dep["name"])
        
        # Merge data
        merged = merger.merge(osv_data, nvd_data)
        
        # Add to findings
        for cve in merged:
            findings.append({
                "package": dep["name"],
                "version": dep["version"],
                "ecosystem": dep["ecosystem"],
                "cve": cve,
            })

    # Score findings
    scored = scorer.score(findings)
    return scored


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.File("w"), default=None, help="Output file.")
@click.option("--format", "output_format", type=click.Choice(["text", "json", "html"]), default=None, help="Output format.")
@click.option("--cache/--no-cache", default=None, help="Enable/disable caching.")
@click.option("--threshold", "-t", type=click.Choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"]), default=None, help="Severity threshold.")
def scan(path, output, output_format, cache, threshold):
    """Scan a dependency file for vulnerabilities."""
    config = ConfigManager()

    # Override config with CLI flags
    if output_format is None:
        output_format = config.get("output_format", "text")
    if cache is None:
        cache = config.get("cache_enabled", True)
    if threshold is None:
        threshold = config.get("severity_threshold", "LOW")

    # Initialize components
    osv_fetcher = CveFetcher(cache_enabled=cache, cache_dir=config.get("cache_dir"))
    nvd_fetcher = NvdFetcher(cache_enabled=cache, cache_dir=config.get("cache_dir"))
    merger = CveDataMerger()
    scorer = VulnScorer(threshold=threshold)

    # Scan
    findings = _scan_file(path, osv_fetcher, nvd_fetcher, merger, scorer, config)

    # Generate report
    if output_format == "json":
        report_gen = JsonReportGenerator()
        report = report_gen.generate(findings)
    elif output_format == "html":
        report_gen = HtmlReportGenerator()
        report = report_gen.generate(findings)
    else:
        report_gen = TextReportGenerator()
        report = report_gen.generate(findings)

    # Output
    if output:
        output.write(report)
    else:
        click.echo(report)

    # Exit with code based on findings
    if findings:
        sys.exit(1)
    sys.exit(0)


@cli.command()
def config_show():
    """Show current configuration."""
    config = ConfigManager()
    click.echo(json.dumps(config.to_dict(), indent=2))


@cli.command()
@click.option("--key", required=True, help="Config key to set.")
@click.option("--value", required=True, help="Config value to set.")
def config_set(key, value):
    """Set a configuration value."""
    config = ConfigManager()
    # Try to parse value as JSON
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
    config.set(key, parsed_value)
    config.save()
    click.echo(f"Set {key} = {parsed_value}")


if __name__ == "__main__":
    cli()
