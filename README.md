# FixOpenclaw - Autonomous OpenClaw Diagnostics & Repair System

🔧 An intelligent AI-powered system that autonomously detects, diagnoses, and repairs OpenClaw anomalies using advanced multi-agent architecture and multiple LLM providers.

## 🌟 Features

### 🤖 Autonomous Agent System
- **Multi-Agent Architecture**: Coordinated agents for monitoring, diagnosis, repair, and validation
- **Self-Healing**: Automatic detection and repair of anomalies without human intervention
- **Intelligent Decision Making**: Context-aware problem analysis and solution generation

### 🧠 Multi-LLM Provider Support
- **OpenAI** (GPT-4, GPT-3.5-turbo)
- **Anthropic** (Claude 3 Opus, Sonnet, Haiku)
- **Google AI** (Gemini Pro, Gemini Ultra)
- **Azure OpenAI**
- **Local Models** (via Ollama, LM Studio)
- **Easy Provider Switching**: Change LLM providers on-the-fly via config or UI

### 🔍 Advanced Monitoring & Detection
- **Real-time Log Monitoring**: Continuous monitoring of OpenClaw logs and system metrics
- **Pattern Recognition**: ML-based anomaly detection with custom pattern matching
- **Multi-source Integration**: Support for logs, metrics, traces, and events
- **Predictive Alerts**: Early warning system for potential issues

### 🛠️ Intelligent Repair Engine
- **Root Cause Analysis**: Deep analysis of error context and system state
- **Multi-strategy Repair**: Multiple repair strategies with automatic selection
- **Validation & Testing**: Automated testing of fixes before deployment
- **Rollback Capability**: Safe rollback if repairs fail
- **Learning from History**: Improves repair strategies based on past successes

### 📊 User Interface
- **Web Dashboard**: Beautiful Streamlit-based UI for monitoring and control
- **CLI Tool**: Command-line interface for automation and scripting
- **Real-time Visualization**: Live charts and graphs of system health
- **Manual Override**: Human-in-the-loop option when needed

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     OpenClaw System Layer                        │
│          (Logs, Metrics, Traces, Configuration)                  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Monitoring Agent Layer                          │
│   • Log Monitor    • Metric Monitor    • Health Checker         │
│   • Pattern Detector    • Anomaly Detector                      │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Diagnostic Agent Layer                          │
│   • Root Cause Analyzer    • Context Aggregator                 │
│   • Error Classifier    • Impact Assessor                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LLM Provider Layer                            │
│   • OpenAI    • Anthropic    • Google AI    • Azure             │
│   • Unified Interface    • Provider Switching                   │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Repair Agent Layer                             │
│   • Fix Generator    • Strategy Selector                        │
│   • Code Patcher    • Configuration Manager                     │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Validation Agent Layer                          │
│   • Fix Validator    • Test Runner                              │
│   • Safety Checker    • Rollback Manager                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Orchestration Layer                             │
│   • Agent Coordinator    • State Manager                        │
│   • Event Bus    • Decision Engine                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface Layer                          │
│   • Web Dashboard (Streamlit)    • CLI Tool                     │
│   • API Server    • Notification System                         │
└─────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or later
- API keys for your preferred LLM provider(s)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/jlhemathematics-hue/fixOpenclaw.git
cd fixOpenclaw

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys and settings
```

### Configuration

Edit `config/config.yaml`:

```yaml
llm_provider:
  default: "openai"  # or "anthropic", "google", "azure", "local"

  openai:
    api_key: "${OPENAI_API_KEY}"
    model: "gpt-4"

  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-3-opus-20240229"

  google:
    api_key: "${GOOGLE_API_KEY}"
    model: "gemini-pro"

monitoring:
  log_paths:
    - "/var/log/openclaw/*.log"
  check_interval: 5  # seconds
  anomaly_threshold: 0.8

repair:
  auto_repair: true
  require_approval: false  # Set to true for manual approval
  max_retry: 3
  rollback_on_failure: true
```

### Usage

#### Web Dashboard

```bash
# Start the web interface
python main.py --mode web

# Access at http://localhost:8501
```

#### CLI Mode

```bash
# Run autonomous monitoring and repair
python main.py --mode auto

# One-time diagnosis
python main.py --mode once --log-file /path/to/log

# Interactive mode
python main.py --mode interactive

# List available backups
python main.py --mode list-backups

# Restore from backup (latest by default)
python main.py --mode restore-backup

