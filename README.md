<!--
===============================================================================
file_id: SOM-DOC-0002-v1.0.0
name: README.md
description: Complete documentation for Privacy Proxy
project_id: BROWSER-MIXER-ANON
category: documentation
tags: [readme, documentation, privacy]
created: 2025-01-22
modified: 2025-01-22
version: 1.0.0
agent_id: AGENT-PRIME-001
execution: Documentation file
===============================================================================
-->

# Privacy Proxy - Browser Anonymization Tool

A comprehensive browser privacy tool that anonymizes your browser fingerprint, blocks tracking cookies, and maintains a database of tracking domains/IPs for automatic blocking.

## Features

### 1. **Browser Fingerprint Randomization**
- Randomizes User-Agent on every request (or configurable intervals)
- Randomizes Accept-Language, Accept-Encoding headers
- Strips tracking headers (Referer, X-Forwarded-For, etc.)
- Multiple rotation modes:
  - `every_request`: New fingerprint for each request (maximum privacy)
  - `interval`: Rotate every N seconds
  - `new_tab`: Rotate on new tab/window
  - `launch`: Rotate only on browser launch

### 2. **Cookie Blocking**
- Blocks ALL cookies by default (configurable)
- Logs all cookie attempts to SQLite database
- Identifies tracking cookies using pattern matching
- Captures cookie data for analysis
- Dev/null cookies - they never reach your browser

### 3. **Automatic Tracker Blocking**
- Builds SQLite database of tracking domains and IPs
- Auto-blocks domains/IPs after threshold hits
- Pattern-based blocking (analytics, ads, trackers)
- Maintains whitelist for trusted sites
- Exports blocklists in multiple formats

### 4. **Privacy Database**
- SQLite database tracks:
  - All cookie traffic attempts
  - Tracking domains and IPs
  - Request logs with fingerprints
  - Fingerprint rotation history
- Query and analyze tracking attempts
- Export data for further analysis

### 5. **Management CLI**
- View statistics
- List blocked domains/IPs
- Export blocklists
- Manage whitelist
- View recent requests and cookies

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser                               │
│          (configured to use proxy 127.0.0.1:8080)           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   Privacy Proxy Server                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Fingerprint Randomizer                               │  │
│  │  - Randomizes User-Agent, headers                    │  │
│  │  - Strips tracking headers                           │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Cookie Interceptor                                    │  │
│  │  - Blocks cookies (request & response)               │  │
│  │  - Logs to database                                  │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Traffic Blocker                                       │  │
│  │  - Blocks known tracking domains/IPs                 │  │
│  │  - Pattern-based blocking                            │  │
│  └──────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ Database Handler                                      │  │
│  │  - SQLite database operations                        │  │
│  │  - Logs cookies, requests, fingerprints              │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Internet                                │
│         (requests sent with randomized fingerprint)          │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Prerequisites
- Python 3.10+ (3.12+ recommended)
- pip or uv package manager
- Windows 10/11, Linux, or macOS

### Option 1: Interactive TUI Setup (Recommended)

**The easiest way to get started!**

```powershell
# Install rich library (required for TUI)
pip install rich

# Run the interactive setup wizard
python setup_tui.py
```

The TUI wizard will:
- ✅ Check prerequisites
- ✅ Create virtual environment
- ✅ Install all dependencies
- ✅ Set up directories
- ✅ Configure privacy settings (with preset levels)
- ✅ Initialize database
- ✅ Verify installation
- ✅ Show you next steps

### Option 2: PowerShell Script

```powershell
.\setup.ps1
```

### Option 3: Manual Setup

```powershell
# Create virtual environment
uv venv .venv
# or: python -m venv .venv

# Activate it
.venv\Scripts\activate.ps1  # Windows
# or: source .venv/bin/activate  # Linux/Mac

# Install dependencies
uv pip install -r requirements.txt
# or: pip install -r requirements.txt

# Initialize database
python -c "from database_handler import DatabaseHandler; DatabaseHandler('database/browser_privacy.db')"
```

---

## Usage

### Starting the Proxy

```powershell
# Activate virtual environment
.venv\Scripts\activate.ps1

# Start proxy (default port 8080)
python start_proxy.py

# Start on custom port
python start_proxy.py --port 9090

# Use custom config
python start_proxy.py --config my_config.yaml
```

### Configure Your Browser

**Firefox:**
1. Settings → Network Settings → Settings
2. Select "Manual proxy configuration"
3. HTTP Proxy: `127.0.0.1`, Port: `8080`
4. HTTPS Proxy: `127.0.0.1`, Port: `8080`
5. Check "Use this proxy server for all protocols"

