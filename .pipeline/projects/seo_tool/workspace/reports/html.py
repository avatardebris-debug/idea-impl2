"""HTML report generator with styled templates."""

from __future__ import annotations

import base64
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from jinja2 import Environment, PackageLoader, select_autoescape

from seo_tool.models import SEOReport
from seo_tool.reports.base import BaseReport, ReportError


class HTMLReport(BaseReport):
    """Generate HTML reports with styled templates."""

    def __init__(
        self,
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
        title: Optional[str] = None,
        company_name: Optional[str] = None,
    ):
        """Initialize HTML report.

        Args:
            report: The SEO analysis report
            score_result: The scoring results
            generated_at: Timestamp when report was generated
            title: Custom report title
            company_name: Company name for branding
        """
        super().__init__(report, score_result, generated_at)
        self.title = title or f"SEO Report: {report.url}"
        self.company_name = company_name or "SEO Tool"
        self._env = self._init_jinja_env()

    def _init_jinja_env(self) -> Environment:
        """Initialize Jinja2 environment."""
        return Environment(
            loader=PackageLoader("seo_tool.reports"),
            autoescape=select_autoescape(["html", "xml", "j2"]),
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def _get_template(self, name: str) -> Any:
        """Get a template by name."""
        try:
            return self._env.get_template(name)
        except Exception as e:
            raise ReportError(f"Template not found: {name}") from e

    def _get_score_color(self, score: int, max_score: int) -> str:
        """Get CSS color based on score percentage."""
        if max_score == 0:
            return "#999999"
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "#28a745"  # Green
        elif percentage >= 50:
            return "#ffc107"  # Yellow
        else:
            return "#dc3545"  # Red

    def _get_score_class(self, score: int, max_score: int) -> str:
        """Get CSS class based on score percentage."""
        if max_score == 0:
            return "score-neutral"
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "score-excellent"
        elif percentage >= 50:
            return "score-good"
        else:
            return "score-poor"

    def _encode_image(self, src: str) -> str:
        """Encode image data URI if local, otherwise return as-is."""
        if src.startswith("data:"):
            return src
        # For external images, just return the URL
        return src

    def generate(self) -> str:
        """Generate HTML report content.

        Returns:
            HTML string
        """
        template = self._get_template("report.html.j2")

        # Prepare data for template
        data = {
            "title": self.title,
            "company_name": self.company_name,
            "url": self.report.url,
            "generated_at": self.generated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "fetch_error": self.report.fetch_error,
            "http_status": self.report.http_status,
            "total_score": self.score_result["total_score"],
            "max_total_score": 100,
            "category_scores": self.score_result["category_scores"],
            "summary": {
                "word_count": self.report.word_count,
                "link_count": self.report.link_count,
                "internal_links": len(self.report.internal_links),
                "external_links": len(self.report.external_links),
                "images": len(self.report.images),
                "headings": len(self.report.headings),
                "og_tags": len(self.report.og_tags),
            },
            "headings": self.report.headings,
            "meta_tags": self.report.meta_tags,
            "og_tags": self.report.og_tags,
            "images": self.report.images,
            "internal_links": self.report.internal_links,
            "external_links": self.report.external_links,
            "metadata": self.metadata,
            "score_color": self._get_score_color,
            "score_class": self._get_score_class,
            "encode_image": self._encode_image,
        }

        return template.render(**data)

    def save(self, path: str | Path) -> Path:
        """Save HTML report to file.

        Args:
            path: Destination file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        html_content = self.generate()
        path.write_text(html_content, encoding="utf-8")

        return path

    def to_bytes(self) -> bytes:
        """Get HTML report as bytes."""
        return self.generate().encode("utf-8")

    def to_stream(self) -> BytesIO:
        """Get HTML report as a file-like object."""
        return BytesIO(self.to_bytes())

    def to_base64(self) -> str:
        """Get HTML report as base64 encoded string."""
        return base64.b64encode(self.to_bytes()).decode("utf-8")
