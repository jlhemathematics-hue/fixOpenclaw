"""
Test cases for agent implementations
"""

import pytest
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.agents.base_agent import BaseAgent, AgentMessage, AgentState
from src.agents.monitor_agent import MonitorAgent
from src.agents.diagnostic_agent import DiagnosticAgent
from src.agents.repair_agent import RepairAgent
from src.agents.validation_agent import ValidationAgent


class TestBaseAgent:
    """Test base agent functionality"""

    def test_agent_initialization(self):
        """Test agent can be initialized"""
        # Create a concrete implementation for testing
        class TestAgent(BaseAgent):
            def process_message(self, message):
                return None

            def execute_task(self, task):
                return {"status": "success"}

        agent = TestAgent("test_agent", "test", {"key": "value"})
        assert agent.agent_id == "test_agent"
        assert agent.agent_type == "test"
        assert agent.config["key"] == "value"
        assert agent.state.status == "idle"

    def test_agent_message_creation(self):
        """Test message creation"""
        message = AgentMessage(
            sender="agent1",
            receiver="agent2",
            message_type="test",
            content={"data": "test"}
        )
        assert message.sender == "agent1"
        assert message.receiver == "agent2"
        assert message.message_type == "test"
        assert message.content["data"] == "test"

    def test_agent_state(self):
        """Test agent state management"""
        state = AgentState()
        assert state.status == "idle"
        assert state.current_task is None

        state.status = "working"
        assert state.status == "working"


class TestMonitorAgent:
    """Test monitor agent functionality"""

    def test_monitor_agent_initialization(self):
        """Test monitor agent initialization"""
        config = {
            "log_paths": ["/tmp/test.log"],
            "check_interval": 5
        }
        agent = MonitorAgent("monitor1", config)
        assert agent.agent_id == "monitor1"
        assert agent.agent_type == "monitor"
        assert agent.log_paths == ["/tmp/test.log"]
        assert agent.check_interval == 5

    def test_default_patterns(self):
        """Test default anomaly patterns"""
        agent = MonitorAgent("monitor1")
        patterns = agent._default_patterns()
        assert len(patterns) > 0
        assert any(p["name"] == "error" for p in patterns)
        assert any(p["name"] == "exception" for p in patterns)

    def test_scan_log_file(self, tmp_path):
        """Test log file scanning"""
        # Create temporary log file
        log_file = tmp_path / "test.log"
        log_file.write_text("""
2024-03-16 10:00:00 INFO Starting service
2024-03-16 10:00:01 ERROR Database connection failed
2024-03-16 10:00:02 Exception in thread main
2024-03-16 10:00:03 WARNING Memory usage high
        """)

        agent = MonitorAgent("monitor1")
        anomalies = agent._scan_log_file(str(log_file))

        assert len(anomalies) >= 2  # At least ERROR and Exception
        assert any(a["type"] == "error" for a in anomalies)
        assert any(a["type"] == "exception" for a in anomalies)

    def test_monitor_logs_task(self, tmp_path):
        """Test monitor logs task execution"""
        log_file = tmp_path / "test.log"
        log_file.write_text("2024-03-16 10:00:00 ERROR Test error\n")

        agent = MonitorAgent("monitor1")
        task = {
            "type": "monitor_logs",
            "log_file": str(log_file)
        }
        result = agent.execute_task(task)

        assert result["status"] == "success"
        assert result["anomalies_found"] > 0

    def test_health_check_task(self):
        """Test health check task"""
        agent = MonitorAgent("monitor1")
        task = {"type": "check_health"}
        result = agent.execute_task(task)

        assert result["status"] == "success"
        assert "overall_health" in result
        assert "checks" in result


class TestDiagnosticAgent:
    """Test diagnostic agent functionality"""

    def test_diagnostic_agent_initialization(self):
        """Test diagnostic agent initialization"""
        config = {"llm_provider": "openai"}
        agent = DiagnosticAgent("diag1", config)
        assert agent.agent_id == "diag1"
        assert agent.agent_type == "diagnostic"

    def test_classify_anomaly(self):
        """Test anomaly classification"""
        agent = DiagnosticAgent("diag1")
        anomaly = {
            "type": "error",
            "severity": "high",
            "line_content": "ERROR Database connection timeout"
        }
        classification = agent._classify_anomaly(anomaly)

        assert "category" in classification
        assert "root_cause_hints" in classification
        assert "impact" in classification

    def test_diagnose_task_without_llm(self):
        """Test diagnosis without LLM (offline mode)"""
        agent = DiagnosticAgent("diag1", {"llm_provider": None})
        anomaly = {
            "type": "error",
            "severity": "high",
            "category": "database",
            "line_content": "ERROR Database connection timeout",
            "context": "Full error context..."
        }
        task = {
            "type": "diagnose",
            "anomaly": anomaly
        }
        result = agent.execute_task(task)

        assert result["status"] == "success"
        assert "diagnosis" in result


