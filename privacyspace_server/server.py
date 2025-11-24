# ==============================================================================
# file_id: SOM-SCR-0010-v1.0.0
# name: server.py
# description: PrivacySpace central server - collaborative tracker intelligence
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [server, websocket, api, collaborative]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python server.py
# ==============================================================================

import os
import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
from threading import Lock
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'privacyspace-secret-key-2025'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Thread-safe locks
db_lock = Lock()
stats_lock = Lock()

# In-memory stats cache
stats_cache = {
    'active_users': set(),
    'total_blocks': 0,
    'recent_trackers': [],
    'top_companies': defaultdict(int)
}

# Database setup
DB_PATH = 'database/privacyspace.db'

def init_database():
    """Initialize the central database"""
    os.makedirs('database', exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Global tracker registry
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS global_trackers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_blocks INTEGER DEFAULT 1,
            unique_users INTEGER DEFAULT 1,
            category TEXT DEFAULT 'unknown',
            company TEXT,
            method TEXT,
            confidence REAL DEFAULT 0.5,
            auto_block BOOLEAN DEFAULT 1
        )
    ''')

    # Tracker reports from users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracker_reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            domain TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            method TEXT,
            confidence REAL,
            context TEXT
        )
    ''')

    # Active users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_users (
            user_id TEXT PRIMARY KEY,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_reports INTEGER DEFAULT 0,
            privacy_score INTEGER DEFAULT 0
        )
    ''')

    # Company tracking
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            total_trackers INTEGER DEFAULT 0,
            total_blocks INTEGER DEFAULT 0,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_domain ON global_trackers(domain)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_last_seen ON global_trackers(last_seen)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_reports ON tracker_reports(user_id)')

    conn.commit()
    conn.close()

    logger.info("Database initialized successfully")

def get_db():
    """Get database connection"""
    return sqlite3.connect(DB_PATH)

def identify_company(domain):
    """Identify company from domain"""
    companies = {
        'google': ['google-analytics', 'doubleclick', 'googletagmanager', 'googlesyndication'],
        'facebook': ['facebook', 'fbcdn', 'fbsbx'],
        'amazon': ['amazon-adsystem', 'amazonpay'],
        'microsoft': ['bing', 'msn', 'live.com'],
        'twitter': ['twitter', 't.co'],
        'adobe': ['adobe', 'omtrdc'],
        'oracle': ['bluekai', 'eloqua'],
        'salesforce': ['salesforce', 'pardot']
    }

    domain_lower = domain.lower()
    for company, patterns in companies.items():
        if any(pattern in domain_lower for pattern in patterns):
            return company.title()

    return 'Unknown'

@app.route('/')
def index():
    """Serve the public dashboard"""
    return render_template('dashboard.html')

@app.route('/api/stats')
def get_stats():
    """Get global statistics"""
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()

        # Total unique trackers
        cursor.execute('SELECT COUNT(DISTINCT domain) FROM global_trackers')
        total_trackers = cursor.fetchone()[0]

        # Total blocks
        cursor.execute('SELECT SUM(total_blocks) FROM global_trackers')
        total_blocks = cursor.fetchone()[0] or 0

        # Active users (seen in last 5 minutes)
        five_mins_ago = (datetime.now() - timedelta(minutes=5)).isoformat()
        cursor.execute('SELECT COUNT(*) FROM active_users WHERE last_seen > ?', (five_mins_ago,))
        active_users = cursor.fetchone()[0]

        # Top companies
        cursor.execute('''
            SELECT company, SUM(total_blocks) as blocks
            FROM global_trackers
            WHERE company IS NOT NULL
            GROUP BY company
            ORDER BY blocks DESC
            LIMIT 10
        ''')
        top_companies = [{'name': row[0], 'blocks': row[1]} for row in cursor.fetchall()]

        # Recent trackers (last hour)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute('''
            SELECT domain, total_blocks, company, last_seen
            FROM global_trackers
            WHERE last_seen > ?
            ORDER BY last_seen DESC
            LIMIT 50
        ''', (one_hour_ago,))
        recent_trackers = [{
            'domain': row[0],
            'blocks': row[1],
            'company': row[2],
            'time': row[3]
        } for row in cursor.fetchall()]

        conn.close()

        return jsonify({
            'total_trackers': total_trackers,
            'total_blocks': total_blocks,
            'active_users': active_users,
            'top_companies': top_companies,
            'recent_trackers': recent_trackers
        })

@app.route('/api/trackers/live')
def get_live_trackers():
    """Get trackers from last 60 seconds"""
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()

        sixty_secs_ago = (datetime.now() - timedelta(seconds=60)).isoformat()
        cursor.execute('''
            SELECT domain, total_blocks, company, method, last_seen
            FROM global_trackers
            WHERE last_seen > ?
            ORDER BY last_seen DESC
            LIMIT 20
        ''', (sixty_secs_ago,))

        trackers = [{
            'domain': row[0],
            'blocks': row[1],
            'company': row[2],
            'method': row[3],
            'time': row[4]
        } for row in cursor.fetchall()]

        conn.close()
        return jsonify(trackers)

@app.route('/api/report', methods=['POST'])
def report_tracker():
    """Receive tracker report from client"""
    data = request.json

    user_id = data.get('user_id', 'anonymous')
    domain = data.get('domain')
    method = data.get('method', 'unknown')
    confidence = data.get('confidence', 0.5)
    context = data.get('context', {})

    if not domain:
        return jsonify({'error': 'Domain required'}), 400

    # Identify company
    company = identify_company(domain)

    with db_lock:
        conn = get_db()
        cursor = conn.cursor()

        # Check if tracker exists
        cursor.execute('SELECT id, total_blocks, unique_users FROM global_trackers WHERE domain = ?', (domain,))
        existing = cursor.fetchone()

        is_new = False
        if existing:
            # Update existing tracker
            tracker_id = existing[0]
            cursor.execute('''
                UPDATE global_trackers
                SET total_blocks = total_blocks + 1,
                    last_seen = CURRENT_TIMESTAMP,
                    company = COALESCE(company, ?),
                    method = COALESCE(method, ?)
                WHERE domain = ?
            ''', (company, method, domain))
        else:
            # New tracker discovered!
            is_new = True
            cursor.execute('''
                INSERT INTO global_trackers (domain, company, method, confidence, category)
                VALUES (?, ?, ?, ?, ?)
            ''', (domain, company, method, confidence, 'tracker'))
            tracker_id = cursor.lastrowid

        # Log the report
        cursor.execute('''
            INSERT INTO tracker_reports (user_id, domain, method, confidence, context)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, domain, method, confidence, json.dumps(context)))

        # Update user record
        cursor.execute('''
            INSERT INTO active_users (user_id, last_seen, total_reports, privacy_score)
            VALUES (?, CURRENT_TIMESTAMP, 1, 10)
            ON CONFLICT(user_id) DO UPDATE SET
                last_seen = CURRENT_TIMESTAMP,
                total_reports = total_reports + 1,
                privacy_score = privacy_score + 10
        ''', (user_id,))

        # Update company stats
        if company != 'Unknown':
            cursor.execute('''
                INSERT INTO companies (name, total_trackers, total_blocks, last_activity)
                VALUES (?, 1, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    total_blocks = total_blocks + 1,
                    last_activity = CURRENT_TIMESTAMP
            ''', (company,))

        conn.commit()
        conn.close()

    # Broadcast to all connected clients
    socketio.emit('new_tracker', {
        'domain': domain,
        'company': company,
        'method': method,
        'is_new': is_new,
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

    logger.info(f"{'NEW' if is_new else 'Updated'} tracker: {domain} (company: {company})")

    return jsonify({
        'success': True,
        'is_new': is_new,
        'tracker_id': tracker_id,
        'message': 'Tracker reported successfully'
    })

@app.route('/api/blocklist')
def get_blocklist():
    """Get current global blocklist"""
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT domain, company, total_blocks, confidence
            FROM global_trackers
            WHERE auto_block = 1
            ORDER BY total_blocks DESC
        ''')

        blocklist = [{
            'domain': row[0],
            'company': row[1],
            'blocks': row[2],
            'confidence': row[3]
        } for row in cursor.fetchall()]

        conn.close()
        return jsonify({
            'count': len(blocklist),
            'blocklist': blocklist,
            'generated': datetime.now().isoformat()
        })

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to PrivacySpace'})

    # Send initial stats
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM global_trackers')
        total_trackers = cursor.fetchone()[0]
        conn.close()

    emit('stats_update', {'total_trackers': total_trackers})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")

@socketio.on('subscribe')
def handle_subscribe(data):
    """Handle client subscription to updates"""
    user_id = data.get('user_id', 'anonymous')
    logger.info(f"User subscribed: {user_id}")

    # Update active users
    with db_lock:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO active_users (user_id, last_seen)
            VALUES (?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET last_seen = CURRENT_TIMESTAMP
        ''', (user_id,))
        conn.commit()
        conn.close()

    emit('subscribed', {'user_id': user_id, 'message': 'Subscribed to updates'})

if __name__ == '__main__':
    print("\n" + "="*70)
    print("  🌍 PRIVACYSPACE CENTRAL SERVER 🌍")
    print("="*70)
    print("  Collaborative Privacy Intelligence Network")
    print("  Version: 1.0.0")
    print("="*70)

    # Initialize database
    init_database()

    print("\n  Starting server...")
    print("  📊 Dashboard: http://localhost:5000")
    print("  🔌 WebSocket: ws://localhost:5000")
    print("  📡 API: http://localhost:5000/api")
    print("\n" + "="*70)
    print("  Press Ctrl+C to stop")
    print("="*70 + "\n")

    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)
