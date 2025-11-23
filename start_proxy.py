# ==============================================================================
# file_id: SOM-SCR-0006-v1.0.0
# name: start_proxy.py
# description: Launcher script for privacy proxy
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [launcher, proxy]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python start_proxy.py [--port 8080] [--config config/config.yaml]
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
    """Start the privacy proxy server"""
    parser = argparse.ArgumentParser(
        description="Privacy Proxy - Browser Anonymization Tool"
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
        "--mode",
        choices=["regular", "transparent", "socks5", "reverse"],
        default="regular",
        help="Proxy mode (default: regular)",
    )
    parser.add_argument(
        "--no-ssl-insecure",
        action="store_true",
        help="Do not verify SSL certificates",
    )

    args = parser.parse_args()

    # Load config
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Config file not found: {config_path}")
        print("Creating default config...")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        # Create minimal config
        default_config = {
            "proxy": {"host": "127.0.0.1", "port": 8080},
            "database": {"path": "database/browser_privacy.db"},
            "logging": {"level": "INFO", "file": "logs/privacy_proxy.log"},
        }
        with open(config_path, "w") as f:
            yaml.dump(default_config, f)
        print(f"Created default config at {config_path}")

    config = load_config(config_path)

    # Get host and port
    host = args.host or config.get("proxy", {}).get("host", "127.0.0.1")
    port = args.port or config.get("proxy", {}).get("port", 8080)

    print("=" * 70)
    print("  PRIVACY PROXY - Browser Anonymization Tool")
    print("=" * 70)
    print(f"  Version: 1.0.0")
    print(f"  Host: {host}")
    print(f"  Port: {port}")
    print(f"  Mode: {args.mode}")
    print(f"  Config: {config_path}")
    print("=" * 70)
    print()
    print("Configure your browser to use this proxy:")
    print(f"  HTTP Proxy: {host}:{port}")
    print(f"  HTTPS Proxy: {host}:{port}")
    print()
    print("Press Ctrl+C to stop the proxy")
    print("=" * 70)
    print()

    # Build mitmproxy arguments
    mitm_args = [
        "--listen-host", host,
        "--listen-port", str(port),
        "--set", "confdir=~/.mitmproxy",
        "-s", "privacy_proxy.py",
        "--set", f"config_path={config_path}",
    ]

    # Add SSL insecure if requested
    if args.no_ssl_insecure:
        mitm_args.extend(["--ssl-insecure"])

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
        print("\n\nShutting down proxy...")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
