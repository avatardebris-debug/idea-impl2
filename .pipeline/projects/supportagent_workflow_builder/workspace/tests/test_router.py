"""Tests for the Router (Task 5)."""

import os
import tempfile
import textwrap
import pytest
from supportagent.router import Router


@pytest.fixture
def router_config_path():
    """Create a temporary router config file for testing."""
    config_yaml = textwrap.dedent("""\
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

          account_team:
            label: "Account Management"
            email: "accounts@company.com"
            slack_channel: "#account-support"
            categories:
              - account

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
            notify_slack: true
            notify_email: true
            target: "escalation_team"

          - priority_threshold: 5
            categories:
              - urgent
            action: "notify_team_lead"
            notify_slack: true
            target: "technical_team"

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

        routing:
          priority_routing:
            9-10: "escalation_team"
            7-8: "technical_team"
            5-6: "billing_team"
            3-4: "general_team"
            1-2: "general_team"
    """)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(config_yaml)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def router(router_config_path):
    """Create a Router instance with the test config."""
    return Router(config_path=router_config_path)


class TestRouterInitialization:
    def test_router_loads_teams(self, router):
        assert "billing_team" in router.teams
        assert "technical_team" in router.teams
        assert "account_team" in router.teams
        assert "escalation_team" in router.teams
        assert "general_team" in router.teams

    def test_router_loads_routing(self, router):
        assert router.routing is not None
        assert "priority_routing" in router.routing

    def test_router_loads_sla(self, router):
        assert router.sla is not None
        assert "urgent" in router.sla
        assert "high" in router.sla
        assert "medium" in router.sla
        assert "low" in router.sla

    def test_router_loads_escalation_rules(self, router):
        assert router.escalation_rules is not None
        assert len(router.escalation_rules) >= 1

    def test_router_invalid_config_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            with pytest.raises(Exception):  # YAML or config parsing error
                Router(config_path=f.name)
        os.unlink(f.name)


class TestGetTeamForCategory:
    def test_get_team_for_billing(self, router):
        team = router.get_team_for_category("billing")
        assert team == "billing_team"

    def test_get_team_for_technical(self, router):
        team = router.get_team_for_category("technical")
        assert team == "technical_team"

    def test_get_team_for_account(self, router):
        team = router.get_team_for_category("account")
        assert team == "account_team"

    def test_get_team_for_urgent(self, router):
        team = router.get_team_for_category("urgent")
        assert team == "escalation_team"

    def test_get_team_for_general(self, router):
        team = router.get_team_for_category("general")
        assert team == "general_team"

    def test_get_team_for_unknown_category(self, router):
        team = router.get_team_for_category("unknown_category")
        assert team == "general_team"


class TestGetPriorityRouting:
    def test_priority_9_10_escalation(self, router):
        team = router.get_priority_routing(9)
        assert team == "escalation_team"

    def test_priority_10_escalation(self, router):
        team = router.get_priority_routing(10)
        assert team == "escalation_team"

    def test_priority_7_8_technical(self, router):
        team = router.get_priority_routing(7)
        assert team == "technical_team"

    def test_priority_8_technical(self, router):
        team = router.get_priority_routing(8)
        assert team == "technical_team"

    def test_priority_5_6_billing(self, router):
        team = router.get_priority_routing(5)
        assert team == "billing_team"

    def test_priority_6_billing(self, router):
        team = router.get_priority_routing(6)
        assert team == "billing_team"

    def test_priority_3_4_general(self, router):
        team = router.get_priority_routing(3)
        assert team == "general_team"

    def test_priority_4_general(self, router):
        team = router.get_priority_routing(4)
        assert team == "general_team"

    def test_priority_1_2_general(self, router):
        team = router.get_priority_routing(1)
        assert team == "general_team"

    def test_priority_2_general(self, router):
        team = router.get_priority_routing(2)
        assert team == "general_team"

    def test_priority_0_defaults_to_general(self, router):
        team = router.get_priority_routing(0)
        assert team == "general_team"

    def test_priority_11_defaults_to_general(self, router):
        team = router.get_priority_routing(11)
        assert team == "general_team"


