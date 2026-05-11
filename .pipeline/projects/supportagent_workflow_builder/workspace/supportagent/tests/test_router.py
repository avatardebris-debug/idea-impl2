"""Tests for the SOP router module."""

import os
import tempfile
import textwrap
import unittest

from supportagent.router import Router


class TestRouter(unittest.TestCase):
    """Tests for the Router class."""

    def _create_router(self, yaml_content: str) -> Router:
        """Create a Router with the given YAML config content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(textwrap.dedent(yaml_content))
            f.flush()
            path = f.name
        try:
            return Router(config_path=path)
        except Exception:
            os.unlink(path)
            raise

    def tearDown(self):
        """Clean up temp files."""
        # Note: the Router context manager doesn't clean up, so we rely on
        # the test framework's temp file handling.

    def test_get_team_for_category(self):
        """Test that categories map to the correct team labels."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing & Payments"
                email: "billing@company.com"
                slack_channel: "#billing-support"
                categories:
                  - billing
              technical_team:
                label: "Technical Support"
                email: "tech@company.com"
                slack_channel: "#tech-support"
                categories:
                  - technical
              general_team:
                label: "General Support"
                email: "general@company.com"
                slack_channel: "#general-support"
                categories:
                  - general
            escalation_rules: []
            routing: {}
        """)

        self.assertEqual(router.get_team_for_category("billing"), "Billing & Payments")
        self.assertEqual(router.get_team_for_category("technical"), "Technical Support")
        self.assertEqual(router.get_team_for_category("general"), "General Support")
        self.assertIsNone(router.get_team_for_category("unknown"))

    def test_get_team_email(self):
        """Test that team emails are returned correctly."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing"
                email: "billing@company.com"
                slack_channel: "#billing"
                categories:
                  - billing
            escalation_rules: []
            routing: {}
        """)

        self.assertEqual(router.get_team_email("billing"), "billing@company.com")
        self.assertIsNone(router.get_team_email("unknown"))

    def test_get_slack_channel(self):
        """Test that Slack channels are returned correctly."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing"
                email: "billing@company.com"
                slack_channel: "#billing-support"
                categories:
                  - billing
            escalation_rules: []
            routing: {}
        """)

        self.assertEqual(router.get_slack_channel("billing"), "#billing-support")
        self.assertIsNone(router.get_slack_channel("unknown"))

    def test_get_routing_team(self):
        """Test priority-based routing."""
        router = self._create_router("""
            teams: {}
            escalation_rules: []
            routing:
              priority_routing:
                "9-10": "escalation_team"
                "7-8": "technical_team"
                "5-6": "billing_team"
                "1-4": "general_team"
        """)

        self.assertEqual(router.get_routing_team(10), "escalation_team")
        self.assertEqual(router.get_routing_team(9), "escalation_team")
        self.assertEqual(router.get_routing_team(8), "technical_team")
        self.assertEqual(router.get_routing_team(7), "technical_team")
        self.assertEqual(router.get_routing_team(6), "billing_team")
        self.assertEqual(router.get_routing_team(5), "billing_team")
        self.assertEqual(router.get_routing_team(4), "general_team")
        self.assertEqual(router.get_routing_team(1), "general_team")
        self.assertIsNone(router.get_routing_team(0))  # Out of range

    def test_should_escalate(self):
        """Test escalation logic."""
        router = self._create_router("""
            teams: {}
            escalation_rules:
              - priority_threshold: 8
                action: "notify_escalation_team"
                target: "escalation_team"
              - priority_threshold: 5
                categories:
                  - urgent
                action: "notify_team_lead"
                target: "technical_team"
            routing: {}
        """)

        # Priority 8+ should always escalate
        self.assertTrue(router.should_escalate(8, "billing"))
        self.assertTrue(router.should_escalate(10, "general"))
        self.assertFalse(router.should_escalate(7, "billing"))

        # Category-specific escalation at threshold 5
        self.assertTrue(router.should_escalate(5, "urgent"))
        self.assertTrue(router.should_escalate(6, "urgent"))
        self.assertFalse(router.should_escalate(4, "urgent"))

    def test_get_escalation_target(self):
        """Test escalation target retrieval."""
        router = self._create_router("""
            teams: {}
            escalation_rules:
              - priority_threshold: 8
                action: "notify_escalation_team"
                target: "escalation_team"
              - priority_threshold: 5
                categories:
                  - urgent
                action: "notify_team_lead"
                target: "technical_team"
            routing: {}
        """)

        self.assertEqual(router.get_escalation_target(8, "billing"), "escalation_team")
        self.assertEqual(router.get_escalation_target(5, "urgent"), "technical_team")
        self.assertIsNone(router.get_escalation_target(4, "urgent"))

    def test_get_sla_hours(self):
        """Test SLA hour retrieval."""
        router = self._create_router("""
            teams: {}
            escalation_rules: []
            routing:
              sla:
                urgent:
                  - priority_max: 10
                    sla_hours: 1
                  - priority_max: 5
                    sla_hours: 4
                high:
                  - priority_max: 10
                    sla_hours: 4
                medium:
                  - priority_max: 10
                    sla_hours: 24
                low:
                  - priority_max: 10
                    sla_hours: 72
        """)

        self.assertEqual(router.get_sla_hours("urgent", 10), 1)
        self.assertEqual(router.get_sla_hours("urgent", 5), 4)
        self.assertEqual(router.get_sla_hours("high", 10), 4)
        self.assertEqual(router.get_sla_hours("medium", 10), 24)
        self.assertEqual(router.get_sla_hours("low", 10), 72)
        self.assertEqual(router.get_sla_hours("unknown", 10), 72)  # Default

    def test_route(self):
        """Test the full routing method."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing & Payments"
                email: "billing@company.com"
                slack_channel: "#billing-support"
                categories:
                  - billing
              technical_team:
                label: "Technical Support"
                email: "tech@company.com"
                slack_channel: "#tech-support"
                categories:
                  - technical
              escalation_team:
                label: "Escalation & Executive"
                email: "escalation@company.com"
                slack_channel: "#escalations"
                categories:
                  - urgent
              general_team:
                label: "General Support"
                email: "general@company.com"
                slack_channel: "#general-support"
                categories:
                  - general
            escalation_rules:
              - priority_threshold: 8
                action: "notify_escalation_team"
                target: "escalation_team"
            routing:
              sla:
                urgent:
                  - priority_max: 10
                    sla_hours: 1
                medium:
                  - priority_max: 10
                    sla_hours: 24
        """)

        result = router.route("billing", 3)
        self.assertEqual(result["team"], "Billing & Payments")
        self.assertEqual(result["email"], "billing@company.com")
        self.assertEqual(result["slack_channel"], "#billing-support")
        self.assertFalse(result["should_escalate"])
        self.assertIsNone(result["escalation_target"])
        self.assertEqual(result["sla_hours"], 24)

    def test_route_escalation(self):
        """Test routing with escalation."""
        router = self._create_router("""
            teams:
              technical_team:
                label: "Technical Support"
                email: "tech@company.com"
                slack_channel: "#tech-support"
                categories:
                  - technical
            escalation_rules:
              - priority_threshold: 8
                action: "notify_escalation_team"
                target: "escalation_team"
            routing:
              sla:
                urgent:
                  - priority_max: 10
                    sla_hours: 1
        """)

        result = router.route("technical", 9)
        self.assertEqual(result["team"], "Technical Support")
        self.assertTrue(result["should_escalate"])
        self.assertEqual(result["escalation_target"], "escalation_team")

    def test_update_config(self):
        """Test dynamic config update."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing"
                email: "billing@company.com"
                slack_channel: "#billing"
                categories:
                  - billing
            escalation_rules: []
            routing: {}
        """)

        new_config = textwrap.dedent("""
            teams:
              billing_team:
                label: "Billing & Payments"
                email: "billing@company.com"
                slack_channel: "#billing-support"
                categories:
                  - billing
            escalation_rules: []
            routing: {}
        """)

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(new_config)
            f.flush()
            path = f.name

        try:
            router.update_config(path)
            self.assertEqual(router.get_team_for_category("billing"), "Billing & Payments")
        finally:
            os.unlink(path)

    def test_get_all_teams(self):
        """Test retrieving all teams."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing"
                email: "billing@company.com"
                slack_channel: "#billing"
                categories:
                  - billing
              technical_team:
                label: "Technical"
                email: "tech@company.com"
                slack_channel: "#tech"
                categories:
                  - technical
            escalation_rules: []
            routing: {}
        """)

        teams = router.get_all_teams()
        self.assertIn("billing_team", teams)
        self.assertIn("technical_team", teams)
        self.assertEqual(len(teams), 2)

    def test_get_team_by_label(self):
        """Test finding team by label."""
        router = self._create_router("""
            teams:
              billing_team:
                label: "Billing & Payments"
                email: "billing@company.com"
                slack_channel: "#billing"
                categories:
                  - billing
            escalation_rules: []
            routing: {}
        """)

        team = router.get_team_by_label("Billing & Payments")
        self.assertIsNotNone(team)
        self.assertEqual(team["email"], "billing@company.com")
        self.assertIsNone(router.get_team_by_label("Unknown"))


if __name__ == "__main__":
    unittest.main()