# Restore a specific backup (dry-run)
python main.py --mode restore-backup --backup-id <id> --dry-run
```

## 📂 Project Structure

```
fixOpenclaw/
│
├── src/
│   ├── agents/                    # Agent implementations
│   │   ├── __init__.py
│   │   ├── base_agent.py         # Base agent class
│   │   ├── monitor_agent.py      # Monitoring agent
│   │   ├── diagnostic_agent.py   # Diagnostic agent
│   │   ├── repair_agent.py       # Repair agent
│   │   ├── validation_agent.py   # Validation agent
│   │   └── orchestrator.py       # Agent orchestrator
│   │
│   ├── llm_providers/            # LLM provider integrations
│   │   ├── __init__.py
│   │   ├── base_provider.py     # Base provider interface
│   │   ├── openai_provider.py   # OpenAI integration
│   │   ├── anthropic_provider.py # Anthropic integration
│   │   ├── google_provider.py   # Google AI integration
│   │   ├── azure_provider.py    # Azure OpenAI integration
│   │   ├── local_provider.py    # Local model integration
│   │   └── provider_factory.py  # Provider factory
│   │
│   ├── monitors/                 # Monitoring modules
│   │   ├── __init__.py
│   │   ├── log_monitor.py       # Log file monitoring
│   │   ├── metric_monitor.py    # Metrics monitoring
│   │   ├── health_checker.py    # Health checking
│   │   └── anomaly_detector.py  # Anomaly detection
│   │
│   ├── repair_engine/            # Repair engine
│   │   ├── __init__.py
│   │   ├── fix_generator.py     # Fix generation
│   │   ├── strategy_selector.py # Strategy selection
│   │   ├── code_patcher.py      # Code patching
│   │   ├── validator.py         # Fix validation
│   │   └── rollback_manager.py  # Rollback management
│   │
│   └── utils/                    # Utilities
│       ├── __init__.py
│       ├── config_loader.py     # Configuration loading
│       ├── logger.py            # Logging utilities
│       ├── parser.py            # Log parsing
│       ├── message_bus.py       # Inter-agent messaging
│       └── metrics.py           # Metrics collection
│
├── config/
│   ├── config.yaml              # Main configuration
│   ├── patterns.yaml            # Error patterns
│   └── strategies.yaml          # Repair strategies
│
├── ui/
│   ├── dashboard.py             # Streamlit dashboard
│   ├── cli.py                   # CLI interface
│   └── api_server.py            # REST API server
│
├── tests/
│   ├── test_agents.py
│   ├── test_providers.py
│   ├── test_monitors.py
│   └── test_repair_engine.py
│
├── logs/                         # Log storage
├── docs/                         # Documentation
│   ├── architecture.md
│   ├── api_reference.md
│   └── user_guide.md
│
├── main.py                       # Main entry point
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project metadata
├── .env.example                 # Environment template
├── .gitignore
└── README.md
```

## 🔧 Advanced Features

### Custom Repair Strategies

Create custom repair strategies in `config/strategies.yaml`:

```yaml
strategies:
  - name: "connection_timeout"
    pattern: "connection.*timeout"
    actions:
      - type: "config_update"
        params:
          key: "timeout"
          value: 60
      - type: "restart_service"
        params:
          service: "openclaw"
    validation:
      - type: "health_check"
        endpoint: "/health"
```

### Custom Anomaly Patterns

Define custom patterns in `config/patterns.yaml`:

```yaml
patterns:
  - name: "memory_leak"
    regex: "OutOfMemory|MemoryError"
    severity: "critical"
    category: "resource"

  - name: "database_error"
    regex: "DatabaseError|Connection refused.*database"
    severity: "high"
    category: "database"
```

### Webhook Notifications

Configure webhooks for alerts:

```yaml
notifications:
  webhooks:
    - url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
      events: ["anomaly_detected", "repair_completed", "repair_failed"]
    - url: "https://discord.com/api/webhooks/YOUR/WEBHOOK"
      events: ["critical_error"]
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_agents.py

# Run with coverage
pytest --cov=src tests/

# Integration tests
pytest tests/integration/
```

## 📊 Monitoring & Metrics

The system exposes Prometheus-compatible metrics:

```
# Metrics endpoint
http://localhost:8000/metrics

# Available metrics:
- openclaw_anomalies_detected_total
- openclaw_repairs_attempted_total
- openclaw_repairs_successful_total
- openclaw_repairs_failed_total
- openclaw_repair_duration_seconds
- openclaw_agent_processing_time_seconds
```

## 🔐 Security

- API keys stored securely in environment variables
- No sensitive data in logs
- Audit trail for all repairs
- Role-based access control for API
- Encrypted communication between agents

## 🤝 Contributing

Contributions welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 👤 Author

**Johnny He**
GitHub: [@jlhemathematics-hue](https://github.com/jlhemathematics-hue)

## 🙏 Acknowledgments

- Inspired by SelfHealingCodeAgent and other autonomous debugging systems
- Built with modern AI agent frameworks and best practices
- Thanks to the open-source community

## 📞 Support

- Issues: [GitHub Issues](https://github.com/jlhemathematics-hue/fixOpenclaw/issues)
- Email: support@fixopenclaw.dev

---

**Built with ❤️ for autonomous system reliability**

*Making OpenClaw systems self-healing, one anomaly at a time.*
