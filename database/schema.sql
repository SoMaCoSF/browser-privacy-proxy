-- ==============================================================================
-- file_id: SOM-DTA-0001-v1.0.0
-- name: schema.sql
-- description: Database schema for browser anonymization tracking
-- project_id: BROWSER-MIXER-ANON
-- category: data
-- tags: [database, schema, privacy, tracking]
-- created: 2025-01-22
-- modified: 2025-01-22
-- version: 1.0.0
-- agent_id: AGENT-PRIME-001
-- execution: sqlite3 browser_privacy.db < schema.sql
-- ==============================================================================

-- Tracking domains and IPs identified from cookie traffic
CREATE TABLE IF NOT EXISTS tracking_domains (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT UNIQUE NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hit_count INTEGER DEFAULT 1,
    blocked BOOLEAN DEFAULT 1,
    category TEXT DEFAULT 'tracker',
    notes TEXT
);

CREATE TABLE IF NOT EXISTS tracking_ips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT UNIQUE NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hit_count INTEGER DEFAULT 1,
    blocked BOOLEAN DEFAULT 1,
    associated_domain TEXT,
    notes TEXT,
    FOREIGN KEY (associated_domain) REFERENCES tracking_domains(domain)
);

-- Cookie traffic log
CREATE TABLE IF NOT EXISTS cookie_traffic (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    domain TEXT NOT NULL,
    cookie_name TEXT,
    cookie_value TEXT,
    ip_address TEXT,
    request_url TEXT,
    blocked BOOLEAN DEFAULT 1
);

-- Browser fingerprint rotation log
CREATE TABLE IF NOT EXISTS fingerprint_rotations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    platform TEXT,
    accept_language TEXT,
    accept_encoding TEXT,
    referer_policy TEXT,
    rotation_trigger TEXT
);

-- Request log for debugging and analysis
CREATE TABLE IF NOT EXISTS request_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method TEXT,
    url TEXT,
    host TEXT,
    ip_address TEXT,
    fingerprint_id INTEGER,
    blocked BOOLEAN DEFAULT 0,
    block_reason TEXT,
    FOREIGN KEY (fingerprint_id) REFERENCES fingerprint_rotations(id)
);

-- Development diary entries
CREATE TABLE IF NOT EXISTS diary_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    entry_type TEXT,
    title TEXT,
    content TEXT,
    agent_id TEXT
);

-- Whitelist for domains that should not be blocked
CREATE TABLE IF NOT EXISTS whitelist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    domain TEXT UNIQUE NOT NULL,
    added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tracking_domains_domain ON tracking_domains(domain);
CREATE INDEX IF NOT EXISTS idx_tracking_ips_ip ON tracking_ips(ip_address);
CREATE INDEX IF NOT EXISTS idx_cookie_traffic_domain ON cookie_traffic(domain);
CREATE INDEX IF NOT EXISTS idx_cookie_traffic_timestamp ON cookie_traffic(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_log_timestamp ON request_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_request_log_host ON request_log(host);
