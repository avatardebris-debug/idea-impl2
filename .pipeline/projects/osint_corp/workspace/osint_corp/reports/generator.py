"""Report generation module — creates PDF/HTML intelligence reports."""

from __future__ import annotations

import html
import json
import logging
from datetime import datetime
from typing import Any, Optional

from osint_corp.analysis.financial import FinancialSummary
from osint_corp.analysis.network import NetworkAnalysis
from osint_corp.analysis.risk import RiskAssessment
from osint_corp.models.entities import Company

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates intelligence reports in various formats."""

    def __init__(self):
        self._templates: dict[str, str] = {}

    def generate_html_report(
        self,
        company: Company,
        financial_summary: Optional[FinancialSummary] = None,
        network_analysis: Optional[NetworkAnalysis] = None,
        risk_assessment: Optional[RiskAssessment] = None,
        title: str = "Corporate Intelligence Report",
    ) -> str:
        """Generate an HTML report.

        Args:
            company: The target Company.
            financial_summary: Optional financial summary.
            network_analysis: Optional network analysis.
            risk_assessment: Optional risk assessment.
            title: Report title.

        Returns:
            HTML string.
        """
        html_parts = []

        # Header
        html_parts.append(f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{html.escape(title)}</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .report-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 10px;
                    margin-bottom: 30px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .report-header h1 {{
                    margin: 0;
                    font-size: 2.5em;
                }}
                .report-header p {{
                    margin: 10px 0 0 0;
                    opacity: 0.9;
                }}
                .section {{
                    background: white;
                    padding: 25px;
                    margin-bottom: 20px;
                    border-radius: 8px;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .section h2 {{
                    color: #667eea;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 10px;
                    margin-top: 0;
                }}
                .metric-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 15px;
                    margin: 20px 0;
                }}
                .metric-card {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 4px solid #667eea;
                }}
                .metric-card .label {{
                    font-size: 0.9em;
                    color: #666;
                    text-transform: uppercase;
                }}
                .metric-card .value {{
                    font-size: 1.8em;
                    font-weight: bold;
                    color: #333;
                    margin: 5px 0;
                }}
                .risk-badge {{
                    display: inline-block;
                    padding: 5px 15px;
                    border-radius: 20px;
                    font-weight: bold;
                    text-transform: uppercase;
                    font-size: 0.9em;
                }}
                .risk-low {{ background: #d4edda; color: #155724; }}
                .risk-medium {{ background: #fff3cd; color: #856404; }}
                .risk-high {{ background: #f8d7da; color: #721c24; }}
                .risk-critical {{ background: #721c24; color: white; }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 15px 0;
                }}
                th, td {{
                    padding: 12px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #667eea;
                    color: white;
                }}
                tr:hover {{
                    background-color: #f5f5f5;
                }}
                .insight {{
                    background: #e7f3ff;
                    border-left: 4px solid #2196F3;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 0 6px 6px 0;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
        """)

        # Report Header
        html_parts.append(f"""
        <div class="report-header">
            <h1>{html.escape(title)}</h1>
            <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Company: {html.escape(company.name)} ({html.escape(company.ticker or 'N/A')})</p>
        </div>
        """)

        # Company Overview
        html_parts.append("""
        <div class="section">
            <h2>Company Overview</h2>
            <div class="metric-grid">
                <div class="metric-card">
                    <div class="label">Company Name</div>
                    <div class="value">{name}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Ticker</div>
                    <div class="value">{ticker}</div>
                </div>
                <div class="metric-card">
                    <div class="label">CIK</div>
                    <div class="value">{cik}</div>
                </div>
                <div class="metric-card">
                    <div class="label">Sector</div>
                    <div class="value">{sector}</div>
                </div>
            </div>
        </div>
        """.format(
            name=html.escape(company.name),
            ticker=html.escape(company.ticker or 'N/A'),
            cik=html.escape(company.cik or 'N/A'),
            sector=html.escape(company.sector or 'N/A'),
        ))

        # Financial Summary
        if financial_summary:
            html_parts.append("""
            <div class="section">
                <h2>Financial Summary</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="label">Revenue (TTM)</div>
                        <div class="value">${revenue:,.0f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Net Income (TTM)</div>
                        <div class="value">${net_income:,.0f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Total Assets</div>
                        <div class="value">${total_assets:,.0f}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Total Equity</div>
                        <div class="value">${total_equity:,.0f}</div>
                    </div>
                </div>
                <h3>Key Ratios</h3>
                <table>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                    <tr>
                        <td>ROE</td>
                        <td>{roe:.2%}</td>
                    </tr>
                    <tr>
                        <td>ROA</td>
                        <td>{roa:.2%}</td>
                    </tr>
                    <tr>
                        <td>Debt-to-Equity</td>
                        <td>{dte:.2f}</td>
                    </tr>
                    <tr>
                        <td>Current Ratio</td>
                        <td>{cr:.2f}</td>
                    </tr>
                    <tr>
                        <td>Quick Ratio</td>
                        <td>{qr:.2f}</td>
                    </tr>
                    <tr>
                        <td>Operating Margin</td>
                        <td>{om:.2%}</td>
                    </tr>
                    <tr>
                        <td>Net Margin</td>
                        <td>{nm:.2%}</td>
                    </tr>
                </table>
            </div>
            """.format(
                revenue=financial_summary.revenue_ttm or 0,
                net_income=financial_summary.net_income_ttm or 0,
                total_assets=financial_summary.total_assets or 0,
                total_equity=financial_summary.total_equity or 0,
                roe=financial_summary.roe or 0,
                roa=financial_summary.roa or 0,
                dte=financial_summary.debt_to_equity or 0,
                cr=financial_summary.current_ratio or 0,
                qr=financial_summary.quick_ratio or 0,
                om=financial_summary.operating_margin or 0,
                nm=financial_summary.net_margin or 0,
            ))

        # Risk Assessment
        if risk_assessment:
            risk_class = f"risk-{risk_assessment.risk_level}"
            html_parts.append("""
            <div class="section">
                <h2>Risk Assessment</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="label">Overall Risk Score</div>
                        <div class="value">{score:.1f}/100</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Risk Level</div>
                        <div class="value"><span class="risk-badge {risk_class}">{level}</span></div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Trend</div>
                        <div class="value">{trend}</div>
                    </div>
                </div>
                <h3>Risk Factors</h3>
                <table>
                    <tr>
                        <th>Factor</th>
                        <th>Score</th>
                        <th>Weight</th>
                        <th>Weighted Score</th>
                    </tr>
            """.format(
                score=risk_assessment.overall_score,
                level=risk_assessment.risk_level,
                risk_class=risk_class,
                trend=risk_assessment.trend or "N/A",
            ))

            for factor in risk_assessment.factors:
                html_parts.append("""
                    <tr>
                        <td>{name}</td>
                        <td>{score:.0f}</td>
                        <td>{weight:.0%}</td>
                        <td>{weighted:.1f}</td>
                    </tr>
                """.format(
                    name=html.escape(factor.name),
                    score=factor.score,
                    weight=factor.weight,
                    weighted=factor.weighted_score(),
                ))

            html_parts.append("""
                </table>
                <h3>Recommendations</h3>
                <ul>
            """)

            for rec in risk_assessment.recommendations:
                html_parts.append(f"<li>{html.escape(rec)}</li>")

            html_parts.append("""
                </ul>
            </div>
            """)

        # Network Analysis
        if network_analysis:
            html_parts.append("""
            <div class="section">
                <h2>Network Analysis</h2>
                <div class="metric-grid">
                    <div class="metric-card">
                        <div class="label">Total Nodes</div>
                        <div class="value">{nodes}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Total Edges</div>
                        <div class="value">{edges}</div>
                    </div>
                    <div class="metric-card">
                        <div class="label">Communities</div>
                        <div class="value">{communities}</div>
                    </div>
                </div>
            """)

            if network_analysis.key_officers:
                html_parts.append("<h3>Key Officers</h3><table><tr><th>Name</th><th>Role</th></tr>")
                for officer in network_analysis.key_officers:
                    html_parts.append("""
                        <tr>
                            <td>{name}</td>
                            <td>{role}</td>
                        </tr>
                    """.format(
                        name=html.escape(officer.get("name", "N/A")),
                        role=html.escape(officer.get("role", "N/A")),
                    ))
                html_parts.append("</table>")

            if network_analysis.related_companies:
                html_parts.append("<h3>Related Companies</h3><table><tr><th>Name</th><th>Relationship</th></tr>")
                for comp in network_analysis.related_companies:
                    html_parts.append("""
                        <tr>
                            <td>{name}</td>
                            <td>{rel}</td>
                        </tr>
                    """.format(
                        name=html.escape(comp.get("name", "N/A")),
                        rel=html.escape(comp.get("relationship_type", "N/A")),
                    ))
                html_parts.append("</table>")

            if network_analysis.insights:
                html_parts.append("<h3>Key Insights</h3>")
                for insight in network_analysis.insights:
                    html_parts.append(f'<div class="insight">{html.escape(insight)}</div>')

            html_parts.append("</div>")

        # Footer
        html_parts.append("""
        <div class="footer">
            <p>Generated by OSINT Corp Intelligence Platform</p>
            <p>This report is for informational purposes only and does not constitute financial advice.</p>
        </div>
        </body>
        </html>
        """)

        return "\n".join(html_parts)

    def generate_json_report(
        self,
        company: Company,
        financial_summary: Optional[FinancialSummary] = None,
        network_analysis: Optional[NetworkAnalysis] = None,
        risk_assessment: Optional[RiskAssessment] = None,
    ) -> str:
        """Generate a JSON report.

        Args:
            company: The target Company.
            financial_summary: Optional financial summary.
            network_analysis: Optional network analysis.
            risk_assessment: Optional risk assessment.

        Returns:
            JSON string.
        """
        report: dict[str, Any] = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "company": {
                    "name": company.name,
                    "ticker": company.ticker,
                    "cik": company.cik,
                    "sector": company.sector,
                },
            },
        }

        if financial_summary:
            report["financial_summary"] = financial_summary.to_dict()

        if network_analysis:
            report["network_analysis"] = network_analysis.to_dict()

        if risk_assessment:
            report["risk_assessment"] = risk_assessment.to_dict()

        return json.dumps(report, indent=2, default=str)

    def generate_text_report(
        self,
        company: Company,
        financial_summary: Optional[FinancialSummary] = None,
        network_analysis: Optional[NetworkAnalysis] = None,
        risk_assessment: Optional[RiskAssessment] = None,
    ) -> str:
        """Generate a plain text report.

        Args:
            company: The target Company.
            financial_summary: Optional financial summary.
            network_analysis: Optional network analysis.
            risk_assessment: Optional risk assessment.

        Returns:
            Text string.
        """
        lines = []
        lines.append("=" * 80)
        lines.append("CORPORATE INTELLIGENCE REPORT")
        lines.append("=" * 80)
        lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Company: {company.name} ({company.ticker or 'N/A'})")
        lines.append(f"CIK: {company.cik or 'N/A'}")
        lines.append(f"Sector: {company.sector or 'N/A'}")
        lines.append("")

        if financial_summary:
            lines.append("-" * 80)
            lines.append("FINANCIAL SUMMARY")
            lines.append("-" * 80)
            lines.append(f"Revenue (TTM): ${financial_summary.revenue_ttm:,.0f}" if financial_summary.revenue_ttm else "Revenue (TTM): N/A")
            lines.append(f"Net Income (TTM): ${financial_summary.net_income_ttm:,.0f}" if financial_summary.net_income_ttm else "Net Income (TTM): N/A")
            lines.append(f"Total Assets: ${financial_summary.total_assets:,.0f}" if financial_summary.total_assets else "Total Assets: N/A")
            lines.append(f"Total Equity: ${financial_summary.total_equity:,.0f}" if financial_summary.total_equity else "Total Equity: N/A")
            lines.append("")
            lines.append("Key Ratios:")
            lines.append(f"  ROE: {financial_summary.roe:.2%}" if financial_summary.roe else "  ROE: N/A")
            lines.append(f"  ROA: {financial_summary.roa:.2%}" if financial_summary.roa else "  ROA: N/A")
            lines.append(f"  Debt-to-Equity: {financial_summary.debt_to_equity:.2f}" if financial_summary.debt_to_equity else "  Debt-to-Equity: N/A")
            lines.append(f"  Current Ratio: {financial_summary.current_ratio:.2f}" if financial_summary.current_ratio else "  Current Ratio: N/A")
            lines.append(f"  Quick Ratio: {financial_summary.quick_ratio:.2f}" if financial_summary.quick_ratio else "  Quick Ratio: N/A")
            lines.append(f"  Operating Margin: {financial_summary.operating_margin:.2%}" if financial_summary.operating_margin else "  Operating Margin: N/A")
            lines.append(f"  Net Margin: {financial_summary.net_margin:.2%}" if financial_summary.net_margin else "  Net Margin: N/A")
            lines.append("")

        if risk_assessment:
            lines.append("-" * 80)
            lines.append("RISK ASSESSMENT")
            lines.append("-" * 80)
            lines.append(f"Overall Score: {risk_assessment.overall_score:.1f}/100")
            lines.append(f"Risk Level: {risk_assessment.risk_level.upper()}")
            lines.append(f"Trend: {risk_assessment.trend or 'N/A'}")
            lines.append("")
            lines.append("Risk Factors:")
            for factor in risk_assessment.factors:
                lines.append(f"  {factor.name}: {factor.score:.0f}/100 (weight: {factor.weight:.0%})")
            lines.append("")
            lines.append("Recommendations:")
            for rec in risk_assessment.recommendations:
                lines.append(f"  • {rec}")
            lines.append("")

        if network_analysis:
            lines.append("-" * 80)
            lines.append("NETWORK ANALYSIS")
            lines.append("-" * 80)
            lines.append(f"Total Nodes: {len(network_analysis.nodes)}")
            lines.append(f"Total Edges: {len(network_analysis.edges)}")
            lines.append(f"Communities: {len(network_analysis.communities)}")
            lines.append("")

            if network_analysis.key_officers:
                lines.append("Key Officers:")
                for officer in network_analysis.key_officers:
                    lines.append(f"  • {officer.get('name', 'N/A')} - {officer.get('role', 'N/A')}")
                lines.append("")

            if network_analysis.related_companies:
                lines.append("Related Companies:")
                for comp in network_analysis.related_companies:
                    lines.append(f"  • {comp.get('name', 'N/A')} ({comp.get('relationship_type', 'N/A')})")
                lines.append("")

            if network_analysis.insights:
                lines.append("Key Insights:")
                for insight in network_analysis.insights:
                    lines.append(f"  • {insight}")
                lines.append("")

        lines.append("=" * 80)
        lines.append("END OF REPORT")
        lines.append("=" * 80)

        return "\n".join(lines)

    def generate_report(
        self,
        company: Company,
        financial_summary: Optional[FinancialSummary] = None,
        network_analysis: Optional[NetworkAnalysis] = None,
        risk_assessment: Optional[RiskAssessment] = None,
        format: str = "html",
        title: str = "Corporate Intelligence Report",
    ) -> str:
        """Generate a report in the specified format.

        Args:
            company: The target Company.
            financial_summary: Optional financial summary.
            network_analysis: Optional network analysis.
            risk_assessment: Optional risk assessment.
            format: Output format ('html', 'json', 'text').
            title: Report title (for HTML).

        Returns:
            Report string in the specified format.
        """
        if format == "html":
            return self.generate_html_report(
                company, financial_summary, network_analysis, risk_assessment, title
            )
        elif format == "json":
            return self.generate_json_report(
                company, financial_summary, network_analysis, risk_assessment
            )
        elif format == "text":
            return self.generate_text_report(
                company, financial_summary, network_analysis, risk_assessment
            )
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'html', 'json', or 'text'.")