class TestRepairAgent:
    """Test repair agent functionality"""

    def test_repair_agent_initialization(self):
        """Test repair agent initialization"""
        config = {"auto_repair": True}
        agent = RepairAgent("repair1", config)
        assert agent.agent_id == "repair1"
        assert agent.agent_type == "repair"
        assert agent.auto_repair is True

    def test_assess_risk(self):
        """Test risk assessment"""
        agent = RepairAgent("repair1")
        diagnosis = {
            "severity": "critical",
            "category": "database",
            "root_cause": "Connection pool exhausted"
        }
        risk = agent._assess_risk(diagnosis)

        assert risk in ["low", "medium", "high"]

    def test_generate_repair_plan_without_llm(self):
        """Test repair plan generation without LLM"""
        agent = RepairAgent("repair1", {"llm_provider": None})
        diagnosis = {
            "anomaly_type": "error",
            "severity": "high",
            "category": "database",
            "root_cause": "Connection timeout",
            "impact": "Service degradation"
        }
        plan = agent._generate_repair_plan(diagnosis)

        assert "strategy" in plan
        assert "steps" in plan
        assert "risk_level" in plan

    def test_generate_repair_task(self):
        """Test repair task execution"""
        agent = RepairAgent("repair1", {"llm_provider": None})
        diagnosis = {
            "anomaly_type": "error",
            "severity": "high",
            "category": "database",
            "root_cause": "Connection timeout"
        }
        task = {
            "type": "generate_repair",
            "diagnosis": diagnosis
        }
        result = agent.execute_task(task)

        assert result["status"] == "success"
        assert "repair_plan" in result


class TestValidationAgent:
    """Test validation agent functionality"""

    def test_validation_agent_initialization(self):
        """Test validation agent initialization"""
        agent = ValidationAgent("valid1")
        assert agent.agent_id == "valid1"
        assert agent.agent_type == "validation"

    def test_pre_validation(self):
        """Test pre-validation"""
        agent = ValidationAgent("valid1")
        repair_plan = {
            "strategy": "restart_service",
            "steps": ["backup", "restart"],
            "risk_level": "medium"
        }
        result = agent._pre_validate(repair_plan)

        assert "status" in result
        assert "checks" in result

    def test_post_validation(self):
        """Test post-validation"""
        agent = ValidationAgent("valid1")
        repair_result = {
            "status": "success",
            "changes": ["restarted service"]
        }
        result = agent._post_validate(repair_result)

        assert "status" in result
        assert "validation_passed" in result

    def test_validate_task(self):
        """Test validation task execution"""
        agent = ValidationAgent("valid1")
        repair_plan = {
            "strategy": "config_update",
            "steps": ["backup", "update", "restart"],
            "risk_level": "low"
        }
        task = {
            "type": "pre_validate",
            "repair_plan": repair_plan
        }
        result = agent.execute_task(task)

        assert result["status"] == "success"


class TestAgentCommunication:
    """Test agent-to-agent communication"""

    def test_message_sending(self):
        """Test sending messages between agents"""
        class TestAgent(BaseAgent):
            def process_message(self, message):
                return self.send_message(
                    receiver=message.sender,
                    message_type="response",
                    content={"received": True}
                )

            def execute_task(self, task):
                return {"status": "success"}

        agent1 = TestAgent("agent1", "test")
        agent2 = TestAgent("agent2", "test")

        # Send message from agent1 to agent2
        message = agent1.send_message(
            receiver="agent2",
            message_type="test",
            content={"data": "test"}
        )

        assert message.sender == "agent1"
        assert message.receiver == "agent2"

        # Agent2 receives and processes
        agent2.receive_message(message)
        assert len(agent2.mailbox) == 1

        responses = agent2.process_mailbox()
        assert len(responses) == 1
        assert responses[0].receiver == "agent1"

    def test_agent_state_updates(self):
        """Test agent state updates"""
        class TestAgent(BaseAgent):
            def process_message(self, message):
                return None

            def execute_task(self, task):
                self.update_state(
                    status="working",
                    current_task="test_task",
                    last_action="processing"
                )
                return {"status": "success"}

        agent = TestAgent("agent1", "test")
        agent.execute_task({"type": "test"})

        state = agent.get_state()
        assert state.status == "working"
        assert state.current_task == "test_task"
        assert state.last_action == "processing"


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
