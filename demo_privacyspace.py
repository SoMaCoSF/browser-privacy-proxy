# ==============================================================================
# file_id: SOM-SCR-0014-v1.0.0
# name: demo_privacyspace.py
# description: Demo script to test PrivacySpace network
# project_id: BROWSER-MIXER-ANON
# category: script
# tags: [demo, test]
# created: 2025-01-23
# modified: 2025-01-23
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python demo_privacyspace.py
# ==============================================================================

"""
Demo script that simulates multiple users discovering trackers
Run this AFTER starting the central server to see live updates!
"""

import time
import random
from privacyspace_client import PrivacySpaceClient

# Simulated tracker discoveries
FAKE_TRACKERS = [
    ('google-analytics.com/collect', 'Google', 'cookie'),
    ('doubleclick.net/pixel', 'Google', 'pixel'),
    ('facebook.com/tr', 'Facebook', 'pixel'),
    ('amazon-adsystem.com/aax2', 'Amazon', 'script'),
    ('twitter.com/i/adsct', 'Twitter', 'pixel'),
    ('ads.linkedin.com/collect', 'LinkedIn', 'cookie'),
    ('scorecardresearch.com/beacon', 'comScore', 'cookie'),
    ('bing.com/bat.js', 'Microsoft', 'script'),
    ('tiktok.com/pixel', 'TikTok', 'pixel'),
    ('snapchat.com/tracking', 'Snapchat', 'pixel'),
]

def simulate_user(user_num, client):
    """Simulate a user discovering trackers"""
    print(f"\n👤 Simulated User #{user_num} starting...")

    # Discover 3-5 random trackers
    num_discoveries = random.randint(3, 5)
    trackers = random.sample(FAKE_TRACKERS, num_discoveries)

    for domain, company, method in trackers:
        time.sleep(random.uniform(1, 3))  # Random delay

        print(f"  🔍 User #{user_num} discovered: {domain}")

        client.report_tracker(
            domain=domain,
            method=method,
            confidence=random.uniform(0.7, 0.95),
            context={'company': company}
        )

    print(f"✅ User #{user_num} finished ({num_discoveries} trackers reported)")


def main():
    print("\n" + "="*70)
    print("  🎭 PRIVACYSPACE DEMO - Simulated Users")
    print("="*70)
    print("\n  This demo simulates multiple users discovering trackers.")
    print("  Watch the dashboard at http://localhost:5000 for live updates!")
    print("\n" + "="*70 + "\n")

    try:
        # Create client
        client = PrivacySpaceClient(server_url='http://localhost:5000')

        # Wait for connection
        print("⏳ Connecting to PrivacySpace...")
        time.sleep(3)

        if not client.connected:
            print("❌ Failed to connect to server!")
            print("   Make sure the server is running: python privacyspace_server/server.py")
            return

        print("✅ Connected to PrivacySpace!\n")

        # Simulate 3 users
        for i in range(1, 4):
            simulate_user(i, client)
            time.sleep(2)

        print("\n" + "="*70)
        print("  ✅ DEMO COMPLETE!")
        print("="*70)
        print("\n  Check the dashboard to see:")
        print("  • Live tracker feed")
        print("  • Updated statistics")
        print("  • Top companies")
        print("\n" + "="*70 + "\n")

        # Fetch final stats
        stats = client.get_stats()
        if stats:
            print("📊 Current Network Stats:")
            print(f"  • Total Trackers: {stats['total_trackers']}")
            print(f"  • Total Blocks: {stats['total_blocks']}")
            print(f"  • Active Users: {stats['active_users']}")
            print()

        client.disconnect()

    except KeyboardInterrupt:
        print("\n\n🛑 Demo interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
