"""Template Renderer — Render proposals as Markdown or HTML."""

from __future__ import annotations

from typing import Any

from proposal_engine.proposal_builder import Proposal


class TemplateRenderer:
    """
    Renders a Proposal object to Markdown or HTML format.
    """

    def render_markdown(self, proposal: Proposal) -> str:
        """Render the proposal as a formatted Markdown document."""
        lines = [
            f"# {proposal.title}",
            "",
            f"**Proposal ID:** {proposal.proposal_id}",
            f"**Date:** {proposal.created_at[:10]}",
            "",
            "---",
            "",
            "## Overview",
            "",
            proposal.overview,
            "",
            "---",
            "",
            "## Scope of Work",
            "",
            f"**Total Timeline:** {proposal.timeline_days} days",
            "",
            "### Deliverables",
            "",
        ]

        for i, deliverable in enumerate(proposal.scope.get("deliverables", []), 1):
            lines.append(f"{i}. {deliverable}")

        lines.append("")
        lines.append("### Milestones")
        lines.append("")

        for milestone in proposal.scope.get("milestones", []):
            lines.append(f"**{milestone.title}** (Day {milestone.deadline_days})")
            lines.append(f"- {milestone.description}")
            if milestone.deliverables:
                lines.append("- Deliverables:")
                for d in milestone.deliverables:
                    lines.append(f"  - {d}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append("## Pricing")
        lines.append("")

        pricing = proposal.pricing_summary
        if pricing.get("tiers"):
            for tier in pricing["tiers"]:
                lines.append(f"- **{tier['name']}**: ${tier['price']:.2f}" +
                            (f" — {tier.get('description', '')}" if tier.get('description') else ""))
            lines.append("")
            lines.append(f"**Minimum:** ${pricing['min_price']:.2f}  |  "
                         f"**Maximum:** ${pricing['max_price']:.2f}  |  "
                         f"**Average:** ${pricing['avg_price']:.2f}")

        if proposal.recommended_tier:
            lines.append(f"\n**Recommended Tier:** {proposal.recommended_tier}")

        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## Terms and Conditions")
        lines.append("")
        lines.append(proposal.terms)
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append(f"*Proposal generated for {proposal.client_name} ({proposal.client_email})*")

        return "\n".join(lines)

    def render_html(self, proposal: Proposal) -> str:
        """Render the proposal as a formatted HTML document."""
        pricing = proposal.pricing_summary
        tiers_html = ""
        if pricing.get("tiers"):
            for tier in pricing["tiers"]:
                desc = f" — {tier.get('description', '')}" if tier.get('description') else ""
                tiers_html += f"<li><strong>{tier['name']}</strong>: ${tier['price']:.2f}{desc}</li>\n"

        milestones_html = ""
        for milestone in proposal.scope.get("milestones", []):
            deliverables_html = ""
            if milestone.deliverables:
                deliverables_html = "<ul>\n"
                for d in milestone.deliverables:
                    deliverables_html += f"  <li>{d}</li>\n"
                deliverables_html += "</ul>\n"
            milestones_html += f"""<div class="milestone">
  <h4>{milestone.title} (Day {milestone.deadline_days})</h4>
  <p>{milestone.description}</p>
  {deliverables_html}
</div>
"""

        deliverables_html = ""
        for d in proposal.scope.get("deliverables", []):
            deliverables_html += f"<li>{d}</li>\n"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{proposal.title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; color: #333; line-height: 1.6; }}
    h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
    h2 {{ color: #2c3e50; margin-top: 30px; }}
    h3 {{ color: #34495e; }}
    h4 {{ color: #7f8c8d; }}
    .meta {{ color: #7f8c8d; font-size: 0.9em; }}
    .pricing {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    .milestone {{ background: #fff; border: 1px solid #e9ecef; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    .terms {{ background: #fdf2f8; padding: 15px; border-radius: 8px; margin: 10px 0; }}
    hr {{ border: none; border-top: 1px solid #e9ecef; margin: 20px 0; }}
    footer {{ color: #95a5a6; font-size: 0.85em; margin-top: 30px; }}
  </style>
</head>
<body>
  <h1>{proposal.title}</h1>
  <p class="meta"><strong>Proposal ID:</strong> {proposal.proposal_id} &nbsp;|&nbsp; <strong>Date:</strong> {proposal.created_at[:10]}</p>
  <hr>
  <h2>Overview</h2>
  <p>{proposal.overview}</p>
  <hr>
  <h2>Scope of Work</h2>
  <p><strong>Total Timeline:</strong> {proposal.timeline_days} days</p>
  <h3>Deliverables</h3>
  <ul>{deliverables_html}</ul>
  <h3>Milestones</h3>
  {milestones_html}
  <hr>
  <h2>Pricing</h2>
  <div class="pricing">
    <ul>{tiers_html}</ul>
    <p><strong>Minimum:</strong> ${pricing['min_price']:.2f} &nbsp;|&nbsp;
       <strong>Maximum:</strong> ${pricing['max_price']:.2f} &nbsp;|&nbsp;
       <strong>Average:</strong> ${pricing['avg_price']:.2f}</p>
    {'<p><strong>Recommended Tier:</strong> ' + proposal.recommended_tier + '</p>' if proposal.recommended_tier else ''}
  </div>
  <hr>
  <h2>Terms and Conditions</h2>
  <div class="terms">
    <p>{proposal.terms}</p>
  </div>
  <hr>
  <footer>Proposal generated for {proposal.client_name} ({proposal.client_email})</footer>
</body>
</html>"""

    def render(self, proposal: Proposal, fmt: str = "markdown") -> str:
        """Render to the specified format ('markdown' or 'html')."""
        if fmt.lower() == "html":
            return self.render_html(proposal)
        return self.render_markdown(proposal)
