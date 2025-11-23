# ==============================================================================
# file_id: SOM-SCR-0004-v1.0.0
# name: cookie_interceptor.py
# description: Cookie interception and blocking module
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [privacy, cookies, blocking]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: Imported by privacy_proxy.py
# ==============================================================================

import logging
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)


class CookieInterceptor:
    """Intercepts and blocks cookies, logs tracking attempts"""

    def __init__(self, db_handler, config):
        self.db = db_handler
        self.config = config
        self.blocked_count = 0
        self.logged_count = 0

        # Common tracking cookie patterns
        self.tracking_patterns = [
            r".*_ga.*",  # Google Analytics
            r".*_gid.*",
            r".*_gat.*",
            r".*fbp.*",  # Facebook
            r".*fbm.*",
            r".*fr.*",
            r".*_fbq.*",
            r".*doubleclick.*",
            r".*adsystem.*",
            r".*scorecard.*",
            r".*adnxs.*",
            r".*pubmatic.*",
            r".*rubiconproject.*",
            r".*criteo.*",
            r".*outbrain.*",
            r".*taboola.*",
        ]

    def should_block_cookie(self, domain, cookie_name):
        """Determine if cookie should be blocked"""

        # Check whitelist first
        if self.db.is_whitelisted(domain):
            logger.debug(f"Domain {domain} is whitelisted, allowing cookie")
            return False

        # Check config
        if self.config.get("cookies", {}).get("block_all", True):
            return True

        # Check if cookie matches tracking patterns
        for pattern in self.tracking_patterns:
            if re.match(pattern, cookie_name, re.IGNORECASE):
                logger.debug(f"Cookie {cookie_name} matches tracking pattern: {pattern}")
                return True

        return False

    def extract_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split("/")[0]
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {e}")
            return url

    def process_request_cookies(self, flow):
        """Process cookies in request, block if needed"""
        try:
            url = flow.request.pretty_url
            domain = self.extract_domain_from_url(url)
            ip_address = flow.server_conn.address[0] if flow.server_conn else None

            cookie_header = flow.request.headers.get("Cookie", "")

            if not cookie_header:
                return

            # Parse cookies
            cookies = {}
            for cookie in cookie_header.split(";"):
                if "=" in cookie:
                    name, value = cookie.strip().split("=", 1)
                    cookies[name] = value

            blocked_cookies = []

            for cookie_name, cookie_value in cookies.items():
                should_block = self.should_block_cookie(domain, cookie_name)

                # Log to database
                if self.config.get("cookies", {}).get("log_attempts", True):
                    self.db.log_cookie_traffic(
                        domain, cookie_name, cookie_value[:100], ip_address, url, should_block
                    )
                    self.logged_count += 1

                if should_block:
                    blocked_cookies.append(cookie_name)
                    self.blocked_count += 1

                    # Track this domain
                    if self.config.get("cookies", {}).get("auto_block_trackers", True):
                        self.db.add_tracking_domain(domain, "cookie-tracker")
                        if ip_address:
                            self.db.add_tracking_ip(ip_address, domain)

            # Remove blocked cookies from request
            if blocked_cookies:
                remaining_cookies = [
                    f"{k}={v}" for k, v in cookies.items() if k not in blocked_cookies
                ]
                if remaining_cookies:
                    flow.request.headers["Cookie"] = "; ".join(remaining_cookies)
                else:
                    # Remove cookie header entirely if all blocked
                    flow.request.headers.pop("Cookie", None)

                logger.info(f"Blocked {len(blocked_cookies)} cookies from {domain}")

        except Exception as e:
            logger.error(f"Error processing request cookies: {e}")

    def process_response_cookies(self, flow):
        """Process Set-Cookie headers in response, block if needed"""
        try:
            url = flow.request.pretty_url
            domain = self.extract_domain_from_url(url)
            ip_address = flow.server_conn.address[0] if flow.server_conn else None

            # Get all Set-Cookie headers
            set_cookie_headers = flow.response.headers.get_all("Set-Cookie")

            if not set_cookie_headers:
                return

            blocked_cookies = []

            for cookie_header in set_cookie_headers:
                # Parse cookie name
                cookie_name = cookie_header.split("=")[0].strip()
                cookie_value = cookie_header.split("=")[1].split(";")[0] if "=" in cookie_header else ""

                should_block = self.should_block_cookie(domain, cookie_name)

                # Log to database
                if self.config.get("cookies", {}).get("log_attempts", True):
                    self.db.log_cookie_traffic(
                        domain, cookie_name, cookie_value[:100], ip_address, url, should_block
                    )
                    self.logged_count += 1

                if should_block:
                    blocked_cookies.append(cookie_header)
                    self.blocked_count += 1

                    # Track this domain
                    if self.config.get("cookies", {}).get("auto_block_trackers", True):
                        self.db.add_tracking_domain(domain, "cookie-tracker")
                        if ip_address:
                            self.db.add_tracking_ip(ip_address, domain)

            # Remove blocked Set-Cookie headers
            if blocked_cookies:
                # Remove all Set-Cookie headers first
                while "Set-Cookie" in flow.response.headers:
                    flow.response.headers.pop("Set-Cookie")

                # Re-add only non-blocked ones
                for cookie_header in set_cookie_headers:
                    if cookie_header not in blocked_cookies:
                        flow.response.headers.add("Set-Cookie", cookie_header)

                logger.info(f"Blocked {len(blocked_cookies)} Set-Cookie headers from {domain}")

        except Exception as e:
            logger.error(f"Error processing response cookies: {e}")

    def get_stats(self):
        """Get cookie blocking statistics"""
        return {
            "blocked_count": self.blocked_count,
            "logged_count": self.logged_count,
        }
