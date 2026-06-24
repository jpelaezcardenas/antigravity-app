"""
Agent operations audit logging
(change agent-operations-multitenant-security, Slice 4).

Persists every agent invocation to agent_operations table via the service-role
client. Failures are logged and swallowed (best-effort) so they never break the
user-facing agent call.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional
import logging
import uuid

from core.supabase_client import get_service_supabase

logger = logging.getLogger("agent-operations-logger")


class AgentOperationsLogger:
    """Persists agent invocation records to agent_operations table."""

    def __init__(self, client=None) -> None:
        # `client` is injectable for tests; defaults to the lazy service-role client.
        self._client = client

    def _supabase(self):
        return self._client if self._client is not None else get_service_supabase()

    async def record(
        self,
        tenant_id: str,
        agent_name: str,
        user_id: str,
        operation_type: str,
        status: str,  # success | failed | blocked
        duration_ms: int,
        cost: Decimal,
        input_data: Optional[dict] = None,
        output_data: Optional[dict] = None,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Persist an agent operation record to agent_operations.

        Returns True if the insert succeeded, False if it failed (failure is logged
        but not raised — audit is best-effort and never breaks the user call).

        All parameters match agent_operations table schema (migration 0014).
        """
        try:
            row = {
                "tenant_id": tenant_id,
                "agent_name": agent_name,
                "user_id": user_id,
                "operation_type": operation_type,
                "status": status,
                "duration_ms": duration_ms,
                "cost": float(cost),  # DECIMAL(10,6) in Postgres
                "input_data": input_data or {},
                "output_data": output_data or {},
                "error_message": error_message,
            }

            result = self._supabase().table("agent_operations").insert([row]).execute()

            if result.data:
                logger.info(
                    "Recorded agent operation: agent=%s op=%s user=%s tenant=%s status=%s",
                    agent_name,
                    operation_type,
                    user_id,
                    tenant_id,
                    status,
                )
                return True
            else:
                logger.warning(
                    "Agent operation insert returned no data: agent=%s op=%s",
                    agent_name,
                    operation_type,
                )
                return False

        except Exception as exc:
            logger.error(
                "Failed to record agent operation: agent=%s op=%s user=%s tenant=%s error=%s",
                agent_name,
                operation_type,
                user_id,
                tenant_id,
                exc,
            )
            # Fail-closed: error is logged but not raised.
            return False


# Shared instance
agent_operations_logger = AgentOperationsLogger()
