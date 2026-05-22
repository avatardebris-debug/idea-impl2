"""PDF report generator using reportlab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    VerticalSpacer,
)

from seo_tool.models import SEOReport
from seo_tool.reports.base import BaseReport, ReportError


class PDFReport(BaseReport):
    """Generate PDF reports using reportlab."""

    def __init__(
        self,
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
        title: Optional[str] = None,
        company_name: Optional[str] = None,
        page_size: tuple = A4,
    ):
        """Initialize PDF report.

        Args:
            report: The SEO analysis report
            score_result: The scoring results
            generated_at: Timestamp when report was generated
            title: Custom report title
            company_name: Company name for branding
            page_size: Page size tuple (default: A4)
        """
        super().__init__(report, score_result, generated_at)
        self.title = title or f"SEO Report: {report.url}"
        self.company_name = company_name or "SEO Tool"
        self.page_size = page_size

    def _get_color(self, score: int, max_score: int) -> colors.Color:
        """Get reportlab color based on score percentage."""
        if max_score == 0:
            return colors.Color(0.5, 0.5, 0.5)
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return colors.Color(0.196, 0.667, 0.271)  # Green
        elif percentage >= 50:
            return colors.Color(0.8, 0.733, 0.031)  # Yellow
        else:
            return colors.Color(0.867, 0.208, 0.271)  # Red

    def _get_score_class(self, score: int, max_score: int) -> str:
        """Get CSS class based on score percentage."""
        if max_score == 0:
            return "neutral"
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "excellent"
        elif percentage >= 50:
            return "good"
        else:
            return "poor"

    def _create_styles(self) -> tuple:
        """Create reportlab styles."""
        styles = getSampleStyleSheet()

        # Custom styles
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            textColor=colors.HexColor("#2563eb"),
            spaceAfter=20,
            alignment=1,  # Center
        )

        subtitle_style = ParagraphStyle(
            "CustomSubtitle",
            parent=styles["Normal"],
            fontSize=12,
            textColor=colors.HexColor("#6c757d"),
            spaceAfter=30,
            alignment=1,
        )

        heading_style = ParagraphStyle(
            "CustomHeading",
            parent=styles["Heading2"],
            fontSize=16,
            textColor=colors.HexColor("#2563eb"),
            spaceBefore=20,
            spaceAfter=10,
        )

        section_style = ParagraphStyle(
            "CustomSection",
            parent=styles["Heading3"],
            fontSize=14,
            textColor=colors.HexColor("#2563eb"),
            spaceBefore=15,
            spaceAfter=10,
        )

        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#212529"),
            leading=12,
        )

        return {
            "title": title_style,
            "subtitle": subtitle_style,
            "heading": heading_style,
            "section": section_style,
            "normal": normal_style,
        }

    def _create_score_table(self, score: int, max_score: int, styles: dict) -> list:
        """Create a table for score display."""
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        color = self._get_color(score, max_score)

        # Create a simple table to show score
        data = [
            [
                Paragraph(f"Score: <b>{score}</b>/{max_score}", styles["normal"]),
                Paragraph(f"Percentage: <b>{percentage:.1f}%</b>", styles["normal"]),
            ],
        ]

        table = Table(data, colWidths=[4 * inch, 4 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), color),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 14),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("LEFTPADDING", (0, 0), (-1, 0), 12),
                    ("RIGHTPADDING", (0, 0), (-1, 0), 12),
                ]
            )
        )

        return [table]

    def _create_category_table(self, category_scores: dict, styles: dict) -> list:
        """Create a table for category scores."""
        data = [["Category", "Score", "Status", "Reason"]]

        for name, cat in category_scores.items():
            score_class = self._get_score_class(cat["score"], cat["max"])
            status_map = {
                "excellent": "✓ Excellent",
                "good": "⚠ Good",
                "poor": "✗ Poor",
                "neutral": "○ Neutral",
            }
            status = status_map.get(score_class, "○ Neutral")

            data.append(
                [
                    Paragraph(f"<b>{name}</b>", styles["normal"]),
                    f"{cat['score']}/{cat['max']}",
                    status,
                    Paragraph(cat["reason"], styles["normal"]),
                ]
            )

        table = Table(data, colWidths=[2.5 * inch, 1 * inch, 1.5 * inch, 3 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("LEFTPADDING", (0, 0), (-1, 0), 12),
                    ("RIGHTPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )

        return [table]

    def _create_summary_table(self, summary: dict, styles: dict) -> list:
        """Create a table for page summary."""
        data = [
            ["Metric", "Value"],
            ["Word Count", str(summary.get("word_count", 0))],
            ["Link Count", str(summary.get("link_count", 0))],
            ["Internal Links", str(summary.get("internal_links", 0))],
            ["External Links", str(summary.get("external_links", 0))],
            ["Images", str(summary.get("images", 0))],
            ["Headings", str(summary.get("headings", 0))],
            ["Open Graph Tags", str(summary.get("og_tags", 0))],
        ]

        table = Table(data, colWidths=[2.5 * inch, 2.5 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("LEFTPADDING", (0, 0), (-1, 0), 12),
                    ("RIGHTPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )

        return [table]

    def _create_list_table(self, items: list, title: str, styles: dict) -> list:
        """Create a table for lists (links, images, etc.)."""
        if not items:
            return []

        data = [[title]]
        for item in items:
            data.append([item])

        table = Table(data, colWidths=[8 * inch])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563eb")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                    ("TOPPADDING", (0, 0), (-1, 0), 12),
                    ("LEFTPADDING", (0, 0), (-1, 0), 12),
                    ("RIGHTPADDING", (0, 0), (-1, 0), 12),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
                ]
            )
        )

        return [table]

    def generate(self) -> bytes:
        """Generate PDF report content.

        Returns:
            PDF bytes
        """
        styles = self._create_styles()
        elements = []

        # Title
        elements.append(Paragraph(self.title, styles["title"]))
        elements.append(Paragraph(f"Generated on {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles["subtitle"]))
        elements.append(Spacer(1, 0.2 * inch))

        # Error banner
        if self.report.fetch_error:
            elements.append(Paragraph("⚠️ Analysis Failed", styles["heading"]))
            elements.append(Paragraph(self.report.fetch_error, styles["normal"]))
            elements.append(Paragraph(f"HTTP Status: {self.report.http_status or 'N/A'}", styles["normal"]))
            elements.append(Spacer(1, 0.2 * inch))

        # Overall score
        elements.append(Paragraph("📊 Overall Score", styles["heading"]))
        elements.extend(self._create_score_table(self.score_result["total_score"], 100, styles))
        elements.append(Spacer(1, 0.2 * inch))

        # Category scores
        elements.append(Paragraph("📈 Category Scores", styles["heading"]))
        elements.extend(self._create_category_table(self.score_result["category_scores"], styles))
        elements.append(Spacer(1, 0.2 * inch))

        # Page summary
        elements.append(Paragraph("📋 Page Summary", styles["heading"]))
        elements.extend(self._create_summary_table(self.to_dict()["summary"], styles))
        elements.append(Spacer(1, 0.2 * inch))

        # Headings
        if self.report.headings:
            elements.append(Paragraph("📑 Headings", styles["heading"]))
            elements.extend(self._create_list_table(self.report.headings, "Headings", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # Meta tags
        if self.report.meta_tags:
            elements.append(Paragraph("🏷️ Meta Tags", styles["heading"]))
            meta_items = [f"{tag.name}: {tag.content[:50]}{'...' if len(tag.content) > 50 else ''}" for tag in self.report.meta_tags]
            elements.extend(self._create_list_table(meta_items, "Meta Tags", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # Open Graph tags
        if self.report.og_tags:
            elements.append(Paragraph("🌐 Open Graph Tags", styles["heading"]))
            og_items = [f"{tag.name}: {tag.content[:50]}{'...' if len(tag.content) > 50 else ''}" for tag in self.report.og_tags]
            elements.extend(self._create_list_table(og_items, "Open Graph Tags", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # Images
        if self.report.images:
            elements.append(Paragraph("🖼️ Images", styles["heading"]))
            img_items = [img.src[:60] + ("..." if len(img.src) > 60 else "") for img in self.report.images]
            elements.extend(self._create_list_table(img_items, "Images", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # Internal links
        if self.report.internal_links:
            elements.append(Paragraph("🔗 Internal Links", styles["heading"]))
            elements.extend(self._create_list_table(self.report.internal_links, "Internal Links", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # External links
        if self.report.external_links:
            elements.append(Paragraph("🌍 External Links", styles["heading"]))
            elements.extend(self._create_list_table(self.report.external_links, "External Links", styles))
            elements.append(Spacer(1, 0.2 * inch))

        # Footer
        elements.append(VerticalSpacer(height=0.5 * inch))
        footer_text = f"Report generated by {self.company_name} - SEO Analysis Tool\nURL: {self.report.url}"
        elements.append(Paragraph(footer_text, styles["normal"]))

        # Build PDF
        doc = SimpleDocTemplate(
            str(Path("/tmp/report.pdf")),  # Temporary path, will be saved properly in save()
            pagesize=self.page_size,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        doc.build(elements)

        # Read the PDF content
        pdf_path = Path("/tmp/report.pdf")
        if pdf_path.exists():
            pdf_content = pdf_path.read_bytes()
            pdf_path.unlink()
            return pdf_content

        raise ReportError("Failed to generate PDF content")

    def save(self, path: str | Path) -> Path:
        """Save PDF report to file.

        Args:
            path: Destination file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        pdf_content = self.generate()
        path.write_bytes(pdf_content)

        return path

    def to_bytes(self) -> bytes:
        """Get PDF report as bytes."""
        return self.generate()

    def to_stream(self):
        """Get PDF report as a file-like object."""
        from io import BytesIO
        return BytesIO(self.to_bytes())
