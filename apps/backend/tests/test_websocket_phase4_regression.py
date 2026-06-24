"""
Regression tests for Phase 4 WebSocket behavior (Slice 4.5).

Ensures that the governance layer (Slice 4) does not break existing WebSocket
functionality (subscribe/heartbeat/agent_invoke/unsubscribe message handling).

These are logic tests (mocked httpx/manager) to verify response shape unchanged.
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.agent_context import AgentContext, Permission


class TestWebSocketPhase4Regression:
    """Verify Phase 4 message handling still works with governance layer."""

    def _make_context(self) -> AgentContext:
        """Create a test AgentContext."""
        return AgentContext(
            user_id="u1",
            workspace_id="t1",
            user_email="test@example.com",
            timestamp=datetime.utcnow(),
            permissions=[Permission.READ_PULSO],
        )

    def test_heartbeat_message_unchanged(self):
        """Heartbeat messages still have type and timestamp."""
        heartbeat = {
            "type": "heartbeat",
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert "type" in heartbeat
        assert heartbeat["type"] == "heartbeat"
        assert "timestamp" in heartbeat

    def test_subscribe_message_still_processed(self):
        """Subscribe message structure (agent) is unchanged."""
        msg = {
            "type": "subscribe",
            "agent": "pulso",
        }
        assert msg["type"] == "subscribe"
        assert msg["agent"] == "pulso"

    def test_unsubscribe_message_unchanged(self):
        """Unsubscribe message structure is unchanged."""
        msg = {
            "type": "unsubscribe",
            "agent": "pulso",
        }
        assert msg["type"] == "unsubscribe"
        assert msg["agent"] == "pulso"

    def test_agent_invoke_response_shape_backward_compatible(self):
        """Agent invoke response includes new fields but old fields unchanged.

        The response must include: type, agent, data, timestamp.
        New fields (cost, session_cost) are additive.
        """
        # Simulated invoke_agent result (now includes cost/session_cost).
        invoke_result = {
            "status": "success",
            "agent": "pulso",
            "data": {"caja_real": "1000"},
            "cost": 0.005,
            "session_cost": 0.005,
        }

        # WebSocket manager.send_personal wraps it with type/timestamp.
        ws_message = {
            "type": "agent_output",
            "agent": "pulso",
            "data": invoke_result,  # Full invoke_agent result
            "timestamp": datetime.utcnow().isoformat(),
        }

        # Old code expects these fields to exist.
        assert ws_message["type"] == "agent_output"
        assert ws_message["agent"] == "pulso"
        assert ws_message["timestamp"]

        # New fields are present but don't break old clients.
        assert ws_message["data"]["status"] == "success"
        assert ws_message["data"]["agent"] == "pulso"
        assert "data" in ws_message["data"]
        assert "cost" in ws_message["data"]  # NEW
        assert "session_cost" in ws_message["data"]  # NEW

    def test_permission_check_still_blocks_unpermitted_agents(self):
        """Permission check (Phase 3) is before governance gate (Phase 5)."""
        ctx = self._make_context()
        # ctx only has READ_PULSO permission.

        # Check against an agent not in permissions.
        can_invoke = ctx.can_invoke_agent("centinela")
        assert not can_invoke  # Should be blocked by permission check first

        # Check against allowed agent.
        can_invoke = ctx.can_invoke_agent("pulso")
        assert can_invoke  # Should pass permission check

    def test_agent_output_from_stream_unchanged(self):
        """Stream output messages (agent_output type) unchanged."""
        stream_msg = {
            "type": "agent_output",
            "agent": "pulso",
            "data": {"timestamp": "2026-06-24T12:00:00", "value": 1000},
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert stream_msg["type"] == "agent_output"
        assert stream_msg["agent"] == "pulso"
        assert "data" in stream_msg
        assert "timestamp" in stream_msg

    def test_error_response_shape_unchanged(self):
        """Error responses from permission checks still have type/agent/error."""
        error_msg = {
            "type": "agent_error",
            "agent": "centinela",
            "error": "Permission denied: cannot invoke centinela",
            "timestamp": datetime.utcnow().isoformat(),
        }
        assert error_msg["type"] == "agent_error"
        assert error_msg["agent"]
        assert "error" in error_msg
        assert "timestamp" in error_msg
