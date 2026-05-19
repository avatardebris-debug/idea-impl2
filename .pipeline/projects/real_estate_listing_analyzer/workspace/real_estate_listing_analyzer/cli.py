"""
real_estate_listing_analyzer/cli.py
CLI entrypoint: fetch, analyze, and report on property listings.

Usage:
    real-estate-analyzer fetch --zip 90210 --count 40
    real-estate-analyzer analyze --zip 90210
    real-estate-analyzer report --zip 90210 --format csv --out ./report.csv
    real-estate-analyzer report --zip 90210 --format md
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import sys
import textwrap


def _fetcher(args: argparse.Namespace) -> None:
    from .fetcher import ZillowFetcher, save_cache

    print(f"Fetching listings for ZIP {args.zip} (count={args.count})...")
    fetcher = ZillowFetcher()
    listings = fetcher.search_by_zip(args.zip, count=args.count)
    raw = [l.raw for l in listings]
    cache_path = save_cache(args.zip, raw)
    print(f"  Fetched {len(listings)} listings → cached at {cache_path}")
    for l in listings[:5]:
        print(f"  {l.address}, {l.city} — ${l.price:,} | {l.sqft} sqft | {l.bedrooms}bd/{l.bathrooms}ba")
    if len(listings) > 5:
        print(f"  ... and {len(listings) - 5} more")


def _analyze(args: argparse.Namespace) -> None:
    from .fetcher import ZillowFetcher, load_latest_cache
    from .analyzer import TrendAnalyzer

    print(f"Analyzing market for ZIP {args.zip}...")

    # Try cache first; fall back to live fetch
    cached = load_latest_cache(args.zip)
    if cached:
        print(f"  Using {len(cached)} cached listings")
        from .fetcher import Listing
        from dataclasses import fields as dc_fields
        listings = []
        for raw in cached:
            from .fetcher import ZillowFetcher as _ZF
            listings.append(_ZF()._parse(raw))
    else:
        print("  No cache found — fetching live data...")
        fetcher = ZillowFetcher()
        listings = fetcher.search_by_zip(args.zip, count=40)

    analyzer = TrendAnalyzer()
    result = analyzer.analyze(listings, zip_code=args.zip)

    print(f"\n{'='*50}")
    print(f"  Market Analysis: ZIP {result.zip_code}")
    print(f"{'='*50}")
    print(f"  Listings analyzed:  {result.listing_count}")
    print(f"  Median price:       ${result.median_price:,.0f}")
    print(f"  Median $/sqft:      ${result.median_price_per_sqft:,.2f}")
    print(f"  Price trend (slope):{result.price_slope_30d:+.4f} $/sqft/day")
    print(f"  Median DOM:         {result.median_dom:.0f} days")
    print(f"  DOM std dev:        {result.dom_stddev:.1f} days")
    print(f"  List/Zestimate:     {result.list_to_sale_ratio:.3f}x")
    print(f"  Neighborhood score: {result.neighborhood_score}/100")
    print(f"{'='*50}\n")

    # Flag deals (>5% below Zestimate)
    deals = [l for l in listings if l.zestimate > 0 and l.price < l.zestimate * 0.95]
    if deals:
        print(f"  🏷  {len(deals)} potential deals (>5% below Zestimate):")
        for d in deals[:5]:
            discount = round((1 - d.price / d.zestimate) * 100, 1)
            print(f"    {d.address}: ${d.price:,} vs Zestimate ${d.zestimate:,} ({discount}% off)")


def _report(args: argparse.Namespace) -> None:
    from .fetcher import ZillowFetcher, load_latest_cache
    from .analyzer import TrendAnalyzer

    cached = load_latest_cache(args.zip)
    if cached:
        from .fetcher import ZillowFetcher as _ZF
        listings = [_ZF()._parse(r) for r in cached]
    else:
        fetcher = ZillowFetcher()
        listings = fetcher.search_by_zip(args.zip, count=40)

    analyzer = TrendAnalyzer()
    result = analyzer.analyze(listings, zip_code=args.zip)
    out_path = pathlib.Path(args.out) if args.out else None

    if args.format == "csv":
        rows = [
            {
                "address": l.address, "city": l.city, "zip": l.zip_code,
                "price": l.price, "sqft": l.sqft, "beds": l.bedrooms,
                "baths": l.bathrooms, "price_per_sqft": l.price_per_sqft,
                "days_on_market": l.days_on_market, "zestimate": l.zestimate,
                "below_zestimate_pct": round(
                    (1 - l.price / l.zestimate) * 100, 1
                ) if l.zestimate > 0 else "",
            }
            for l in listings
        ]
        target = out_path or pathlib.Path(f"real_estate_{args.zip}.csv")
        with open(target, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
        print(f"  CSV report written to {target} ({len(rows)} rows)")

    elif args.format == "md":
        lines = [
            f"# Real Estate Market Report — ZIP {args.zip}",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| Listings | {result.listing_count} |",
            f"| Median Price | ${result.median_price:,.0f} |",
            f"| Median $/sqft | ${result.median_price_per_sqft:,.2f} |",
            f"| Median DOM | {result.median_dom:.0f} days |",
            f"| Neighborhood Score | {result.neighborhood_score}/100 |",
            "",
            "## Listings",
            "",
            "| Address | Price | $/sqft | Beds | Baths | DOM |",
            "|---|---|---|---|---|---|",
        ]
        for l in sorted(listings, key=lambda x: x.price_per_sqft):
            lines.append(
                f"| {l.address} | ${l.price:,} | ${l.price_per_sqft:.0f} "
                f"| {l.bedrooms} | {l.bathrooms} | {l.days_on_market} |"
            )
        content = "\n".join(lines) + "\n"
        target = out_path or pathlib.Path(f"real_estate_{args.zip}.md")
        target.write_text(content, encoding="utf-8")
        print(f"  Markdown report written to {target}")

    elif args.format == "json":
        data = {
            "summary": {
                "zip": result.zip_code,
                "listing_count": result.listing_count,
                "median_price": result.median_price,
                "median_price_per_sqft": result.median_price_per_sqft,
                "neighborhood_score": result.neighborhood_score,
            },
            "listings": [
                {
                    "address": l.address, "price": l.price, "sqft": l.sqft,
                    "beds": l.bedrooms, "baths": l.bathrooms,
                    "price_per_sqft": l.price_per_sqft,
                    "days_on_market": l.days_on_market,
                }
                for l in listings
            ],
        }
        target = out_path or pathlib.Path(f"real_estate_{args.zip}.json")
        target.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"  JSON report written to {target}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real Estate Listing Analyzer — fetch, analyze, and report",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
            Examples:
              real-estate-analyzer fetch --zip 90210 --count 40
              real-estate-analyzer analyze --zip 78701
              real-estate-analyzer report --zip 78701 --format csv --out ./austin.csv
              real-estate-analyzer report --zip 78701 --format md
        """),
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # fetch
    p_fetch = sub.add_parser("fetch", help="Fetch and cache listings for a ZIP code")
    p_fetch.add_argument("--zip", required=True, help="ZIP code")
    p_fetch.add_argument("--count", type=int, default=40, help="Max listings (default 40)")

    # analyze
    p_analyze = sub.add_parser("analyze", help="Analyze cached or live listings")
    p_analyze.add_argument("--zip", required=True, help="ZIP code")

    # report
    p_report = sub.add_parser("report", help="Generate a market report")
    p_report.add_argument("--zip", required=True, help="ZIP code")
    p_report.add_argument("--format", choices=["csv", "md", "json"], default="csv")
    p_report.add_argument("--out", default=None, help="Output file path")

    args = parser.parse_args()
    {
        "fetch": _fetcher,
        "analyze": _analyze,
        "report": _report,
    }[args.command](args)


if __name__ == "__main__":
    main()
