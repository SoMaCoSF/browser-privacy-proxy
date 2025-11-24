<!--
===============================================================================
file_id: SOM-DOC-0005-v1.0.0
name: TUI_SETUP_GUIDE.md
description: Guide for the Interactive TUI Setup System
project_id: BROWSER-MIXER-ANON
category: documentation
tags: [tui, setup, guide, wizard]
created: 2025-01-23
modified: 2025-01-23
version: 1.0.0
agent_id: AGENT-PRIME-001
execution: Documentation file
===============================================================================
-->

# Interactive TUI Setup Guide

The Privacy Proxy now includes a **beautiful, interactive TUI (Text User Interface) setup wizard** that makes installation trivial!

## Quick Start

```bash
# Install rich library (one-time)
pip install rich

# Run the wizard
python setup_tui.py
```

That's it! The wizard handles everything.

---

## What the TUI Does

### Step 1: Welcome Banner
```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║               🛡️  PRIVACY PROXY SETUP WIZARD  🛡️                    ║
║                                                                      ║
║            Browser Anonymization & Tracker Blocking Tool            ║
║                          Version 1.0.0                               ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
```

### Step 2: Prerequisites Check

Automatically checks:
- ✅ Python version (3.10+)
- ✅ uv package manager (preferred)
- ✅ pip (fallback)
- ✅ git (optional)

**Output:**
```
┌─────────────────────────────────────────────────────────────────┐
│                          System Check                            │
├──────────────────────┬──────────────┬──────────────────────────┤
│ Component            │ Status       │ Details                  │
├──────────────────────┼──────────────┼──────────────────────────┤
│ Python 3.10+         │ ✓ Pass       │ 3.12.1                   │
│ uv package manager   │ ✓ Pass       │ Found                    │
│ pip                  │ ✓ Pass       │ Found                    │
│ git                  │ ✓ Pass       │ Found (optional)         │
└──────────────────────┴──────────────┴──────────────────────────┘
```

### Step 3: Virtual Environment

Creates `.venv` automatically with progress indicator:
```
⠋ Creating virtual environment...
```

### Step 4: Install Dependencies

Installs all packages from `requirements.txt`:
```
⠋ Installing dependencies (this may take a few minutes)...
```

Installs:
- mitmproxy (proxy engine)
- fake-useragent (fingerprint randomization)
- requests (HTTP client)
- pyyaml (config parsing)
- rich (TUI library)

### Step 5: Directory Setup

Creates necessary directories:
```
┌────────────────────────────────────────────────────────────┐
│                      Directory Setup                        │
├────────────────────┬──────────────────┬────────────────────┤
│ Directory          │ Purpose          │ Status             │
├────────────────────┼──────────────────┼────────────────────┤
│ database           │ Database storage │ ✓ Created          │
│ logs               │ Log files        │ ✓ Created          │
│ config             │ Configuration    │ ✓ Created          │
└────────────────────┴──────────────────┴────────────────────┘
```

### Step 6: Privacy Configuration

**Interactive privacy level selection:**

```
┌──────────────────────────────────────────────────────────────────────┐
│ Option │ Privacy Level                    │ Description             │
├────────┼──────────────────────────────────┼─────────────────────────┤
│   1    │ Maximum Privacy (Paranoid)       │ New fingerprint every   │
│        │                                  │ request, block ALL      │
│        │                                  │ cookies, aggressive     │
├────────┼──────────────────────────────────┼─────────────────────────┤
│   2    │ Balanced Privacy (Recommended)   │ Rotate every 5 minutes, │
│        │                                  │ block cookies, moderate │
├────────┼──────────────────────────────────┼─────────────────────────┤
│   3    │ Minimal Privacy (Testing)        │ Rotate on launch,       │
│        │                                  │ log only, no blocking   │
├────────┼──────────────────────────────────┼─────────────────────────┤
│   4    │ Custom Configuration             │ Configure manually      │
└────────┴──────────────────────────────────┴─────────────────────────┘
```

**Privacy Presets:**

