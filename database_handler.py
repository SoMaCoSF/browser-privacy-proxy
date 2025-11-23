# ==============================================================================
# file_id: SOM-SCR-0003-v1.0.0
# name: database_handler.py
# description: SQLite database operations for privacy tracking
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [database, sqlite, logging]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: Imported by privacy_proxy.py
# ==============================================================================

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
import threading

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """Handles all database operations for privacy tracking"""

    def __init__(self, db_path):
        self.db_path = db_path
        self.local = threading.local()
        self._init_database()

    def _get_connection(self):
        """Get thread-local database connection"""
        if not hasattr(self.local, "conn"):
            self.local.conn = sqlite3.connect(self.db_path)
            self.local.conn.row_factory = sqlite3.Row
        return self.local.conn

    def _init_database(self):
        """Initialize database with schema"""
        try:
            # Create database directory if needed
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            # Read and execute schema
            schema_path = Path(__file__).parent / "database" / "schema.sql"
            if schema_path.exists():
                with open(schema_path, "r") as f:
                    schema = f.read()
                conn = self._get_connection()
                conn.executescript(schema)
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
            else:
                logger.warning(f"Schema file not found: {schema_path}")

        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

    def log_cookie_traffic(self, domain, cookie_name, cookie_value, ip_address, url, blocked=True):
        """Log cookie traffic attempt"""
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO cookie_traffic
                (domain, cookie_name, cookie_value, ip_address, request_url, blocked)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (domain, cookie_name, cookie_value, ip_address, url, blocked),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging cookie traffic: {e}")

    def log_fingerprint_rotation(self, fingerprint):
        """Log fingerprint rotation"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                """
                INSERT INTO fingerprint_rotations
                (user_agent, platform, accept_language, accept_encoding, rotation_trigger)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fingerprint.get("user_agent"),
                    fingerprint.get("platform"),
                    fingerprint.get("accept_language"),
                    fingerprint.get("accept_encoding"),
                    fingerprint.get("trigger"),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            logger.error(f"Error logging fingerprint rotation: {e}")
            return None

    def log_request(self, method, url, host, ip_address, fingerprint_id, blocked=False, block_reason=None):
        """Log HTTP request"""
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO request_log
                (method, url, host, ip_address, fingerprint_id, blocked, block_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (method, url, host, ip_address, fingerprint_id, blocked, block_reason),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error logging request: {e}")

    def add_tracking_domain(self, domain, category="tracker"):
        """Add or update tracking domain"""
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO tracking_domains (domain, category, hit_count, last_seen)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(domain) DO UPDATE SET
                    hit_count = hit_count + 1,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (domain, category),
            )
            conn.commit()

            # Check if domain should be auto-blocked
            cursor = conn.execute(
                "SELECT hit_count FROM tracking_domains WHERE domain = ?", (domain,)
            )
            row = cursor.fetchone()
            if row and row[0] >= 3:  # Auto-block threshold
                logger.info(f"Auto-blocking domain: {domain} (hits: {row[0]})")
                return True
            return False

        except Exception as e:
            logger.error(f"Error adding tracking domain: {e}")
            return False

    def add_tracking_ip(self, ip_address, associated_domain=None):
        """Add or update tracking IP"""
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO tracking_ips (ip_address, associated_domain, hit_count, last_seen)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(ip_address) DO UPDATE SET
                    hit_count = hit_count + 1,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (ip_address, associated_domain),
            )
            conn.commit()

            # Check if IP should be auto-blocked
            cursor = conn.execute(
                "SELECT hit_count FROM tracking_ips WHERE ip_address = ?", (ip_address,)
            )
            row = cursor.fetchone()
            if row and row[0] >= 3:  # Auto-block threshold
                logger.info(f"Auto-blocking IP: {ip_address} (hits: {row[0]})")
                return True
            return False

        except Exception as e:
            logger.error(f"Error adding tracking IP: {e}")
            return False

    def is_domain_blocked(self, domain):
        """Check if domain is blocked"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT blocked FROM tracking_domains WHERE domain = ?", (domain,)
            )
            row = cursor.fetchone()
            return row[0] if row else False
        except Exception as e:
            logger.error(f"Error checking domain block status: {e}")
            return False

    def is_ip_blocked(self, ip_address):
        """Check if IP is blocked"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT blocked FROM tracking_ips WHERE ip_address = ?", (ip_address,)
            )
            row = cursor.fetchone()
            return row[0] if row else False
        except Exception as e:
            logger.error(f"Error checking IP block status: {e}")
            return False

    def is_whitelisted(self, domain):
        """Check if domain is whitelisted"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT COUNT(*) FROM whitelist WHERE domain = ?", (domain,)
            )
            return cursor.fetchone()[0] > 0
        except Exception as e:
            logger.error(f"Error checking whitelist: {e}")
            return False

    def add_to_whitelist(self, domain, reason=""):
        """Add domain to whitelist"""
        try:
            conn = self._get_connection()
            conn.execute(
                "INSERT OR IGNORE INTO whitelist (domain, reason) VALUES (?, ?)",
                (domain, reason),
            )
            conn.commit()
            logger.info(f"Added {domain} to whitelist")
        except Exception as e:
            logger.error(f"Error adding to whitelist: {e}")

    def get_blocked_domains(self):
        """Get list of all blocked domains"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT domain FROM tracking_domains WHERE blocked = 1"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting blocked domains: {e}")
            return []

    def get_blocked_ips(self):
        """Get list of all blocked IPs"""
        try:
            conn = self._get_connection()
            cursor = conn.execute(
                "SELECT ip_address FROM tracking_ips WHERE blocked = 1"
            )
            return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting blocked IPs: {e}")
            return []

    def get_statistics(self):
        """Get database statistics"""
        try:
            conn = self._get_connection()
            stats = {}

            cursor = conn.execute("SELECT COUNT(*) FROM tracking_domains WHERE blocked = 1")
            stats["blocked_domains"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM tracking_ips WHERE blocked = 1")
            stats["blocked_ips"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM cookie_traffic WHERE blocked = 1")
            stats["blocked_cookies"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM request_log")
            stats["total_requests"] = cursor.fetchone()[0]

            cursor = conn.execute("SELECT COUNT(*) FROM fingerprint_rotations")
            stats["fingerprint_rotations"] = cursor.fetchone()[0]

            return stats

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}

    def add_diary_entry(self, entry_type, title, content, agent_id="AGENT-PRIME-001"):
        """Add development diary entry"""
        try:
            conn = self._get_connection()
            conn.execute(
                """
                INSERT INTO diary_entries (entry_type, title, content, agent_id)
                VALUES (?, ?, ?, ?)
                """,
                (entry_type, title, content, agent_id),
            )
            conn.commit()
        except Exception as e:
            logger.error(f"Error adding diary entry: {e}")

    def close(self):
        """Close database connection"""
        if hasattr(self.local, "conn"):
            self.local.conn.close()
            del self.local.conn
