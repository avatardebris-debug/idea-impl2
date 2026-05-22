"""Executive summary report generator."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from seo_tool.models import SEOReport
from seo_tool.reports.base import BaseReport, ReportError


class ExecutiveSummaryReport(BaseReport):
    """Generate executive summary reports."""

    def __init__(
        self,
        report: SEOReport,
        score_result: Dict[str, Any],
        generated_at: Optional[datetime] = None,
        title: Optional[str] = None,
        company_name: Optional[str] = None,
    ):
        """Initialize executive summary report.

        Args:
            report: The SEO analysis report
            score_result: The scoring results
            generated_at: Timestamp when report was generated
            title: Custom report title
            company_name: Company name for branding
        """
        super().__init__(report, score_result, generated_at)
        self.title = title or f"Executive Summary: {report.url}"
        self.company_name = company_name or "SEO Tool"

    def _get_recommendation_priority(self, score: int, max_score: int) -> str:
        """Get priority level for recommendations."""
        if max_score == 0:
            return "Low"
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "Low"
        elif percentage >= 50:
            return "Medium"
        else:
            return "High"

    def _get_action_items(self) -> List[Dict[str, str]]:
        """Generate action items based on scores."""
        action_items = []

        for name, cat in self.score_result["category_scores"].items():
            priority = self._get_recommendation_priority(cat["score"], cat["max"])
            if priority != "Low":
                action_items.append(
                    {
                        "category": name,
                        "priority": priority,
                        "current_score": f"{cat['score']}/{cat['max']}",
                        "reason": cat["reason"],
                    }
                )

        # Sort by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        action_items.sort(key=lambda x: priority_order.get(x["priority"], 3))

        return action_items

    def _generate_executive_summary(self) -> str:
        """Generate executive summary text."""
        total_score = self.score_result["total_score"]
        max_total_score = self.score_result["max_total_score"]

        if total_score == 0:
            summary = "The website requires significant SEO improvements. Immediate attention is needed across multiple areas."
        elif total_score >= 80:
            summary = "The website has a strong SEO foundation with excellent performance across most categories. Continue monitoring and optimizing."
        elif total_score >= 50:
            summary = "The website has a moderate SEO score with room for improvement. Focus on addressing the identified issues to enhance visibility."
        else:
            summary = "The website has a low SEO score and requires comprehensive improvements to compete effectively."

        return summary

    def _generate_key_findings(self) -> List[str]:
        """Generate key findings."""
        findings = []

        # Overall score finding
        total_score = self.score_result["total_score"]
        if total_score >= 80:
            findings.append(f"✅ Strong overall SEO score of {total_score}/100")
        elif total_score >= 50:
            findings.append(f"⚠️ Moderate SEO score of {total_score}/100")
        else:
            findings.append(f"❌ Low SEO score of {total_score}/100")

        # Best category
        category_scores = self.score_result["category_scores"]
        if category_scores:
            best_cat = max(category_scores.items(), key=lambda x: x[1]["score"])
            findings.append(f"🏆 Best performing category: {best_cat[0]} ({best_cat[1]['score']}/{best_cat[1]['max']})")

        # Worst category
        if category_scores:
            worst_cat = min(category_scores.items(), key=lambda x: x[1]["score"])
            findings.append(f"📉 Needs improvement: {worst_cat[0]} ({worst_cat[1]['score']}/{worst_cat[1]['max']})")

        # Content analysis
        if self.report.word_count < 300:
            findings.append("📝 Content length is below recommended minimum (300 words)")
        elif self.report.word_count > 2000:
            findings.append("📝 Content length is excellent (over 2000 words)")

        # Link analysis
        if self.report.link_count == 0:
            findings.append("🔗 No internal or external links found")
        elif self.report.link_count < 10:
            findings.append("🔗 Limited number of links found")

        # Image analysis
        if self.report.images == 0:
            findings.append("🖼️ No images found on the page")
        elif self.report.images > 10:
            findings.append("🖼️ Good use of images (over 10)")

        # Meta tags
        if self.report.meta_tags:
            findings.append(f"🏷️ {len(self.report.meta_tags)} meta tags found")
        else:
            findings.append("🏷️ No meta tags found")

        # Open Graph
        if self.report.og_tags:
            findings.append(f"🌐 {len(self.report.og_tags)} Open Graph tags found")
        else:
            findings.append("🌐 No Open Graph tags found")

        return findings

    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """Generate specific recommendations."""
        recommendations = []

        # Content recommendations
        if self.report.word_count < 300:
            recommendations.append(
                {
                    "category": "Content",
                    "recommendation": "Increase content length to at least 300 words for better SEO performance.",
                    "impact": "High",
                }
            )

        # Heading recommendations
        if self.report.headings < 3:
            recommendations.append(
                {
                    "category": "Structure",
                    "recommendation": "Add more headings (H1, H2, H3) to improve content structure and readability.",
                    "impact": "Medium",
                }
            )

        # Image recommendations
        if self.report.images == 0:
            recommendations.append(
                {
                    "category": "Images",
                    "recommendation": "Add relevant images with descriptive alt text to improve engagement.",
                    "impact": "Medium",
                }
            )

        # Link recommendations
        if self.report.link_count < 5:
            recommendations.append(
                {
                    "category": "Links",
                    "recommendation": "Add more internal and external links to improve site navigation and authority.",
                    "impact": "Medium",
                }
            )

        # Meta tag recommendations
        if not self.report.meta_tags:
            recommendations.append(
                {
                    "category": "Meta Tags",
                    "recommendation": "Add meta title and description tags for better search engine visibility.",
                    "impact": "High",
                }
            )

        # Open Graph recommendations
        if not self.report.og_tags:
            recommendations.append(
                {
                    "category": "Social Media",
                    "recommendation": "Add Open Graph tags for better social media sharing and preview.",
                    "impact": "Low",
                }
            )

        return recommendations

    def generate(self) -> str:
        """Generate executive summary text.

        Returns:
            Executive summary text
        """
        lines = []

        # Header
        lines.append("=" * 80)
        lines.append(f"EXECUTIVE SUMMARY: {self.title}")
        lines.append("=" * 80)
        lines.append("")

        # Report info
        lines.append(f"URL: {self.report.url}")
        lines.append(f"Generated: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Company: {self.company_name}")
        lines.append("")

        # Overall score
        lines.append("-" * 80)
        lines.append("OVERALL SCORE")
        lines.append("-" * 80)
        lines.append(f"SEO Score: {self.score_result['total_score']}/100")
        lines.append("")

        # Executive summary
        lines.append("-" * 80)
        lines.append("EXECUTIVE SUMMARY")
        lines.append("-" * 80)
        lines.append(self._generate_executive_summary())
        lines.append("")

        # Key findings
        lines.append("-" * 80)
        lines.append("KEY FINDINGS")
        lines.append("-" * 80)
        for finding in self._generate_key_findings():
            lines.append(f"• {finding}")
        lines.append("")

        # Action items
        lines.append("-" * 80)
        lines.append("ACTION ITEMS")
        lines.append("-" * 80)
        for i, item in enumerate(self._get_action_items(), 1):
            lines.append(f"{i}. [{item['priority']}] {item['category']}: {item['reason']}")
            lines.append(f"   Current: {item['current_score']}")
        lines.append("")

        # Recommendations
        lines.append("-" * 80)
        lines.append("RECOMMENDATIONS")
        lines.append("-" * 80)
        for i, rec in enumerate(self._generate_recommendations(), 1):
            lines.append(f"{i}. [{rec['impact']}] {rec['category']}: {rec['recommendation']}")
        lines.append("")

        # Category breakdown
        lines.append("-" * 80)
        lines.append("CATEGORY BREAKDOWN")
        lines.append("-" * 80)
        for name, cat in self.score_result["category_scores"].items():
            lines.append(f"{name}: {cat['score']}/{cat['max']} ({cat['reason']})")
        lines.append("")

        # Footer
        lines.append("=" * 80)
        lines.append(f"Report generated by {self.company_name} - SEO Analysis Tool")
        lines.append("=" * 80)

        return "\n".join(lines)

    def save(self, path: str | Path) -> Path:
        """Save executive summary to file.

        Args:
            path: Destination file path

        Returns:
            Path to saved file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        summary_text = self.generate()
        path.write_text(summary_text, encoding="utf-8")

        return path

    def to_bytes(self) -> bytes:
        """Get executive summary as bytes."""
        return self.generate().encode("utf-8")

    def to_stream(self):
        """Get executive summary as a file-like object."""
        from io import BytesIO
        return BytesIO(self.to_bytes())
