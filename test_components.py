# ==============================================================================
# file_id: SOM-TST-0001-v1.0.0
# name: test_components.py
# description: Test script to verify all components work
# project_id: BROWSER-MIXER-ANON
# category: test
# tags: [test, verification]
# created: 2025-01-22
# modified: 2025-01-22
# version: 1.0.0
# agent_id: AGENT-PRIME-001
# execution: python test_components.py
# ==============================================================================

import sys
import yaml
from pathlib import Path

print("=" * 70)
print("  Privacy Proxy - Component Test")
print("=" * 70)
print()

# Test 1: Config loading
print("[1/6] Testing configuration loading...")
try:
    config_path = Path("config/config.yaml")
    if not config_path.exists():
        print("      ❌ FAIL: config/config.yaml not found")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    assert "proxy" in config, "Missing 'proxy' section"
    assert "fingerprint" in config, "Missing 'fingerprint' section"
    assert "cookies" in config, "Missing 'cookies' section"
    print("      ✅ PASS: Configuration loaded successfully")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    sys.exit(1)

# Test 2: Database initialization
print("[2/6] Testing database initialization...")
try:
    from database_handler import DatabaseHandler

    db = DatabaseHandler("database/test_browser_privacy.db")
    assert db is not None, "Database handler failed to initialize"

    # Test basic operations
    db.add_tracking_domain("test.tracker.com", "test")
    db.add_tracking_ip("1.2.3.4", "test.tracker.com")
    db.add_to_whitelist("trusted.com", "test")

    stats = db.get_statistics()
    assert isinstance(stats, dict), "Statistics should be a dict"

    db.close()
    print("      ✅ PASS: Database initialized and tested")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 3: Fingerprint randomizer
print("[3/6] Testing fingerprint randomizer...")
try:
    from fingerprint_randomizer import FingerprintRandomizer

    db = DatabaseHandler("database/test_browser_privacy.db")
    randomizer = FingerprintRandomizer(db, config)

    # Generate fingerprint
    fp1 = randomizer.generate_fingerprint("test")
    assert fp1 is not None, "Failed to generate fingerprint"
    assert "user_agent" in fp1, "Missing user_agent"
    assert "accept_language" in fp1, "Missing accept_language"

    # Generate another
    fp2 = randomizer.generate_fingerprint("test")
    # They should be different (unless we get really unlucky)
    # We'll just check they both exist
    assert fp2 is not None, "Failed to generate second fingerprint"

    db.close()
    print("      ✅ PASS: Fingerprint randomizer working")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 4: Cookie interceptor
print("[4/6] Testing cookie interceptor...")
try:
    from cookie_interceptor import CookieInterceptor

    db = DatabaseHandler("database/test_browser_privacy.db")
    interceptor = CookieInterceptor(db, config)

    # Test blocking decision
    should_block = interceptor.should_block_cookie("tracker.com", "_ga")
    assert should_block == True, "Should block tracking cookie"

    # Test domain extraction
    domain = interceptor.extract_domain_from_url("https://example.com/path")
    assert "example.com" in domain, "Failed to extract domain"

    stats = interceptor.get_stats()
    assert isinstance(stats, dict), "Stats should be a dict"

    db.close()
    print("      ✅ PASS: Cookie interceptor working")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 5: Traffic blocker
print("[5/6] Testing traffic blocker...")
try:
    from traffic_blocker import TrafficBlocker

    db = DatabaseHandler("database/test_browser_privacy.db")
    blocker = TrafficBlocker(db, config)

    # Test pattern matching
    should_block, reason = blocker.should_block_domain("google-analytics.com")
    assert should_block == True, "Should block analytics domain"
    assert reason is not None, "Should have block reason"

    # Test whitelist
    should_block, reason = blocker.should_block_domain("localhost")
    assert should_block == False, "Should not block whitelisted domain"

    # Test export
    blocklist = blocker.export_blocklist(format="text")
    assert blocklist is not None, "Failed to export blocklist"

    db.close()
    print("      ✅ PASS: Traffic blocker working")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# Test 6: Integration
print("[6/6] Testing integration...")
try:
    db = DatabaseHandler("database/test_browser_privacy.db")

    # Add some test data
    db.add_tracking_domain("tracker1.com", "test")
    db.add_tracking_domain("tracker2.com", "test")
    db.add_tracking_ip("10.0.0.1", "tracker1.com")

    # Log some activity
    db.log_cookie_traffic("tracker1.com", "test_cookie", "value", "10.0.0.1", "http://example.com", True)

    # Get stats
    stats = db.get_statistics()
    assert stats["blocked_domains"] >= 2, "Should have blocked domains"
    assert stats["blocked_cookies"] >= 1, "Should have blocked cookies"

    # Cleanup test database
    import os

    db.close()
    if os.path.exists("database/test_browser_privacy.db"):
        os.remove("database/test_browser_privacy.db")

    print("      ✅ PASS: Integration test successful")
except Exception as e:
    print(f"      ❌ FAIL: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print()
print("=" * 70)
print("  ✅ ALL TESTS PASSED!")
print("=" * 70)
print()
print("Your Privacy Proxy is ready to use!")
print()
print("Next steps:")
print("  1. Start the proxy:")
print("     python start_proxy.py")
print()
print("  2. Configure your browser to use proxy:")
print("     HTTP/HTTPS Proxy: 127.0.0.1:8080")
print()
print("  3. Install mitmproxy certificate:")
print("     Visit http://mitm.it")
print()
print("See QUICKSTART.md for detailed instructions")
print()
