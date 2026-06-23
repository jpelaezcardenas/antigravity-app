#!/usr/bin/env python3
"""
Quick validation script for WebSocket setup before deployment.
Checks imports, configuration, and basic connectivity.
"""

import sys
import os

def test_imports():
    """Test that all required imports work."""
    print("\n1. Testing backend imports...")

    try:
        from api.websocket_handler import router, manager, ConnectionManager
        print("   OK: websocket_handler imports")
    except Exception as e:
        print(f"   FAIL: websocket_handler - {e}")
        return False

    try:
        from services.agent_context import (
            context_manager,
            AgentContext,
            Permission,
        )
        print("   OK: agent_context imports")
    except Exception as e:
        print(f"   FAIL: agent_context - {e}")
        return False

    try:
        from config import settings
        print("   OK: config imports")
    except Exception as e:
        print(f"   FAIL: config - {e}")
        return False

    return True


def test_config():
    """Test that configuration is valid."""
    print("\n2. Testing configuration...")

    try:
        from config import settings

        # Check JWT_SECRET
        if not settings.JWT_SECRET or len(settings.JWT_SECRET) < 10:
            print("   WARN: JWT_SECRET appears empty or too short")
            print("         Set JWT_SECRET env var before deployment")
        else:
            print("   OK: JWT_SECRET is set")

        # Check JWT_ALGORITHM
        if settings.JWT_ALGORITHM != "HS256":
            print(f"   WARN: JWT_ALGORITHM is {settings.JWT_ALGORITHM} (expected HS256)")
        else:
            print("   OK: JWT_ALGORITHM is HS256")

        # Check DEBUG mode
        if settings.DEBUG:
            print("   WARN: DEBUG=true (should be false in production)")
        else:
            print("   OK: DEBUG=false (production mode)")

        return True
    except Exception as e:
        print(f"   FAIL: {e}")
        return False


def test_agent_context():
    """Test AgentContext functionality."""
    print("\n3. Testing AgentContext...")

    try:
        from services.agent_context import (
            context_manager,
            AgentContext,
            Permission,
            build_agent_payload,
        )
        from datetime import datetime

        # Create test context
        ctx = context_manager.create_context(
            user_id="test-user-123",
            workspace_id="test-workspace-456",
            user_email="test@example.com",
            permissions=["read:pulso", "write:approval"],
        )

        # Test permissions
        assert ctx.can_invoke_agent("pulso"), "Should allow pulso agent"
        print("   OK: Permission check works")

        # Test context serialization
        ctx_dict = ctx.to_dict()
        assert ctx_dict["user_id"] == "test-user-123"
        assert ctx_dict["workspace_id"] == "test-workspace-456"
        print("   OK: Context serialization works")

        # Test payload builder
        payload = build_agent_payload(ctx, {"test": "param"})
        assert "context" in payload
        assert "params" in payload
        print("   OK: Payload builder works")

        return True
    except Exception as e:
        print(f"   FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_connection_manager():
    """Test ConnectionManager functionality."""
    print("\n4. Testing ConnectionManager...")

    try:
        from api.websocket_handler import ConnectionManager

        manager = ConnectionManager()

        # Test basic operations (without actual WebSocket)
        assert len(manager.active_connections) == 0
        print("   OK: ConnectionManager initializes empty")

        return True
    except Exception as e:
        print(f"   FAIL: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("  WebSocket Setup Validation")
    print("=" * 60)

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Config", test_config()))
    results.append(("AgentContext", test_agent_context()))
    results.append(("ConnectionManager", test_connection_manager()))

    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)

    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {name:20} ... {status}")

    all_passed = all(passed for _, passed in results)

    print("=" * 60)
    if all_passed:
        print("  All checks passed! Ready for deployment.")
        return 0
    else:
        print("  Some checks failed. Review above and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
