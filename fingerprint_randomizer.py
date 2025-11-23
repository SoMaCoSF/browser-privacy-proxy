# ==============================================================================
# file_id: SOM-SCR-0002-v1.0.0
# name: fingerprint_randomizer.py
# description: Browser fingerprint randomization module
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [privacy, fingerprint, randomization]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: Imported by privacy_proxy.py
# ==============================================================================

import random
import logging
from fake_useragent import UserAgent
from datetime import datetime

logger = logging.getLogger(__name__)


class FingerprintRandomizer:
    """Randomizes browser fingerprints to prevent tracking"""

    def __init__(self, db_handler, config):
        self.db = db_handler
        self.config = config
        self.ua = UserAgent()
        self.current_fingerprint = None
        self.rotation_count = 0

        # Common languages
        self.languages = [
            "en-US,en;q=0.9",
            "en-GB,en;q=0.9",
            "de-DE,de;q=0.9,en;q=0.8",
            "fr-FR,fr;q=0.9,en;q=0.8",
            "es-ES,es;q=0.9,en;q=0.8",
            "ja-JP,ja;q=0.9,en;q=0.8",
            "zh-CN,zh;q=0.9,en;q=0.8",
        ]

        # Common encoding preferences
        self.encodings = [
            "gzip, deflate, br",
            "gzip, deflate",
            "br, gzip, deflate",
        ]

        # Common platforms
        self.platforms = [
            "Windows NT 10.0; Win64; x64",
            "Windows NT 11.0; Win64; x64",
            "Macintosh; Intel Mac OS X 10_15_7",
            "X11; Linux x86_64",
            "X11; Ubuntu; Linux x86_64",
        ]

        # DNT values
        self.dnt_values = ["1", "0", None]

    def generate_fingerprint(self, trigger="manual"):
        """Generate a new random fingerprint"""
        try:
            fingerprint = {
                "user_agent": self._random_user_agent(),
                "accept_language": self._random_language(),
                "accept_encoding": self._random_encoding(),
                "platform": self._random_platform(),
                "dnt": self._random_dnt(),
                "timestamp": datetime.now(),
                "trigger": trigger,
            }

            # Log to database
            if self.config.get("database", {}).get("log_fingerprints", True):
                self.db.log_fingerprint_rotation(fingerprint)

            self.current_fingerprint = fingerprint
            self.rotation_count += 1

            logger.info(
                f"Generated new fingerprint #{self.rotation_count} (trigger: {trigger})"
            )
            logger.debug(f"User-Agent: {fingerprint['user_agent'][:50]}...")

            return fingerprint

        except Exception as e:
            logger.error(f"Error generating fingerprint: {e}")
            return self._fallback_fingerprint()

    def _random_user_agent(self):
        """Get random user agent"""
        if not self.config.get("fingerprint", {}).get("randomize_user_agent", True):
            return None

        try:
            return self.ua.random
        except Exception:
            # Fallback user agents if fake_useragent fails
            fallback_uas = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            ]
            return random.choice(fallback_uas)

    def _random_language(self):
        """Get random Accept-Language header"""
        if not self.config.get("fingerprint", {}).get("randomize_accept_language", True):
            return None
        return random.choice(self.languages)

    def _random_encoding(self):
        """Get random Accept-Encoding header"""
        if not self.config.get("fingerprint", {}).get("randomize_accept_encoding", True):
            return None
        return random.choice(self.encodings)

    def _random_platform(self):
        """Get random platform identifier"""
        if not self.config.get("fingerprint", {}).get("randomize_platform", True):
            return None
        return random.choice(self.platforms)

    def _random_dnt(self):
        """Get random Do Not Track value"""
        if not self.config.get("fingerprint", {}).get("randomize_dnt", True):
            return None
        return random.choice(self.dnt_values)

    def _fallback_fingerprint(self):
        """Provide a fallback fingerprint in case of errors"""
        return {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "accept_language": "en-US,en;q=0.9",
            "accept_encoding": "gzip, deflate, br",
            "platform": "Windows NT 10.0; Win64; x64",
            "dnt": "1",
            "timestamp": datetime.now(),
            "trigger": "fallback",
        }

    def should_rotate(self, trigger_type):
        """Determine if fingerprint should be rotated based on config"""
        rotation_mode = self.config.get("fingerprint", {}).get(
            "rotation_mode", "every_request"
        )

        if rotation_mode == "every_request":
            return True
        elif rotation_mode == "new_tab":
            return trigger_type == "new_tab"
        elif rotation_mode == "launch":
            return trigger_type == "launch" or self.current_fingerprint is None
        elif rotation_mode == "interval":
            # Check if enough time has passed
            if self.current_fingerprint is None:
                return True
            interval = self.config.get("fingerprint", {}).get("rotation_interval", 300)
            elapsed = (
                datetime.now() - self.current_fingerprint["timestamp"]
            ).total_seconds()
            return elapsed >= interval

        return False

    def get_current_fingerprint(self):
        """Get current fingerprint, generating one if needed"""
        if self.current_fingerprint is None:
            return self.generate_fingerprint("initial")
        return self.current_fingerprint

    def apply_to_headers(self, headers):
        """Apply current fingerprint to request headers"""
        fingerprint = self.get_current_fingerprint()

        # Apply randomized headers
        if fingerprint.get("user_agent"):
            headers["User-Agent"] = fingerprint["user_agent"]

        if fingerprint.get("accept_language"):
            headers["Accept-Language"] = fingerprint["accept_language"]

        if fingerprint.get("accept_encoding"):
            headers["Accept-Encoding"] = fingerprint["accept_encoding"]

        if fingerprint.get("dnt"):
            headers["DNT"] = fingerprint["dnt"]

        # Strip unwanted headers
        strip_headers = self.config.get("fingerprint", {}).get("strip_headers", [])
        for header in strip_headers:
            headers.pop(header, None)

        # Strip referer if configured
        if self.config.get("fingerprint", {}).get("strip_referer", True):
            headers.pop("Referer", None)

        return headers