1. **Maximum (Paranoid):**
   - Rotation: `every_request`
   - Block cookies: `YES`
   - Auto-block threshold: `1` hit
   - **Use case:** Maximum anonymity

2. **Balanced (Recommended):**
   - Rotation: `interval` (5 minutes)
   - Block cookies: `YES`
   - Auto-block threshold: `3` hits
   - **Use case:** Daily browsing

3. **Minimal (Testing):**
   - Rotation: `launch` (once per session)
   - Block cookies: `NO` (log only)
   - Auto-block: `NO` (log only)
   - **Use case:** Testing/debugging

4. **Custom:**
   - Configure each setting manually
   - Full control over all options

### Step 7: Database Initialization

Creates SQLite database with all tables:
```
⠋ Initializing database...

✓ Database initialized successfully!
Location: D:\...\database\browser_privacy.db
```

### Step 8: Verification

Checks all components:
```
┌─────────────────────────────────────────────────────────────────┐
│                    Installation Verification                     │
├────────────────────────┬──────────────┬─────────────────────────┤
│ Component              │ Status       │ Details                 │
├────────────────────────┼──────────────┼─────────────────────────┤
│ Virtual Environment    │ ✓ OK         │ .venv                   │
│ Configuration File     │ ✓ OK         │ config/config.yaml      │
│ Database File          │ ✓ OK         │ database/...db          │
│ privacy_proxy.py       │ ✓ OK         │ Main proxy module       │
│ start_proxy.py         │ ✓ OK         │ Launcher script         │
│ manage.py              │ ✓ OK         │ Management CLI          │
└────────────────────────┴──────────────┴─────────────────────────┘

✓ All components verified successfully!
```

### Step 9: Completion & Next Steps

Shows platform-specific instructions:

```
╔══════════════════════════════════════════════════════════════════════╗
║                                                                      ║
║                    ✓ SETUP COMPLETE! ✓                              ║
║                                                                      ║
║              Privacy Proxy is ready to use!                          ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝

🚀 Next Steps

1. Start the Proxy
   .venv\Scripts\activate.ps1
   python start_proxy.py

2. Configure Your Browser
   Firefox: Settings → Network → Manual proxy
   - HTTP: 127.0.0.1:8080
   - HTTPS: 127.0.0.1:8080

3. Install HTTPS Certificate
   Visit: http://mitm.it
   Download and trust certificate

4. Management Commands
   python manage.py stats
   python manage.py domains --limit 50
   python manage.py export blocklist.txt

📖 Full Documentation: README.md
```

---

## Features

### Beautiful UI
- ✨ Color-coded output
- 📊 Progress bars and spinners
- 📋 Tables for structured data
- 🎨 Panels and borders
- ✅ Clear status indicators

### Smart Checks
- Validates Python version
- Detects package managers
- Checks for existing installations
- Prevents overwrites (with confirmation)

### Error Handling
- Clear error messages
- Graceful failures
- Rollback on interruption (Ctrl+C)
- Helpful suggestions

### Cross-Platform
- ✅ Windows (PowerShell/CMD)
- ✅ Linux (bash/zsh)
- ✅ macOS (bash/zsh)
- Auto-detects platform
- Platform-specific commands

---

## Advanced Usage

### Silent Installation (Custom Config)

You can pre-create `config/config.yaml` before running the wizard, and it will detect and use it.

### Automated Installation (CI/CD)

For headless environments:
```bash
# Install dependencies first
pip install rich pyyaml

# Set environment variables
export PRIVACY_LEVEL=2  # Balanced

# Run with defaults (future feature)
python setup_tui.py --auto
```

### Re-running Setup

Safe to re-run anytime:
- Detects existing virtual environment
- Preserves existing database (with confirmation)
- Updates configuration
- Reinstalls dependencies

---

## Troubleshooting

### "rich library not found"
```bash
pip install rich
```

### Virtual environment creation fails
```bash
# Try standard venv instead of uv
python -m venv .venv
```

### Permission errors
```bash
# Run as administrator (Windows)
# or use sudo (Linux/Mac)
```

