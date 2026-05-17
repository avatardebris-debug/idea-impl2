"""Comparative report formatting for competitor analysis."""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class ComparativeReportFormatter:
    """Formats competitor analysis results into comparative reports."""

    def format_comparison(
        self,
        stores: List,
        overlaps: List[dict],
        margins: List[dict],
        price_gaps: List[dict],
        insights: List[str],
    ) -> str:
        """Format a comprehensive comparative report.

        Args:
            stores: List of StoreAnalysis objects.
            overlaps: List of product overlap dictionaries.
            margins: List of margin analysis dictionaries.
            price_gaps: List of price gap dictionaries.
            insights: List of insight strings.

        Returns:
            Formatted report string.
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append("COMPETITOR ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")

        # Store overview
        lines.append("STORE OVERVIEW")
        lines.append("-" * 40)
        for i, store in enumerate(stores, 1):
            lines.append(f"{i}. {store.stores_url}")
            lines.append(f"   Platform: {store.platform}")
            lines.append(f"   Products: {len(store.products)}")
            lines.append(f"   Suppliers: {len(store.supplier_info)}")
            lines.append("")

        # Product overlaps
        if overlaps:
            lines.append("PRODUCT OVERLAPS")
            lines.append("-" * 40)
            for overlap in overlaps:
                lines.append(f"Product: {overlap.get('product_name', 'Unknown')}")
                lines.append(f"  Stores: {', '.join(overlap.get('stores', []))}")
                lines.append(f"  Price Range: ${overlap.get('min_price', 0):.2f} - ${overlap.get('max_price', 0):.2f}")
                lines.append("")

        # Price gaps
        if price_gaps:
            lines.append("PRICE GAPS")
            lines.append("-" * 40)
            for gap in price_gaps:
                lines.append(f"Product: {gap.get('product_name', 'Unknown')}")
                lines.append(f"  Gap: {gap.get('gap_pct', 0):.1f}%")
                lines.append(f"  Cheapest: {gap.get('min_price', 0):.2f} at {gap.get('min_store', 'Unknown')}")
                lines.append(f"  Most Expensive: {gap.get('max_price', 0):.2f} at {gap.get('max_store', 'Unknown')}")
                lines.append("")

        # Margins
        if margins:
            lines.append("MARGIN ANALYSIS")
            lines.append("-" * 40)
            for margin in margins:
                lines.append(f"Product: {margin.get('product_name', 'Unknown')}")
                lines.append(f"  Margin: {margin.get('margin_pct', 0):.1f}%")
                lines.append(f"  Supplier: {margin.get('supplier_source', 'Unknown')}")
                lines.append("")

        # Insights
        if insights:
            lines.append("KEY INSIGHTS")
            lines.append("-" * 40)
            for i, insight in enumerate(insights, 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def format_table(
        self,
        data: List[dict],
        headers: List[str],
    ) -> str:
        """Format data as a simple table.

        Args:
            data: List of dictionaries with column data.
            headers: List of column headers.

        Returns:
            Formatted table string.
        """
        if not data:
            return "No data to display."

        # Calculate column widths
        col_widths = [len(h) for h in headers]
        for row in data:
            for i, header in enumerate(headers):
                val = str(row.get(header, ""))
                col_widths[i] = max(col_widths[i], len(val))

        # Format header
        header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
        separator = "-+-".join("-" * w for w in col_widths)

        lines = [header_line, separator]

        # Format rows
        for row in data:
            row_line = " | ".join(
                str(row.get(h, "")).ljust(col_widths[i])
                for i, h in enumerate(headers)
            )
            lines.append(row_line)

        return "\n".join(lines)
