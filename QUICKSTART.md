# FixOpenclaw Quick Start Guide

Get started with FixOpenclaw in 5 minutes!

## Prerequisites

- Python 3.10 or later
- API key for at least one LLM provider (OpenAI, Anthropic, or Google)

## Installation

### 1. Clone or download the repository

```bash
cd fixOpenclaw
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# For OpenAI:
OPENAI_API_KEY=sk-your-key-here

# For Anthropic:
ANTHROPIC_API_KEY=your-anthropic-key-here

# For Google:
GOOGLE_API_KEY=your-google-key-here
```

### 5. Create log directory (if not exists)

```bash
mkdir -p logs
```

## Usage

### Option 1: Autonomous Mode (Recommended)

Run continuous monitoring and automatic repair:

```bash
python main.py --mode auto
```

This will:
- Monitor log files every 60 seconds (configurable)
- Automatically detect anomalies
- Diagnose issues using LLM
- Generate and apply repairs
- Validate fixes

**Press Ctrl+C to stop**

### Option 2: One-Time Analysis

Analyze a specific log file once:

```bash
python main.py --mode once --log-file logs/openclaw.log
```

This will run a single diagnostic cycle and display results.

### Option 3: Web Dashboard

Launch the interactive web dashboard:

```bash
python main.py --mode web
```

Then open http://localhost:8501 in your browser.

The dashboard provides:
- Real-time system status
- Anomaly detection results
- Diagnostic reports
- Repair history
- System metrics

### Option 4: Interactive Mode

Run in interactive command-line mode:

```bash
python main.py --mode interactive
```

This gives you a menu to:
1. Run monitoring manually
2. View system status
3. View metrics
4. Run full cycle
5. Exit

## Testing with Sample Data

A sample log file is provided at `logs/openclaw.log` with various error scenarios.

Try analyzing it:

```bash
python main.py --mode once --log-file logs/openclaw.log
```

You should see:
- Multiple anomalies detected (errors, warnings, fatal issues)
- LLM-powered diagnostic analysis
- Generated repair strategies
- Validation results

## Configuration

### Change LLM Provider

Edit `config/config.yaml`:

```yaml
llm_provider:
  default: "anthropic"  # Change from "openai" to "anthropic" or "google"
```

### Adjust Monitoring Frequency

```yaml
orchestrator:
  cycle_interval: 30  # Check every 30 seconds instead of 60
```

### Enable/Disable Auto-Repair

```yaml
repair:
  auto_repair: false  # Require manual approval for all repairs
```

### Add Custom Log Paths

```yaml
monitoring:
  log_paths:
    - "logs/openclaw.log"
    - "logs/application.log"
    - "/var/log/system.log"
```

## Understanding the Output

### Autonomous Mode Output

```
2024-03-16 10:30:00 - INFO - Running autonomous cycle
2024-03-16 10:30:05 - INFO - Monitoring complete: 3 anomalies detected
2024-03-16 10:30:15 - INFO - Diagnostics complete: 3 diagnostics generated
2024-03-16 10:30:25 - INFO - Repairs complete: 3 repair plans generated
2024-03-16 10:30:35 - INFO - Validation complete: 2/3 repairs successful
2024-03-16 10:30:35 - INFO - Cycle complete: 3 anomalies, 2 repairs successful
```

### One-Time Analysis Output

```
============================================================
FixOpenclaw Diagnostic Results
============================================================
Status: success
Anomalies detected: 5
Diagnostics completed: 5
Repairs attempted: 3
Repairs successful: 2
Duration: 12.34 seconds
============================================================
```

## Troubleshooting

### "Config file not found"

Make sure you're running from the project root directory:

```bash
cd fixOpenclaw
python main.py --mode auto
```

### "API key not found"

Check your `.env` file has the correct API key:

```bash
cat .env  # Should show your API keys
```

### "No module named 'openai'"

Install dependencies:

```bash
pip install -r requirements.txt
```

### "Permission denied" on log files

Make sure the log files are readable:

```bash
chmod 644 logs/openclaw.log
```

Or specify a different log path in `config/config.yaml`.

## Next Steps

1. **Customize Anomaly Patterns**: Add your own patterns in `config/config.yaml`
2. **Integrate with Your System**: Point to your actual log files
3. **Set Up Notifications**: Configure webhooks for alerts
4. **Extend Repair Strategies**: Add custom repair logic
5. **Run Tests**: `pytest tests/` to verify functionality

## Getting Help

- Read the full README.md for detailed documentation
- Check the architecture documentation in `docs/`
- Open an issue on GitHub for bugs or questions
- Review the code examples in `tests/`

## Safety Notes

⚠️ **Important**: FixOpenclaw can automatically apply repairs to your system. Before using in production:

1. Test thoroughly in a development environment
2. Review generated repairs before auto-applying
3. Enable `require_approval: true` for high-risk repairs
4. Set up proper backups
5. Monitor the repair results

Start with `auto_repair: false` to review all repairs manually.

---

**Happy debugging! 🔧**