### "Command not found: python"
```bash
# Use python3 on Linux/Mac
python3 setup_tui.py
```

---

## Technical Details

### Built With
- **rich** - Terminal formatting and UI
- **pathlib** - Cross-platform paths
- **subprocess** - Running system commands
- **platform** - OS detection

### Code Structure
```python
class PrivacyProxySetup:
    def __init__(self)          # Initialize paths
    def clear_screen(self)      # Clear terminal
    def show_banner(self)       # Welcome message
    def check_prerequisites(self) # System checks
    def create_virtual_environment(self)
    def install_dependencies(self)
    def setup_directories(self)
    def configure_privacy_level(self) # Interactive config
    def initialize_database(self)
    def run_verification(self)
    def show_completion(self)   # Final instructions
    def run(self)               # Main orchestrator
```

### Dependencies
- Python 3.10+ (required)
- rich 13.7+ (for TUI)
- pip or uv (for package installation)

---

## Why TUI?

**Before (manual setup):**
1. Read documentation
2. Run multiple commands
3. Edit configuration files
4. Initialize database manually
5. Verify everything works
6. Figure out next steps

**After (TUI setup):**
1. Run `python setup_tui.py`
2. Follow prompts
3. Done!

**Benefits:**
- ✅ No need to remember commands
- ✅ No manual configuration editing
- ✅ Guided experience
- ✅ Automatic verification
- ✅ Clear feedback
- ✅ Less error-prone
- ✅ Beautiful UI

---

## Screenshots

### Welcome Screen
```
╔══════════════════════════════════════════════════════════════════════╗
║               🛡️  PRIVACY PROXY SETUP WIZARD  🛡️                    ║
╚══════════════════════════════════════════════════════════════════════╝

Welcome to the Privacy Proxy Interactive Setup!
This wizard will guide you through the installation and configuration.

Ready to begin? [Y/n]:
```

### Privacy Selection
```
┌──────┬────────────────────────────┬───────────────────────────────┐
│ Option │ Privacy Level              │ Description                   │
├──────┼────────────────────────────┼───────────────────────────────┤
│   1    │ Maximum Privacy (Paranoid) │ New fingerprint every request │
│   2    │ Balanced (Recommended)     │ Rotate every 5 minutes        │
│   3    │ Minimal (Testing)          │ Rotate on launch only         │
│   4    │ Custom Configuration       │ Configure manually            │
└──────┴────────────────────────────┴───────────────────────────────┘

Select option [1/2/3/4] (2):
```

### Progress Indicator
```
⠋ Installing dependencies (this may take a few minutes)...
```

### Completion
```
✓ SETUP COMPLETE!

Privacy Proxy is ready to use!
```

---

## Comparison: TUI vs Manual

| Feature | Manual Setup | TUI Setup |
|---------|-------------|-----------|
| Steps | 10+ commands | 1 command |
| Time | 10-15 minutes | 3-5 minutes |
| Configuration | Edit YAML manually | Interactive prompts |
| Errors | Manual troubleshooting | Auto-detected |
| Verification | Manual | Automatic |
| Documentation | Read multiple files | Built-in guidance |
| User-friendly | ❌ | ✅ |
| Beautiful UI | ❌ | ✅ |

---

## Future Enhancements

Planned features:
- [ ] Automated installation mode (`--auto`)
- [ ] Configuration profiles (save/load)
- [ ] Update checker
- [ ] System integration (systemd/launchd)
- [ ] Docker containerization option
- [ ] One-line installer script
- [ ] Web-based GUI setup
- [ ] Configuration import/export

---

## Contributing

Want to improve the TUI?

Ideas:
- Add more color themes
- Add animations
- Add config templates
- Add backup/restore
- Add diagnostic mode
- Add performance testing

---

## Credits

**Created with:** Python, rich library
**Designed by:** AGENT-PRIME-001 (Claude Sonnet 4.5)
**Version:** 1.0.0

---

**Happy private browsing!** 🛡️
