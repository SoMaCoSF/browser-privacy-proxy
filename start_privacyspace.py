# ==============================================================================
# file_id: SOM-SCR-0013-v1.0.0
# name: start_privacyspace.py
# description: Launcher for networked privacy proxy with PrivacySpace
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [launcher, networked]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.1.0
# agent_id: AGENT-PRIME-001
# execution: python start_privacyspace.py
# ==============================================================================

import sys
import argparse
import yaml
from pathlib import Path
from mitmproxy.tools.main import mitmdump


def load_config(config_path):
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        return {}


def main():
    """Start the networked privacy proxy server"""
    parser = argparse.ArgumentParser(
        description="PrivacySpace Networked Privacy Proxy"
    )
    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="Path to configuration file (default: config/config.yaml)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Proxy port (overrides config)",
    )
    parser.add_argument(
        "--host",
        help="Proxy host (overrides config)",
    )
    parser.add_argument(
        "--server",
        default="http://localhost:5000",
        help="PrivacySpace server URL (default: http://localhost:5000)",
    )
    parser.add_argument(
        "--no-network",
        action="store_true",
        help="Disable PrivacySpace network (standalone mode)",
    )
    parser.add_argument(
        "--mode",
        choices=["regular", "transparent", "socks5", "reverse"],
        default="regular",
        help="Proxy mode (default: regular)",
    )

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        sys.exit(1)

    config = load_config(config_path)

    # Get host and port
    host = args.host or config.get("proxy", {}).get("host", "127.0.0.1")
    port = args.port or config.get("proxy", {}).get("port", 8080)

    print("\n" + "="*70)
    print("  🌐 PRIVACYSPACE NETWORKED PRIVACY PROXY")
    print("="*70)
    print(f"  Version: 1.1.0")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Mode: {args.mode}")
    print(f"  Config: {config_path}")
    if not args.no_network:
        print(f"  PrivacySpace Server: {args.server}")
        print("  🌍 Network Mode: ENABLED")
    else:
        print("  🔒 Network Mode: DISABLED (standalone)")
    print("="*70)
    print()
    print("Configure your browser to use this proxy:")
    print(f"  HTTP Proxy: {host}:{port}")
    print(f"  HTTPS Proxy: {host}:{port}")
    print()
    if not args.no_network:
        print("💡 Your discoveries will be shared with the network!")
        print("💡 You'll receive real-time blocklist updates from all users!")
        print()
    print("Press Ctrl+C to stop the proxy")
    print("="*70)
    print()

    # Build mitmproxy arguments
    mitm_args = [
        "--listen-host", host,
        "--listen-port", str(port),
        "--set", "confdir=~/.mitmproxy",
        "-s", "privacy_proxy_networked.py",
        "--set", f"config_path={config_path}",
        "--set", f"server_url={args.server}",
    ]

    if args.no_network:
        mitm_args.extend(["--set", "no_network=true"])

    # Set mode
    if args.mode == "transparent":
        mitm_args.extend(["--mode", "transparent"])
    elif args.mode == "socks5":
        mitm_args.extend(["--mode", "socks5"])
    elif args.mode == "reverse":
        mitm_args.extend(["--mode", "reverse"])

    # Run mitmdump
    try:
        sys.argv = ["mitmdump"] + mitm_args
        mitmdump()
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down proxy...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
