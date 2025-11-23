# ==============================================================================
# file_id: SOM-SCR-0005-v1.0.0
# name: traffic_blocker.py
# description: IP and domain blocking mechanism
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [privacy, blocking, firewall]
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


class TrafficBlocker:
    """Blocks traffic to/from tracking IPs and domains"""

    def __init__(self, db_handler, config):
        self.db = db_handler
        self.config = config
        self.blocked_requests = 0
        self.allowed_requests = 0

        # Load block patterns from config
        self.block_patterns = config.get("blocking", {}).get("block_patterns", [])

        # Compile regex patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.block_patterns]

    def should_block_domain(self, domain):
        """Determine if domain should be blocked"""

        # Check whitelist first
        if self.db.is_whitelisted(domain):
            logger.debug(f"Domain {domain} is whitelisted")
            return False, None

        # Check if explicitly blocked in database
        if self.db.is_domain_blocked(domain):
            return True, "database_blocklist"

        # Check against patterns
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.match(domain):
                logger.debug(f"Domain {domain} matches block pattern: {self.block_patterns[i]}")
                # Add to database for future quick lookup
                self.db.add_tracking_domain(domain, "pattern-match")
                return True, f"pattern: {self.block_patterns[i]}"

        return False, None

    def should_block_ip(self, ip_address):
        """Determine if IP should be blocked"""
        if not ip_address:
            return False, None

        # Skip localhost
        if ip_address in ["127.0.0.1", "::1", "localhost"]:
            return False, None

        # Check if explicitly blocked in database
        if self.db.is_ip_blocked(ip_address):
            return True, "database_blocklist"

        return False, None

    def extract_domain_from_url(self, url):
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            return parsed.netloc or parsed.path.split("/")[0]
        except Exception as e:
            logger.error(f"Error extracting domain from {url}: {e}")
            return url

    def process_request(self, flow):
        """Process request and block if necessary"""
        try:
            url = flow.request.pretty_url
            domain = self.extract_domain_from_url(url)
            ip_address = flow.server_conn.address[0] if flow.server_conn else None

            # Check if should block
            if not self.config.get("blocking", {}).get("auto_block", True):
                self.allowed_requests += 1
                return False  # Blocking disabled

            # Check domain
            should_block_domain, domain_reason = self.should_block_domain(domain)

            # Check IP
            should_block_ip, ip_reason = self.should_block_ip(ip_address)

            # Block if either is true
            should_block = should_block_domain or should_block_ip
            block_reason = domain_reason or ip_reason

            if should_block:
                self.blocked_requests += 1
                logger.warning(f"BLOCKED: {flow.request.method} {url} (reason: {block_reason})")

                # Log to database
                fingerprint_id = getattr(flow, "fingerprint_id", None)
                self.db.log_request(
                    flow.request.method,
                    url,
                    domain,
                    ip_address,
                    fingerprint_id,
                    blocked=True,
                    block_reason=block_reason,
                )

                # Kill the connection
                flow.kill()
                return True

            else:
                self.allowed_requests += 1
                return False

        except Exception as e:
            logger.error(f"Error processing request for blocking: {e}")
            return False

    def add_domain_to_blocklist(self, domain, category="manual"):
        """Manually add domain to blocklist"""
        try:
            self.db.add_tracking_domain(domain, category)
            logger.info(f"Added {domain} to blocklist (category: {category})")
        except Exception as e:
            logger.error(f"Error adding domain to blocklist: {e}")

    def add_ip_to_blocklist(self, ip_address, associated_domain=None):
        """Manually add IP to blocklist"""
        try:
            self.db.add_tracking_ip(ip_address, associated_domain)
            logger.info(f"Added {ip_address} to blocklist")
        except Exception as e:
            logger.error(f"Error adding IP to blocklist: {e}")

    def get_blocklist_stats(self):
        """Get blocklist statistics"""
        return {
            "blocked_domains": len(self.db.get_blocked_domains()),
            "blocked_ips": len(self.db.get_blocked_ips()),
            "blocked_requests": self.blocked_requests,
            "allowed_requests": self.allowed_requests,
        }

    def export_blocklist(self, format="text"):
        """Export blocklist in various formats"""
        try:
            domains = self.db.get_blocked_domains()
            ips = self.db.get_blocked_ips()

            if format == "text":
                output = "# Blocked Domains\n"
                for domain in domains:
                    output += f"{domain}\n"
                output += "\n# Blocked IPs\n"
                for ip in ips:
                    output += f"{ip}\n"
                return output

            elif format == "hosts":
                # /etc/hosts format
                output = "# Privacy Proxy Blocklist\n"
                for domain in domains:
                    output += f"0.0.0.0 {domain}\n"
                    output += f"0.0.0.0 www.{domain}\n"
                return output

            elif format == "list":
                return {"domains": domains, "ips": ips}

        except Exception as e:
            logger.error(f"Error exporting blocklist: {e}")
            return None
