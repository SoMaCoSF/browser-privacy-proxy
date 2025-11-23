# ==============================================================================
# file_id: SOM-SCR-0007-v1.0.0
# name: manage.py
# description: Management CLI for privacy proxy
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [cli, management, admin]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python manage.py [command] [args]
# ==============================================================================

import argparse
import yaml
import sys
from pathlib import Path
from datetime import datetime
from database_handler import DatabaseHandler


def load_config(config_path="config/config.yaml"):
    """Load configuration"""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {"database": {"path": "database/browser_privacy.db"}}


def print_stats(db):
    """Print database statistics"""
    stats = db.get_statistics()

    print("\n" + "=" * 70)
    print("  PRIVACY PROXY STATISTICS")
    print("=" * 70)
    print(f"  Total Requests:         {stats.get('total_requests', 0):,}")
    print(f"  Blocked Domains:        {stats.get('blocked_domains', 0):,}")
    print(f"  Blocked IPs:            {stats.get('blocked_ips', 0):,}")
    print(f"  Blocked Cookies:        {stats.get('blocked_cookies', 0):,}")
    print(f"  Fingerprint Rotations:  {stats.get('fingerprint_rotations', 0):,}")
    print("=" * 70 + "\n")


def list_blocked_domains(db, limit=50):
    """List blocked domains"""
    conn = db._get_connection()
    cursor = conn.execute(
        """
        SELECT domain, category, hit_count, first_seen, last_seen
        FROM tracking_domains
        WHERE blocked = 1
        ORDER BY hit_count DESC
        LIMIT ?
        """,
        (limit,),
    )

    print("\n" + "=" * 70)
    print(f"  TOP {limit} BLOCKED DOMAINS")
    print("=" * 70)
    print(f"{'Domain':<40} {'Hits':<10} {'Category':<15}")
    print("-" * 70)

    for row in cursor.fetchall():
        domain = row[0][:38]
        category = row[1][:13]
        hit_count = row[2]
        print(f"{domain:<40} {hit_count:<10} {category:<15}")

    print("=" * 70 + "\n")


def list_blocked_ips(db, limit=50):
    """List blocked IPs"""
    conn = db._get_connection()
    cursor = conn.execute(
        """
        SELECT ip_address, associated_domain, hit_count, first_seen, last_seen
        FROM tracking_ips
        WHERE blocked = 1
        ORDER BY hit_count DESC
        LIMIT ?
        """,
        (limit,),
    )

    print("\n" + "=" * 70)
    print(f"  TOP {limit} BLOCKED IPs")
    print("=" * 70)
    print(f"{'IP Address':<20} {'Hits':<10} {'Associated Domain':<35}")
    print("-" * 70)

    for row in cursor.fetchall():
        ip = row[0]
        domain = (row[1] or "")[:33]
        hit_count = row[2]
        print(f"{ip:<20} {hit_count:<10} {domain:<35}")

    print("=" * 70 + "\n")


