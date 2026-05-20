"""
real_estate_listing_analyzer/report.py
Report generation (CSV, PDF, Markdown) and deal-alert engine.
"""
from __future__ import annotations

import csv
import io
import math
import statistics
from dataclasses import dataclass
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .fetcher import Listing
    from .analyzer import TrendResult

# ---------------------------------------------------------------------------
# AlertEngine
# ---------------------------------------------------------------------------


@dataclass
class DealAlert:
    """A listing flagged as a potential deal."""
    listing: Listing
    trend: TrendResult
    discount_pct: float  # how far below trend (positive = deal)


class AlertEngine:
    """Flag listings priced >5% below the neighborhood trend."""

    def __init__(self, threshold: float = 5.0):
        self.threshold = threshold  # percentage

    def find_deals(self, listings: List[Listing], trend: TrendResult) -> List[DealAlert]:
        """Return listings whose price_per_sqft is below trend median by >threshold%."""
        deals: List[DealAlert] = []
        if trend.median_price_per_sqft == 0:
            return deals

        for listing in listings:
            if listing.price_per_sqft is None or listing.price_per_sqft == 0:
                continue
            discount_pct = (trend.median_price_per_sqft - listing.price_per_sqft) / trend.median_price_per_sqft * 100
            if discount_pct > self.threshold:
                deals.append(DealAlert(listing=listing, trend=trend, discount_pct=discount_pct))
        return deals


# ---------------------------------------------------------------------------
# ReportBuilder
# ---------------------------------------------------------------------------


