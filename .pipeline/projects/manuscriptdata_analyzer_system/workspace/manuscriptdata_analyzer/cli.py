"""CLI entry point for manuscriptdata-analyzer."""

import click

from manuscriptdata_analyzer.database import Database


@click.group()
def cli():
    """ManuscriptData Analyzer — ingest CSV book sales data and generate analytics."""
    pass


@cli.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--db", "db_path", default=None, help="Path to SQLite database (default: manuscript_data.db)")
def import_data(filepath, db_path):
    """Import a CSV file into the SQLite database.

    Auto-detects data type (sales, demographics, or content metrics)
    based on the CSV header columns.
    """
    from manuscriptdata_analyzer.csv_parser import detect_and_parse

    db = Database(db_path)
    db.connect()

    try:
        data_type, records = detect_and_parse(filepath)
    except ValueError as exc:
        click.echo(f"Error: {exc}", err=True)
        db.close()
        raise SystemExit(1)

    count = db.insert_records(data_type, records)
    click.echo(f"Imported {count} rows of {data_type} from {filepath}")
    db.close()


@cli.command("summary")
@click.option("--db", "db_path", default=None, help="Path to SQLite database (default: manuscript_data.db)")
def summary(db_path):
    """Display summary statistics from the imported data."""
    db = Database(db_path)
    db.connect()

    click.echo("=" * 60)
    click.echo("  ManuscriptData Analyzer — Summary Report")
    click.echo("=" * 60)

    # Sales summary
    sales = db.get_sales_summary()
    if sales:
        click.echo("")
        click.echo("--- Sales Data ---")
        click.echo(f"  Total Units Sold : {sales['total_units']}")
        click.echo(f"  Total Revenue    : ${sales['total_revenue']:,.2f}")
        click.echo(f"  Avg Revenue      : ${sales['avg_revenue']:,.2f}")
        click.echo(f"  Avg Units Sold   : {sales['avg_units']:.1f}")
        click.echo(f"  Records          : {sales['record_count']}")
        if sales.get("platform_breakdown"):
            click.echo("  Platform Breakdown:")
            for platform, info in sales["platform_breakdown"].items():
                click.echo(f"    {platform}: {info['count']} records, {info['units']} units, ${info['revenue']:,.2f}")

    # Demographics summary
    demo = db.get_demographics_summary()
    if demo:
        click.echo("")
        click.echo("--- Demographics Data ---")
        click.echo(f"  Total Records    : {demo['total_records']}")
        if demo.get("age_breakdown"):
            click.echo("  Age Group Breakdown:")
            for age, info in demo["age_breakdown"].items():
                click.echo(f"    {age}: {info['count']} ({info['pct']:.1f}%), avg rating {info['avg_rating']:.2f}")
        if demo.get("gender_breakdown"):
            click.echo("  Gender Breakdown:")
            for gender, info in demo["gender_breakdown"].items():
                click.echo(f"    {gender}: {info['count']} ({info['pct']:.1f}%), avg rating {info['avg_rating']:.2f}")
        if demo.get("country_breakdown"):
            click.echo("  Country Breakdown:")
            for country, info in demo["country_breakdown"].items():
                click.echo(f"    {country}: {info['count']} ({info['pct']:.1f}%), avg rating {info['avg_rating']:.2f}")

    # Content metrics summary
    content = db.get_content_metrics_summary()
    if content:
        click.echo("")
        click.echo("--- Content Metrics ---")
        click.echo(f"  Total Chapters   : {content['total_chapters']}")
        click.echo(f"  Total Word Count : {content['total_words']:,}")
        click.echo(f"  Avg Word Count   : {content['avg_words']:,}")
        click.echo(f"  Avg Read-Through : {content['avg_read_through']:.2f}%")
        click.echo(f"  Avg Completion   : {content['avg_completion']:.2f}%")
        if content.get("chapter_details"):
            click.echo("  Chapter Details:")
            for ch in content["chapter_details"]:
                click.echo(f"    Ch {ch['chapter']}: {ch['word_count']:,} words, "
                           f"read-through {ch['read_through']:.2f}%, completion {ch['completion']:.2f}%")

    click.echo("")
    click.echo("=" * 60)

    db.close()


# ──────────────────────────────────────────────
# Phase 2 CLI commands
# ──────────────────────────────────────────────