def list_cookies(db, limit=50):
    """List recent cookie attempts"""
    conn = db._get_connection()
    cursor = conn.execute(
        """
        SELECT timestamp, domain, cookie_name, blocked
        FROM cookie_traffic
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )

    print("\n" + "=" * 70)
    print(f"  RECENT {limit} COOKIE ATTEMPTS")
    print("=" * 70)
    print(f"{'Time':<20} {'Domain':<30} {'Cookie':<20}")
    print("-" * 70)

    for row in cursor.fetchall():
        timestamp = row[0][:19]
        domain = row[1][:28]
        cookie_name = row[2][:18]
        blocked = "BLOCKED" if row[3] else "ALLOWED"
        print(f"{timestamp:<20} {domain:<30} {cookie_name:<20}")

    print("=" * 70 + "\n")


def export_blocklist(db, output_file, format="hosts"):
    """Export blocklist to file"""
    from traffic_blocker import TrafficBlocker

    config = load_config()
    blocker = TrafficBlocker(db, config)

    blocklist = blocker.export_blocklist(format=format)

    if blocklist:
        with open(output_file, "w") as f:
            f.write(blocklist)
        print(f"\nBlocklist exported to: {output_file}")
        print(f"Format: {format}\n")
    else:
        print("\nError exporting blocklist\n")


def add_to_whitelist(db, domain, reason=""):
    """Add domain to whitelist"""
    db.add_to_whitelist(domain, reason)
    print(f"\nAdded {domain} to whitelist\n")


def add_to_blocklist(db, domain, category="manual"):
    """Add domain to blocklist"""
    db.add_tracking_domain(domain, category)
    print(f"\nAdded {domain} to blocklist (category: {category})\n")


def view_recent_requests(db, limit=50):
    """View recent requests"""
    conn = db._get_connection()
    cursor = conn.execute(
        """
        SELECT timestamp, method, host, blocked, block_reason
        FROM request_log
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,),
    )

    print("\n" + "=" * 70)
    print(f"  RECENT {limit} REQUESTS")
    print("=" * 70)
    print(f"{'Time':<20} {'Method':<8} {'Host':<30} {'Status':<12}")
    print("-" * 70)

    for row in cursor.fetchall():
        timestamp = row[0][:19]
        method = row[1]
        host = row[2][:28]
        blocked = "BLOCKED" if row[3] else "ALLOWED"
        print(f"{timestamp:<20} {method:<8} {host:<30} {blocked:<12}")

    print("=" * 70 + "\n")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Privacy Proxy Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  stats                     Show database statistics
  domains [--limit N]       List blocked domains
  ips [--limit N]           List blocked IPs
  cookies [--limit N]       List recent cookie attempts
  requests [--limit N]      List recent requests
  export FILE [--format]    Export blocklist (formats: hosts, text, list)
  whitelist DOMAIN          Add domain to whitelist
  block DOMAIN              Add domain to blocklist

Examples:
  python manage.py stats
  python manage.py domains --limit 100
  python manage.py export blocklist.txt --format hosts
  python manage.py whitelist example.com
  python manage.py block tracker.com
        """,
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to config file",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Stats command
    subparsers.add_parser("stats", help="Show statistics")

    # Domains command
    domains_parser = subparsers.add_parser("domains", help="List blocked domains")
    domains_parser.add_argument("--limit", type=int, default=50, help="Number of domains to show")

    # IPs command
    ips_parser = subparsers.add_parser("ips", help="List blocked IPs")
    ips_parser.add_argument("--limit", type=int, default=50, help="Number of IPs to show")

    # Cookies command
    cookies_parser = subparsers.add_parser("cookies", help="List cookie attempts")
    cookies_parser.add_argument("--limit", type=int, default=50, help="Number of cookies to show")

    # Requests command
    requests_parser = subparsers.add_parser("requests", help="List recent requests")
    requests_parser.add_argument("--limit", type=int, default=50, help="Number of requests to show")

    # Export command
    export_parser = subparsers.add_parser("export", help="Export blocklist")
    export_parser.add_argument("output_file", help="Output file path")
    export_parser.add_argument(
        "--format",
        choices=["hosts", "text", "list"],
        default="hosts",
        help="Export format",
    )

    # Whitelist command
    whitelist_parser = subparsers.add_parser("whitelist", help="Add to whitelist")
    whitelist_parser.add_argument("domain", help="Domain to whitelist")
    whitelist_parser.add_argument("--reason", default="", help="Reason for whitelisting")

    # Block command
    block_parser = subparsers.add_parser("block", help="Add to blocklist")
    block_parser.add_argument("domain", help="Domain to block")
    block_parser.add_argument("--category", default="manual", help="Block category")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Load config and initialize database
    config = load_config(args.config)
    db_path = config.get("database", {}).get("path", "database/browser_privacy.db")
    db = DatabaseHandler(db_path)

    # Execute command
    try:
        if args.command == "stats":
            print_stats(db)

        elif args.command == "domains":
            list_blocked_domains(db, args.limit)

        elif args.command == "ips":
            list_blocked_ips(db, args.limit)

        elif args.command == "cookies":
            list_cookies(db, args.limit)

        elif args.command == "requests":
            view_recent_requests(db, args.limit)

        elif args.command == "export":
            export_blocklist(db, args.output_file, args.format)

        elif args.command == "whitelist":
            add_to_whitelist(db, args.domain, args.reason)

        elif args.command == "block":
            add_to_blocklist(db, args.domain, args.category)

    except Exception as e:
        print(f"\nError: {e}\n")
        sys.exit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()
