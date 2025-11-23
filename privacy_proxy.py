# ==============================================================================
# file_id: SOM-SCR-0001-v1.0.0
# name: privacy_proxy.py
# description: Main privacy proxy server using mitmproxy
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [proxy, privacy, main]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python privacy_proxy.py [--config config/config.yaml]
# ==============================================================================

import logging
import sys
import yaml
import argparse
from pathlib import Path
from mitmproxy import http
from mitmproxy.tools.main import mitmdump

from database_handler import DatabaseHandler
from fingerprint_randomizer import FingerprintRandomizer
from cookie_interceptor import CookieInterceptor
from traffic_blocker import TrafficBlocker


# Global instances (mitmproxy requires module-level addons)
db_handler = None
fingerprint_randomizer = None
cookie_interceptor = None
traffic_blocker = None
config = None


def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def setup_logging(config):
    """Setup logging configuration"""
    log_level = config.get("logging", {}).get("level", "INFO")
    log_file = config.get("logging", {}).get("file", "logs/privacy_proxy.log")
    console = config.get("logging", {}).get("console", True)

    # Create logs directory
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Configure logging
    handlers = [logging.FileHandler(log_file)]
    if console:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return logging.getLogger(__name__)


class PrivacyProxyAddon:
    """Main mitmproxy addon for privacy protection"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_count = 0

    def request(self, flow: http.HTTPFlow) -> None:
        """Process outgoing requests"""
        try:
            self.request_count += 1

            # Check if request should be blocked
            if traffic_blocker and traffic_blocker.process_request(flow):
                # Request was blocked, don't process further
                return

            # Rotate fingerprint if needed
            if fingerprint_randomizer:
                trigger = "request"
                if self.request_count == 1:
                    trigger = "launch"

                if fingerprint_randomizer.should_rotate(trigger):
                    fingerprint = fingerprint_randomizer.generate_fingerprint(trigger)
                    flow.fingerprint_id = getattr(fingerprint_randomizer.db, "last_fingerprint_id", None)
                else:
                    fingerprint = fingerprint_randomizer.get_current_fingerprint()

                # Apply fingerprint to headers
                fingerprint_randomizer.apply_to_headers(flow.request.headers)

            # Process cookies in request
            if cookie_interceptor:
                cookie_interceptor.process_request_cookies(flow)

            # Log request
            if db_handler and config.get("database", {}).get("log_requests", True):
                url = flow.request.pretty_url
                domain = cookie_interceptor.extract_domain_from_url(url) if cookie_interceptor else ""
                ip_address = flow.server_conn.address[0] if flow.server_conn else None
                fingerprint_id = getattr(flow, "fingerprint_id", None)

                db_handler.log_request(
                    flow.request.method,
                    url,
                    domain,
                    ip_address,
                    fingerprint_id,
                    blocked=False,
                )

        except Exception as e:
            self.logger.error(f"Error in request handler: {e}", exc_info=True)

    def response(self, flow: http.HTTPFlow) -> None:
        """Process incoming responses"""
        try:
            # Process Set-Cookie headers in response
            if cookie_interceptor:
                cookie_interceptor.process_response_cookies(flow)

        except Exception as e:
            self.logger.error(f"Error in response handler: {e}", exc_info=True)

    def running(self) -> None:
        """Called when proxy starts"""
        self.logger.info("=" * 60)
        self.logger.info("Privacy Proxy Started")
        self.logger.info("=" * 60)

        if config:
            self.logger.info(f"Host: {config.get('proxy', {}).get('host', '127.0.0.1')}")
            self.logger.info(f"Port: {config.get('proxy', {}).get('port', 8080)}")
            self.logger.info(f"Fingerprint Mode: {config.get('fingerprint', {}).get('rotation_mode', 'every_request')}")
            self.logger.info(f"Block Cookies: {config.get('cookies', {}).get('block_all', True)}")
            self.logger.info(f"Auto Block: {config.get('blocking', {}).get('auto_block', True)}")

        self.logger.info("=" * 60)

        # Add startup diary entry
        if db_handler:
            db_handler.add_diary_entry(
                "session",
                "Privacy Proxy Started",
                f"Started with rotation mode: {config.get('fingerprint', {}).get('rotation_mode', 'every_request')}",
            )

    def done(self) -> None:
        """Called when proxy shuts down"""
        self.logger.info("=" * 60)
        self.logger.info("Privacy Proxy Shutting Down")
        self.logger.info("=" * 60)

        # Print statistics
        if db_handler:
            stats = db_handler.get_statistics()
            self.logger.info(f"Total Requests: {stats.get('total_requests', 0)}")
            self.logger.info(f"Blocked Domains: {stats.get('blocked_domains', 0)}")
            self.logger.info(f"Blocked IPs: {stats.get('blocked_ips', 0)}")
            self.logger.info(f"Blocked Cookies: {stats.get('blocked_cookies', 0)}")
            self.logger.info(f"Fingerprint Rotations: {stats.get('fingerprint_rotations', 0)}")

        if cookie_interceptor:
            cookie_stats = cookie_interceptor.get_stats()
            self.logger.info(f"Total Cookie Blocks: {cookie_stats.get('blocked_count', 0)}")

        if traffic_blocker:
            block_stats = traffic_blocker.get_blocklist_stats()
            self.logger.info(f"Blocked Requests: {block_stats.get('blocked_requests', 0)}")
            self.logger.info(f"Allowed Requests: {block_stats.get('allowed_requests', 0)}")

        self.logger.info("=" * 60)

        # Add shutdown diary entry
        if db_handler:
            stats = db_handler.get_statistics()
            db_handler.add_diary_entry(
                "session",
                "Privacy Proxy Stopped",
                f"Processed {stats.get('total_requests', 0)} requests, "
                f"blocked {stats.get('blocked_cookies', 0)} cookies",
            )

        # Close database
        if db_handler:
            db_handler.close()


def main():
    """Main entry point"""
    global db_handler, fingerprint_randomizer, cookie_interceptor, traffic_blocker, config

    # Parse arguments
    parser = argparse.ArgumentParser(description="Privacy Proxy Server")
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file",
    )
    args = parser.parse_args()

    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Setup logging
    logger = setup_logging(config)

    # Initialize database
    db_path = config.get("database", {}).get("path", "database/browser_privacy.db")
    db_handler = DatabaseHandler(db_path)

    # Initialize components
    fingerprint_randomizer = FingerprintRandomizer(db_handler, config)
    cookie_interceptor = CookieInterceptor(db_handler, config)
    traffic_blocker = TrafficBlocker(db_handler, config)

    # Add default whitelisted domains
    for domain in config.get("whitelist", []):
        db_handler.add_to_whitelist(domain, "config")

    logger.info("All components initialized successfully")

    # Run mitmproxy with our addon
    # Note: mitmproxy will be controlled via command line args
    # We'll create a separate launcher script


addons = [PrivacyProxyAddon()]


if __name__ == "__main__":
    main()
