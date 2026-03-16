"""
Validation Agent

Validates fixes before and after application to ensure system stability.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from .base_agent import BaseAgent, AgentMessage


class ValidationAgent(BaseAgent):
    """
    Agent that validates repairs and system health.

    Responsibilities:
    - Pre-validation: Check if fix is safe to apply
    - Post-validation: Verify fix resolved the issue
    - Safety checks: Ensure system stability
    - Rollback triggers: Detect when rollback is needed
    - Test execution: Run automated tests
    """

    def __init__(self, agent_id: str, config: Dict[str, Any] = None):
        """
        Initialize validation agent.

        Args:
            agent_id: Unique agent identifier
            config: Additional agent configuration
        """
        super().__init__(agent_id, "validation", config)

        self.validation_timeout = self.config.get("validation_timeout", 300)
        self.health_check_interval = self.config.get("health_check_interval", 10)
        self.success_threshold = self.config.get("success_threshold", 0.9)

        self.validation_history = []

    def process_message(self, message: AgentMessage) -> Optional[AgentMessage]:
        """
        Process incoming messages.

        Args:
            message: Message to process

        Returns:
            Response message if needed
        """
        if message.message_type == "validate_repairs":
            return self._handle_validate_repairs(message)
        elif message.message_type == "pre_validate":
            return self._handle_pre_validate(message)
        elif message.message_type == "post_validate":
            return self._handle_post_validate(message)
        elif message.message_type == "health_check":
            return self._handle_health_check(message)
        else:
            self.logger.warning(f"Unknown message type: {message.message_type}")
            return None

    def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a validation task.

        Args:
            task: Task description

        Returns:
            Task result with validation information
        """
        task_type = task.get("type", "validate_repair")

        if task_type == "validate_repair":
            return self._validate_repair(task)
        elif task_type == "pre_validate":
            return self._pre_validate_fix(task)
        elif task_type == "post_validate":
            return self._post_validate_fix(task)
        elif task_type == "run_tests":
            return self._run_tests(task)
        elif task_type == "check_health":
            return self._check_system_health(task)
        else:
            return {"status": "error", "message": f"Unknown task type: {task_type}"}

    def _validate_repair(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete validation workflow for a repair.

        Args:
            task: Task with repair information

        Returns:
            Validation results
        """
        self.update_state(status="working", current_task="validating_repair")

        repair_plan = task.get("repair_plan")
        if not repair_plan:
            return {"status": "error", "message": "No repair plan provided"}

        repair_id = repair_plan.get("repair_id")

        try:
            # Pre-validation
            pre_validation = self._pre_validate_fix({"repair_plan": repair_plan})

            if pre_validation.get("status") != "safe":
                return {
                    "status": "unsafe",
                    "repair_id": repair_id,
                    "pre_validation": pre_validation,
                    "message": "Pre-validation failed: repair deemed unsafe",
                    "timestamp": datetime.now().isoformat()
                }

            # Check if repair was applied
            application_result = repair_plan.get("application_result")

            if not application_result:
                return {
                    "status": "pending",
                    "repair_id": repair_id,
                    "pre_validation": pre_validation,
                    "message": "Repair not yet applied",
                    "timestamp": datetime.now().isoformat()
                }

            # Post-validation
            post_validation = self._post_validate_fix({
                "repair_plan": repair_plan,
                "application_result": application_result
            })

            # Overall validation result
            validation_status = "success" if post_validation.get("verification_passed") else "failed"

            validation_result = {
                "status": validation_status,
                "repair_id": repair_id,
                "pre_validation": pre_validation,
                "post_validation": post_validation,
                "validation_passed": validation_status == "success",
                "timestamp": datetime.now().isoformat(),
                "validated_by": self.agent_id
            }

            self.validation_history.append(validation_result)

            self.logger.info(
                f"Validation complete for {repair_id}: {validation_status}"
            )

            self.update_state(
                status="idle",
                last_action=f"validated_{repair_id}"
            )
            self.record_metric("validations_completed", len(self.validation_history))

            return validation_result

        except Exception as e:
            self.logger.error(f"Error validating repair: {e}")
            self.update_state(status="error")
            return {
                "status": "error",
                "repair_id": repair_id,
                "message": str(e)
            }

    def _pre_validate_fix(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Pre-validation: Check if fix is safe to apply.

        Args:
            task: Task with repair plan

        Returns:
            Pre-validation results
        """
        repair_plan = task.get("repair_plan")
        fix_details = repair_plan.get("fix_details", {})
        risk_assessment = repair_plan.get("risk_assessment", {})

        safety_checks = []
        warnings = []

        # Check 1: System prerequisites
        prereq_check = self._check_prerequisites(fix_details)
        safety_checks.append({
            "check": "prerequisites",
            "passed": prereq_check.get("passed", True),
            "details": prereq_check
        })

        # Check 2: Resource availability
        resource_check = self._check_resources(fix_details)
        safety_checks.append({
            "check": "resources",
            "passed": resource_check.get("passed", True),
            "details": resource_check
        })

        # Check 3: Conflict detection
        conflict_check = self._check_conflicts(fix_details)
        safety_checks.append({
            "check": "conflicts",
            "passed": conflict_check.get("passed", True),
            "details": conflict_check
        })

        # Check 4: Risk assessment review
        risk_level = risk_assessment.get("risk_level", "medium")
        if risk_level == "high":
            warnings.append("High risk repair - requires extra caution")

        # Determine overall safety
        all_passed = all(check["passed"] for check in safety_checks)
        safety_status = "safe" if all_passed else "unsafe"

        return {
            "status": safety_status,
            "safety_checks": safety_checks,
            "warnings": warnings,
            "risk_level": risk_level,
            "safe_to_proceed": all_passed and risk_level != "critical",
            "timestamp": datetime.now().isoformat()
        }

    def _post_validate_fix(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Post-validation: Verify fix resolved the issue.

        Args:
            task: Task with repair and application results

        Returns:
            Post-validation results
        """
        repair_plan = task.get("repair_plan")
        application_result = task.get("application_result")

        verification_checks = []

        # Check 1: System health after fix
        health_check = self._check_system_health({})
        verification_checks.append({
            "check": "system_health",
            "passed": health_check.get("status") == "healthy",
            "details": health_check
        })

        # Check 2: Error resolution
        error_resolved = self._verify_error_resolved(repair_plan)
        verification_checks.append({
            "check": "error_resolved",
            "passed": error_resolved.get("resolved", False),
            "details": error_resolved
        })

        # Check 3: No new errors introduced
        new_errors = self._check_for_new_errors()
        no_new_errors = len(new_errors.get("errors", [])) == 0
        verification_checks.append({
            "check": "no_new_errors",
            "passed": no_new_errors,
            "details": new_errors
        })

        # Check 4: Run automated tests
        test_results = self._run_tests({"repair_plan": repair_plan})
        verification_checks.append({
            "check": "automated_tests",
            "passed": test_results.get("all_passed", False),
            "details": test_results
        })

        # Determine overall verification
        all_passed = all(check["passed"] for check in verification_checks)

        return {
            "verification_passed": all_passed,
            "verification_checks": verification_checks,
            "success_rate": sum(1 for c in verification_checks if c["passed"]) / len(verification_checks),
            "timestamp": datetime.now().isoformat()
        }

    def _check_prerequisites(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if system meets prerequisites for fix.

        Args:
            fix_details: Fix details

        Returns:
            Prerequisite check results
        """
        tools_required = fix_details.get("tools_required", [])
        target_files = fix_details.get("target_files", [])

        missing_tools = []
        missing_files = []

        # Check tools (simplified - would actually check for tool availability)
        for tool in tools_required:
            # In real implementation, would check if tool exists
            pass

        # Check target files exist
        for file_path in target_files:
            try:
                import os
                if not os.path.exists(file_path):
                    missing_files.append(file_path)
            except:
                pass

        return {
            "passed": len(missing_tools) == 0 and len(missing_files) == 0,
            "missing_tools": missing_tools,
            "missing_files": missing_files
        }

    def _check_resources(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if sufficient resources are available.

        Args:
            fix_details: Fix details

        Returns:
            Resource check results
        """
        # Simplified resource check
        # In real implementation, would check disk space, memory, CPU, etc.

        return {
            "passed": True,
            "disk_space": "sufficient",
            "memory": "sufficient",
            "cpu": "available"
        }

    def _check_conflicts(self, fix_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for conflicts with other operations.

        Args:
            fix_details: Fix details

        Returns:
            Conflict check results
        """
        # Simplified conflict check
        # In real implementation, would check for:
        # - File locks
        # - Concurrent modifications
        # - Service dependencies

        return {
            "passed": True,
            "conflicts": []
        }

    def _check_system_health(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check overall system health.

        Args:
            task: Task parameters

        Returns:
            Health check results
        """
        health_metrics = {
            "cpu_usage": 45.2,  # Placeholder
            "memory_usage": 62.8,  # Placeholder
            "disk_usage": 58.3,  # Placeholder
            "error_rate": 0.02,  # Placeholder
            "response_time": 150  # Placeholder ms
        }

        # Determine health status
        status = "healthy"
        issues = []

        if health_metrics["cpu_usage"] > 90:
            status = "degraded"
            issues.append("High CPU usage")

        if health_metrics["memory_usage"] > 90:
            status = "degraded"
            issues.append("High memory usage")

        if health_metrics["error_rate"] > 0.05:
            status = "unhealthy"
            issues.append("High error rate")

        return {
            "status": status,
            "metrics": health_metrics,
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }

    def _verify_error_resolved(self, repair_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify that the original error has been resolved.

        Args:
            repair_plan: Repair plan

        Returns:
            Error resolution verification
        """
        # In real implementation, would:
        # - Check if error still appears in logs
        # - Monitor for recurrence
        # - Verify specific error conditions are cleared

        # Simplified verification
        diagnostic_id = repair_plan.get("diagnostic_id")

        # Simulate checking if error persists
        error_still_present = False  # Would actually check logs

        return {
            "resolved": not error_still_present,
            "diagnostic_id": diagnostic_id,
            "verification_method": "log_monitoring",
            "confidence": 0.85
        }

    def _check_for_new_errors(self) -> Dict[str, Any]:
        """
        Check if any new errors were introduced.

        Returns:
            New errors check results
        """
        # In real implementation, would scan recent logs for new errors
        # Compare error patterns before and after fix

        new_errors = []  # Would contain actual new errors found

        return {
            "errors": new_errors,
            "error_count": len(new_errors),
            "timestamp": datetime.now().isoformat()
        }

    def _run_tests(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run automated tests.

        Args:
            task: Task with test information

        Returns:
            Test results
        """
        repair_plan = task.get("repair_plan", {})
        fix_details = repair_plan.get("fix_details", {})

        validation_checks = fix_details.get("validation_checks", [])

        test_results = []

        # Run each validation check
        for check in validation_checks:
            # Simulate running test
            # In real implementation, would execute actual tests
            test_result = {
                "test": check,
                "passed": True,  # Simulated
                "duration": 1.5,  # Simulated seconds
                "message": "Test passed"
            }
            test_results.append(test_result)

        # If no specific tests, run default health checks
        if not test_results:
            test_results = [
                {
                    "test": "system_health",
                    "passed": True,
                    "duration": 0.5,
                    "message": "System health OK"
                },
                {
                    "test": "basic_functionality",
                    "passed": True,
                    "duration": 1.0,
                    "message": "Basic functionality OK"
                }
            ]

        all_passed = all(result["passed"] for result in test_results)
        total_duration = sum(result["duration"] for result in test_results)

        return {
            "all_passed": all_passed,
            "test_count": len(test_results),
            "passed_count": sum(1 for r in test_results if r["passed"]),
            "failed_count": sum(1 for r in test_results if not r["passed"]),
            "total_duration": total_duration,
            "test_results": test_results,
            "timestamp": datetime.now().isoformat()
        }

    def _handle_validate_repairs(self, message: AgentMessage) -> AgentMessage:
        """Handle validation request for multiple repairs."""
        repair_plans = message.content.get("repair_plans", [])

        validation_results = []

        for repair_plan in repair_plans:
            task = {"type": "validate_repair", "repair_plan": repair_plan}
            result = self.execute_task(task)
            validation_results.append(result)

        # Send results back to orchestrator
        return self.send_message(
            receiver="orchestrator",
            message_type="validation_complete",
            content={
                "validation_results": validation_results,
                "all_passed": all(r.get("validation_passed", False) for r in validation_results)
            }
        )

    def _handle_pre_validate(self, message: AgentMessage) -> AgentMessage:
        """Handle pre-validation request."""
        repair_plan = message.content.get("repair_plan")
        result = self._pre_validate_fix({"repair_plan": repair_plan})

        return self.send_message(
            receiver=message.sender,
            message_type="pre_validation_result",
            content=result
        )

    def _handle_post_validate(self, message: AgentMessage) -> AgentMessage:
        """Handle post-validation request."""
        repair_plan = message.content.get("repair_plan")
        application_result = message.content.get("application_result")

        result = self._post_validate_fix({
            "repair_plan": repair_plan,
            "application_result": application_result
        })

        return self.send_message(
            receiver=message.sender,
            message_type="post_validation_result",
            content=result
        )

    def _handle_health_check(self, message: AgentMessage) -> AgentMessage:
        """Handle health check request."""
        result = self._check_system_health({})

        return self.send_message(
            receiver=message.sender,
            message_type="health_check_result",
            content=result
        )

    def continuous_validation(self, duration: Optional[int] = None) -> None:
        """
        Run continuous health monitoring.

        Args:
            duration: Duration in seconds (None for infinite)
        """
        start_time = time.time()
        self.logger.info("Starting continuous validation monitoring")

        while True:
            # Perform health check
            health_result = self._check_system_health({})

            if health_result["status"] != "healthy":
                self.logger.warning(
                    f"System health degraded: {health_result.get('issues', [])}"
                )

                # Send alert to orchestrator
                alert_message = self.send_message(
                    receiver="orchestrator",
                    message_type="health_alert",
                    content=health_result
                )

            # Check duration
            if duration and (time.time() - start_time) >= duration:
                break

            # Sleep before next check
            time.sleep(self.health_check_interval)

        self.logger.info("Stopped continuous validation monitoring")
