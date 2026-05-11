"""Tests for the smart_router module — Agent, Team, TeamRegistry, SmartRouter."""

import os
import tempfile
import textwrap
import unittest

from supportagent.smart_router import (
    Agent,
    SmartRouter,
    Team,
    TeamRegistry,
)


class TestAgent(unittest.TestCase):
    """Tests for the Agent class."""

    def test_agent_creation(self):
        """Test basic Agent creation."""
        agent = Agent(
            name="Alice",
            team="billing",
            skills=["billing", "account"],
            availability=0.8,
        )
        self.assertEqual(agent.name, "Alice")
        self.assertEqual(agent.team, "billing")
        self.assertEqual(agent.skills, ["billing", "account"])
        self.assertEqual(agent.availability, 0.8)
        self.assertEqual(agent.workload, 0)
        self.assertEqual(agent.status, "available")

    def test_agent_availability_calculation(self):
        """Test that availability is clamped to [0, 1]."""
        agent = Agent(name="Bob", team="tech", skills=["technical"], availability=1.5)
        self.assertEqual(agent.availability, 1.0)

        agent2 = Agent(name="Carol", team="tech", skills=["technical"], availability=-0.5)
        self.assertEqual(agent2.availability, 0.0)

    def test_agent_status_update(self):
        """Test updating agent status."""
        agent = Agent(name="Dave", team="tech", skills=["technical"])
        self.assertEqual(agent.status, "available")

        agent.status = "busy"
        self.assertEqual(agent.status, "busy")

        agent.status = "offline"
        self.assertEqual(agent.status, "offline")


class TestTeam(unittest.TestCase):
    """Tests for the Team class."""

    def test_team_creation(self):
        """Test basic Team creation."""
        team = Team(
            name="billing",
            label="Billing & Payments",
            email="billing@company.com",
            slack_channel="#billing-support",
            categories=["billing"],
        )
        self.assertEqual(team.name, "billing")
        self.assertEqual(team.label, "Billing & Payments")
        self.assertEqual(team.email, "billing@company.com")
        self.assertEqual(team.slack_channel, "#billing-support")
        self.assertEqual(team.categories, ["billing"])
        self.assertEqual(team.agents, [])

    def test_team_add_agent(self):
        """Test adding an agent to a team."""
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        agent = Agent(name="Eve", team="tech", skills=["technical"])
        team.add_agent(agent)
        self.assertIn(agent, team.agents)
        self.assertEqual(len(team.agents), 1)

    def test_team_remove_agent(self):
        """Test removing an agent from a team."""
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        agent = Agent(name="Frank", team="tech", skills=["technical"])
        team.add_agent(agent)
        team.remove_agent(agent)
        self.assertNotIn(agent, team.agents)
        self.assertEqual(len(team.agents), 0)