@cli.command("analyze")
@click.option("--db", "db_path", default=None, help="Path to SQLite database")
@click.option("--window", "window", default=3, help="Rolling average window (default: 3)")
def analyze(db_path, window):
    """Run full analytics: trends, rankings, demographics, and report."""
    db = Database(db_path)
    db.connect()
    try:
        from manuscriptdata_analyzer.analytics import run_full_analysis
        report = run_full_analysis(db)
        click.echo(report)
    finally:
        db.close()


@cli.command("export")
@click.argument("output_path", type=click.Path())
@click.option("--db", "db_path", default=None, help="Path to SQLite database")
@click.option("--type", "data_type", default="sales", type=click.Choice(["sales", "demographics", "content_metrics"]),
              help="Data type to export (default: sales)")
def export_csv(output_path, db_path, data_type):
    """Export analytics data to a CSV file."""
    db = Database(db_path)
    db.connect()
    try:
        from manuscriptdata_analyzer.analytics import ReportGenerator
        generator = ReportGenerator(db)
        generator.export_csv(output_path, data_type)
        click.echo(f"Exported {data_type} data to {output_path}")
    finally:
        db.close()


@cli.command("trends")
@click.option("--db", "db_path", default=None, help="Path to SQLite database")
@click.option("--window", "window", default=3, help="Rolling average window (default: 3)")
def trends(db_path, window):
    """Show trend analysis (spikes and drops) for all books."""
    db = Database(db_path)
    db.connect()
    try:
        from manuscriptdata_analyzer.analytics import TrendAnalyzer
        analyzer = TrendAnalyzer(db)
        trends = analyzer.analyze_all_books(window)
        for t in trends:
            click.echo(f"\nBook: {t['book_title']}")
            if t["spikes"]:
                click.echo("  Spikes:")
                for s in t["spikes"]:
                    click.echo(f"    Day {s['index']+1}: {s['value']} units ({s['deviation_pct']:+.1f}%)")
            if t["drops"]:
                click.echo("  Drops:")
                for d in t["drops"]:
                    click.echo(f"    Day {d['index']+1}: {d['value']} units ({d['deviation_pct']:+.1f}%)")
            if not t["spikes"] and not t["drops"]:
                click.echo("  No significant spikes or drops detected.")
    finally:
        db.close()


@cli.command("rankings")
@click.option("--db", "db_path", default=None, help="Path to SQLite database")
@click.option("--metric", "metric", default="revenue", type=click.Choice(["revenue", "units_sold", "engagement"]))
def rankings(db_path, metric):
    """Show book rankings by the given metric."""
    db = Database(db_path)
    db.connect()
    try:
        from manuscriptdata_analyzer.analytics import BookComparator
        comparator = BookComparator(db)
        ranked = comparator.get_book_rankings(metric)
        click.echo(f"\n{'Rank':<6}{'Book Title':<30}{'Value':>15}")
        click.echo("-" * 55)
        for i, entry in enumerate(ranked, 1):
            val = entry[metric]
            if metric == "engagement":
                val_str = f"{val:.2f}"
            else:
                val_str = f"{val:,.2f}"
            click.echo(f"{i:<6}{entry['book_title']:<30}{val_str:>15}")
    finally:
        db.close()


@cli.command("compare")
@click.option("--db", "db_path", default=None, help="Path to SQLite database")
@click.option("--books", "book_titles", multiple=True, help="Book titles to compare (can specify multiple times)")
def compare(db_path, book_titles):
    """Compare selected books across metrics."""
    db = Database(db_path)
    db.connect()
    try:
        from manuscriptdata_analyzer.analytics import BookComparator
        comparator = BookComparator(db)
        if not book_titles:
            # Auto-select top 3 by revenue
            ranked = comparator.get_book_rankings("revenue")
            book_titles = tuple(r["book_title"] for r in ranked[:3])
            click.echo(f"Auto-selected top 3 books: {', '.join(book_titles)}")
        comparison = comparator.compare_books(book_titles)
        click.echo("\nCross-Book Comparison:")
        for title, metrics in comparison.items():
            click.echo(f"  {title}:")
            for metric, value in metrics.items():
                click.echo(f"    {metric}: {value}")
    finally:
        db.close()


if __name__ == "__main__":
    cli()
