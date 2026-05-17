"""Stakes calculator — generates accountability mechanisms per module."""

from __future__ import annotations

import random
from brain_download.core.models import CourseOutline, StakesConfig, StakesMechanism


# ── Built-in stakes mechanisms ──────────────────────────────────────────────

_MECHANISM_TEMPLATES: list[dict] = [
    {
        "name": "Public Commitment",
        "description": "Announce your learning goal publicly on social media or a community forum.",
        "type": "social",
        "impact_score": 0.75,
        "effort_required": "low",
        "steps": [
            "Choose a platform (Twitter, LinkedIn, Reddit, Discord)",
            "Write a clear commitment post with your timeline",
            "Share weekly progress updates",
            "Engage with others on their commitments too",
        ],
    },
    {
        "name": "Study Group Formation",
        "description": "Form or join a study group with 2-5 people learning the same topic.",
        "type": "social",
        "impact_score": 0.80,
        "effort_required": "medium",
        "steps": [
            "Find 2-5 people with similar goals",
            "Set up a regular meeting schedule (weekly/bi-weekly)",
            "Define shared milestones and accountability rules",
            "Rotate who leads each session",
        ],
    },
    {
        "name": "Teach-Back Challenge",
        "description": "Commit to teaching each module's content to someone else within a week.",
        "type": "social",
        "impact_score": 0.85,
        "effort_required": "medium",
        "steps": [
            "Identify an audience (friend, blog readers, YouTube viewers)",
            "Schedule teaching sessions after each module",
            "Prepare materials in advance",
            "Record sessions for review and sharing",
        ],
    },
    {
        "name": "Financial Pledge",
        "description": "Put money at stake — donate to a cause you dislike if you don't complete modules.",
        "type": "financial",
        "impact_score": 0.90,
        "effort_required": "high",
        "steps": [
            "Choose an opposing charity or cause",
            "Set a per-module penalty amount ($5-$50)",
            "Use a commitment platform like StickK or Beeminder",
            "Set up automatic deductions on missed deadlines",
        ],
    },
    {
        "name": "Progress Betting",
        "description": "Bet with a friend that you'll complete modules on time.",
        "type": "financial",
        "impact_score": 0.70,
        "effort_required": "medium",
        "steps": [
            "Find a friend willing to be your accountability partner",
            "Agree on a bet amount and terms",
            "Set clear completion criteria for each module",
            "Settle bets honestly after each deadline",
        ],
    },
    {
        "name": "Portfolio Project",
        "description": "Build a real project that demonstrates mastery of each module's skills.",
        "type": "portfolio",
        "impact_score": 0.85,
        "effort_required": "high",
        "steps": [
            "Define a project scope for each module",
            "Set deadlines for project milestones",
            "Document your process and results",
            "Publish your work on GitHub or a personal site",
        ],
    },
    {
        "name": "Certification Goal",
        "description": "Set a certification exam date as your deadline for the entire course.",
        "type": "credential",
        "impact_score": 0.75,
        "effort_required": "medium",
        "steps": [
            "Research relevant certifications for your field",
            "Register for an exam date (creates real deadline)",
            "Map certification topics to your course modules",
            "Schedule practice exams as module checkpoints",
        ],
    },
    {
        "name": "Content Creation",
        "description": "Create blog posts, videos, or tutorials documenting your learning journey.",
        "type": "portfolio",
        "impact_score": 0.80,
        "effort_required": "high",
        "steps": [
            "Choose your content format (blog, video, podcast)",
            "Set a publishing schedule (e.g., weekly)",
            "Write about each module's key takeaways",
            "Share content on relevant platforms",
        ],
    },
    {
        "name": "Mentor Check-ins",
        "description": "Schedule regular check-ins with a mentor or expert in the field.",
        "type": "social",
        "impact_score": 0.70,
        "effort_required": "medium",
        "steps": [
            "Find a mentor (through networks, LinkedIn, or communities)",
            "Schedule monthly or bi-weekly check-in calls",
            "Prepare progress reports and questions for each session",
            "Act on feedback and report back next time",
        ],
    },
    {
        "name": "Public Dashboard",
        "description": "Create a public dashboard tracking your learning progress and metrics.",
        "type": "social",
        "impact_score": 0.65,
        "effort_required": "low",
        "steps": [
            "Choose a dashboard tool (Notion, GitHub, personal site)",
            "Define metrics to track (hours, modules, projects)",
            "Update the dashboard daily or weekly",
            "Share the dashboard link publicly",
        ],
    },
]


def _calculate_stakes_score(mechanism: dict, config: StakesConfig) -> float:
    """Calculate a composite stakes score for a mechanism."""
    base_score = mechanism["impact_score"]

    # Adjust based on config preferences
    if config.prefer_social:
        base_score *= 1.1 if mechanism["type"] == "social" else 0.9
    if config.prefer_financial:
        base_score *= 1.1 if mechanism["type"] == "financial" else 0.9
    if config.prefer_portfolio:
        base_score *= 1.1 if mechanism["type"] == "portfolio" else 0.9
    if config.prefer_credential:
        base_score *= 1.1 if mechanism["type"] == "credential" else 0.9

    # Adjust based on effort tolerance
    effort_multiplier = {
        "low": 1.2,
        "medium": 1.0,
        "high": 0.8,
    }
    base_score *= effort_multiplier.get(mechanism["effort_required"], 1.0)

    return min(1.0, base_score)


def generate_stakes(
    outline: CourseOutline,
    config: StakesConfig | None = None,
) -> list[StakesMechanism]:
    """Generate accountability mechanisms for the course.

    Args:
        outline: The CourseOutline to generate stakes for.
        config: Stakes configuration. Defaults to StakesConfig().

    Returns:
        A list of StakesMechanism objects.
    """
    if config is None:
        config = StakesConfig()

    # Score all mechanisms
    scored_mechanisms = []
    for idx, template in enumerate(_MECHANISM_TEMPLATES):
        score = _calculate_stakes_score(template, config)
        mechanism = StakesMechanism(
            id=f"stakes_{idx:03d}",
            name=template["name"],
            description=template["description"],
            type=template["type"],
            impact_score=round(score, 2),
            effort_required=template["effort_required"],
            implementation_steps=template["steps"],
        )
        scored_mechanisms.append(mechanism)

    # Sort by score descending
    scored_mechanisms.sort(key=lambda m: m.impact_score, reverse=True)

    # Select top N mechanisms
    n_select = min(config.max_mechanisms, len(scored_mechanisms))
    selected = scored_mechanisms[:n_select]

    # Add module-specific recommendations
    for module in outline.modules:
        for mechanism in selected:
            if not hasattr(mechanism, "module_recommendations"):
                mechanism.module_recommendations = []
            mechanism.module_recommendations.append(module.id)

    return selected


def get_recommended_stakes(outline: CourseOutline) -> list[StakesMechanism]:
    """Get recommended stakes for an outline using default config."""
    return generate_stakes(outline)
