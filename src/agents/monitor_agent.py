"""
Monitor Agent

Responsible for monitoring OpenClaw systems for anomalies.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime
import re

from .base_agent import BaseAgent, AgentMessage


class MonitorAgent(BaseAgent):
    """
    Agent that monitors OpenClaw systems for anomalies.

    Responsibilities:
    - Monitor log files
    - Track system metrics
    - Detect anomalies and errors
    - Alert diagnostic agents when issues are found
    """

    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        Initialize monitor agent.

        Args:
            agent_id: Unique agent identifier
            config: Configuration including log paths, patterns, etc.
        """
        super().__init__(agent_id, "monitor", config)

        self.log_paths = self.config.get("log_paths", [])
        self.check_interval = self.config.get("check_interval", 5)
        self.anomaly_patterns = self.config.get("anomaly_patterns", self._default_patterns())
        self.anomaly_threshold = self.config.get("anomaly_threshold", 0.8)

        self.last_check_time = {}
        self.detected_anomalies = []

    def _default_patterns(self) -> List[Dict[str, Any]]:
        """Get default anomaly patterns."""
        return [
            {
                "name": "error",
                "pattern": r"ERROR|Error|error",
                "severity": "high",
                "category": "error"
            },
            {
                "name": "exception",
                "pattern": r"Exception|EXCEPTION|Traceback",
                "severity": "critical",
                "category": "exception"
            },
            {
                "name": "fatal",
                "pattern": r"FATAL|Fatal|fatal",
                "severity": "critical",
                "category": "fatal"
            },
            {
                "name": "warning",
                "pattern": r"WARNING|Warning|warning",
                "severity": "medium",
                "category": "warning"
            },
            {
                "name": "connection_error",
                "pattern": r"connection.*(?:refused|timeout|failed)|Connection.*(?:refused|timeout|failed)",
                "severity": "high",
                "category": "network"
            },
            {
                "name": "memory_error",
                "pattern": r"OutOfMemory|MemoryError|memory.*exhausted",
                "severity": "critical",
                "category": "resource"
            },
            {
                "name": "database_error",
                "pattern": r"DatabaseError|database.*error|SQL.*error",
                "severity": "high",
                "category": "database"
            }
        ]

    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming messages.

        Args:
            message: Message to process

        Returns:
            Response message if needed
        """
        if message.message_type == "start_monitoring":
            return self._handle_start_monitoring(message)
        elif message.message_type == "stop_monitoring":
            return self._handle_stop_monitoring(message)
        elif message.message_type == "get_anomalies":
            return self._handle_get_anomalies(message)
        elif message.message_type == "update_patterns":
            return self._handle_update_patterns(message)
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}")
            return None

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a monitoring task.

        Args:
            task: Task description

        Returns:
            Task result with detected anomalies
        """
        task_type = task.get("type", "monitor_logs")

        if task_type == "monitor_logs":
            return self._monitor_logs(task)
        elif task_type == "check_health":
            return self._check_health(task)
        elif task_type == "analyze_metrics":
            return self._analyze_metrics(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    def _monitor_logs(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Monitor log files for anomalies.

        Args:
            task: Task parameters

        Returns:
            Monitoring results
        """
        self.update_state(status="working", current_task="monitoring_logs")

        log_file = task.get("log_file")
        if not log_file:
            log_file = self.log_paths[0] if self.log_paths else None

        if not log_file:
            return {"status": "error", "message": "No log file specified"}

        try:
            anomalies = self._scan_log_file(log_file)

            result = {
                "status": "success",
                "log_file": log_file,
                "anomalies_found": len(anomalies),
                "anomalies": anomalies,
                "timestamp": datetime.now().isoformat()
            }

            if anomalies:
                self.detected_anomalies.extend(anomalies)
                self.logger.info(f"Detected {len(anomalies)} anomalies in {log_file}")

            self.update_state(status="idle", last_action=f"monitored {log_file}")
            self.record_metric("anomalies_detected", len(self.detected_anomalies))

            return result

        except Exception as e:
            self.logger.error(f"Error monitoring logs: {e}")
            self.update_state(status="error")
            return {"status": "error", "message": str(e)}

    def _scan_log_file(self, log_file: str) -> List[Dict[str, Any]]:
        """
        Scan a log file for anomalies.

        Args:
            log_file: Path to log file

        Returns:
            List of detected anomalies
        """
        anomalies = []

        try:
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for pattern_def in self.anomaly_patterns:
                    pattern = pattern_def["pattern"]
                    if re.search(pattern, line, re.IGNORECASE):
                        # Extract context (surrounding lines)
                        start = max(0, line_num - 3)
                        end = min(len(lines), line_num + 2)
                        context = "".join(lines[start:end])

                        anomaly = {
                            "type": pattern_def["name"],
                            "severity": pattern_def["severity"],
                            "category": pattern_def["category"],
                            "line_number": line_num,
                            "line_content": line.strip(),
                            "context": context,
                            "log_file": log_file,
                            "timestamp": datetime.now().isoformat(),
                            "pattern": pattern
                        }

                        anomalies.append(anomaly)

        except FileNotFoundError:
            self.logger.error(f"Log file not found: {log_file}")
        except Exception as e:
            self.logger.error(f"Error scanning log file: {e}")

        return anomalies

    def _check_health(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check system health.

        Args:
            task: Task parameters

        Returns:
            Health check results
        """
        self.update_state(status="working", current_task="checking_health")

        # Placeholder for health check logic
        health_status = {
            "status": "success",
            "overall_health": "healthy",
            "checks": {
                "logs_accessible": True,
                "monitoring_active": True,
                "anomalies_count": len(self.detected_anomalies)
            },
            "timestamp": datetime.now().isoformat()
        }

        self.update_state(status="idle", last_action="health_check")
        return health_status

    def _analyze_metrics(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze system metrics.

        Args:
            task: Task parameters

        Returns:
            Metrics analysis results
        """
        self.update_state(status="working", current_task="analyzing_metrics")

        # Placeholder for metrics analysis
        metrics = {
            "status": "success",
            "metrics": {
                "total_anomalies": len(self.detected_anomalies),
                "critical_anomalies": sum(1 for a in self.detected_anomalies if a.get("severity") == "critical"),
                "high_anomalies": sum(1 for a in self.detected_anomalies if a.get("severity") == "high"),
                "monitoring_uptime": "99.9%"
            },
            "timestamp": datetime.now().isoformat()
        }

        self.update_state(status="idle", last_action="analyzed_metrics")
        return metrics

    def _handle_start_monitoring(self, message: AgentMessage) -> AgentMessage:
        """Handle start monitoring request."""
        self.update_state(status="working", current_task="continuous_monitoring")
        return self.send_message(
            receiver=message.sender,
            message_type="monitoring_started",
            content={"status": "monitoring_active"}
        )

    def _handle_stop_monitoring(self, message: AgentMessage) -> AgentMessage:
        """Handle stop monitoring request."""
        self.update_state(status="idle", current_task=None)
        return self.send_message(
            receiver=message.sender,
            message_type="monitoring_stopped",
            content={"status": "monitoring_stopped"}
        )

    def _handle_get_anomalies(self, message: AgentMessage) -> AgentMessage:
        """Handle get anomalies request."""
        return self.send_message(
            receiver=message.sender,
            message_type="anomalies_report",
            content={"anomalies": self.detected_anomalies}
        )

    def _handle_update_patterns(self, message: AgentMessage) -> AgentMessage:
        """Handle update patterns request."""
        new_patterns = message.content.get("patterns", [])
        self.anomaly_patterns.extend(new_patterns)
        return self.send_message(
            receiver=message.sender,
            message_type="patterns_updated",
            content={"status": "success", "total_patterns": len(self.anomaly_patterns)}
        )

    def continuous_monitor(self, duration: Optional[int] = None) -> None:
        """
        Run continuous monitoring.

        Args:
            duration: Duration in seconds (None for infinite)
        """
        start_time = time.time()
        self.logger.info("Starting continuous monitoring")

        while True:
            # Check each log file
            for log_path in self.log_paths:
                task = {"type": "monitor_logs", "log_file": log_path}
                result = self.execute_task(task)

                if result["status"] == "success" and result["anomalies_found"] > 0:
                    # Send alert to diagnostic agent
                    alert_message = self.send_message(
                        receiver="diagnostic_agent",
                        message_type="anomaly_alert",
                        content=result
                    )
                    self.logger.info(f"Sent anomaly alert: {result['anomalies_found']} anomalies")

            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break

            # Sleep before next check
            time.sleep(self.check_interval)

        self.logger.info("Stopped continuous monitoring")
