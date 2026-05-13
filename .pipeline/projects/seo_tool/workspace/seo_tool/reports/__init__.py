"""Report generation module."""

from seo_tool.reports.base import BaseReport, ReportError
from seo_tool.reports.executive import ExecutiveSummaryReport
from seo_tool.reports.html import HTMLReport
from seo_tool.reports.comparative import ComparativeReport

try:
    from seo_tool.reports.pdf import PDFReport
except ImportError:
    PDFReport = None  # reportlab not installed

__all__ = [
    "BaseReport",
    "ReportError",
    "HTMLReport",
    "PDFReport",
    "ExecutiveSummaryReport",
    "ComparativeReport",
]