**Chrome/Edge:**
1. Settings → System → Open proxy settings
2. LAN Settings → Use proxy server
3. Address: `127.0.0.1`, Port: `8080`

**System-wide (Windows):**
```powershell
# Set proxy
netsh winhttp set proxy 127.0.0.1:8080

# Remove proxy
netsh winhttp reset proxy
```

### Installing mitmproxy Certificate

For HTTPS interception to work, install the mitmproxy CA certificate:

1. Start the proxy
2. Navigate to: `http://mitm.it`
3. Download and install certificate for your OS
4. Restart browser

---

## Management CLI

### View Statistics
```powershell
python manage.py stats
```

### List Blocked Domains
```powershell
# Top 50 blocked domains
python manage.py domains

# Top 100
python manage.py domains --limit 100
```

### List Blocked IPs
```powershell
python manage.py ips --limit 50
```

### View Cookie Attempts
```powershell
python manage.py cookies --limit 100
```

### View Recent Requests
```powershell
python manage.py requests --limit 50
```

### Export Blocklist
```powershell
# Export as hosts file format
python manage.py export blocklist.txt --format hosts

# Export as plain text
python manage.py export blocklist.txt --format text
```

### Manage Whitelist
```powershell
# Add domain to whitelist
python manage.py whitelist example.com --reason "trusted site"

# Block domain manually
python manage.py block tracker.evil.com --category "malicious"
```

---

## Configuration

Edit `config/config.yaml` to customize behavior:

### Fingerprint Randomization
```yaml
fingerprint:
  # When to rotate: "every_request", "interval", "new_tab", "launch"
  rotation_mode: "every_request"

  # Interval in seconds (if rotation_mode is "interval")
  rotation_interval: 300

  # What to randomize
  randomize_user_agent: true
  randomize_accept_language: true
  strip_referer: true
```

### Cookie Blocking
```yaml
cookies:
  # Block all cookies by default
  block_all: true

  # Log all cookie attempts
  log_attempts: true

  # Auto-block domains that send tracking cookies
  auto_block_trackers: true
```

### Traffic Blocking
```yaml
blocking:
  # Auto-block identified trackers
  auto_block: true

  # Minimum hits before auto-blocking
  auto_block_threshold: 3

  # Block patterns (regex)
  block_patterns:
    - ".*analytics.*"
    - ".*doubleclick.*"
    - ".*facebook.*"
```

---

## Privacy Levels

### Maximum Privacy (Paranoid)
```yaml
fingerprint:
  rotation_mode: "every_request"  # New fingerprint every request
cookies:
  block_all: true                  # Block ALL cookies
blocking:
  auto_block: true                 # Auto-block trackers
  auto_block_threshold: 1          # Block after first hit
```

**Pros:** Maximum anonymity, hardest to track
**Cons:** May break some websites, slower browsing

### Balanced Privacy (Recommended)
```yaml
fingerprint:
  rotation_mode: "interval"        # Rotate every 5 minutes
  rotation_interval: 300
cookies:
  block_all: true                  # Block cookies
blocking:
  auto_block: true                 # Auto-block trackers
  auto_block_threshold: 3          # Block after 3 hits
```

**Pros:** Good privacy, decent compatibility
**Cons:** Some sites may still track within 5-minute window

### Minimal Privacy (Testing)
```yaml
fingerprint:
  rotation_mode: "launch"          # Only rotate on browser start
cookies:
  block_all: false                 # Allow cookies (log them)
  log_attempts: true
blocking:
  auto_block: false                # Don't block, just log
```

**Pros:** Maximum compatibility
**Cons:** Minimal privacy protection

---

## Database Schema

The SQLite database (`database/browser_privacy.db`) contains:

### Tables
- **tracking_domains**: Domains identified as trackers
- **tracking_ips**: IP addresses of tracking servers
- **cookie_traffic**: All cookie attempts (blocked/allowed)
- **fingerprint_rotations**: History of fingerprint changes
- **request_log**: All HTTP requests with fingerprint info
- **whitelist**: Trusted domains that won't be blocked
- **diary_entries**: Session logs

### Query Examples
```sql
-- Top tracking domains
SELECT domain, hit_count, category
FROM tracking_domains
WHERE blocked = 1
ORDER BY hit_count DESC
LIMIT 50;

-- Cookie attempts today
SELECT domain, COUNT(*) as attempts
FROM cookie_traffic
WHERE DATE(timestamp) = DATE('now')
GROUP BY domain
ORDER BY attempts DESC;

-- Fingerprint rotation frequency
SELECT COUNT(*) as rotations,
       strftime('%H', timestamp) as hour
FROM fingerprint_rotations
GROUP BY hour;
```

