"""Comparative report generator for multiple SEO analyses."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from seo_tool.models import SEOReport
from seo_tool.reports.base import BaseReport, ReportError


class ComparativeReport(BaseReport):
    """Generate comparative reports for multiple SEO analyses."""

    def __init__(
        self,
        reports: List[SEOReport],
        score_results: List[Dict[str, Any]],
        generated_at: Optional[datetime] = None,
        title: Optional[str] = None,
        company_name: Optional[str] = None,
    ):
        """Initialize comparative report.

        Args:
            reports: List of SEO reports to compare
            score_results: List of scoring results for each report
            generated_at: Timestamp when report was generated
            title: Custom report title
            company_name: Company name for branding
        """
        if len(reports) != len(score_results):
            raise ValueError("Number of reports must match number of score results")

        super().__init__(reports[0], score_results[0], generated_at)
        self.reports = reports
        self.score_results = score_results
        self.title = title or "SEO Comparative Analysis"
        self.company_name = company_name or "SEO Tool"

    def _get_trend(self, scores: List[int]) -> str:
        """Determine trend from a list of scores."""
        if len(scores) < 2:
            return "N/A"

        first = scores[0]
        last = scores[-1]

        if last > first:
            return "↑ Improving"
        elif last < first:
            return "↓ Declining"
        else:
            return "→ Stable"

    def _get_score_change(self, scores: List[int]) -> str:
        """Calculate score change."""
        if len(scores) < 2:
            return "N/A"

        first = scores[0]
        last = scores[-1]
        change = last - first

        if change > 0:
            return f"+{change}"
        elif change < 0:
            return f"{change}"
        else:
            return "0"

    def _generate_comparison_table(self) -> List[Dict[str, Any]]:
        """Generate comparison data for all reports."""
        comparison_data = []

        for i, (report, score_result) in enumerate(zip(self.reports, self.score_results)):
            comparison_data.append(
                {
                    "index": i + 1,
                    "url": report.url,
                    "total_score": score_result["total_score"],
                    "max_score": score_result["max_total_score"],
                    "generated_at": report.generated_at or self.generated_at,
                    "fetch_error": report.fetch_error,
                    "http_status": report.http_status,
                    "word_count": report.word_count,
                    "link_count": report.link_count,
                    "images": report.images,
                    "headings": report.headings,
                    "meta_tags": len(report.meta_tags),
                    "og_tags": len(report.og_tags),
                }
            )

        return comparison_data

    def _generate_trend_analysis(self) -> Dict[str, Any]:
        """Generate trend analysis from multiple reports."""
        scores = [sr["total_score"] for sr in self.score_results]
        word_counts = [r.word_count for r in self.reports]
        link_counts = [r.link_count for r in self.reports]
        image_counts = [r.images for r in self.reports]

        return {
            "score_trend": self._get_trend(scores),
            "score_change": self._get_score_change(scores),
            "score_range": f"{min(scores)}-{max(scores)}",
            "score_avg": sum(scores) / len(scores) if scores else 0,
            "word_count_trend": self._get_trend(word_counts),
            "word_count_change": self._get_score_change(word_counts),
            "link_count_trend": self._get_trend(link_counts),
            "link_count_change": self._get_score_change(link_counts),
            "image_count_trend": self._get_trend(image_counts),
            "image_count_change": self._get_score_change(image_counts),
        }

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate recommendations based on comparative analysis."""
        recommendations = []

        # Score trend recommendations
        trend = self._generate_trend_analysis()["score_trend"]
        if trend == "↓ Declining":
            recommendations.append(
                {
                    "priority": "High",
                    "category": "Performance",
                    "recommendation": "SEO score is declining. Investigate recent changes that may have negatively impacted rankings.",
                }
            )
        elif trend == "↑ Improving":
            recommendations.append(
                {
                    "priority": "Low",
                    "category": "Performance",
                    "recommendation": "SEO score is improving. Continue current optimization strategies.",
                }
            )

        # Content recommendations
        word_counts = [r.word_count for r in self.reports]
        if max(word_counts) < 300:
            recommendations.append(
                {
                    "priority": "High",
                    "category": "Content",
                    "recommendation": "Content length is consistently low across all analyses. Increase content to at least 300 words.",
                }
            )

        # Link recommendations
        link_counts = [r.link_count for r in self.reports]
        if max(link_counts) < 5:
            recommendations.append(
                {
                    "priority": "Medium",
                    "category": "Links",
                    "recommendation": "Limited number of links across all analyses. Add more internal and external links.",
                }
            )

        # Image recommendations
        image_counts = [r.images for r in self.reports]
        if max(image_counts) == 0:
            recommendations.append(
                {
                    "priority": "Medium",
                    "category": "Images",
                    "recommendation": "No images found in any analysis. Add relevant images with alt text.",
                }
            )

        return recommendations

    def generate(self) -> str:
        """Generate comparative report text.

        Returns:
            Comparative report text
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"SEO COMPARATIVE ANALYSIS: {self.title}")
        lines.append("=" * 80)
        lines.append("")

        # Report info
        lines.append(f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Number of Analyses: {len(self.reports)}")
        lines.append(f"Company: {self.company_name}")
        lines.append("")

        # Trend analysis
        trend = self._generate_trend_analysis()
        lines.append("-" * 80)
        lines.append("TREND ANALYSIS")
        lines.append("-" * 80)
        lines.append(f"SEO Score Trend: {trend['score_trend']}")
        lines.append(f"Score Change: {trend['score_change']}")
        lines.append(f"Score Range: {trend['score_range']}")
        lines.append(f"Average Score: {trend['score_avg']:.1f}")
        lines.append("")
        lines.append(f"Content Trend: {trend['word_count_trend']}")
        lines.append(f"Content Change: {trend['word_count_change']}")
        lines.append("")
        lines.append(f"Link Trend: {trend['link_count_trend']}")
        lines.append(f"Link Change: {trend['link_count_change']}")
        lines.append("")
        lines.append(f"Image Trend: {trend['image_count_trend']}")
        lines.append(f"Image Change: {trend['image_count_change']}")
        lines.append("")

        # Comparison table
        lines.append("-" * 80)
        lines.append("COMPARISON TABLE")
        lines.append("-" * 80)
        lines.append(f"{'#':<3} {'URL':<40} {'Score':<8} {'Words':<8} {'Links':<8} {'Images':<8}")
        lines.append("-" * 80)

        for item in self._generate_comparison_table():
            url_display = item["url"][:38] + ".." if len(item["url"]) > 40 else item["url"]
            lines.append(
                f"{item['index']:<3} {url_display:<40} {item['total_score']:<8} {item['word_count']:<8} {item['link_count']:<8} {item['images']:<8}"
            )

        lines.append("")

        # Detailed analysis for each report
        for i, (report, score_result) in enumerate(zip(self.reports, self.score_results), 1):
            lines.append("-" * 80)
            lines.append(f"ANALYSIS #{i}")
            lines.append("-" * 80)
            lines.append(f"URL: {report.url}")
            lines.append(f"Generated: {report.generated_at or self.generated_at}")
            lines.append(f"SEO Score: {score_result['total_score']}/{score_result['max_total_score']}")

            if report.fetch_error:
                lines.append(f"Error: {report.fetch_error}")
                lines.append(f"HTTP Status: {report.http_status or 'N/A'}")

            lines.append("")
            lines.append("Category Breakdown:")
            for name, cat in score_result["category_scores"].items():
                lines.append(f"  {name}: {cat['score']}/{cat['max']} ({cat['reason']})")

            lines.append("")
            lines.append(f"Summary:")
            lines.append(f"  Words: {report.word_count}")
            lines.append(f"  Links: {report.link_count}")
            lines.append(f"  Internal: {report.internal_links}")
            lines.append(f"  External: {report.external_links}")
            lines.append(f"  Images: {report.images}")
            lines.append(f"  Headings: {report.headings}")
            lines.append(f"  Meta Tags: {len(report.meta_tags)}")
            lines.append(f"  OG Tags: {len(report.og_tags)}")
            lines.append("")

        # Recommendations
        lines.append("-" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        for i, rec in enumerate(self._generate_recommendations(), 1):
            lines.append(f"{i}. [{rec['priority']}] {rec['category']}: {rec['recommendation']}")
        lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append(f"Report generated by {self.company_name} - SEO Analysis Tool")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save(self, path: str | Path) -> Path:
        """Save comparative report to file.

        Args:
            path: Destination file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        report_text = self.generate()
        path.write_text(report_text, encoding="utf-8")

        return path

    def to_bytes(self) -> bytes:
        """Get comparative report as bytes."""
        return self.generate().encode("utf-8")

    def to_stream(self):
        """Get comparative report as a file-like object."""
        from io import BytesIO
        return BytesIO(self.to_bytes())
