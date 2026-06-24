"""
Agent Context Service
Propagates user session context to Hermes agents.

Context includes: workspace_id, user_id, email, permissions, timestamp
All agent invocations receive this context for proper isolation and audit trail.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum
import logging

logger = logging.getLogger("agent-context")


class Permission(str, Enum):
    """Agent operation permissions."""

    # Read permissions
    READ_PULSO = "read:pulso"
    READ_CENTINELA = "read:centinela"
    READ_RADAR = "read:radar"
    READ_AUDIT = "read:audit"
    READ_APPROVALS = "read:approvals"

    # Write permissions
    WRITE_APPROVAL = "write:approval"
    WRITE_COMMAND = "write:command"
    WRITE_TAX_CORRECTION = "write:tax_correction"

    # Admin
    ADMIN = "admin"


@dataclass
class AgentContext:
    """
    Context passed to all agent invocations.
    Provides isolation, auditability, and permission checking.
    """

    user_id: str
    workspace_id: str
    user_email: str
    timestamp: datetime
    permissions: List[Permission]
    metadata: Optional[Dict[str, Any]] = None
    # Per-session membership cache: None = not yet checked, True/False = result.
    # Set once by the WebSocket chokepoint so access control runs one query per
    # session (workspace_id is fixed per context). See change
    # agent-operations-multitenant-security, design D2/D6.
    tenant_membership_verified: Optional[bool] = None

    @property
    def tenant_id(self) -> str:
        """Explicit alias: in this system workspace_id IS the tenant id."""
        return self.workspace_id

    def to_dict(self) -> dict:
        """Convert context to JSON-serializable dict."""
        return {
            "user_id": self.user_id,
            "workspace_id": self.workspace_id,
            "user_email": self.user_email,
            "timestamp": self.timestamp.isoformat(),
            "permissions": [p.value for p in self.permissions],
            "metadata": self.metadata or {},
        }

    def has_permission(self, permission: Permission) -> bool:
        """Check if context has a specific permission."""
        if Permission.ADMIN in self.permissions:
            return True
        return permission in self.permissions

    def can_invoke_agent(self, agent_name: str) -> bool:
        """Check if context can invoke a specific agent."""
        # Map agents to required permissions
        agent_perms = {
            "pulso": Permission.READ_PULSO,
            "centinela": Permission.READ_CENTINELA,
            "radar": Permission.READ_RADAR,
            "audit": Permission.READ_AUDIT,
            "approvals": Permission.READ_APPROVALS,
            "taty": Permission.READ_PULSO,  # Taty is conversational, minimal perms
            "social-ops": Permission.READ_PULSO,
        }

        required_perm = agent_perms.get(agent_name)
        if not required_perm:
            return True  # Unknown agents allowed by default

        return self.has_permission(required_perm)

    def can_approve_draft(self, draft_type: str) -> bool:
        """Check if context can approve a specific draft type."""
        draft_perms = {
            "tax_correction": Permission.WRITE_TAX_CORRECTION,
            "command": Permission.WRITE_COMMAND,
            "sales": Permission.WRITE_APPROVAL,
            "service_desk": Permission.WRITE_APPROVAL,
        }

        required_perm = draft_perms.get(draft_type)
        if not required_perm:
            return False

        return self.has_permission(required_perm)


class AgentContextManager:
    """
    Manages agent contexts during WebSocket sessions.
    """

    def __init__(self):
        # workspace_id -> {user_id -> AgentContext}
        self.contexts: Dict[str, Dict[str, AgentContext]] = {}

    def create_context(
        self,
        user_id: str,
        workspace_id: str,
        user_email: str,
        permissions: Optional[List[str]] = None,
    ) -> AgentContext:
        """Create a new agent context from JWT payload."""

        # Default permissions if none provided
        if permissions is None:
            permissions = [
                Permission.READ_PULSO,
                Permission.READ_CENTINELA,
                Permission.READ_RADAR,
                Permission.READ_APPROVALS,
                Permission.WRITE_APPROVAL,
            ]

        # Convert string permissions to Permission enum
        perm_objects = []
        for perm_str in permissions:
            try:
                perm_objects.append(Permission(perm_str))
            except ValueError:
                logger.warning(f"Unknown permission: {perm_str}")

        context = AgentContext(
            user_id=user_id,
            workspace_id=workspace_id,
            user_email=user_email,
            timestamp=datetime.utcnow(),
            permissions=perm_objects,
        )

        # Store in manager
        if workspace_id not in self.contexts:
            self.contexts[workspace_id] = {}
        self.contexts[workspace_id][user_id] = context

        logger.info(f"Context created: workspace={workspace_id}, user={user_id}")
        return context

    def get_context(self, workspace_id: str, user_id: str) -> Optional[AgentContext]:
        """Retrieve stored context."""
        return self.contexts.get(workspace_id, {}).get(user_id)

    def invalidate_context(self, workspace_id: str, user_id: str) -> None:
        """Invalidate a context (on logout or disconnect)."""
        if workspace_id in self.contexts:
            self.contexts[workspace_id].pop(user_id, None)
            logger.info(f"Context invalidated: workspace={workspace_id}, user={user_id}")

    def cleanup_workspace(self, workspace_id: str) -> None:
        """Cleanup all contexts for a workspace (on app shutdown)."""
        if workspace_id in self.contexts:
            del self.contexts[workspace_id]
            logger.info(f"Workspace cleanup: {workspace_id}")


# Global context manager
context_manager = AgentContextManager()


def build_agent_headers(context: AgentContext) -> dict:
    """
    Build HTTP headers to send to Hermes agents.
    These headers carry the session context.
    """
    return {
        "X-User-ID": context.user_id,
        "X-Workspace-ID": context.workspace_id,
        "X-User-Email": context.user_email,
        "X-Context-Timestamp": context.timestamp.isoformat(),
        "X-Permissions": ",".join([p.value for p in context.permissions]),
    }


def build_agent_payload(context: AgentContext, params: dict) -> dict:
    """
    Build complete payload for agent invocation.
    Includes context + user params.
    """
    return {
        "context": context.to_dict(),
        "params": params,
    }