---

## Advanced Usage

### Custom Rotation Triggers

To implement "rotate on new tab" behavior:
1. Use browser extension to detect new tab
2. Send signal to proxy (can extend with HTTP endpoint)
3. Proxy rotates fingerprint

### Export Blocklist to System

```powershell
# Export as hosts file
python manage.py export blocklist.txt --format hosts

# Append to Windows hosts file (run as admin)
Get-Content blocklist.txt | Add-Content C:\Windows\System32\drivers\etc\hosts
```

### Analyze Tracking Data

```python
from database_handler import DatabaseHandler

db = DatabaseHandler('database/browser_privacy.db')
stats = db.get_statistics()

# Get all blocked domains
blocked = db.get_blocked_domains()

# Custom queries
conn = db._get_connection()
cursor = conn.execute("""
    SELECT domain, COUNT(*) as cookie_attempts
    FROM cookie_traffic
    WHERE blocked = 1
    GROUP BY domain
    ORDER BY cookie_attempts DESC
""")
```

---

## Troubleshooting

### Proxy won't start
- Check if port 8080 is already in use
- Try different port: `python start_proxy.py --port 9090`
- Check logs: `logs/privacy_proxy.log`

### HTTPS sites not working
- Install mitmproxy certificate: `http://mitm.it`
- Trust the certificate in your browser/system
- Restart browser after installing

### Some sites broken
- Add to whitelist: `python manage.py whitelist example.com`
- Temporarily disable blocking in config
- Check logs to see what's being blocked

### Performance issues
- Use `rotation_mode: interval` instead of `every_request`
- Disable logging: `log_requests: false` in config
- Clear old database entries

---

## Files

- `privacy_proxy.py`: Main proxy server (mitmproxy addon)
- `start_proxy.py`: Launcher script
- `manage.py`: Management CLI
- `database_handler.py`: Database operations
- `fingerprint_randomizer.py`: Browser fingerprinting
- `cookie_interceptor.py`: Cookie blocking
- `traffic_blocker.py`: IP/domain blocking
- `config/config.yaml`: Configuration
- `database/schema.sql`: Database schema
- `setup.ps1`: Setup script

---

## Security Notes

1. **HTTPS Interception**: This tool intercepts HTTPS traffic by acting as a man-in-the-middle. Only use on your own traffic.

2. **Certificate Trust**: The mitmproxy CA certificate must be trusted. Never share this certificate.

3. **Database Privacy**: The database contains your browsing history. Keep it secure.

4. **Not a VPN**: This tool doesn't hide your IP address from websites. Use with Tor/VPN for IP anonymity.

5. **Browser Extensions**: Some browser extensions can still fingerprint you. Use with privacy-focused browser.

---

## Ideal Privacy Scenario

For maximum privacy:

1. **Use this tool with:**
   - Tor Browser or hardened Firefox
   - VPN or Tor network
   - Privacy-focused DNS (1.1.1.1, 9.9.9.9)

2. **Configuration:**
   - `rotation_mode: every_request`
   - `block_all: true`
   - `auto_block: true`
   - `strip_referer: true`

3. **Additional measures:**
   - Disable JavaScript (uMatrix/NoScript)
   - Block WebRTC
   - Use container tabs (Firefox)
   - Clear cookies/storage on exit

4. **Analysis:**
   - Regularly review blocked domains
   - Export and analyze tracking attempts
   - Update block patterns based on findings

---

## Future Enhancements

- [ ] Browser extension for seamless integration
- [ ] WebRTC blocking
- [ ] Canvas/WebGL fingerprint randomization
- [ ] Auto-update tracker lists from public sources
- [ ] Machine learning to identify new trackers
- [ ] Web dashboard for management
- [ ] Multi-profile support
- [ ] Export analytics reports

---

## License

This tool is for educational and personal privacy protection purposes.

---

## Credits

Built with:
- [mitmproxy](https://mitmproxy.org/) - HTTP/HTTPS proxy
- [fake-useragent](https://pypi.org/project/fake-useragent/) - User agent randomization
- SQLite - Database
- Python 3.12+

---

## Version

**Version:** 1.0.0
**Created:** 2025-01-22
**Agent:** AGENT-PRIME-001 (Claude Sonnet 4.5)

---

## Support

For issues or questions, check the logs:
- `logs/privacy_proxy.log` - Proxy server logs
- `database/browser_privacy.db` - Tracking database

Use management CLI for diagnostics:
```powershell
python manage.py stats
python manage.py requests --limit 100
```
