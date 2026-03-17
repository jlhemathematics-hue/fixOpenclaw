# 🐍 Using Python 3.13 with FixOpenclaw

This guide explains how to set up and use FixOpenclaw with Homebrew's Python 3.13.12.

---

## ✅ Python Version Support

FixOpenclaw supports:
- **Minimum**: Python 3.9
- **Recommended**: Python 3.13 (latest)
- **Tested on**: Python 3.9.6, 3.13.12

---

## 🚀 Quick Setup with Python 3.13

### Option 1: Automated Setup (Recommended)

```bash
# Run the setup script
./setup_python313.sh
```

This script will:
1. ✅ Verify Python 3.13 is installed
2. ✅ Create virtual environment with Python 3.13
3. ✅ Install all dependencies
4. ✅ Ready to use!

### Option 2: Manual Setup

```bash
# 1. Create virtual environment with Python 3.13
/opt/homebrew/bin/python3.13 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip setuptools wheel

# 4. Install dependencies
pip install -r requirements.txt

# 5. Verify installation
python --version  # Should show Python 3.13.12
```

---

## 🔌 Activating the Environment

### Quick Activation
```bash
# Use the activation script
./activate_python313.sh
```

### Manual Activation
```bash
source venv/bin/activate
```

---

## 🧪 Testing

After setup, verify everything works:

```bash
# Activate environment
source venv/bin/activate

# Run quick tests
python quick_test.py

# Run end-to-end test
python main.py --mode once --log-file logs/openclaw.log
```

Expected output:
```
✓ 6/6 tests passed
🎉 All tests passed!
```

---

## 📋 Prerequisites

### Install Python 3.13 via Homebrew

If you don't have Python 3.13 installed:

```bash
# Install Python 3.13
brew install python@3.13

# Verify installation
/opt/homebrew/bin/python3.13 --version
# Should output: Python 3.13.12
```

---

## 🔧 Troubleshooting

### Python 3.13 not found
```bash
# Check if Homebrew Python is installed
brew list | grep python

# Install if missing
brew install python@3.13

# Verify path
which python3.13
# Should output: /opt/homebrew/bin/python3.13
```

### Virtual environment issues
```bash
# Remove old environment
rm -rf venv

# Create new one
/opt/homebrew/bin/python3.13 -m venv venv

# Activate and reinstall
source venv/bin/activate
pip install -r requirements.txt
```

### Import errors
```bash
# Make sure you're in the virtual environment
which python
# Should output: /Users/.../fixOpenclaw/venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

## 📊 Python Version Comparison

| Version | Status | Notes |
|---------|--------|-------|
| 3.9 | ✅ Supported | Minimum version |
| 3.10 | ✅ Supported | Previously minimum |
| 3.11 | ✅ Supported | Tested |
| 3.12 | ✅ Supported | Tested |
| 3.13 | ✅ Recommended | Latest, best performance |

---

## 🎯 Why Python 3.13?

### Benefits
- ✅ **Latest features** - Access to newest Python capabilities
- ✅ **Better performance** - Improved speed and efficiency
- ✅ **Security** - Latest security patches
- ✅ **Long-term support** - Future-proof your setup

### Compatibility
- ✅ All FixOpenclaw features work on Python 3.13
- ✅ All dependencies compatible
- ✅ No breaking changes from 3.9-3.13

---

## 📝 Project Configuration

The project is configured to support Python 3.13:

**pyproject.toml**:
```toml
requires-python = ">=3.9"

classifiers = [
    ...
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Programming Language :: Python :: 3.13",
]
```

---

## 🚀 Daily Usage

### Starting a session
```bash
cd /Users/hejohnny/Desktop/AI/fixOpenclaw
source venv/bin/activate
```

### Running the application
```bash
# Web dashboard
python main.py --mode web

# CLI mode
python main.py --mode auto

# One-time diagnostic
python main.py --mode once --log-file logs/openclaw.log
```

### Ending a session
```bash
deactivate
```

---

## 📚 Additional Resources

- **Setup Script**: `setup_python313.sh`
- **Activation Script**: `activate_python313.sh`
- **Main README**: `README.md`
- **Installation Guide**: `INSTALL_DEPENDENCIES.md`

---

## ✅ Verification Checklist

After setup, verify:
- [ ] Python 3.13 installed: `/opt/homebrew/bin/python3.13 --version`
- [ ] Virtual environment created: `ls venv/`
- [ ] Environment activated: `which python` shows venv path
- [ ] Dependencies installed: `pip list | grep openai`
- [ ] Tests pass: `python quick_test.py`
- [ ] Application runs: `python main.py --help`

---

## 🎉 Success!

Once all checks pass, you're ready to use FixOpenclaw with Python 3.13!

For any issues, check:
1. This guide's troubleshooting section
2. Main README.md
3. GitHub issues: https://github.com/jlhemathematics-hue/fixOpenclaw/issues

---

**Last Updated**: 2026-03-17
**Python Version**: 3.13.12
**Homebrew Path**: /opt/homebrew/bin/python3.13
