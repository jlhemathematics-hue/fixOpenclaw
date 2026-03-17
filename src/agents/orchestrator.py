"""
Orchestrator

Coordinates all agents and manages the overall autonomous repair workflow.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
from queue import Queue
from threading import Thread, Lock

from .base_agent import BaseAgent, AgentMessage
from .monitor_agent import MonitorAgent
from .diagnostic_agent import DiagnosticAgent
from .repair_agent import RepairAgent
from .validation_agent import ValidationAgent


class Orchestrator:
    """
    Central orchestrator that coordinates all agents.

    Responsibilities:
    - Initialize and manage all agents
    - Route messages between agents
    - Coordinate autonomous repair workflow
    - Manage system state
    - Handle events and notifications
    - Provide unified status reporting
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize orchestrator.

        Args:
            config: System configuration
        """
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Message routing
        self.message_queue = Queue()
        self.message_lock = Lock()

        # State management (initialize BEFORE agents)
        self.system_state = {
            "status": "initializing",
            "active_workflows": [],
            "total_anomalies_detected": 0,
            "total_repairs_attempted": 0,
            "total_repairs_successful": 0,
            "total_repairs_failed": 0,
            "last_activity": None
        }

        # Workflow tracking
        self.workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_counter = 0

        self.running = False
        self.message_thread = None

        # Agents (initialize AFTER state)
        self.agents: Dict[str, BaseAgent] = {}
        self._initialize_agents()

    def _initialize_agents(self) -> None:
        """Initialize all agents."""
        try:
            # Monitor agent
            monitor_config = self.config.get("monitoring", {})
            self.agents["monitor"] = MonitorAgent(
                agent_id="monitor_agent",
                config=monitor_config
            )
            self.logger.info("Initialized Monitor Agent")

            # Diagnostic agent
            llm_config = self._get_llm_config()
            diagnostic_config = self.config.get("diagnostic", {})
            self.agents["diagnostic"] = DiagnosticAgent(
                agent_id="diagnostic_agent",
                llm_config=llm_config,
                config=diagnostic_config
            )
            self.logger.info("Initialized Diagnostic Agent")

            # Repair agent
            repair_config = self.config.get("repair", {})
            self.agents["repair"] = RepairAgent(
                agent_id="repair_agent",
                llm_config=llm_config,
                config=repair_config
            )
            self.logger.info("Initialized Repair Agent")

            # Validation agent
            validation_config = self.config.get("validation", {})
            self.agents["validation"] = ValidationAgent(
                agent_id="validation_agent",
                config=validation_config
            )
            self.logger.info("Initialized Validation Agent")

            self.system_state["status"] = "ready"

        except Exception as e:
            self.logger.error(f"Failed to initialize agents: {e}")
            self.system_state["status"] = "error"
            raise

    def _get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration.

        Returns:
            LLM configuration dictionary
        """
        llm_config = self.config.get("llm_provider", {})
        default_provider = llm_config.get("default", "openai")

        provider_config = llm_config.get(default_provider, {})

        return {
            "provider": default_provider,
            **provider_config
        }

    def start(self) -> None:
        """Start the orchestrator and all agents."""
        self.logger.info("Starting orchestrator")
        self.running = True
        self.system_state["status"] = "running"

        # Start message processing thread
        self.message_thread = Thread(target=self._process_messages, daemon=True)
        self.message_thread.start()

        self.logger.info("Orchestrator started")

    def stop(self) -> None:
        """Stop the orchestrator and all agents."""
        self.logger.info("Stopping orchestrator")
        self.running = False

        if self.message_thread:
            self.message_thread.join(timeout=5)

        self.system_state["status"] = "stopped"
        self.logger.info("Orchestrator stopped")

    def run_autonomous_cycle(self) -> Dict[str, Any]:
        """
        Run one complete autonomous monitoring and repair cycle.

        Returns:
            Cycle results
        """
        self.logger.info("Starting autonomous cycle")
        cycle_start = datetime.now()

        try:
            # Step 1: Monitor for anomalies
            monitor_result = self._run_monitoring()

            if not monitor_result.get("anomalies"):
                return {
                    "status": "success",
                    "message": "No anomalies detected",
                    "duration": (datetime.now() - cycle_start).total_seconds()
                }

            # Step 2: Diagnose anomalies
            diagnostic_result = self._run_diagnostics(monitor_result["anomalies"])

            if not diagnostic_result.get("diagnostics"):
                return {
                    "status": "success",
                    "message": "No actionable diagnostics",
                    "duration": (datetime.now() - cycle_start).total_seconds()
                }

            # Step 3: Generate and apply repairs
            repair_result = self._run_repairs(diagnostic_result["diagnostics"])

            # Step 4: Validate repairs
            validation_result = self._run_validation(repair_result.get("repair_plans", []))

            # Update system state
            self._update_system_state(
                monitor_result,
                diagnostic_result,
                repair_result,
                validation_result
            )

            cycle_duration = (datetime.now() - cycle_start).total_seconds()

            return {
                "status": "success",
                "cycle_duration": cycle_duration,
                "anomalies_detected": len(monitor_result.get("anomalies", [])),
                "diagnostics_completed": len(diagnostic_result.get("diagnostics", [])),
                "repairs_attempted": len(repair_result.get("repair_plans", [])),
                "repairs_successful": validation_result.get("successful_count", 0),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error in autonomous cycle: {e}")
            return {
                "status": "error",
                "message": str(e),
                "duration": (datetime.now() - cycle_start).total_seconds()
            }

    def _run_monitoring(self) -> Dict[str, Any]:
        """
        Run monitoring phase.

        Returns:
            Monitoring results
        """
        self.logger.info("Running monitoring phase")

        monitor_agent = self.agents.get("monitor")
        if not monitor_agent:
            raise RuntimeError("Monitor agent not initialized")

        # Execute monitoring task
        task = {
            "type": "monitor_logs",
            "log_file": self.config.get("monitoring", {}).get("log_paths", ["logs/openclaw.log"])[0]
        }

        result = monitor_agent.execute_task(task)

        if result.get("status") == "success":
            anomalies = result.get("anomalies", [])
            self.logger.info(f"Monitoring complete: {len(anomalies)} anomalies detected")
            return {"anomalies": anomalies}

        return {"anomalies": []}

    def _run_diagnostics(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run diagnostic phase.

        Args:
            anomalies: List of detected anomalies

        Returns:
            Diagnostic results
        """
        self.logger.info(f"Running diagnostics for {len(anomalies)} anomalies")

        diagnostic_agent = self.agents.get("diagnostic")
        if not diagnostic_agent:
            raise RuntimeError("Diagnostic agent not initialized")

        diagnostics = []

        for anomaly in anomalies:
            task = {
                "type": "diagnose_anomaly",
                "anomaly": anomaly
            }

            result = diagnostic_agent.execute_task(task)

            if result.get("status") == "success":
                diagnostics.append(result)

        self.logger.info(f"Diagnostics complete: {len(diagnostics)} diagnostics generated")
        return {"diagnostics": diagnostics}

    def _run_repairs(self, diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run repair phase.

        Args:
            diagnostics: List of diagnostic results

        Returns:
            Repair results
        """
        self.logger.info(f"Running repairs for {len(diagnostics)} diagnostics")

        repair_agent = self.agents.get("repair")
        if not repair_agent:
            raise RuntimeError("Repair agent not initialized")

        repair_plans = []

        for diagnostic in diagnostics:
            # Generate repair plan
            task = {
                "type": "generate_repair",
                "diagnostic": diagnostic
            }

            repair_plan = repair_agent.execute_task(task)

            if repair_plan.get("status") == "success":
                repair_plans.append(repair_plan)

                # Check if auto-repair is enabled and safe
                risk = repair_plan.get("risk_assessment", {})
                auto_repair = self.config.get("repair", {}).get("auto_repair", True)

                if risk.get("safe_to_auto_apply") and auto_repair:
                    # Apply repair
                    apply_task = {
                        "type": "apply_repair",
                        "repair_plan": repair_plan,
                        "approved": True
                    }

                    apply_result = repair_agent.execute_task(apply_task)
                    repair_plan["application_result"] = apply_result

                    self.logger.info(
                        f"Applied repair {repair_plan['repair_id']}: "
                        f"{apply_result.get('status')}"
                    )

        self.logger.info(f"Repairs complete: {len(repair_plans)} repair plans generated")
        return {"repair_plans": repair_plans}

    def _run_validation(self, repair_plans: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run validation phase.

        Args:
            repair_plans: List of repair plans

        Returns:
            Validation results
        """
        self.logger.info(f"Running validation for {len(repair_plans)} repairs")

        validation_agent = self.agents.get("validation")
        if not validation_agent:
            raise RuntimeError("Validation agent not initialized")

        validation_results = []
        successful_count = 0

        for repair_plan in repair_plans:
            task = {
                "type": "validate_repair",
                "repair_plan": repair_plan
            }

            result = validation_agent.execute_task(task)
            validation_results.append(result)

            if result.get("validation_passed"):
                successful_count += 1

        self.logger.info(
            f"Validation complete: {successful_count}/{len(repair_plans)} repairs successful"
        )

        return {
            "validation_results": validation_results,
            "successful_count": successful_count,
            "failed_count": len(repair_plans) - successful_count
        }

    def _update_system_state(
        self,
        monitor_result: Dict[str, Any],
        diagnostic_result: Dict[str, Any],
        repair_result: Dict[str, Any],
        validation_result: Dict[str, Any]
    ) -> None:
        """
        Update system state after cycle completion.

        Args:
            monitor_result: Monitoring results
            diagnostic_result: Diagnostic results
            repair_result: Repair results
            validation_result: Validation results
        """
        self.system_state["total_anomalies_detected"] += len(monitor_result.get("anomalies", []))
        self.system_state["total_repairs_attempted"] += len(repair_result.get("repair_plans", []))
        self.system_state["total_repairs_successful"] += validation_result.get("successful_count", 0)
        self.system_state["total_repairs_failed"] += validation_result.get("failed_count", 0)
        self.system_state["last_activity"] = datetime.now().isoformat()

    def _process_messages(self) -> None:
        """Message processing loop (for future inter-agent messaging)."""
        while self.running:
            try:
                if not self.message_queue.empty():
                    message = self.message_queue.get(timeout=1)
                    self._route_message(message)
            except Exception as e:
                self.logger.error(f"Error processing message: {e}")

    def _route_message(self, message: AgentMessage) -> None:
        """
        Route message to appropriate agent.

        Args:
            message: Message to route
        """
        receiver_id = message.receiver

        # Extract agent name from receiver ID (e.g., "monitor_agent" -> "monitor")
        agent_name = receiver_id.replace("_agent", "")

        agent = self.agents.get(agent_name)

        if agent:
            agent.receive_message(message)
        else:
            self.logger.warning(f"Unknown agent: {receiver_id}")

    def send_message_to_agent(
        self,
        agent_name: str,
        message_type: str,
        content: Any
    ) -> Optional[AgentMessage]:
        """
        Send message to an agent.

        Args:
            agent_name: Name of target agent
            message_type: Type of message
            content: Message content

        Returns:
            Response message if any
        """
        agent = self.agents.get(agent_name)

        if not agent:
            self.logger.error(f"Agent not found: {agent_name}")
            return None

        message = AgentMessage(
            sender="orchestrator",
            receiver=f"{agent_name}_agent",
            message_type=message_type,
            content=content
        )

        agent.receive_message(message)
        responses = agent.process_mailbox()

        return responses[0] if responses else None

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system status.

        Returns:
            System status dictionary
        """
        agent_statuses = {}

        for name, agent in self.agents.items():
            agent_statuses[name] = agent.get_status()

        return {
            "system_state": self.system_state,
            "agents": agent_statuses,
            "timestamp": datetime.now().isoformat()
        }

    def get_agent_status(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific agent.

        Args:
            agent_name: Agent name

        Returns:
            Agent status or None
        """
        agent = self.agents.get(agent_name)
        return agent.get_status() if agent else None

    def trigger_monitoring(self) -> Dict[str, Any]:
        """
        Manually trigger monitoring.

        Returns:
            Monitoring results
        """
        return self._run_monitoring()

    def trigger_diagnostics(self, anomalies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Manually trigger diagnostics.

        Args:
            anomalies: Anomalies to diagnose

        Returns:
            Diagnostic results
        """
        return self._run_diagnostics(anomalies)

    def trigger_repair(self, diagnostic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manually trigger repair.

        Args:
            diagnostic: Diagnostic to repair

        Returns:
            Repair results
        """
        return self._run_repairs([diagnostic])

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics.

        Returns:
            Metrics dictionary
        """
        return {
            "total_anomalies_detected": self.system_state["total_anomalies_detected"],
            "total_repairs_attempted": self.system_state["total_repairs_attempted"],
            "total_repairs_successful": self.system_state["total_repairs_successful"],
            "total_repairs_failed": self.system_state["total_repairs_failed"],
            "success_rate": (
                self.system_state["total_repairs_successful"] /
                max(self.system_state["total_repairs_attempted"], 1)
            ),
            "agent_count": len(self.agents),
            "system_status": self.system_state["status"],
            "last_activity": self.system_state["last_activity"]
        }

    def __repr__(self) -> str:
        return f"Orchestrator(status={self.system_state['status']}, agents={len(self.agents)})"
