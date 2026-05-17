"""Report formatting — Markdown and plain text outputs."""

from typing import List

from src.models.product import Product


class ReportFormatter:
    """Formats extracted products into human-readable reports."""

    def format(self, products: List[Product], store_url: str = "", fmt: str = "markdown") -> str:
        """Format products into a report.

        Args:
            products: List of extracted products.
            store_url: The store URL that was scanned.
            fmt: Output format — 'markdown', 'text', or 'comparative'.

        Returns:
            Formatted report string.
        """
        if fmt == "markdown":
            return self._format_markdown(products, store_url)
        elif fmt == "text":
            return self._format_text(products, store_url)
        elif fmt == "comparative":
            return self._format_comparative(products, store_url)
        else:
            return self._format_markdown(products, store_url)

    def _format_markdown(self, products: List[Product], store_url: str = "") -> str:
        """Format products as Markdown."""
        lines = []
        lines.append("# Dropsearch Report")
        lines.append("")
        if store_url:
            lines.append(f"**Store URL:** {store_url}")
        lines.append(f"**Products Found:** {len(products)}")
        lines.append("")
        lines.append("---")
        lines.append("")

        if not products:
            lines.append("*No products found.*")
            return "\n".join(lines)

        for i, product in enumerate(products, 1):
            lines.append(f"## Product {i}")
            lines.append("")
            lines.append(f"**Name:** {product.name}")
            lines.append(f"**Price:** ${product.price:.2f}")
            if product.description:
                lines.append(f"**Description:** {product.description}")
            if product.image_url:
                lines.append(f"**Image:** ![product]({product.image_url})")
            if product.url:
                lines.append(f"**URL:** {product.url}")
            lines.append("")
            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def _format_text(self, products: List[Product], store_url: str = "") -> str:
        """Format products as plain text."""
        lines = []
        lines.append("=" * 60)
        lines.append("DROPSEARCH REPORT")
        lines.append("=" * 60)
        lines.append("")
        if store_url:
            lines.append(f"Store URL: {store_url}")
        lines.append(f"Products Found: {len(products)}")
        lines.append("")
        lines.append("-" * 60)
        lines.append("")

        if not products:
            lines.append("No products found.")
            return "\n".join(lines)

        for i, product in enumerate(products, 1):
            lines.append(f"Product {i}:")
            lines.append(f"  Name:    {product.name}")
            lines.append(f"  Price:   ${product.price:.2f}")
            if product.description:
                lines.append(f"  Desc:    {product.description}")
            if product.image_url:
                lines.append(f"  Image:   {product.image_url}")
            if product.url:
                lines.append(f"  URL:     {product.url}")
            lines.append("")
            lines.append("-" * 60)
            lines.append("")

        return "\n".join(lines)

    def _format_comparative(self, products: List[Product], store_url: str = "") -> str:
        """Format products as a comparative report (compact table format)."""
        lines = []
        lines.append("# Dropsearch Comparative Report")
        lines.append("")
        if store_url:
            lines.append(f"**Store URL:** {store_url}")
        lines.append(f"**Products Found:** {len(products)}")
        lines.append("")
        lines.append("| # | Name | Price | Description |")
        lines.append("|---|------|-------|-----------------|")

        if not products:
            lines.append("| | *No products found.* | | |")
        else:
            for i, product in enumerate(products, 1):
                desc = product.description[:50] + "..." if product.description and len(product.description) > 50 else (product.description or "")
                lines.append(f"| {i} | {product.name} | ${product.price:.2f} | {desc} |")

        lines.append("")
        return "\n".join(lines)
