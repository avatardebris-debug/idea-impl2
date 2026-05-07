"""SOP router — maps categories to teams, escalation rules, and SLA targets."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import yaml


class Router:
    """Routes tickets to teams based on category, priority, and escalation rules."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the router.

        Args:
            config_path: Path to the YAML router config file. If None, uses default path.
        """
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), "config", "router_config.yaml"
            )
        self.config = self._load_config(config_path)
        self.teams = self.config.get("teams", {})
        self.escalation_rules = self.config.get("escalation_rules", {})
        self.routing = self.config.get("routing", {})

    def _load_config(self, path: str) -> Dict[str, Any]:
        """Load router configuration from YAML file."""
        with open(path, "r") as f:
            return yaml.safe_load(f)

    def get_team_for_category(self, category: str) -> Optional[str]:
        """Get the team label for a given category.

        Args:
            category: The ticket category.

        Returns:
            Team label string, or None if no team found.
        """
        for team_name, team_info in self.teams.items():
            if category in team_info.get("categories", []):
                return team_info.get("label", team_name)
        return None

    def get_team_email(self, category: str) -> Optional[str]:
        """Get the email address for a team handling a category.

        Args:
            category: The ticket category.

        Returns:
            Email address string, or None if no team found.
        """
        for team_name, team_info in self.teams.items():
            if category in team_info.get("categories", []):
                return team_info.get("email")
        return None

    def get_slack_channel(self, category: str) -> Optional[str]:
        """Get the Slack channel for a team handling a category.

        Args:
            category: The ticket category.

        Returns:
            Slack channel string, or None if no team found.
        """
        for team_name, team_info in self.teams.items():
            if category in team_info.get("categories", []):
                return team_info.get("slack_channel")
        return None

    def get_routing_team(self, priority_score: int) -> Optional[str]:
        """Get the team to route to based on priority score.

        Args:
            priority_score: The ticket priority score (1-10).

        Returns:
            Team name string, or None if no routing rule matches.
        """
        priority_routing = self.routing.get("priority_routing", {})
        for range_str, team_name in priority_routing.items():
            low, high = map(int, range_str.split("-"))
            if low <= priority_score <= high:
                return team_name
        return None

    def should_escalate(self, priority_score: int, category: str) -> bool:
        """Check if a ticket should be escalated based on priority.

        Args:
            priority_score: The ticket priority score (1-10).
            category: The ticket category.

        Returns:
            True if the ticket should be escalated.
        """
        for rule in self.escalation_rules:
            if rule["priority_threshold"] <= priority_score:
                if rule.get("categories") is None or category in rule["categories"]:
                    return True
        return False

    def get_escalation_target(self, priority_score: int, category: str) -> Optional[str]:
        """Get the escalation target for a ticket.

        Args:
            priority_score: The ticket priority score (1-10).
            category: The ticket category.

        Returns:
            Escalation target string (e.g., team name or email), or None.
        """
        for rule in self.escalation_rules:
            if rule["priority_threshold"] <= priority_score:
                if rule.get("categories") is None or category in rule["categories"]:
                    return rule.get("target")
        return None

    def get_sla_hours(self, category: str, priority_score: int) -> int:
        """Get the SLA hours for a ticket.

        Args:
            category: The ticket category.
            priority_score: The ticket priority score (1-10).

        Returns:
            SLA hours as an integer.
        """
        sla = self.routing.get("sla", {})
        for cat, tiers in sla.items():
            if cat == category:
                for tier in tiers:
                    if tier["priority_max"] >= priority_score:
                        return tier["sla_hours"]
        return 72  # Default SLA

    def route(self, category: str, priority_score: int) -> Dict[str, Any]:
        """Route a ticket and return routing information.

        Args:
            category: The ticket category.
            priority_score: The ticket priority score (1-10).

        Returns:
            Dict with keys: team, email, slack_channel, should_escalate, escalation_target, sla_hours
        """
        team = self.get_team_for_category(category)
        email = self.get_team_email(category)
        slack_channel = self.get_slack_channel(category)
        should_escalate = self.should_escalate(priority_score, category)
        escalation_target = self.get_escalation_target(priority_score, category) if should_escalate else None
        sla_hours = self.get_sla_hours(category, priority_score)

        return {
            "team": team,
            "email": email,
            "slack_channel": slack_channel,
            "should_escalate": should_escalate,
            "escalation_target": escalation_target,
            "sla_hours": sla_hours,
        }

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Update the router configuration.

        Args:
            new_config: New configuration dictionary.
        """
        self.config = new_config
        self.teams = new_config.get("teams", {})
        self.escalation_rules = new_config.get("escalation_rules", [])
        self.routing = new_config.get("routing", {})

    def get_config(self) -> Dict[str, Any]:
        """Return the current configuration."""
        return self.config