class TestTeamRegistry(unittest.TestCase):
    """Tests for the TeamRegistry class."""

    def test_registry_creation(self):
        """Test basic TeamRegistry creation."""
        registry = TeamRegistry()
        self.assertEqual(registry.teams, {})
        self.assertEqual(registry.agents, [])

    def test_add_team(self):
        """Test adding a team to the registry."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)
        self.assertIn("billing", registry.teams)
        self.assertEqual(registry.teams["billing"], team)

    def test_get_team(self):
        """Test retrieving a team by name."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        retrieved = registry.get_team("tech")
        self.assertEqual(retrieved, team)

        self.assertIsNone(registry.get_team("nonexistent"))

    def test_get_team_by_category(self):
        """Test retrieving a team by category."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing", "payments"])
        registry.add_team(team)

        retrieved = registry.get_team_by_category("billing")
        self.assertEqual(retrieved, team)

        retrieved2 = registry.get_team_by_category("payments")
        self.assertEqual(retrieved2, team)

        self.assertIsNone(registry.get_team_by_category("unknown"))

    def test_get_all_teams(self):
        """Test retrieving all teams."""
        registry = TeamRegistry()
        team1 = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        team2 = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team1)
        registry.add_team(team2)

        teams = registry.get_all_teams()
        self.assertIn(team1, teams)
        self.assertIn(team2, teams)
        self.assertEqual(len(teams), 2)

    def test_get_agents_by_team(self):
        """Test retrieving agents by team name."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical"])
        agent2 = Agent(name="Bob", team="tech", skills=["technical"])
        registry.agents.extend([agent1, agent2])

        agents = registry.get_agents_by_team("tech")
        self.assertIn(agent1, agents)
        self.assertIn(agent2, agents)
        self.assertEqual(len(agents), 2)

    def test_get_agents_by_team_empty(self):
        """Test retrieving agents for a team with no agents."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agents = registry.get_agents_by_team("tech")
        self.assertEqual(agents, [])

    def test_get_agents_by_skill(self):
        """Test retrieving agents by skill."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical", "billing"])
        agent2 = Agent(name="Bob", team="tech", skills=["technical"])
        agent3 = Agent(name="Carol", team="billing", skills=["billing"])
        registry.agents.extend([agent1, agent2, agent3])

        agents = registry.get_agents_by_skill("technical")
        self.assertIn(agent1, agents)
        self.assertIn(agent2, agents)
        self.assertNotIn(agent3, agents)
        self.assertEqual(len(agents), 2)

    def test_get_agents_by_skill_empty(self):
        """Test retrieving agents by skill when no agents have that skill."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent = Agent(name="Alice", team="tech", skills=["billing"])
        registry.agents.append(agent)

        agents = registry.get_agents_by_skill("technical")
        self.assertEqual(agents, [])

    def test_get_agents_by_availability(self):
        """Test retrieving agents by minimum availability."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical"], availability=0.9)
        agent2 = Agent(name="Bob", team="tech", skills=["technical"], availability=0.3)
        agent3 = Agent(name="Carol", team="tech", skills=["technical"], availability=0.5)
        registry.agents.extend([agent1, agent2, agent3])

        agents = registry.get_agents_by_availability(min_availability=0.5)
        self.assertIn(agent1, agents)
        self.assertIn(agent3, agents)
        self.assertNotIn(agent2, agents)
        self.assertEqual(len(agents), 2)

    def test_get_agents_by_availability_all(self):
        """Test retrieving all agents when min_availability is 0."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical"], availability=0.1)
        agent2 = Agent(name="Bob", team="tech", skills=["technical"], availability=0.0)
        registry.agents.extend([agent1, agent2])

        agents = registry.get_agents_by_availability(min_availability=0)
        self.assertIn(agent1, agents)
        self.assertIn(agent2, agents)
        self.assertEqual(len(agents), 2)

    def test_get_agents_by_availability_none(self):
        """Test retrieving no agents when min_availability is 1.0 and all have less."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical"], availability=0.5)
        agent2 = Agent(name="Bob", team="tech", skills=["technical"], availability=0.3)
        registry.agents.extend([agent1, agent2])

        agents = registry.get_agents_by_availability(min_availability=1.0)
        self.assertEqual(agents, [])

    def test_get_all_agents(self):
        """Test retrieving all agents."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent1 = Agent(name="Alice", team="tech", skills=["technical"])
        agent2 = Agent(name="Bob", team="tech", skills=["technical"])
        registry.agents.extend([agent1, agent2])

        agents = registry.get_all_agents()
        self.assertIn(agent1, agents)
        self.assertIn(agent2, agents)
        self.assertEqual(len(agents), 2)

    def test_get_all_agents_empty(self):
        """Test retrieving all agents when registry is empty."""
        registry = TeamRegistry()
        agents = registry.get_all_agents()
        self.assertEqual(agents, [])

    def test_get_team_by_label(self):
        """Test retrieving a team by label."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing & Payments", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_label("Billing & Payments")
        self.assertEqual(retrieved, team)

        self.assertIsNone(registry.get_team_by_label("Unknown"))

    def test_get_team_by_slack_channel(self):
        """Test retrieving a team by Slack channel."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech-support", categories=["technical"])
        registry.add_team(team)

        retrieved = registry.get_team_by_slack_channel("#tech-support")
        self.assertEqual(retrieved, team)

        self.assertIsNone(registry.get_team_by_slack_channel("#unknown"))

    def test_get_team_by_email(self):
        """Test retrieving a team by email."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_email("billing@company.com")
        self.assertEqual(retrieved, team)

        self.assertIsNone(registry.get_team_by_email("unknown@company.com"))

    def test_get_all_teams_by_category(self):
        """Test retrieving all teams that have a given category."""
        registry = TeamRegistry()
        team1 = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing", "payments"])
        team2 = Team(name="account", label="Account", email="account@company.com", slack_channel="#account", categories=["account", "billing"])
        team3 = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team1)
        registry.add_team(team2)
        registry.add_team(team3)

        teams = registry.get_all_teams_by_category("billing")
        self.assertIn(team1, teams)
        self.assertIn(team2, teams)
        self.assertNotIn(team3, teams)
        self.assertEqual(len(teams), 2)

    def test_get_all_teams_by_category_empty(self):
        """Test retrieving all teams by category when no teams match."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        teams = registry.get_all_teams_by_category("billing")
        self.assertEqual(teams, [])

    def test_get_team_by_name(self):
        """Test retrieving a team by name."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_name("billing")
        self.assertEqual(retrieved, team)

        self.assertIsNone(registry.get_team_by_name("nonexistent"))

    def test_remove_team(self):
        """Test removing a team from the registry."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)
        registry.remove_team("billing")
        self.assertNotIn("billing", registry.teams)
        self.assertIsNone(registry.get_team("billing"))

    def test_remove_team_nonexistent(self):
        """Test removing a nonexistent team."""
        registry = TeamRegistry()
        registry.remove_team("nonexistent")
        self.assertEqual(len(registry.teams), 0)

    def test_remove_agent(self):
        """Test removing an agent from the registry."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent = Agent(name="Alice", team="tech", skills=["technical"])
        registry.agents.append(agent)
        registry.remove_agent(agent)
        self.assertNotIn(agent, registry.agents)
        self.assertEqual(len(registry.agents), 0)

    def test_remove_agent_nonexistent(self):
        """Test removing a nonexistent agent."""
        registry = TeamRegistry()
        agent = Agent(name="Alice", team="tech", skills=["technical"])
        registry.remove_agent(agent)
        self.assertEqual(len(registry.agents), 0)

    def test_update_team(self):
        """Test updating a team in the registry."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        updated_team = Team(name="billing", label="Billing & Payments", email="billing@company.com", slack_channel="#billing-support", categories=["billing", "payments"])
        registry.update_team(updated_team)
        self.assertEqual(registry.teams["billing"].label, "Billing & Payments")
        self.assertEqual(registry.teams["billing"].categories, ["billing", "payments"])

    def test_update_team_nonexistent(self):
        """Test updating a nonexistent team."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.update_team(team)
        self.assertNotIn("billing", registry.teams)

    def test_update_agent(self):
        """Test updating an agent in the registry."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#tech", categories=["technical"])
        registry.add_team(team)

        agent = Agent(name="Alice", team="tech", skills=["technical"])
        registry.agents.append(agent)

        updated_agent = Agent(name="Alice", team="tech", skills=["technical", "billing"])
        registry.update_agent(updated_agent)
        self.assertEqual(registry.agents[0].skills, ["technical", "billing"])

    def test_update_agent_nonexistent(self):
        """Test updating a nonexistent agent."""
        registry = TeamRegistry()
        agent = Agent(name="Alice", team="tech", skills=["technical"])
        registry.update_agent(agent)
        self.assertEqual(len(registry.agents), 0)

    def test_get_team_by_name_case_insensitive(self):
        """Test that get_team_by_name is case-insensitive."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_name("BILLING")
        self.assertEqual(retrieved, team)

        retrieved2 = registry.get_team_by_name("Billing")
        self.assertEqual(retrieved2, team)

    def test_get_team_by_label_case_insensitive(self):
        """Test that get_team_by_label is case-insensitive."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing & Payments", email="billing@company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_label("BILLING & PAYMENTS")
        self.assertEqual(retrieved, team)

        retrieved2 = registry.get_team_by_label("billing & payments")
        self.assertEqual(retrieved2, team)

    def test_get_team_by_slack_channel_case_insensitive(self):
        """Test that get_team_by_slack_channel is case-insensitive."""
        registry = TeamRegistry()
        team = Team(name="tech", label="Technical", email="tech@company.com", slack_channel="#Tech-Support", categories=["technical"])
        registry.add_team(team)

        retrieved = registry.get_team_by_slack_channel("#tech-support")
        self.assertEqual(retrieved, team)

    def test_get_team_by_email_case_insensitive(self):
        """Test that get_team_by_email is case-insensitive."""
        registry = TeamRegistry()
        team = Team(name="billing", label="Billing", email="Billing@Company.com", slack_channel="#billing", categories=["billing"])
        registry.add_team(team)

        retrieved = registry.get_team_by_email("billing@company.com")
        self.assertEqual(retrieved, team)


class TestSmartRouter(unittest.TestCase):
    """Tests for the SmartRouter class."""

    def _create_router(self, yaml_content: str) -> SmartRouter:
        """Create a Router with the given YAML config content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write(textwrap.dedent(yaml_content))
            f.flush()
            path = f.name
        try:
            return SmartRouter(config_path=path)
        except Exception:
            os.unlink(path)
            raise

    def tearDown(self):
        """Clean up temp files."""
        pass

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
