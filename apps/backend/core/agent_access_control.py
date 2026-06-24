"""
Agent access control — tenant membership enforcement.

Before any agent runs through the WebSocket invoke_agent() chokepoint, this
module verifies that the calling user actually belongs to the requested tenant
(user_tenants, is_active). This is the application-level isolation boundary:
the backend connects to Supabase with the anon key and authenticates users with
its own HS256 JWT, so RLS auth.uid() is NULL for the backend and cannot isolate
tenants on its own. Reads therefore use the service-role client (controlled RLS
bypass) — see change agent-operations-multitenant-security, design D6/D2.

Fail-closed: any error confirming membership results in a block.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import logging

from core.supabase_client import get_service_supabase

logger = logging.getLogger("agent-access-control")

# Roles (user_roles.role enum role_type) allowed to read the full audit trail.
PRIVILEGED_AUDIT_ROLES = ("admin", "finance")


@dataclass(frozen=True)
class AccessDecision:
    """Outcome of an access-control check."""

    allowed: bool
    reason: str
    role: Optional[str] = None

    @property
    def status(self) -> str:
        """Maps to the agent_operations.status taxonomy."""
        return "allowed" if self.allowed else "blocked"


class AgentAccessControl:
    """Verifies tenant membership for agent invocations via the service client."""

    def __init__(self, client=None) -> None:
        # `client` is injectable for tests; defaults to the lazy service-role client.
        self._client = client

    def _supabase(self):
        return self._client if self._client is not None else get_service_supabase()

    def is_member(self, user_id: str, tenant_id: str) -> bool:
        """True if user_id is an active member of tenant_id."""
        result = (
            self._supabase()
            .table("user_tenants")
            .select("id")
            .eq("user_id", user_id)
            .eq("tenant_id", tenant_id)
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return bool(result.data)

    def get_role(self, user_id: str, tenant_id: str) -> Optional[str]:
        """Return the user's role in the tenant, or None."""
        result = (
            self._supabase()
            .table("user_roles")
            .select("role")
            .eq("user_id", user_id)
            .eq("tenant_id", tenant_id)
            .limit(1)
            .execute()
        )
        if result.data:
            return result.data[0].get("role")
        return None

    def check_access(
        self, user_id: str, tenant_id: str, agent_name: str
    ) -> AccessDecision:
        """Decide whether `user_id` may invoke `agent_name` in `tenant_id`.

        agent_name is accepted for traceability and future per-agent rules; the
        current rule is tenant membership only (agent-level permissions are
        enforced separately by AgentContext.can_invoke_agent).
        """
        if not user_id:
            return AccessDecision(False, "missing_user")
        if not tenant_id:
            return AccessDecision(False, "missing_tenant")

        try:
            member = self.is_member(user_id, tenant_id)
        except Exception as exc:  # fail-closed on any membership-check error
            logger.error(
                "Access check failed for user=%s tenant=%s agent=%s: %s",
                user_id,
                tenant_id,
                agent_name,
                exc,
            )
            return AccessDecision(False, "access_check_error")

        if not member:
            return AccessDecision(False, "not_a_member")

        role: Optional[str] = None
        try:
            role = self.get_role(user_id, tenant_id)
        except Exception as exc:  # role is non-blocking metadata
            logger.warning(
                "Role lookup failed for user=%s tenant=%s: %s",
                user_id,
                tenant_id,
                exc,
            )

        return AccessDecision(True, "member", role=role)

    def can_read_full_audit(self, user_id: str, tenant_id: str) -> bool:
        """True if the user holds a privileged role (admin/finance) in the tenant."""
        return self.get_role(user_id, tenant_id) in PRIVILEGED_AUDIT_ROLES


# Shared instance
agent_access_control = AgentAccessControl()
