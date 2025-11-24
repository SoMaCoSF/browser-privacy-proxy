<!--
===============================================================================
file_id: SOM-DOC-0003-v1.0.0
name: QUICKSTART.md
description: Quick start guide for Privacy Proxy
project_id: BROWSER-MIXER-ANON
category: documentation
tags: [quickstart, guide]
created: 2025-01-22
modified: 2025-01-22
version: 1.0.0
agent_id: AGENT-PRIME-001
execution: Documentation file
===============================================================================
-->

# Privacy Proxy - Quick Start Guide

Get up and running in 5 minutes!

## Step 1: Setup (2 minutes)

### Option A: Interactive TUI Setup (Easiest!)

```powershell
# Install rich (one-time only)
pip install rich

# Run the interactive wizard
python setup_tui.py
```

Follow the on-screen prompts - it handles everything automatically!

### Option B: Automated Script

```powershell
.\setup.ps1
```

### Option C: Manual Setup

```powershell
uv venv .venv
.venv\Scripts\activate.ps1
uv pip install -r requirements.txt
```

## Step 2: Start the Proxy (30 seconds)

```powershell
# Activate virtual environment
.venv\Scripts\activate.ps1

# Start proxy
python start_proxy.py
```

You should see:
```
======================================================================
  PRIVACY PROXY - Browser Anonymization Tool
======================================================================
  Version: 1.0.0
  Host: 127.0.0.1
  Port: 8080
  Mode: regular
  Config: config\config.yaml
======================================================================

Configure your browser to use this proxy:
  HTTP Proxy: 127.0.0.1:8080
  HTTPS Proxy: 127.0.0.1:8080
```

## Step 3: Configure Browser (1 minute)

### Firefox (Recommended)
1. Open Settings (or type `about:preferences` in address bar)
2. Scroll to **Network Settings** → Click **Settings**
3. Select **Manual proxy configuration**
4. Set both:
   - **HTTP Proxy:** `127.0.0.1` **Port:** `8080`
   - **HTTPS Proxy:** `127.0.0.1` **Port:** `8080`
5. Check **"Also use this proxy for HTTPS"**
6. Click **OK**

### Chrome/Edge
1. Settings → Search for "proxy"
2. Click **Open your computer's proxy settings**
3. Enable **Use a proxy server**
4. **Address:** `127.0.0.1` **Port:** `8080`
5. Click **Save**

## Step 4: Install Certificate (1 minute)

For HTTPS to work, you need the mitmproxy certificate:

1. With proxy running and browser configured, visit: **http://mitm.it**
2. Click on your OS (Windows/Mac/Linux)
3. Download and install the certificate
4. **Important:** Trust the certificate for "websites" or "SSL"
5. Restart your browser

## Step 5: Test It! (30 seconds)

1. Browse to any website
2. Check the proxy terminal - you should see activity
3. Open a new terminal and run:

```powershell
.venv\Scripts\activate.ps1
python manage.py stats
```

You should see:
```
======================================================================
  PRIVACY PROXY STATISTICS
======================================================================
  Total Requests:         42
  Blocked Domains:        15
  Blocked IPs:            8
  Blocked Cookies:        127
  Fingerprint Rotations:  42
======================================================================
```

**Congratulations! You're now browsing privately!**

---

## What's Happening?

Every request you make:
1. ✅ Gets a **new random fingerprint** (User-Agent, headers)
2. ✅ **Blocks ALL cookies** (both sending and receiving)
3. ✅ **Logs tracking domains** to database
4. ✅ **Auto-blocks** known trackers
5. ✅ **Strips** Referer and tracking headers

---

## Quick Commands

### View Statistics
```powershell
python manage.py stats
```

### See What's Being Blocked
```powershell
python manage.py domains --limit 20
python manage.py ips --limit 20
```

### See Blocked Cookies
```powershell
python manage.py cookies --limit 50
```

