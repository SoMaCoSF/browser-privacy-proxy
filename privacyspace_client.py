# ==============================================================================
# file_id: SOM-SCR-0011-v1.0.0
# name: privacyspace_client.py
# description: PrivacySpace sync client - connects local proxy to central server
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [client, sync, websocket, collaborative]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: Imported by privacy_proxy.py
# ==============================================================================

import requests
import socketio
import logging
import hashlib
import threading
from datetime import datetime
import time

logger = logging.getLogger(__name__)


class PrivacySpaceClient:
    """Client for syncing with PrivacySpace central server"""

    def __init__(self, server_url='http://localhost:5000', enabled=True):
        self.server_url = server_url
        self.enabled = enabled
        self.connected = False
        self.user_id = self._generate_user_id()
        self.sio = None
        self.shared_blocklist = set()
        self.update_callbacks = []

        if self.enabled:
            self._init_socketio()

    def _generate_user_id(self):
        """Generate anonymous user ID"""
        import uuid
        import platform

        # Generate based on machine ID (anonymous but consistent)
        machine_id = f"{platform.node()}{platform.machine()}".encode()
        return hashlib.sha256(machine_id).hexdigest()[:16]

    def _init_socketio(self):
        """Initialize SocketIO connection"""
        try:
            self.sio = socketio.Client(logger=False, engineio_logger=False)

            @self.sio.event
            def connect():
                logger.info("✅ Connected to PrivacySpace central server")
                self.connected = True
                self.sio.emit('subscribe', {'user_id': self.user_id})
                self._fetch_blocklist()

            @self.sio.event
            def disconnect():
                logger.warning("❌ Disconnected from PrivacySpace")
                self.connected = False

            @self.sio.event
            def new_tracker(data):
                logger.info(f"📡 New tracker from network: {data['domain']} (company: {data['company']})")
                self.shared_blocklist.add(data['domain'])

                # Notify callbacks
                for callback in self.update_callbacks:
                    callback(data)

            @self.sio.event
            def subscribed(data):
                logger.info(f"✅ Subscribed to PrivacySpace updates (User: {data['user_id'][:8]}...)")

            # Start connection in background thread
            threading.Thread(target=self._connect, daemon=True).start()

        except Exception as e:
            logger.error(f"Failed to initialize SocketIO: {e}")
            self.enabled = False

    def _connect(self):
        """Connect to server (blocking, run in thread)"""
        max_retries = 5
        retry_count = 0

        while retry_count < max_retries and not self.connected:
            try:
                logger.info(f"Connecting to PrivacySpace server: {self.server_url}")
                self.sio.connect(self.server_url, wait_timeout=10)
                break
            except Exception as e:
                retry_count += 1
                logger.warning(f"Connection attempt {retry_count}/{max_retries} failed: {e}")
                if retry_count < max_retries:
                    time.sleep(5)
                else:
                    logger.error("Failed to connect to PrivacySpace server. Running in standalone mode.")
                    self.enabled = False

    def _fetch_blocklist(self):
        """Fetch current blocklist from server"""
        try:
            response = requests.get(f"{self.server_url}/api/blocklist", timeout=5)
            if response.status_code == 200:
                data = response.json()
                self.shared_blocklist = {item['domain'] for item in data['blocklist']}
                logger.info(f"📥 Fetched shared blocklist: {len(self.shared_blocklist)} domains")
        except Exception as e:
            logger.warning(f"Failed to fetch blocklist: {e}")

    def report_tracker(self, domain, method='cookie', confidence=0.8, context=None):
        """Report tracker discovery to central server"""
        if not self.enabled or not domain:
            return

        try:
            data = {
                'user_id': self.user_id,
                'domain': domain,
                'method': method,
                'confidence': confidence,
                'context': context or {}
            }

            response = requests.post(
                f"{self.server_url}/api/report",
                json=data,
                timeout=5
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('is_new'):
                    logger.info(f"🎉 NEW TRACKER DISCOVERY: {domain}")
                return result
            else:
                logger.warning(f"Failed to report tracker: {response.status_code}")

        except Exception as e:
            logger.error(f"Error reporting tracker: {e}")

    def is_blocked(self, domain):
        """Check if domain is in shared blocklist"""
        if not self.enabled:
            return False

        # Check exact match and parent domains
        parts = domain.split('.')
        for i in range(len(parts)):
            check_domain = '.'.join(parts[i:])
            if check_domain in self.shared_blocklist:
                return True

        return False

    def add_update_callback(self, callback):
        """Register callback for blocklist updates"""
        self.update_callbacks.append(callback)

    def get_stats(self):
        """Get stats from central server"""
        try:
            response = requests.get(f"{self.server_url}/api/stats", timeout=5)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Error fetching stats: {e}")
        return None

    def disconnect(self):
        """Disconnect from server"""
        if self.sio and self.connected:
            self.sio.disconnect()
            logger.info("Disconnected from PrivacySpace")
