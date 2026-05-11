"""Click CLI for ReviewPulse Aggregator."""

from __future__ import annotations

import click
import logging

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """ReviewPulse Aggregator — CLI for managing review sync and analysis."""
    pass


@cli.command()
@click.argument("place_id")
@click.option("--business-name", "-n", default="", help="Business name for logging")
def sync_google_reviews(place_id: str, business_name: str):
    """Sync reviews from Google Places for a given place_id."""
    from app.tasks.ingestion_task import sync_google_reviews as celery_task
    from app.config import settings

    click.echo(f"Starting sync for place_id={place_id} (business={business_name or 'N/A'})")
    click.echo(f"Using Google API key: {settings.google_places_api_key[:4]}...")

    result = celery_task.delay(place_id, business_name or place_id)
    click.echo(f"Task submitted with ID: {result.id}")
    click.echo("Use 'celery -A app.tasks.sync_reviews inspect active' to monitor.")


@cli.command()
@click.argument("text")
def analyze_sentiment(text: str):
    """Analyze sentiment of the given text."""
    from app.services.sentiment_analyzer import analyze_sentiment

    result = analyze_sentiment(text)
    click.echo(f"Sentiment Analysis Result:")
    click.echo(f"  Compound: {result['compound']:.4f}")
    click.echo(f"  Positive: {result['pos']:.4f}")
    click.echo(f"  Neutral:  {result['neu']:.4f}")
    click.echo(f"  Negative: {result['neg']:.4f}")
    click.echo(f"  Label:    {result['label']}")


@cli.command()
def health():
    """Check the health of the application."""
    from app.config import settings
    from app.database import engine

    click.echo(f"App: {settings.app_name}")
    click.echo(f"Database: {engine.url.drivername}")
    click.echo(f"Redis: {settings.redis_url}")
    click.echo("Status: OK")


if __name__ == "__main__":
    cli()
