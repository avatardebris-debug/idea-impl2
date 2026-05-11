"""Scope Extractor — Extract deliverables and milestones from SOPs."""

from __future__ import annotations

from typing import Any

from core.service_offering import ServiceOffering, Milestone


class ScopeExtractor:
    """
    Extracts scope information from a ServiceOffering:
    - Deliverables list
    - Milestones with deadlines
    - Timeline summary
    """

    def extract(self, offering: ServiceOffering) -> dict[str, Any]:
        """
        Extract scope from an SOP.

        Returns:
            dict with keys:
              - deliverables: list[str]
              - milestones: list[Milestone]
              - total_days: int
              - summary: str
        """
        deliverables = list(offering.deliverables)

        # Extract milestones from timeline
        milestones: list[Milestone] = []
        timeline_data = offering.timeline
        total_days = timeline_data.get("total_days", 0)

        if "milestones" in timeline_data:
            raw_milestones = timeline_data["milestones"]
            for m in raw_milestones:
                if isinstance(m, Milestone):
                    milestones.append(m)
                elif isinstance(m, dict):
                    milestones.append(Milestone(
                        title=m.get("title", "Untitled"),
                        description=m.get("description", ""),
                        deadline_days=m.get("deadline_days", 0),
                        deliverables=m.get("deliverables", []),
                    ))

        # Build summary
        summary_parts = [
            f"Service: {offering.title}",
            f"Total timeline: {total_days} days",
            f"Deliverables: {len(deliverables)} items",
            f"Milestones: {len(milestones)} items",
        ]
        summary = "\n".join(summary_parts)

        return {
            "deliverables": deliverables,
            "milestones": milestones,
            "total_days": total_days,
            "summary": summary,
        }

    def get_deliverables(self, offering: ServiceOffering) -> list[str]:
        """Return just the deliverables list."""
        return list(offering.deliverables)

    def get_milestones(self, offering: ServiceOffering) -> list[Milestone]:
        """Return just the milestones list."""
        timeline_data = offering.timeline
        if "milestones" not in timeline_data:
            return []
        raw = timeline_data["milestones"]
        result = []
        for m in raw:
            if isinstance(m, Milestone):
                result.append(m)
            elif isinstance(m, dict):
                result.append(Milestone(
                    title=m.get("title", "Untitled"),
                    description=m.get("description", ""),
                    deadline_days=m.get("deadline_days", 0),
                    deliverables=m.get("deliverables", []),
                ))
        return result
