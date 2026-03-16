#!/usr/bin/env python3
"""
FixOpenclaw Installation Verification Script

Verifies that all components are properly installed and configured.
"""

import sys
from pathlib import Path
import importlib.util

# Colors for output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def check_mark(passed: bool) -> str:
    return f"{Colors.GREEN}✓{Colors.END}" if passed else f"{Colors.RED}✗{Colors.END}"

def print_header(text: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def check_python_version():
    """Check Python version."""
    print("Checking Python version...")
    version = sys.version_info
    required = (3, 10)

    passed = version >= required
    print(f"{check_mark(passed)} Python {version.major}.{version.minor}.{version.micro}")

    if not passed:
        print(f"{Colors.RED}  Error: Python 3.10+ required{Colors.END}")

    return passed

def check_file_exists(path: str, description: str) -> bool:
    """Check if a file exists."""
    exists = Path(path).exists()
    print(f"{check_mark(exists)} {description}: {path}")
    return exists

def check_module(module_name: str, package_name: str = None) -> bool:
    """Check if a Python module is available."""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"{check_mark(True)} {package_name or module_name}")
            return True
    except:
        pass

    print(f"{check_mark(False)} {package_name or module_name}")
    return False

def main():
    print_header("FixOpenclaw Installation Verification")

    all_passed = True

    # Check Python version
    all_passed &= check_python_version()

    print("\n" + "-"*60)
    print("Checking Core Files...")
    print("-"*60)

    # Check core files
    core_files = [
        ("main.py", "Main entry point"),
        ("config/config.yaml", "Configuration file"),
        (".env.example", "Environment template"),
        ("requirements.txt", "Dependencies"),
        ("pyproject.toml", "Project metadata"),
    ]

    for path, desc in core_files:
        all_passed &= check_file_exists(path, desc)

    print("\n" + "-"*60)
    print("Checking Source Files...")
    print("-"*60)

    # Check source files
    source_files = [
        ("src/agents/base_agent.py", "Base Agent"),
        ("src/agents/monitor_agent.py", "Monitor Agent"),
        ("src/agents/diagnostic_agent.py", "Diagnostic Agent"),
        ("src/agents/repair_agent.py", "Repair Agent"),
        ("src/agents/validation_agent.py", "Validation Agent"),
        ("src/agents/orchestrator.py", "Orchestrator"),
        ("src/llm_providers/provider_factory.py", "LLM Provider Factory"),
        ("src/utils/config_loader.py", "Config Loader"),
        ("src/utils/logger.py", "Logger"),
    ]

    for path, desc in source_files:
        all_passed &= check_file_exists(path, desc)

    print("\n" + "-"*60)
    print("Checking UI Files...")
    print("-"*60)

    all_passed &= check_file_exists("ui/dashboard.py", "Web Dashboard")

    print("\n" + "-"*60)
    print("Checking Dependencies...")
    print("-"*60)

    # Check key dependencies
    dependencies = [
        ("dotenv", "python-dotenv"),
        ("yaml", "pyyaml"),
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("google.generativeai", "google-generativeai"),
        ("streamlit", "streamlit"),
    ]

    for module, package in dependencies:
        check_module(module, package)

    print("\n" + "-"*60)
    print("Checking Directories...")
    print("-"*60)

    directories = [
        "logs",
        "src",
        "ui",
        "config",
        "tests",
    ]

    for directory in directories:
        exists = Path(directory).is_dir()
        print(f"{check_mark(exists)} Directory: {directory}/")

    print("\n" + "-"*60)
    print("Configuration Check...")
    print("-"*60)

    # Check .env
    env_exists = Path(".env").exists()
    if env_exists:
        print(f"{check_mark(True)} .env file exists")
        print(f"{Colors.YELLOW}  ⚠ Make sure to add your API keys!{Colors.END}")
    else:
        print(f"{check_mark(False)} .env file not found")
        print(f"{Colors.YELLOW}  Run: cp .env.example .env{Colors.END}")

    # Summary
    print_header("Verification Summary")

    if all_passed and env_exists:
        print(f"{Colors.GREEN}✓ All checks passed!{Colors.END}")
        print(f"\nYou're ready to run FixOpenclaw:")
        print(f"  python main.py --mode once")
    elif all_passed:
        print(f"{Colors.YELLOW}⚠ Almost ready!{Colors.END}")
        print(f"\nNext steps:")
        print(f"  1. cp .env.example .env")
        print(f"  2. Edit .env and add your API keys")
        print(f"  3. python main.py --mode once")
    else:
        print(f"{Colors.RED}✗ Some checks failed{Colors.END}")
        print(f"\nPlease:")
        print(f"  1. Fix the issues above")
        print(f"  2. Run: pip install -r requirements.txt")
        print(f"  3. Run this script again")

    print()

if __name__ == "__main__":
    main()
