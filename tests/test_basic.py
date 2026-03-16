"""
Basic tests for FixOpenclaw components.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.agents.base_agent import BaseAgent, AgentMessage, AgentState
from src.agents.monitor_agent import MonitorAgent
from src.utils.config_loader import ConfigLoader


class TestAgent(BaseAgent):
    """Test agent implementation."""

    def process_message(self, message: AgentMessage):
        return None

    def execute_task(self, task):
        return {"status": "success"}


def test_base_agent_creation():
    """Test base agent creation."""
    agent = TestAgent("test_agent", "test", {})
    assert agent.agent_id == "test_agent"
    assert agent.agent_type == "test"
    assert agent.state.status == "idle"


def test_agent_message():
    """Test agent message creation."""
    message = AgentMessage(
        sender="agent1",
        receiver="agent2",
        message_type="test",
        content={"data": "test"}
    )
    assert message.sender == "agent1"
    assert message.receiver == "agent2"
    assert message.message_type == "test"


def test_monitor_agent():
    """Test monitor agent creation."""
    config = {
        "log_paths": ["logs/test.log"],
        "check_interval": 5
    }
    agent = MonitorAgent("monitor_test", config)
    assert agent.agent_id == "monitor_test"
    assert agent.agent_type == "monitor"


def test_config_loader():
    """Test configuration loader."""
    loader = ConfigLoader("config/config.yaml")

    # Test if config file exists
    try:
        config = loader.load()
        assert isinstance(config, dict)
        assert "llm_provider" in config or "monitoring" in config
    except FileNotFoundError:
        # Config file might not exist in test environment
        pytest.skip("Config file not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
