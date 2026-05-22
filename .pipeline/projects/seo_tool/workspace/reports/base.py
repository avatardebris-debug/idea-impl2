"""Base report class and utilities."""

from __future__ import annotations

import abc
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from seo_tool.models import SEOReport


class ReportError(Exception):
    """Base exception for report-related errors."""

    pass


class BaseReport(abc.ABC):
    """Abstract base class for all report types."""

    def __init__(
        self,
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
    ):
        """Initialize a report.

        Args:
            report: The SEO analysis report to include
            score_result: The scoring results from the Scorer
            generated_at: Timestamp when report was generated (defaults to now)
        """
        self.report = report
        self.score_result = score_result
        self.generated_at = generated_at or datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the report."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value."""
        return self.metadata.get(key, default)

    @abc.abstractmethod
    def generate(self) -> Any:
        """Generate the report content.

        Returns:
            The generated report content (string, bytes, or other format)
        """
        pass

    @abc.abstractmethod
    def save(self, path: str | Path) -> Path:
        """Save the report to a file.

        Args:
            path: Destination file path

        Returns:
            Path to the saved file
        """
        pass

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to a dictionary for serialization."""
        return {
            "url": self.report.url,
            "fetch_error": self.report.fetch_error,
            "http_status": self.report.http_status,
            "total_score": self.score_result["total_score"],
            "category_scores": {
                name: {
                    "score": cat["score"],
                    "max": cat["max"],
                    "reason": cat["reason"],
                }
                for name, cat in self.score_result["category_scores"].items()
            },
            "summary": {
                "word_count": self.report.word_count,
                "link_count": self.report.link_count,
                "internal_links": len(self.report.internal_links),
                "external_links": len(self.report.external_links),
                "images": len(self.report.images),
                "headings": len(self.report.headings),
                "og_tags": len(self.report.og_tags),
            },
            "generated_at": self.generated_at.isoformat(),
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class ReportGenerator:
    """Factory class for creating reports."""

    @staticmethod
    def create_html(
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
    ) -> HTMLReport:
        """Create an HTML report."""
        from seo_tool.reports.html import HTMLReport

        return HTMLReport(report, score_result, generated_at)

    @staticmethod
    def create_pdf(
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
    ) -> PDFReport:
        """Create a PDF report."""
        from seo_tool.reports.pdf import PDFReport

        return PDFReport(report, score_result, generated_at)

    @staticmethod
    def create_summary(
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
    ) -> ExecutiveSummary:
        """Create an executive summary report."""
        from seo_tool.reports.summary import ExecutiveSummary

        return ExecutiveSummary(report, score_result, generated_at)

    @staticmethod
    def create_comparative(
        reports: List[SEOReport],
        score_results: List[Dict[str, Any]],
        generated_at: Optional[datetime] = None,
    ) -> ComparativeReport:
        """Create a comparative report."""
        from seo_tool.reports.comparative import ComparativeReport

        return ComparativeReport(reports, score_results, generated_at)
