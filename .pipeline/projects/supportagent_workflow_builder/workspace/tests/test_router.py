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
    f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
    f.write(config_yaml)
    f.close()
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



    def test_router_loads_escalation_rules(self, router):
        assert router.escalation_rules is not None
        assert len(router.escalation_rules) >= 1

    def test_router_invalid_config_raises(self):
        f = tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False)
        f.write("invalid: yaml: content: [")
        f.close()
        with pytest.raises(Exception):  # YAML or config parsing error
            Router(config_path=f.name)
        os.unlink(f.name)


