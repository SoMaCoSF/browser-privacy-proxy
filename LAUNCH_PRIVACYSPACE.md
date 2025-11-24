# 🌐 PrivacySpace - Launch Guide

## What is PrivacySpace?

**PrivacySpace** is a collaborative privacy intelligence network where users share tracker discoveries in real-time!

### The Magic:
- 🌍 **Central Server** - Public billboard showing live tracking attempts
- 🔗 **Local Proxies** - Your proxy connects to the network
- 📡 **Real-Time Sync** - Discover once, protect everyone
- 🎯 **Collective Intelligence** - More users = better protection

---

## 🚀 Quick Start (2 Components)

### Step 1: Start the Central Server

```bash
# Install server dependencies
cd privacyspace_server
pip install -r requirements.txt

# Start the server
python server.py
```

The server will start at: **http://localhost:5000**

Open in browser to see the live dashboard!

### Step 2: Start Your Local Proxy (Networked Mode)

```bash
# In main directory, activate venv
.venv\Scripts\activate.ps1

# Install client dependency
pip install python-socketio

# Start networked proxy
python start_privacyspace.py
```

Your proxy is now connected to PrivacySpace! 🎉

---

## 📊 What You'll See

### Central Dashboard (http://localhost:5000)

```
╔══════════════════════════════════════════════════════════╗
║           🌍 PRIVACYSPACE LIVE FEED 🌍                   ║
╚══════════════════════════════════════════════════════════╝

Active Users: 5
Total Trackers: 1,247
Blocks Today: 45,291

🔴 LIVE (Last 60 seconds):
  • google-analytics.com (blocked 234 times)
  • doubleclick.net (blocked 187 times)
  • ⚡ NEW: evil-tracker.xyz (discovered 2 min ago!)
```

### Your Local Proxy Logs

```
🌐 NETWORKED PRIVACY PROXY - Connected to PrivacySpace
PrivacySpace: CONNECTED (User: 8a7f2c1e...)
Shared Blocklist: 1,247 domains

📡 New tracker from network: evil-tracker.xyz
🚫 BLOCKED by PrivacySpace network: evil-tracker.xyz
🎉 NEW TRACKER DISCOVERY: super-evil-corp.io
```

---

## 🎯 How It Works

### When YOU discover a tracker:
1. Your local proxy detects tracking cookie
2. Reports to PrivacySpace central server
3. Server broadcasts to ALL connected users
4. Everyone's blocklist updates instantly
5. Shows on public dashboard

### When SOMEONE ELSE discovers a tracker:
1. Their proxy reports to central server
2. Server broadcasts to you
3. Your proxy adds to blocklist automatically
4. You're protected before you even visit that site!

---

## 🔧 Configuration Options

### Run in Standalone Mode (No Network)

```bash
python start_privacyspace.py --no-network
```

### Connect to Remote Server

```bash
python start_privacyspace.py --server http://your-server.com:5000
```

### Change Proxy Port

```bash
python start_privacyspace.py --port 9090
```

---

## 🌐 Public Server Setup

Want to run a public PrivacySpace server for the community?

### Server Requirements:
- Python 3.10+
- Flask + SocketIO
- 1GB RAM minimum
- Public IP/domain
- Port 5000 open

### Deploy to Cloud:

```bash
# On your server
git clone <repo>
cd browser-privacy-proxy/privacyspace_server

# Install dependencies
pip install -r requirements.txt

# Run with production WSGI server
gunicorn --worker-class eventlet -w 1 -b 0.0.0.0:5000 server:app
```

### Users connect to your server:

```bash
python start_privacyspace.py --server http://your-server.com:5000
```

---

## 📊 Database

The central server stores:
- `global_trackers` - All discovered trackers
- `tracker_reports` - Individual reports from users
- `active_users` - Connected users
- `companies` - Tracking company stats

**Location:** `privacyspace_server/database/privacyspace.db`

---

## 🎨 Dashboard Features

### Live Feed
- Real-time tracker discoveries
- Animated new discoveries
- Color-coded by company
- Auto-scrolling

### Statistics
- Active users (live)
- Total trackers discovered
- Blocks per minute
- Top tracking companies

### API Endpoints

```
GET  /api/stats           - Global statistics
GET  /api/trackers/live   - Last 60 seconds
GET  /api/blocklist       - Current shared blocklist
POST /api/report          - Report tracker discovery
```

---

## 🔒 Privacy Considerations

### What is Sent to Central Server:
- ✅ Tracker domain name
- ✅ Tracking method (cookie/pixel/etc)
- ✅ Anonymous user ID (hashed)
- ✅ Timestamp

### What is NOT Sent:
- ❌ Your browsing history
- ❌ Your IP address
- ❌ Personal data
- ❌ URLs you visit
- ❌ Cookie values

**Your user ID is anonymous!** Generated from machine ID hash.

---

## 🎯 Network Effects

The more users, the better the protection:

| Users | New Trackers/Day | Coverage |
|-------|------------------|----------|
| 10    | ~50             | Niche    |
| 100   | ~500            | Good     |
| 1,000 | ~5,000          | Great    |
| 10,000| ~50,000         | Excellent|

With enough users, **nearly every tracker on the internet is discovered within hours!**

---

## 🛠️ Troubleshooting

### Server won't start
```bash
# Check if port 5000 is in use
netstat -ano | findstr :5000

# Try different port
python server.py --port 5001
```

### Can't connect to server
```bash
# Check server is running
curl http://localhost:5000/api/stats

# Check firewall
# Allow port 5000 in Windows Firewall
```

### Proxy not reporting
```bash
# Check logs
tail -f logs/privacy_proxy.log

# Verify server URL
python start_privacyspace.py --server http://localhost:5000
```

---

## 🚀 Advanced Usage

### Multiple Local Proxies

Run multiple proxies on different ports, all connected to one server:

```bash
# Terminal 1
python start_privacyspace.py --port 8080

# Terminal 2
python start_privacyspace.py --port 8081

# Terminal 3
python start_privacyspace.py --port 8082
```

### High-Availability Server

Run multiple server instances with load balancer:

```bash
# Use nginx or HAProxy to load balance
# Multiple Flask-SocketIO instances with Redis
```

---

## 📈 Monitoring

### Server Stats

```bash
# Get stats via API
curl http://localhost:5000/api/stats | json_pp

# Monitor database
sqlite3 database/privacyspace.db "SELECT COUNT(*) FROM global_trackers"
```

### Client Stats

```python
from privacyspace_client import PrivacySpaceClient

client = PrivacySpaceClient()
stats = client.get_stats()
print(stats)
```

---

## 🎉 You're Part of the Network!

Every tracker you discover helps protect everyone.
Every tracker discovered by others protects you.

**Welcome to PrivacySpace!** 🌍🛡️

---

## 📞 Support

- Server Dashboard: http://localhost:5000
- Server Logs: `privacyspace_server/server.log`
- Client Logs: `logs/privacy_proxy.log`
- Database: `privacyspace_server/database/privacyspace.db`
