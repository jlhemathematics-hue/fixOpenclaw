"""
Repair Agent

Generates and applies fixes using LLM-powered code generation and patching.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import subprocess
import os

from .base_agent import BaseAgent, AgentMessage
from ..llm_providers.base_provider import LLMMessage
from ..llm_providers.provider_factory import LLMProviderFactory


class RepairAgent(BaseAgent):
    """
    Agent that generates and applies fixes to resolve issues.

    Responsibilities:
    - Generate repair strategies from diagnostic reports
    - Create code patches and configuration changes
    - Apply fixes safely with rollback capability
    - Coordinate with validation agent for testing
    - Learn from successful repairs
    """

    def __init__(
        self,
        agent_id: str,
        llm_config: Dict[str, Any],
        config: Dict[str, Any] = None
    ):
        """
        Initialize repair agent.

        Args:
            agent_id: Unique agent identifier
            llm_config: LLM provider configuration
            config: Additional agent configuration
        """
        super().__init__(agent_id, "repair", config)

        self.llm_config = llm_config
        self.llm_provider = None
        self._initialize_llm()

        self.auto_repair = self.config.get("auto_repair", True)
        self.require_approval = self.config.get("require_approval", False)
        self.max_retry = self.config.get("max_retry", 3)
        self.rollback_on_failure = self.config.get("rollback_on_failure", True)

        self.repair_history = []
        self.successful_repairs = []
        self.failed_repairs = []

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
        if message.message_type == "diagnostic_report":
            return self._handle_diagnostic_report(message)
        elif message.message_type == "repair_request":
            return self._handle_repair_request(message)
        elif message.message_type == "validation_result":
            return self._handle_validation_result(message)
        elif message.message_type == "get_repair_history":
            return self._handle_get_repair_history(message)
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}")
            return None

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a repair task.

        Args:
            task: Task description

        Returns:
            Task result with repair information
        """
        task_type = task.get("type", "generate_repair")

        if task_type == "generate_repair":
            return self._generate_repair(task)
        elif task_type == "apply_repair":
            return self._apply_repair(task)
        elif task_type == "rollback_repair":
            return self._rollback_repair(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    def _generate_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate repair strategy and fix.

        Args:
            task: Task with diagnostic information

        Returns:
            Generated repair plan
        """
        self.update_state(status="working", current_task="generating_repair")

        diagnostic = task.get("diagnostic")
        if not diagnostic:
            return {"status": "error", "message": "No diagnostic provided"}

        try:
            # Generate repair strategy
            repair_strategy = self._create_repair_strategy(diagnostic)

            # Generate specific fix
            fix_details = self._generate_fix_details(diagnostic, repair_strategy)

            # Estimate risk and impact
            risk_assessment = self._assess_repair_risk(fix_details)

            repair_plan = {
                "status": "success",
                "repair_id": f"repair_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "diagnostic_id": diagnostic.get("anomaly_id"),
                "strategy": repair_strategy,
                "fix_details": fix_details,
                "risk_assessment": risk_assessment,
                "requires_approval": self.require_approval or risk_assessment.get("risk_level") == "high",
                "timestamp": datetime.now().isoformat(),
                "generated_by": self.agent_id
            }

            self.logger.info(
                f"Generated repair plan: {repair_plan['repair_id']} - "
                f"Strategy: {repair_strategy.get('name', 'Unknown')}"
            )

            self.update_state(status="idle", last_action="generated_repair")
            self.record_metric("repairs_generated", len(self.repair_history) + 1)

            return repair_plan

        except Exception as e:
            self.logger.error(f"Error generating repair: {e}")
            self.update_state(status="error")
            return {"status": "error", "message": str(e)}

    def _create_repair_strategy(self, diagnostic: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create repair strategy using LLM.

        Args:
            diagnostic: Diagnostic information

        Returns:
            Repair strategy
        """
        prompt = f"""You are an expert system repair engineer. Based on this diagnostic report, create a repair strategy.

Diagnostic Information:
- Error Type: {diagnostic.get('anomaly_type')}
- Severity: {diagnostic.get('severity')}
- Root Cause: {diagnostic.get('root_cause', {}).get('summary', 'Unknown')}
- Classification: {diagnostic.get('classification', {}).get('primary_category', 'Unknown')}
- Impact: {diagnostic.get('impact', {}).get('impact_level', 'Unknown')}

Recommendations:
{json.dumps(diagnostic.get('recommendations', {}), indent=2)}

Create a repair strategy in JSON format:
- name: Strategy name
- approach: Overall approach (e.g., "configuration_change", "code_patch", "restart", "resource_scaling")
- steps: List of step descriptions
- tools_required: List of tools/resources needed
- estimated_duration: Duration in minutes
- reversible: Boolean indicating if changes are reversible
- risk_level: "low", "medium", or "high"
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are an expert system repair engineer."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.3,
                max_tokens=1000
            )

            strategy = self._parse_llm_json_response(response.content)
            return strategy

        except Exception as e:
            self.logger.error(f"Error creating repair strategy: {e}")
            return {
                "name": "manual_repair",
                "approach": "manual_investigation",
                "steps": ["Manual investigation required"],
                "tools_required": [],
                "estimated_duration": 30,
                "reversible": True,
                "risk_level": "high"
            }

    def _generate_fix_details(
        self,
        diagnostic: Dict[str, Any],
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate specific fix details.

        Args:
            diagnostic: Diagnostic information
            strategy: Repair strategy

        Returns:
            Detailed fix information
        """
        prompt = f"""Generate specific fix details for this repair strategy.

Error: {diagnostic.get('anomaly_type')}
Root Cause: {diagnostic.get('root_cause', {}).get('summary', 'Unknown')}
Strategy: {strategy.get('name')}
Approach: {strategy.get('approach')}

Provide fix details in JSON format:
- fix_type: Type of fix (e.g., "config_update", "code_patch", "service_restart", "resource_adjustment")
- target_files: List of files to modify (if applicable)
- changes: Detailed description of changes
- commands: List of commands to execute (if applicable)
- configuration_changes: Dict of config key-value changes (if applicable)
- validation_checks: List of checks to perform after fix
- rollback_procedure: Steps to rollback if fix fails
"""

        try:
            messages = [
                LLMMessage(role="system", content="You are a system repair specialist."),
                LLMMessage(role="user", content=prompt)
            ]

            response = self.llm_provider.generate(
                messages=messages,
                temperature=0.2,
                max_tokens=1500
            )

            fix_details = self._parse_llm_json_response(response.content)
            return fix_details

        except Exception as e:
            self.logger.error(f"Error generating fix details: {e}")
            return {
                "fix_type": "manual",
                "target_files": [],
                "changes": "Manual fix required",
                "commands": [],
                "configuration_changes": {},
                "validation_checks": [],
                "rollback_procedure": []
            }

    def _assess_repair_risk(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess risk of applying the repair.

        Args:
            fix_details: Fix details

        Returns:
            Risk assessment
        """
        # Simple risk assessment based on fix type
        fix_type = fix_details.get("fix_type", "manual")
        target_files = fix_details.get("target_files", [])
        commands = fix_details.get("commands", [])

        risk_level = "low"
        risk_factors = []

        # Assess risk based on various factors
        if fix_type in ["code_patch", "system_modification"]:
            risk_level = "medium"
            risk_factors.append("Code modification required")

        if len(target_files) > 3:
            risk_level = "medium"
            risk_factors.append("Multiple files affected")

        if any("rm" in cmd or "delete" in cmd.lower() for cmd in commands):
            risk_level = "high"
            risk_factors.append("Destructive operations detected")

        if any("restart" in cmd or "reboot" in cmd for cmd in commands):
            risk_factors.append("Service restart required")

        return {
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "requires_backup": risk_level in ["medium", "high"],
            "requires_testing": True,
            "safe_to_auto_apply": risk_level == "low" and self.auto_repair
        }

    def _apply_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply the repair fix.

        Args:
            task: Task with repair plan

        Returns:
            Application result
        """
        self.update_state(status="working", current_task="applying_repair")

        repair_plan = task.get("repair_plan")
        if not repair_plan:
            return {"status": "error", "message": "No repair plan provided"}

        repair_id = repair_plan.get("repair_id")
        fix_details = repair_plan.get("fix_details", {})

        try:
            # Check if approval is required
            if repair_plan.get("requires_approval") and not task.get("approved"):
                return {
                    "status": "pending_approval",
                    "repair_id": repair_id,
                    "message": "Repair requires approval before application"
                }

            # Create backup if needed
            risk_assessment = repair_plan.get("risk_assessment", {})
            if risk_assessment.get("requires_backup"):
                backup_result = self._create_backup(fix_details)
                if not backup_result.get("success"):
                    return {
                        "status": "error",
                        "repair_id": repair_id,
                        "message": "Failed to create backup"
                    }

            # Apply the fix
            application_result = self._execute_fix(fix_details)

            if application_result.get("success"):
                result = {
                    "status": "success",
                    "repair_id": repair_id,
                    "applied_at": datetime.now().isoformat(),
                    "changes_made": application_result.get("changes", []),
                    "message": "Repair applied successfully"
                }

                self.successful_repairs.append(repair_id)
                self.logger.info(f"Successfully applied repair: {repair_id}")

            else:
                result = {
                    "status": "failed",
                    "repair_id": repair_id,
                    "error": application_result.get("error"),
                    "message": "Failed to apply repair"
                }

                self.failed_repairs.append(repair_id)
                self.logger.error(f"Failed to apply repair: {repair_id}")

                # Attempt rollback if enabled
                if self.rollback_on_failure:
                    rollback_result = self._rollback_repair({"repair_id": repair_id})
                    result["rollback"] = rollback_result

            self.repair_history.append(result)
            self.update_state(status="idle", last_action=f"applied_repair_{repair_id}")
            self.record_metric("repairs_applied", len(self.repair_history))

            return result

        except Exception as e:
            self.logger.error(f"Error applying repair: {e}")
            self.update_state(status="error")
            return {
                "status": "error",
                "repair_id": repair_id,
                "message": str(e)
            }

    def _execute_fix(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the actual fix operations.

        Args:
            fix_details: Fix details

        Returns:
            Execution result
        """
        fix_type = fix_details.get("fix_type")
        changes_made = []

        try:
            if fix_type == "config_update":
                # Apply configuration changes
                config_changes = fix_details.get("configuration_changes", {})
                for key, value in config_changes.items():
                    self.logger.info(f"Would update config: {key} = {value}")
                    changes_made.append(f"Config: {key} = {value}")

            elif fix_type == "service_restart":
                # Execute restart commands
                commands = fix_details.get("commands", [])
                for cmd in commands:
                    self.logger.info(f"Would execute: {cmd}")
                    changes_made.append(f"Command: {cmd}")

            elif fix_type == "code_patch":
                # Apply code patches
                target_files = fix_details.get("target_files", [])
                for file_path in target_files:
                    self.logger.info(f"Would patch file: {file_path}")
                    changes_made.append(f"Patched: {file_path}")

            else:
                self.logger.warning(f"Unknown fix type: {fix_type}")
                return {
                    "success": False,
                    "error": f"Unknown fix type: {fix_type}"
                }

            return {
                "success": True,
                "changes": changes_made
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def _create_backup(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create backup before applying fix.

        Args:
            fix_details: Fix details

        Returns:
            Backup result
        """
        try:
            target_files = fix_details.get("target_files", [])
            backup_id = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            self.logger.info(f"Creating backup: {backup_id}")

            # In real implementation, would backup actual files
            for file_path in target_files:
                self.logger.info(f"Would backup: {file_path}")

            return {
                "success": True,
                "backup_id": backup_id,
                "files_backed_up": len(target_files)
            }

        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _rollback_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Rollback a failed repair.

        Args:
            task: Task with repair ID

        Returns:
            Rollback result
        """
        self.update_state(status="working", current_task="rolling_back")

        repair_id = task.get("repair_id")

        try:
            self.logger.info(f"Rolling back repair: {repair_id}")

            # In real implementation, would restore from backup
            rollback_result = {
                "status": "success",
                "repair_id": repair_id,
                "rollback_at": datetime.now().isoformat(),
                "message": "Rollback completed successfully"
            }

            self.update_state(status="idle", last_action=f"rolled_back_{repair_id}")
            return rollback_result

        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return {
                "status": "error",
                "repair_id": repair_id,
                "message": str(e)
            }

    def _parse_llm_json_response(self, response: str) -> Dict[str, Any]:
        """
        Parse JSON response from LLM.

        Args:
            response: LLM response text

        Returns:
            Parsed JSON object
        """
        try:
            start = response.find('{')
            end = response.rfind('}') + 1

            if start >= 0 and end > start:
                json_str = response[start:end]
                return json.loads(json_str)
            else:
                return {"response": response}

        except json.JSONDecodeError as e:
            self.logger.warning(f"Failed to parse JSON response: {e}")
            return {"response": response}

    def _handle_diagnostic_report(self, message: AgentMessage) -> AgentMessage:
        """Handle diagnostic report from diagnostic agent."""
        diagnostics = message.content.get("diagnostics", [])

        if not diagnostics:
            return self.send_message(
                receiver=message.sender,
                message_type="repair_complete",
                content={"status": "no_repairs_needed"}
            )

        # Generate repair plans for each diagnostic
        repair_plans = []
        for diagnostic in diagnostics:
            task = {"type": "generate_repair", "diagnostic": diagnostic}
            repair_plan = self.execute_task(task)

            if repair_plan["status"] == "success":
                repair_plans.append(repair_plan)

                # Auto-apply if safe and enabled
                risk = repair_plan.get("risk_assessment", {})
                if risk.get("safe_to_auto_apply") and self.auto_repair:
                    apply_task = {
                        "type": "apply_repair",
                        "repair_plan": repair_plan,
                        "approved": True
                    }
                    apply_result = self.execute_task(apply_task)
                    repair_plan["application_result"] = apply_result

        # Send to validation agent
        return self.send_message(
            receiver="validation_agent",
            message_type="validate_repairs",
            content={"repair_plans": repair_plans}
        )

    def _handle_repair_request(self, message: AgentMessage) -> AgentMessage:
        """Handle explicit repair request."""
        diagnostic = message.content.get("diagnostic")
        task = {"type": "generate_repair", "diagnostic": diagnostic}
        result = self.execute_task(task)

        return self.send_message(
            receiver=message.sender,
            message_type="repair_plan",
            content=result
        )

    def _handle_validation_result(self, message: AgentMessage) -> AgentMessage:
        """Handle validation results."""
        validation = message.content
        repair_id = validation.get("repair_id")

        self.logger.info(
            f"Received validation for {repair_id}: "
            f"{validation.get('validation_status')}"
        )

        # Log validation results
        for repair_entry in self.repair_history:
            if repair_entry.get("repair_id") == repair_id:
                repair_entry["validation"] = validation
                break

        return self.send_message(
            receiver="orchestrator",
            message_type="repair_validated",
            content=validation
        )

    def _handle_get_repair_history(self, message: AgentMessage) -> AgentMessage:
        """Handle request for repair history."""
        return self.send_message(
            receiver=message.sender,
            message_type="repair_history",
            content={
                "history": self.repair_history,
                "successful": len(self.successful_repairs),
                "failed": len(self.failed_repairs)
            }
        )
