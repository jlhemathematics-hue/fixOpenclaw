# Changelog

All notable changes to FixOpenclaw will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.1] - 2026-03-17

### Added
- Python 3.13 support and configuration
- Automated setup script for Python 3.13 (`setup_python313.sh`)
- Quick activation script (`activate_python313.sh`)
- Comprehensive Python 3.13 setup guide (`PYTHON_313_SETUP.md`)
- `.python-version` file for version management
- `.envrc` file for direnv integration
- `CHANGELOG.md` for tracking changes

### Changed
- Updated `pyproject.toml` to include Python 3.13 in classifiers
- Updated black configuration to support Python 3.13
- Enhanced documentation with Python 3.13 specific instructions

### Documentation
- Added detailed Python 3.13 setup guide
- Added automated setup scripts with inline documentation
- Updated installation instructions

---

## [1.2] - 2026-03-17

### Fixed
- **Python Version Requirement** (Medium Priority)
  - Lowered minimum Python version from 3.10+ to 3.9+
  - Makes installation easier on more systems

- **Google AI Package Dependency Mismatch** (Medium Priority)
  - Fixed inconsistency between `requirements.txt` and `pyproject.toml`
  - Both now use `google-generativeai>=0.3.0`
  - Added `tiktoken>=0.5.0` to `pyproject.toml`

- **Missing Manual Repair Type Handler** (High Priority)
  - Added handler for "manual" fix type in repair agent
  - Eliminates "Unknown fix type: manual" errors
  - Improves offline mode reliability

### Added
- Comprehensive bug fix documentation (`BUGFIXES_v1.2.md`)
- Detailed testing report (`TESTING_REPORT_v1.2.md`)
- Release notes (`VERSION_1.2_RELEASE_NOTES.md`)
- Installation test summary (`INSTALLATION_TEST_SUMMARY.md`)

### Changed
- Updated Python version requirement from 3.10+ to 3.9+
- Enhanced offline mode with graceful degradation
- Improved error handling for LLM failures

### Testing
- All unit tests passed (6/6)
- End-to-end testing successful
- Fresh installation verified
- Python 3.9 compatibility confirmed

---

## [1.1] - 2026-03-16

### Fixed
- **LLM Provider Initialization Failure** (Critical)
  - Added null check for provider_name in diagnostic and repair agents
  - Fixed crash when no LLM provider specified
  - Agents can now run in offline mode

- **Orchestrator Initialization Order** (Critical)
  - Fixed AttributeError by moving system_state initialization before agent initialization
  - Orchestrator now initializes correctly

- **Google AI Deprecation Warning** (Medium)
  - Added warning suppression for deprecated google-generativeai package
  - Documented future migration to google-genai

### Added
- Bug fix documentation (`BUGFIXES_v1.1.md`)
- Offline mode support
- Better error handling

### Changed
- Improved agent initialization sequence
- Enhanced error messages

---

## [1.0] - 2026-03-16

### Added
- Initial release of FixOpenclaw
- Multi-agent architecture for autonomous diagnostics and repair
- Support for multiple LLM providers (OpenAI, Anthropic, Google AI, Azure, Local)
- Real-time log monitoring and anomaly detection
- Intelligent repair engine with multiple strategies
- Web dashboard (Streamlit)
- CLI tool
- REST API server
- Comprehensive documentation

### Features
- Autonomous anomaly detection
- Root cause analysis
- Automated repair generation and execution
- Fix validation and rollback capability
- Multi-LLM provider support with easy switching
- Pattern-based error detection
- Custom repair strategies
- Webhook notifications

### Documentation
- Comprehensive README
- Architecture documentation
- API reference
- User guide
- Deployment guide
- Quick start guide
- Project status reports

---

## Version History Summary

- **v1.2.1** (2026-03-17) - Python 3.13 support and automation
- **v1.2** (2026-03-17) - Bug fixes and improved compatibility
- **v1.1** (2026-03-16) - Critical bug fixes for initialization
- **v1.0** (2026-03-16) - Initial release

---

## Upgrade Guides

### From v1.2 to v1.2.1
```bash
git pull origin main
./setup_python313.sh  # Optional: for Python 3.13 support
```

### From v1.1 to v1.2
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python quick_test.py
```

### From v1.0 to v1.1
```bash
git pull origin main
python quick_test.py
```

---

## Links

- **Repository**: https://github.com/jlhemathematics-hue/fixOpenclaw
- **Issues**: https://github.com/jlhemathematics-hue/fixOpenclaw/issues
- **Documentation**: See README.md and docs/

---

*For detailed information about each release, see the corresponding version documentation files.*
