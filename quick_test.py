#!/usr/bin/env python3
"""
Quick Test Script for FixOpenclaw

Tests basic functionality without requiring API keys.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Change to project directory
os.chdir(project_root)

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")

    try:
        from src.agents.base_agent import BaseAgent, AgentMessage
        print("✓ Base agent imports OK")
    except Exception as e:
        print(f"✗ Base agent import failed: {e}")
        return False

    try:
        from src.agents.monitor_agent import MonitorAgent
        print("✓ Monitor agent imports OK")
    except Exception as e:
        print(f"✗ Monitor agent import failed: {e}")
        return False

    try:
        from src.agents.diagnostic_agent import DiagnosticAgent
        print("✓ Diagnostic agent imports OK")
    except Exception as e:
        print(f"✗ Diagnostic agent import failed: {e}")
        return False

    try:
        from src.agents.repair_agent import RepairAgent
        print("✓ Repair agent imports OK")
    except Exception as e:
        print(f"✗ Repair agent import failed: {e}")
        return False

    try:
        from src.agents.validation_agent import ValidationAgent
        print("✓ Validation agent imports OK")
    except Exception as e:
        print(f"✗ Validation agent import failed: {e}")
        return False

    try:
        from src.utils.config_loader import ConfigLoader
        print("✓ Config loader imports OK")
    except Exception as e:
        print(f"✗ Config loader import failed: {e}")
        return False

    try:
        from src.utils.logger import setup_logger
        print("✓ Logger imports OK")
    except Exception as e:
        print(f"✗ Logger import failed: {e}")
        return False

    return True


def test_monitor_agent():
    """Test monitor agent basic functionality."""
    print("\nTesting Monitor Agent...")

    try:
        from src.agents.monitor_agent import MonitorAgent

        # Create agent
        agent = MonitorAgent("test_monitor")
        print("✓ Monitor agent created")

        # Test log scanning with sample file
        if os.path.exists("logs/openclaw.log"):
            task = {
                "type": "monitor_logs",
                "log_file": "logs/openclaw.log"
            }
            result = agent.execute_task(task)
            print(f"✓ Log scanning works: {result['anomalies_found']} anomalies found")

            if result['anomalies_found'] > 0:
                print(f"  Sample anomaly: {result['anomalies'][0]['type']}")
        else:
            print("⚠ Sample log file not found, skipping scan test")

        return True

    except Exception as e:
        print(f"✗ Monitor agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_diagnostic_agent():
    """Test diagnostic agent basic functionality."""
    print("\nTesting Diagnostic Agent...")

    try:
        from src.agents.diagnostic_agent import DiagnosticAgent

        # Create agent (without LLM for testing)
        agent = DiagnosticAgent("test_diag", {"llm_provider": None})
        print("✓ Diagnostic agent created")

        # Test classification
        anomaly = {
            "type": "error",
            "severity": "high",
            "category": "database",
            "line_content": "ERROR Database connection timeout"
        }
        classification = agent._classify_anomaly(anomaly)
        print(f"✓ Anomaly classification works: {classification['category']}")

        return True

    except Exception as e:
        print(f"✗ Diagnostic agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_repair_agent():
    """Test repair agent basic functionality."""
    print("\nTesting Repair Agent...")

    try:
        from src.agents.repair_agent import RepairAgent

        # Create agent (without LLM for testing)
        agent = RepairAgent("test_repair", {"llm_provider": None})
        print("✓ Repair agent created")

        # Test risk assessment
        diagnosis = {
            "severity": "high",
            "category": "database",
            "root_cause": "Connection timeout"
        }
        risk = agent._assess_risk(diagnosis)
        print(f"✓ Risk assessment works: {risk} risk")

        return True

    except Exception as e:
        print(f"✗ Repair agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_agent():
    """Test validation agent basic functionality."""
    print("\nTesting Validation Agent...")

    try:
        from src.agents.validation_agent import ValidationAgent

        # Create agent
        agent = ValidationAgent("test_valid")
        print("✓ Validation agent created")

        # Test pre-validation
        repair_plan = {
            "strategy": "restart_service",
            "steps": ["backup", "restart"],
            "risk_level": "medium"
        }
        result = agent._pre_validate(repair_plan)
        print(f"✓ Pre-validation works: {result['status']}")

        return True

    except Exception as e:
        print(f"✗ Validation agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_loader():
    """Test configuration loading."""
    print("\nTesting Config Loader...")

    try:
        from src.utils.config_loader import ConfigLoader

        # Load config
        config = ConfigLoader("config/config.yaml")
        print("✓ Config loaded")

        # Access config
        if hasattr(config, 'monitoring'):
            print(f"✓ Config access works: check_interval={config.monitoring.check_interval}")
        else:
            print("⚠ Config structure may be different")

        return True

    except Exception as e:
        print(f"✗ Config loader test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("FixOpenclaw Quick Test")
    print("=" * 60)

    results = []

    results.append(("Imports", test_imports()))
    results.append(("Monitor Agent", test_monitor_agent()))
    results.append(("Diagnostic Agent", test_diagnostic_agent()))
    results.append(("Repair Agent", test_repair_agent()))
    results.append(("Validation Agent", test_validation_agent()))
    results.append(("Config Loader", test_config_loader()))

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{name:20s} {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
