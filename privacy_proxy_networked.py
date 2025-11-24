# ==============================================================================
# file_id: SOM-SCR-0012-v1.0.0
# name: privacy_proxy_networked.py
# description: Privacy proxy with PrivacySpace network integration
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [proxy, privacy, networked, collaborative]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.1.0
# agent_id: AGENT-PRIME-001
# execution: Used by start_proxy.py with --networked flag
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
from privacyspace_client import PrivacySpaceClient


# Global instances
db_handler = None
fingerprint_randomizer = None
cookie_interceptor = None
traffic_blocker = None
privacyspace_client = None
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

    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    handlers = [logging.FileHandler(log_file)]
    if console:
        handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=getattr(logging, log_level),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=handlers,
    )

    return logging.getLogger(__name__)


class NetworkedPrivacyProxyAddon:
    """Privacy proxy addon with PrivacySpace integration"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.request_count = 0
        self.discoveries_reported = 0

    def request(self, flow: http.HTTPFlow) -> None:
        """Process outgoing requests"""
        try:
            self.request_count += 1

            # Check shared blocklist first
            url = flow.request.pretty_url
            domain = cookie_interceptor.extract_domain_from_url(url) if cookie_interceptor else ""

            if privacyspace_client and privacyspace_client.enabled:
                if privacyspace_client.is_blocked(domain):
                    self.logger.warning(f"🌐 BLOCKED by PrivacySpace network: {domain}")
                    flow.kill()
                    return

            # Check local traffic blocker
            if traffic_blocker and traffic_blocker.process_request(flow):
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

                fingerprint_randomizer.apply_to_headers(flow.request.headers)

            # Process cookies in request
            if cookie_interceptor:
                cookie_interceptor.process_request_cookies(flow)

            # Log request
            if db_handler and config.get("database", {}).get("log_requests", True):
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
                # Get cookies before processing
                url = flow.request.pretty_url
                domain = cookie_interceptor.extract_domain_from_url(url)
                set_cookie_headers = flow.response.headers.get_all("Set-Cookie")

                # Process cookies
                cookie_interceptor.process_response_cookies(flow)

                # Report to PrivacySpace if cookies were found
                if set_cookie_headers and privacyspace_client and privacyspace_client.enabled:
                    for cookie_header in set_cookie_headers:
                        cookie_name = cookie_header.split("=")[0].strip()

                        # Check if it's a tracking cookie
                        if cookie_interceptor.should_block_cookie(domain, cookie_name):
                            # Report to network
                            privacyspace_client.report_tracker(
                                domain=domain,
                                method='cookie',
                                confidence=0.9,
                                context={'cookie_name': cookie_name}
                            )
                            self.discoveries_reported += 1

        except Exception as e:
            self.logger.error(f"Error in response handler: {e}", exc_info=True)

    def running(self) -> None:
        """Called when proxy starts"""
        self.logger.info("=" * 70)
        self.logger.info("🌐 NETWORKED PRIVACY PROXY - Connected to PrivacySpace")
        self.logger.info("=" * 70)

        if config:
            self.logger.info(f"Host: {config.get('proxy', {}).get('host', '127.0.0.1')}")
            self.logger.info(f"Port: {config.get('proxy', {}).get('port', 8080)}")
            self.logger.info(f"Fingerprint Mode: {config.get('fingerprint', {}).get('rotation_mode', 'every_request')}")
            self.logger.info(f"Block Cookies: {config.get('cookies', {}).get('block_all', True)}")
            self.logger.info(f"Auto Block: {config.get('blocking', {}).get('auto_block', True)}")

        if privacyspace_client and privacyspace_client.enabled:
            self.logger.info(f"PrivacySpace: CONNECTED (User: {privacyspace_client.user_id[:8]}...)")
            self.logger.info(f"Shared Blocklist: {len(privacyspace_client.shared_blocklist)} domains")
        else:
            self.logger.info("PrivacySpace: DISABLED (standalone mode)")

        self.logger.info("=" * 70)

        if db_handler:
            db_handler.add_diary_entry(
                "session",
                "Networked Privacy Proxy Started",
                f"Connected to PrivacySpace with {len(privacyspace_client.shared_blocklist) if privacyspace_client else 0} shared domains"
            )

    def done(self) -> None:
        """Called when proxy shuts down"""
        self.logger.info("=" * 70)
        self.logger.info("Privacy Proxy Shutting Down")
        self.logger.info("=" * 70)

        if db_handler:
            stats = db_handler.get_statistics()
            self.logger.info(f"Total Requests: {stats.get('total_requests', 0)}")
            self.logger.info(f"Blocked Domains: {stats.get('blocked_domains', 0)}")
            self.logger.info(f"Blocked Cookies: {stats.get('blocked_cookies', 0)}")
            self.logger.info(f"Discoveries Reported: {self.discoveries_reported}")

        if privacyspace_client:
            privacyspace_client.disconnect()

        self.logger.info("=" * 70)

        if db_handler:
            db_handler.close()


def main():
    """Main entry point"""
    global db_handler, fingerprint_randomizer, cookie_interceptor, traffic_blocker, privacyspace_client, config

    parser = argparse.ArgumentParser(description="Networked Privacy Proxy Server")
    parser.add_argument("--config", default="config/config.yaml", help="Path to configuration file")
    parser.add_argument("--server", default="http://localhost:5000", help="PrivacySpace server URL")
    parser.add_argument("--no-network", action="store_true", help="Disable PrivacySpace network")
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)
    logger = setup_logging(config)

    # Initialize database
    db_path = config.get("database", {}).get("path", "database/browser_privacy.db")
    db_handler = DatabaseHandler(db_path)

    # Initialize PrivacySpace client
    if not args.no_network:
        logger.info("Initializing PrivacySpace network connection...")
        privacyspace_client = PrivacySpaceClient(server_url=args.server, enabled=True)
    else:
        logger.info("Running in standalone mode (--no-network)")
        privacyspace_client = PrivacySpaceClient(enabled=False)

    # Initialize components
    fingerprint_randomizer = FingerprintRandomizer(db_handler, config)
    cookie_interceptor = CookieInterceptor(db_handler, config)
    traffic_blocker = TrafficBlocker(db_handler, config)

    # Add default whitelisted domains
    for domain in config.get("whitelist", []):
        db_handler.add_to_whitelist(domain, "config")

    logger.info("All components initialized successfully")


addons = [NetworkedPrivacyProxyAddon()]


if __name__ == "__main__":
    main()
