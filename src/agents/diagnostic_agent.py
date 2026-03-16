"""
Diagnostic Agent

Analyzes anomalies and determines root causes using LLM-powered analysis.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from .base_agent import BaseAgent, AgentMessage
from ..llm_providers.base_provider import LLMMessage
from ..llm_providers.provider_factory import LLMProviderFactory


class DiagnosticAgent(BaseAgent):
    """
    Agent that diagnoses anomalies and determines root causes.

    Responsibilities:
    - Analyze anomalies reported by monitor agents
    - Use LLM to understand error context
    - Determine root causes
    - Classify error types
    - Assess impact and severity
    - Generate diagnostic reports for repair agents
    """

    def __init__(
        self,
        agent_id: str,
        llm_config: Dict[str, Any],
        config: Dict[str, Any] = None
    ):
        """
        Initialize diagnostic agent.

        Args:
            agent_id: Unique agent identifier
            llm_config: LLM provider configuration
            config: Additional agent configuration
        """
        super().__init__(agent_id, "diagnostic", config)

        self.llm_config = llm_config
        self.llm_provider = None
        self._initialize_llm()

        self.diagnostic_history = []
        self.known_patterns = {}

    def _initialize_llm(self) -> None:
        """Initialize LLM provider."""
        try:
            provider_name = self.llm_config.get("provider", "openai")
            self.llm_provider = LLMProviderFactory.create_provider(
                provider_name=provider_name,
                **self.llm_config
            )
            self.llm_provider.initialize()
            self.logger.info(f"Initialized LLM provider: {provider_name}")
        except Exception as e:
            self.logger.error(f"Failed to initialize LLM provider: {e}")
            raise

    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming messages.

        Args:
            message: Message to process

        Returns:
            Response message if needed
        """
        if message.message_type == "anomaly_alert":
            return self._handle_anomaly_alert(message)
        elif message.message_type == "diagnose_request":
            return self._handle_diagnose_request(message)
        elif message.message_type == "get_diagnostics":
            return self._handle_get_diagnostics(message)
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}")
            return None

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a diagnostic task.

        Args:
            task: Task description

        Returns:
            Task result with diagnostic information
        """
        task_type = task.get("type", "diagnose_anomaly")

        if task_type == "diagnose_anomaly":
            return self._diagnose_anomaly(task)
        elif task_type == "analyze_pattern":
            return self._analyze_pattern(task)
        elif task_type == "assess_impact":
            return self._assess_impact(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    def _diagnose_anomaly(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Diagnose an anomaly using LLM analysis.

        Args:
            task: Task with anomaly information

        Returns:
            Diagnostic results
        """
        self.update_state(status="working", current_task="diagnosing_anomaly")

        anomaly = task.get("anomaly")
        if not anomaly:
            return {"status": "error", "message": "No anomaly provided"}

        try:
            # Perform root cause analysis
            root_cause = self._analyze_root_cause(anomaly)

            # Classify the error
            error_classification = self._classify_error(anomaly)

            # Assess impact
            impact_assessment = self._assess_error_impact(anomaly)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                anomaly, root_cause, error_classification
            )

            diagnostic_result = {
                "status": "success",
                "anomaly_id": anomaly.get("timestamp", "unknown"),
                "anomaly_type": anomaly.get("type"),
                "severity": anomaly.get("severity"),
                "root_cause": root_cause,
                "classification": error_classification,
                "impact": impact_assessment,
                "recommendations": recommendations,
                "timestamp": datetime.now().isoformat(),
                "diagnosed_by": self.agent_id
            }

            self.diagnostic_history.append(diagnostic_result)
            self.logger.info(
                f"Diagnosed anomaly: {anomaly.get('type')} - "
                f"Root cause: {root_cause.get('summary', 'Unknown')}"
            )

            self.update_state(
                status="idle",
                last_action=f"diagnosed {anomaly.get('type')}"
            )
            self.record_metric("diagnostics_completed", len(self.diagnostic_history))

            return diagnostic_result

        except Exception as e:
            self.logger.error(f"Error diagnosing anomaly: {e}")
            self.update_state(status="error")
            return {"status": "error", "message": str(e)}

    def _analyze_root_cause(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze root cause using LLM.

        Args:
            anomaly: Anomaly information

        Returns:
            Root cause analysis
        """
        # Prepare context for LLM
        context = self._prepare_diagnostic_context(anomaly)

        # Create prompt for root cause analysis
        prompt = f"""You are an expert system diagnostician analyzing an OpenClaw system anomaly.

Anomaly Information:
- Type: {anomaly.get('type')}
- Severity: {anomaly.get('severity')}
- Category: {anomaly.get('category')}
- Log Line: {anomaly.get('line_content')}
- Context:
{anomaly.get('context', 'No context available')}

Please analyze this anomaly and provide:
1. The most likely root cause
2. Contributing factors
3. Why this error occurred
4. Related system components affected

Provide your analysis in JSON format with these fields:
- summary: Brief root cause summary
- detailed_analysis: Detailed explanation
- contributing_factors: List of contributing factors
- affected_components: List of affected system components
- confidence: Confidence level (0.0 to 1.0)
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are an expert system diagnostician."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.3,  # Lower temperature for more focused analysis
                max_tokens=1000
            )

            # Parse LLM response
            analysis = self._parse_llm_json_response(response.content)

            return analysis

        except Exception as e:
            self.logger.error(f"Error in root cause analysis: {e}")
            return {
                "summary": "Unable to determine root cause",
                "detailed_analysis": f"Analysis failed: {str(e)}",
                "contributing_factors": [],
                "affected_components": [],
                "confidence": 0.0
            }

    def _classify_error(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify the error type.

        Args:
            anomaly: Anomaly information

        Returns:
            Error classification
        """
        prompt = f"""Classify this error into specific categories:

Error: {anomaly.get('line_content')}
Type: {anomaly.get('type')}
Category: {anomaly.get('category')}

Provide classification in JSON format:
- primary_category: Main error category (e.g., "network", "memory", "database", "configuration", "logic")
- secondary_categories: List of related categories
- error_patterns: List of specific error patterns identified
- is_transient: Boolean indicating if error is likely transient
- is_recoverable: Boolean indicating if error is recoverable
- requires_restart: Boolean indicating if restart is needed
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are an error classification expert."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )

            classification = self._parse_llm_json_response(response.content)
            return classification

        except Exception as e:
            self.logger.error(f"Error in error classification: {e}")
            return {
                "primary_category": anomaly.get("category", "unknown"),
                "secondary_categories": [],
                "error_patterns": [],
                "is_transient": False,
                "is_recoverable": True,
                "requires_restart": False
            }

    def _assess_error_impact(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess the impact of the error.

        Args:
            anomaly: Anomaly information

        Returns:
            Impact assessment
        """
        prompt = f"""Assess the impact of this error on the system:

Error Type: {anomaly.get('type')}
Severity: {anomaly.get('severity')}
Category: {anomaly.get('category')}
Error: {anomaly.get('line_content')}

Provide impact assessment in JSON format:
- impact_level: "low", "medium", "high", or "critical"
- affected_operations: List of operations that may be affected
- user_impact: Description of impact on end users
- business_impact: Description of business impact
- urgency: "low", "medium", "high", or "critical"
- estimated_downtime: Estimated downtime if not resolved (in minutes)
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are a system impact analyst."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=500
            )

            impact = self._parse_llm_json_response(response.content)
            return impact

        except Exception as e:
            self.logger.error(f"Error in impact assessment: {e}")
            severity_map = {
                "critical": "critical",
                "high": "high",
                "medium": "medium",
                "warning": "low"
            }
            return {
                "impact_level": severity_map.get(anomaly.get("severity", "medium"), "medium"),
                "affected_operations": [],
                "user_impact": "Unknown",
                "business_impact": "Unknown",
                "urgency": severity_map.get(anomaly.get("severity", "medium"), "medium"),
                "estimated_downtime": 0
            }

    def _generate_recommendations(
        self,
        anomaly: Dict[str, Any],
        root_cause: Dict[str, Any],
        classification: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate repair recommendations.

        Args:
            anomaly: Anomaly information
            root_cause: Root cause analysis
            classification: Error classification

        Returns:
            Repair recommendations
        """
        prompt = f"""Based on this diagnostic information, provide repair recommendations:

Error: {anomaly.get('line_content')}
Root Cause: {root_cause.get('summary', 'Unknown')}
Classification: {classification.get('primary_category', 'Unknown')}

Provide recommendations in JSON format:
- immediate_actions: List of immediate actions to take
- repair_strategies: List of potential repair strategies (with priority 1-5)
- prevention_measures: List of measures to prevent recurrence
- monitoring_suggestions: What to monitor after repair
- estimated_resolution_time: Estimated time to resolve (in minutes)
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are a system repair advisor."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.4,
                max_tokens=800
            )

            recommendations = self._parse_llm_json_response(response.content)
            return recommendations

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return {
                "immediate_actions": ["Review error logs", "Check system status"],
                "repair_strategies": [
                    {"strategy": "Manual investigation required", "priority": 1}
                ],
                "prevention_measures": [],
                "monitoring_suggestions": ["Monitor error logs"],
                "estimated_resolution_time": 30
            }

    def _prepare_diagnostic_context(self, anomaly: Dict[str, Any]) -> str:
        """
        Prepare context information for diagnostic analysis.

        Args:
            anomaly: Anomaly information

        Returns:
            Formatted context string
        """
        context_parts = [
            f"Anomaly Type: {anomaly.get('type')}",
            f"Severity: {anomaly.get('severity')}",
            f"Category: {anomaly.get('category')}",
            f"Line Number: {anomaly.get('line_number')}",
            f"Log File: {anomaly.get('log_file')}",
            f"\nError Line:\n{anomaly.get('line_content')}",
            f"\nContext:\n{anomaly.get('context', 'No context available')}"
        ]

        return "\n".join(context_parts)

    def _parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: LLM response text

        Returns:
            Parsed JSON object
        """
        try:
            # Try to find JSON in the response
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                # If no JSON found, return the response as text
                return {"response": response}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return {"response": response}

    def _analyze_pattern(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze error patterns across multiple anomalies.

        Args:
            task: Task parameters

        Returns:
            Pattern analysis results
        """
        self.update_state(status="working", current_task="analyzing_patterns")

        anomalies = task.get("anomalies", [])

        if not anomalies:
            return {"status": "error", "message": "No anomalies provided"}

        # Group anomalies by type
        pattern_groups = {}
        for anomaly in anomalies:
            anom_type = anomaly.get("type", "unknown")
            if anom_type not in pattern_groups:
                pattern_groups[anom_type] = []
            pattern_groups[anom_type].append(anomaly)

        analysis = {
            "status": "success",
            "total_anomalies": len(anomalies),
            "pattern_groups": {},
            "common_patterns": [],
            "timestamp": datetime.now().isoformat()
        }

        for pattern_type, group_anomalies in pattern_groups.items():
            analysis["pattern_groups"][pattern_type] = {
                "count": len(group_anomalies),
                "severity": group_anomalies[0].get("severity"),
                "category": group_anomalies[0].get("category")
            }

        self.update_state(status="idle", last_action="analyzed_patterns")
        return analysis

    def _assess_impact(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess impact of multiple anomalies.

        Args:
            task: Task parameters

        Returns:
            Impact assessment
        """
        self.update_state(status="working", current_task="assessing_impact")

        anomalies = task.get("anomalies", [])

        critical_count = sum(1 for a in anomalies if a.get("severity") == "critical")
        high_count = sum(1 for a in anomalies if a.get("severity") == "high")

        overall_impact = "low"
        if critical_count > 0:
            overall_impact = "critical"
        elif high_count > 2:
            overall_impact = "high"
        elif high_count > 0:
            overall_impact = "medium"

        assessment = {
            "status": "success",
            "overall_impact": overall_impact,
            "critical_anomalies": critical_count,
            "high_anomalies": high_count,
            "requires_immediate_action": critical_count > 0 or high_count > 2,
            "timestamp": datetime.now().isoformat()
        }

        self.update_state(status="idle", last_action="assessed_impact")
        return assessment

    def _handle_anomaly_alert(self, message: AgentMessage) -> AgentMessage:
        """Handle anomaly alert from monitor agent."""
        anomalies = message.content.get("anomalies", [])

        if not anomalies:
            return self.send_message(
                receiver=message.sender,
                message_type="diagnostic_complete",
                content={"status": "no_anomalies"}
            )

        # Diagnose each anomaly
        diagnostics = []
        for anomaly in anomalies:
            task = {"type": "diagnose_anomaly", "anomaly": anomaly}
            result = self.execute_task(task)
            if result["status"] == "success":
                diagnostics.append(result)

        # Send diagnostics to repair agent
        return self.send_message(
            receiver="repair_agent",
            message_type="diagnostic_report",
            content={
                "diagnostics": diagnostics,
                "requires_repair": len(diagnostics) > 0
            }
        )

    def _handle_diagnose_request(self, message: AgentMessage) -> AgentMessage:
        """Handle explicit diagnosis request."""
        anomaly = message.content.get("anomaly")
        task = {"type": "diagnose_anomaly", "anomaly": anomaly}
        result = self.execute_task(task)

        return self.send_message(
            receiver=message.sender,
            message_type="diagnosis_result",
            content=result
        )

    def _handle_get_diagnostics(self, message: AgentMessage) -> AgentMessage:
        """Handle request for diagnostic history."""
        return self.send_message(
            receiver=message.sender,
            message_type="diagnostics_report",
            content={"diagnostics": self.diagnostic_history}
        )
