"""Tests for Agent Registry."""

import pytest
import json
from pathlib import Path
import tempfile

from drop_servicing_tool.agent_registry import AgentRegistry


class TestAgentRegistry:
    """Tests for AgentRegistry class."""

    def test_registry_initialization(self, tmp_path):
        """Test registry initialization."""
        registry = AgentRegistry(tmp_path)
        assert registry is not None
        assert registry._agents_dir.exists()

    def test_registry_default_directory(self, tmp_path):
        """Test registry uses default directory."""
        registry = AgentRegistry(tmp_path)
        assert registry._base == tmp_path
        assert registry._agents_dir == tmp_path / "agents"

    def test_register_agent(self, tmp_path):
        """Test registering an agent."""
        registry = AgentRegistry(tmp_path)
        mock_client = {"type": "mock_client"}

        registry.register_agent("test_agent", mock_client, {"description": "Test agent"})

        assert "test_agent" in registry._agents
        assert registry._agents["test_agent"] == mock_client
        assert registry._metadata["test_agent"] == {"description": "Test agent"}

    def test_register_agent_without_metadata(self, tmp_path):
        """Test registering agent without metadata."""
        registry = AgentRegistry(tmp_path)
        mock_client = {"type": "mock_client"}

        registry.register_agent("test_agent", mock_client)

        assert "test_agent" in registry._agents
        assert registry._metadata["test_agent"] == {}

    def test_register_agent_persists_to_disk(self, tmp_path):
        """Test that registered agent is persisted to disk."""
        registry = AgentRegistry(tmp_path)
        mock_client = {"type": "mock_client"}

        registry.register_agent("test_agent", mock_client, {"description": "Test"})

        agent_file = tmp_path / "agents" / "test_agent.json"
        assert agent_file.exists()

        data = json.loads(agent_file.read_text(encoding="utf-8"))
        assert data["name"] == "test_agent"
        assert data["metadata"] == {"description": "Test"}

    def test_get_agent(self, tmp_path):
        """Test getting a registered agent."""
        registry = AgentRegistry(tmp_path)
        mock_client = {"type": "mock_client"}

        registry.register_agent("test_agent", mock_client)

        agent = registry.get_agent("test_agent")
        assert agent == mock_client

    def test_get_agent_not_found(self, tmp_path):
        """Test getting non-existent agent."""
        registry = AgentRegistry(tmp_path)

        with pytest.raises(KeyError, match="Agent 'nonexistent' not found"):
            registry.get_agent("nonexistent")

    def test_list_agents(self, tmp_path):
        """Test listing registered agents."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("agent1", {"type": "mock"})
        registry.register_agent("agent2", {"type": "mock"})
        registry.register_agent("agent3", {"type": "mock"})

        agents = registry.list_agents()
        assert len(agents) == 3
        assert "agent1" in agents
        assert "agent2" in agents
        assert "agent3" in agents

    def test_delete_agent(self, tmp_path):
        """Test deleting an agent."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("test_agent", {"type": "mock"})

        result = registry.delete_agent("test_agent")
        assert result is True
        assert "test_agent" not in registry._agents
        assert "test_agent" not in registry._metadata

    def test_delete_agent_not_found(self, tmp_path):
        """Test deleting non-existent agent."""
        registry = AgentRegistry(tmp_path)

        result = registry.delete_agent("nonexistent")
        assert result is False

    def test_delete_agent_removes_from_disk(self, tmp_path):
        """Test that deleting agent removes from disk."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("test_agent", {"type": "mock"})

        agent_file = tmp_path / "agents" / "test_agent.json"
        assert agent_file.exists()

        registry.delete_agent("test_agent")
        assert not agent_file.exists()

    def test_get_metadata(self, tmp_path):
        """Test getting agent metadata."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("test_agent", {"type": "mock"}, {"description": "Test"})

        metadata = registry.get_metadata("test_agent")
        assert metadata == {"description": "Test"}

    def test_get_metadata_not_found(self, tmp_path):
        """Test getting metadata for non-existent agent."""
        registry = AgentRegistry(tmp_path)

        with pytest.raises(KeyError, match="Agent 'nonexistent' not found"):
            registry.get_metadata("nonexistent")

    def test_load_existing_agents(self, tmp_path):
        """Test loading existing agents from disk."""
        # Create agent files manually
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        agent_file = agents_dir / "existing_agent.json"
        agent_file.write_text(json.dumps({
            "name": "existing_agent",
            "metadata": {"description": "Existing"}
        }), encoding="utf-8")

        registry = AgentRegistry(tmp_path)

        assert "existing_agent" in registry._agents
        assert registry._metadata["existing_agent"] == {"description": "Existing"}

    def test_load_existing_agents_with_client(self, tmp_path):
        """Test loading existing agents with client data."""
        agents_dir = tmp_path / "agents"
        agents_dir.mkdir()

        agent_file = agents_dir / "existing_agent.json"
        agent_file.write_text(json.dumps({
            "name": "existing_agent",
            "client": {"type": "mock_client"},
            "metadata": {"description": "Existing"}
        }), encoding="utf-8")

        registry = AgentRegistry(tmp_path)

        assert "existing_agent" in registry._agents
        assert registry._agents["existing_agent"] == {"type": "mock_client"}


class TestAgentRegistryPersistence:
    """Tests for AgentRegistry persistence."""

    def test_persistence_across_instances(self, tmp_path):
        """Test that agents persist across registry instances."""
        # Create first registry and register agent
        registry1 = AgentRegistry(tmp_path)
        registry1.register_agent("test_agent", {"type": "mock"}, {"description": "Test"})

        # Create second registry instance
        registry2 = AgentRegistry(tmp_path)

        # Agent should still be registered
        assert "test_agent" in registry2._agents
        assert registry2.get_agent("test_agent") == {"type": "mock"}

    def test_multiple_agents_persistence(self, tmp_path):
        """Test persistence of multiple agents."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("agent1", {"type": "mock1"}, {"desc": "1"})
        registry.register_agent("agent2", {"type": "mock2"}, {"desc": "2"})
        registry.register_agent("agent3", {"type": "mock3"}, {"desc": "3"})

        # Create new instance
        registry2 = AgentRegistry(tmp_path)

        assert len(registry2.list_agents()) == 3
        assert registry2.get_agent("agent1") == {"type": "mock1"}
        assert registry2.get_agent("agent2") == {"type": "mock2"}
        assert registry2.get_agent("agent3") == {"type": "mock3"}


class TestAgentRegistryValidation:
    """Tests for AgentRegistry validation."""

    def test_register_agent_with_empty_name(self, tmp_path):
        """Test registering agent with empty name."""
        registry = AgentRegistry(tmp_path)

        with pytest.raises(ValueError, match="Agent name cannot be empty"):
            registry.register_agent("", {"type": "mock"})

    def test_register_agent_with_special_chars(self, tmp_path):
        """Test registering agent with special characters."""
        registry = AgentRegistry(tmp_path)

        # Should work with special characters
        registry.register_agent("test-agent_123", {"type": "mock"})
        assert "test-agent_123" in registry._agents

    def test_delete_agent_with_special_chars(self, tmp_path):
        """Test deleting agent with special characters."""
        registry = AgentRegistry(tmp_path)

        registry.register_agent("test-agent_123", {"type": "mock"})
        result = registry.delete_agent("test-agent_123")
        assert result is True
