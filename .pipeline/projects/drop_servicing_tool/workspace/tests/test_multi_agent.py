"""Tests for Multi-Agent SOP Executor."""

import pytest
from drop_servicing_tool.multi_agent import MultiAgentSOPExecutor
from drop_servicing_tool.agent_config import AgentConfigList, AgentConfig, ProviderType
from drop_servicing_tool.agent_router import LLMClientRouter


class TestMultiAgentSOPExecutor:
    """Tests for MultiAgentSOPExecutor."""

    def test_init(self):
        """Test executor initialization."""
        acl = AgentConfigList()
        router = LLMClientRouter()
        executor = MultiAgentSOPExecutor(
            sop_name="test_sop",
            agent_config_list=acl,
            router=router,
        )
        assert executor.sop_name == "test_sop"
        assert executor.agent_config_list is acl
        assert executor.router is router

    def test_run_with_mock(self, tmp_path):
        """Test running SOP with mock client."""
        from drop_servicing_tool.executor import MockLLMClient

        # Create a test SOP
        sop_content = """
name: test_sop
description: Test SOP
inputs:
  - name: topic
    type: string
    required: true
steps:
  - name: step1
    description: First step
    llm_required: false
output_format: Test output
"""
        (tmp_path / "sops" / "test_sop.yaml").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "sops" / "test_sop.yaml").write_text(sop_content, encoding="utf-8")

        acl = AgentConfigList()
        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
        )
        acl.add_config(0, config)

        router = LLMClientRouter()
        executor = MultiAgentSOPExecutor(
            sop_name="test_sop",
            agent_config_list=acl,
            router=router,
            base_dir=tmp_path,
        )

        # Run with mock
        result = executor.run({"topic": "Test topic"})
        assert result["topic"] == "Test topic"
        assert "_sop_name" in result
        assert "_steps" in result

    def test_run_invalid_input(self, tmp_path):
        """Test running SOP with invalid input."""
        # Create a test SOP
        sop_content = """
name: test_sop
description: Test SOP
inputs:
  - name: topic
    type: string
    required: true
steps:
  - name: step1
    description: First step
    llm_required: false
output_format: Test output
"""
        (tmp_path / "sops" / "test_sop.yaml").parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / "sops" / "test_sop.yaml").write_text(sop_content, encoding="utf-8")

        acl = AgentConfigList()
        config = AgentConfig(
            provider=ProviderType.OPENAI,
            model="gpt-4o-mini",
        )
        acl.add_config(0, config)

        router = LLMClientRouter()
        executor = MultiAgentSOPExecutor(
            sop_name="test_sop",
            agent_config_list=acl,
            router=router,
            base_dir=tmp_path,
        )

        # Run with missing required field
        with pytest.raises(ValueError, match="Required input field"):
            executor.run({})

    def test_run_missing_sop(self):
        """Test running non-existent SOP."""
        acl = AgentConfigList()
        router = LLMClientRouter()
        executor = MultiAgentSOPExecutor(
            sop_name="nonexistent_sop",
            agent_config_list=acl,
            router=router,
        )

        with pytest.raises(FileNotFoundError):
            executor.run({"topic": "Test"})
