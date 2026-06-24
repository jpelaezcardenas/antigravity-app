"""
Tests for AgentContext governance additions
(change agent-operations-multitenant-security, Slice 2.3):
tenant_id alias + per-session membership cache field.
"""

from __future__ import annotations

from datetime import datetime

from services.agent_context import AgentContext, Permission


def _ctx() -> AgentContext:
    return AgentContext(
        user_id="u1",
        workspace_id="t-123",
        user_email="u1@example.com",
        timestamp=datetime.utcnow(),
        permissions=[Permission.READ_PULSO],
    )


def test_tenant_id_aliases_workspace_id():
    ctx = _ctx()
    assert ctx.tenant_id == ctx.workspace_id == "t-123"


def test_membership_cache_defaults_to_unchecked():
    assert _ctx().tenant_membership_verified is None


def test_membership_cache_is_settable():
    ctx = _ctx()
    ctx.tenant_membership_verified = True
    assert ctx.tenant_membership_verified is True