class ReportBuilder:
    """Generate CSV, PDF, and Markdown reports from listings + trend data."""

    def __init__(self, trend: TrendResult, deals: List[DealAlert] | None = None):
        self.trend = trend
        self.deals = deals or []

    # ---- CSV ---------------------------------------------------------------

    def build_csv(self, listings: List[Listing]) -> str:
        """Return CSV content as a string. One row per listing with all metrics."""
        output = io.StringIO()
        writer = csv.writer(output)
        header = [
            "zpid", "address", "city", "state", "zip_code",
            "bedrooms", "bathrooms", "sqft", "price", "price_per_sqft",
            "days_on_market", "zestimate", "list_to_zestimate_ratio",
            "neighborhood_score", "trend_slope_30d", "trend_slope_90d",
            "trend_slope_365d", "median_dom", "dom_std",
        ]
        writer.writerow(header)

        for listing in listings:
            ratio = listing.price / listing.zestimate if listing.zestimate else 0.0
            writer.writerow([
                listing.zpid,
                listing.address,
                listing.city,
                listing.state,
                listing.zip_code,
                listing.bedrooms,
                listing.bathrooms,
                listing.sqft,
                listing.price,
                listing.price_per_sqft,
                listing.days_on_market,
                listing.zestimate,
                round(ratio, 4),
                round(self.trend.neighborhood_score, 2),
                round(self.trend.price_slope_30d, 4),
                round(self.trend.price_slope_90d, 4),
                round(self.trend.price_slope_365d, 4),
                round(self.trend.median_dom, 2),
                round(self.trend.dom_std, 2),
            ])
        return output.getvalue()

    # ---- PDF ---------------------------------------------------------------

    def build_pdf(self, listings: List[Listing]) -> bytes:
        """Return PDF bytes: CMA summary page + price trend chart."""
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from io import BytesIO

        # ---- CMA Summary PDF ----
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=letter, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph("Comparative Market Analysis", styles["Title"]))
        elements.append(Spacer(1, 12))

        # Trend summary
        summary_data = [
            ["Metric", "Value"],
            ["Zip Code", self.trend.zip_code],
            ["Listing Count", str(self.trend.listing_count)],
            ["Median Price", f"${self.trend.median_price:,.0f}"],
            ["Median Price/sqft", f"${self.trend.median_price_per_sqft:,.2f}"],
            ["30-Day Trend ($/sqft/day)", f"{self.trend.price_slope_30d:+.4f}"],
            ["90-Day Trend ($/sqft/day)", f"{self.trend.price_slope_90d:+.4f}"],
            ["365-Day Trend ($/sqft/day)", f"{self.trend.price_slope_365d:+.4f}"],
            ["Median DOM", f"{self.trend.median_dom:.1f} days"],
            ["DOM Std Dev", f"{self.trend.dom_std:.1f} days"],
            ["List-to-Sale Ratio", f"{self.trend.list_to_sale_ratio:.4f}"],
            ["Neighborhood Score", f"{self.trend.neighborhood_score:.1f}/100"],
        ]
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 24))

        # Deals section
        if self.deals:
            elements.append(Paragraph("Deal Alerts", styles["Heading2"]))
            deal_data = [["Address", "Price/sqft", "Discount %"]]
            for deal in self.deals:
                deal_data.append([
                    deal.listing.address,
                    f"${deal.listing.price_per_sqft:,.2f}",
                    f"{deal.discount_pct:.1f}%",
                ])
            deal_table = Table(deal_data)
            deal_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.green),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            elements.append(deal_table)
            elements.append(Spacer(1, 24))

        # ---- Price Trend Chart ----
        chart_buf = BytesIO()
        fig, ax = plt.subplots(figsize=(8, 4))
        prices = [l.price_per_sqft for l in listings if l.price_per_sqft is not None]
        if prices:
            ax.plot(range(1, len(prices) + 1), prices, "o-", label="Price/sqft")
            ax.axhline(y=self.trend.median_price_per_sqft, color="r", linestyle="--",
                       label=f"Median ${self.trend.median_price_per_sqft:,.2f}")
            ax.set_xlabel("Listing Index")
            ax.set_ylabel("Price per sqft ($)")
            ax.set_title("Price per Square Foot Trend")
            ax.legend()
        plt.tight_layout()
        plt.savefig(chart_buf, format="png", dpi=100)
        plt.close(fig)
        chart_buf.seek(0)

        # Add chart to PDF
        from reportlab.platypus import Image
        elements.append(Paragraph("Price Trend Chart", styles["Heading2"]))
        img = Image(chart_buf)
        img.drawWidth = 500
        img.drawHeight = 250
        elements.append(img)

        doc.build(elements)
        return buf.getvalue()

    # ---- Markdown ------------------------------------------------------------

    def build_markdown(self, listings: List[Listing]) -> str:
        """Return Markdown content: ranked listing table with neighborhood highlights."""
        lines = []
        lines.append("# Comparative Market Analysis Report")
        lines.append("")
        lines.append(f"**Zip Code:** {self.trend.zip_code}  ")
        lines.append(f"**Listings Analyzed:** {self.trend.listing_count}  ")
        lines.append(f"**Median Price:** ${self.trend.median_price:,.0f}  ")
        lines.append(f"**Median Price/sqft:** ${self.trend.median_price_per_sqft:,.2f}  ")
        lines.append(f"**Neighborhood Score:** {self.trend.neighborhood_score:.1f}/100  ")
        lines.append("")

        # Ranked table
        sorted_listings = sorted(listings, key=lambda l: l.price_per_sqft or 0)
        lines.append("## Ranked Listings (by price/sqft — lowest first)")
        lines.append("")
        lines.append("| Rank | Address | City | Beds | Baths | Sqft | Price | Price/sqft | DOM | Zestimate | Ratio |")
        lines.append("|------|---------|------|------|-------|------|-------|------------|-----|-----------|-------|")
        for i, listing in enumerate(sorted_listings, 1):
            ratio = listing.price / listing.zestimate if listing.zestimate else 0.0
            lines.append(
                f"| {i} | {listing.address} | {listing.city} | "
                f"{listing.bedrooms} | {listing.bathrooms} | {listing.sqft} | "
                f"${listing.price:,} | ${listing.price_per_sqft:,.2f} | "
                f"{listing.days_on_market} | ${listing.zestimate:,} | {ratio:.4f} |"
            )
        lines.append("")

        # Deal alerts
        if self.deals:
            lines.append("## Deal Alerts")
            lines.append("")
            lines.append("| Address | Price/sqft | Discount % |")
            lines.append("|---------|------------|------------|")
            for deal in self.deals:
                lines.append(
                    f"| {deal.listing.address} | ${deal.listing.price_per_sqft:,.2f} | {deal.discount_pct:.1f}% |"
                )
            lines.append("")

        return "\n".join(lines)