### Export Blocklist
```powershell
python manage.py export myblocklist.txt --format hosts
```

### Whitelist a Site (if it's broken)
```powershell
python manage.py whitelist example.com
```

---

## Configuration Modes

Edit `config/config.yaml` and restart proxy:

### Maximum Privacy (Paranoid)
```yaml
fingerprint:
  rotation_mode: "every_request"  # New fingerprint EVERY request
cookies:
  block_all: true                  # Block ALL cookies
```
**Effect:** Hardest to track, but may break some sites

### Balanced (Recommended)
```yaml
fingerprint:
  rotation_mode: "interval"        # Rotate every 5 minutes
  rotation_interval: 300
cookies:
  block_all: true
```
**Effect:** Good privacy, better compatibility

### Minimal (Testing)
```yaml
fingerprint:
  rotation_mode: "launch"          # Only rotate on browser start
cookies:
  block_all: false                 # Allow cookies (but log them)
  log_attempts: true
```
**Effect:** Test mode, minimal blocking

---

## Troubleshooting

### "Connection refused" or "Can't connect"
- Check proxy is running: Look for activity in terminal
- Check port: `python start_proxy.py --port 9090` (use 9090 instead)
- Restart proxy and browser

### "Certificate error" on HTTPS sites
- Install mitmproxy cert: Visit **http://mitm.it**
- Trust the certificate in your system
- Restart browser
- If still fails: `python start_proxy.py --no-ssl-insecure`

### Website is broken/not loading
- Add to whitelist: `python manage.py whitelist example.com`
- Check logs: `logs/privacy_proxy.log`
- Temporarily disable blocking: Set `auto_block: false` in config

### Slow performance
- Change rotation mode to `interval` or `launch`
- Disable request logging: `log_requests: false` in config

---

## What's Next?

1. **Browse the web** - The proxy works silently in background
2. **Check stats regularly** - See what's being blocked
3. **Export blocklists** - Share with friends or import to firewall
4. **Customize config** - Tune privacy vs compatibility
5. **Read full docs** - See [README.md](README.md) for advanced usage

---

## Stop the Proxy

Press **Ctrl+C** in the terminal running the proxy

To disable proxy in browser:
- Firefox: Settings → Network Settings → **No proxy**
- Chrome: Proxy Settings → **Disable** "Use a proxy server"

---

## Privacy Tips

For maximum privacy, combine with:
- 🛡️ **VPN or Tor** (hides your IP)
- 🔒 **HTTPS Everywhere** (browser extension)
- 🚫 **uBlock Origin** (ad blocker)
- 🦊 **Firefox** (more privacy-friendly than Chrome)
- 🔐 **Privacy-focused DNS** (1.1.1.1 or 9.9.9.9)

This tool handles:
- ✅ Browser fingerprinting
- ✅ Cookie tracking
- ✅ Known tracker domains/IPs

This tool does NOT hide:
- ❌ Your IP address (use VPN/Tor)
- ❌ DNS queries (use private DNS)
- ❌ WebRTC leaks (disable in browser)

---

## Files You Care About

- `config/config.yaml` - Your settings
- `logs/privacy_proxy.log` - What's happening
- `database/browser_privacy.db` - All tracking data

---

## Example Session

```powershell
# Start proxy
.venv\Scripts\activate.ps1
python start_proxy.py

# In another terminal, monitor activity
.venv\Scripts\activate.ps1
python manage.py stats         # Every few minutes

# Export your blocklist
python manage.py export blocklist.txt --format hosts

# Check what's being blocked
python manage.py domains --limit 50
python manage.py cookies --limit 100

# Whitelist a broken site
python manage.py whitelist mybank.com

# Stop proxy
Ctrl+C
```

---

## Support

**Logs:** `logs/privacy_proxy.log`
**Database:** `database/browser_privacy.db`
**Config:** `config/config.yaml`

**Full docs:** [README.md](README.md)

Happy private browsing! 🕵️