class TestGetSLA:
    def test_get_sla_urgent_high_priority(self, router):
        sla = router.get_sla("urgent", 10)
        assert sla == 1

    def test_get_sla_urgent_medium_priority(self, router):
        sla = router.get_sla("urgent", 5)
        assert sla == 4

    def test_get_sla_high(self, router):
        sla = router.get_sla("high", 10)
        assert sla == 4

    def test_get_sla_medium(self, router):
        sla = router.get_sla("medium", 10)
        assert sla == 24

    def test_get_sla_low(self, router):
        sla = router.get_sla("low", 10)
        assert sla == 72

    def test_get_sla_unknown_urgency(self, router):
        sla = router.get_sla("unknown", 10)
        assert sla == 24  # default


class TestGetEscalationRules:
    def test_get_escalation_rules_returns_list(self, router):
        rules = router.get_escalation_rules()
        assert isinstance(rules, list)
        assert len(rules) >= 1

    def test_escalation_rule_has_required_fields(self, router):
        rules = router.get_escalation_rules()
        for rule in rules:
            assert "priority_threshold" in rule
            assert "action" in rule
            assert "target" in rule


class TestRouteTicket:
    def test_route_ticket_billing(self, router):
        result = router.route_ticket(
            category="billing",
            urgency="medium",
            priority_score=5,
        )
        assert result["assigned_team"] == "billing_team"
        assert result["sla_hours"] == 24

    def test_route_ticket_technical(self, router):
        result = router.route_ticket(
            category="technical",
            urgency="high",
            priority_score=7,
        )
        assert result["assigned_team"] == "technical_team"
        assert result["sla_hours"] == 4

    def test_route_ticket_urgent(self, router):
        result = router.route_ticket(
            category="urgent",
            urgency="high",
            priority_score=9,
        )
        assert result["assigned_team"] == "escalation_team"
        assert result["sla_hours"] == 1

    def test_route_ticket_general(self, router):
        result = router.route_ticket(
            category="general",
            urgency="low",
            priority_score=2,
        )
        assert result["assigned_team"] == "general_team"
        assert result["sla_hours"] == 72

    def test_route_ticket_account(self, router):
        result = router.route_ticket(
            category="account",
            urgency="medium",
            priority_score=4,
        )
        assert result["assigned_team"] == "account_team"
        assert result["sla_hours"] == 24

    def test_route_ticket_unknown_category(self, router):
        result = router.route_ticket(
            category="unknown",
            urgency="low",
            priority_score=1,
        )
        assert result["assigned_team"] == "general_team"
        assert result["sla_hours"] == 72

    def test_route_ticket_high_priority_escalation(self, router):
        result = router.route_ticket(
            category="technical",
            urgency="high",
            priority_score=9,
        )
        assert result["assigned_team"] == "escalation_team"

    def test_route_ticket_with_slack_notification(self, router):
        result = router.route_ticket(
            category="urgent",
            urgency="high",
            priority_score=9,
        )
        assert result["notify_slack"] is True
        assert result["notify_email"] is True

    def test_route_ticket_low_priority_no_notification(self, router):
        result = router.route_ticket(
            category="general",
            urgency="low",
            priority_score=1,
        )
        assert result["notify_slack"] is False
        assert result["notify_email"] is False


class TestGetTeamDetails:
    def test_get_team_details_billing(self, router):
        details = router.get_team_details("billing_team")
        assert details["label"] == "Billing & Payments"
        assert details["email"] == "billing@company.com"
        assert details["slack_channel"] == "#billing-support"

    def test_get_team_details_technical(self, router):
        details = router.get_team_details("technical_team")
        assert details["label"] == "Technical Support"
        assert details["email"] == "tech@company.com"

    def test_get_team_details_unknown(self, router):
        details = router.get_team_details("unknown_team")
        assert details is None


class TestGetCategoryTeams:
    def test_get_category_teams_billing(self, router):
        teams = router.get_category_teams("billing")
        assert "billing_team" in teams

    def test_get_category_teams_technical(self, router):
        teams = router.get_category_teams("technical")
        assert "technical_team" in teams

    def test_get_category_teams_urgent(self, router):
        teams = router.get_category_teams("urgent")
        assert "escalation_team" in teams

    def test_get_category_teams_unknown(self, router):
        teams = router.get_category_teams("unknown")
        assert len(teams) == 0
