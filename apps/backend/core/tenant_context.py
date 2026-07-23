"""Shared tenant-resolution helper.

Extracted from services/operator_task_service.py (hermes-manus-execution-bridge, Change F) so
other write paths (approval_queue_service, centinela_service) can stamp the real Cliente Cero
tenant_id at write time instead of relying on column defaults — see
hermes-multi-tenant-wrapper/tasks.md, Ground Truth Correction #3.
"""

from __future__ import annotations

from typing import Optional


def resolve_cliente_cero_tenant_id(client) -> Optional[str]:
    """Look up the real Cliente Cero tenant UUID via the `tenants` table.

    Returns None if no row is flagged `is_cliente_cero` (caller decides whether that's fatal).
    """
    result = client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
    return result.data["id"] if result.data else None


class TenantResolutionError(ValueError):
    """A tenant-scoped read/write path was invoked without an explicit tenant_id.

    Cliente Cero is never an implicit fallback — it must be resolved explicitly
    by the caller (see ARCHITECTURE.md Decisión #13 and its Centinela extension).
    Subclasses ValueError so any existing broad `except ValueError` handler
    upstream keeps working unchanged.
    """


def require_tenant_id(tenant_id: Optional[str], *, context: str) -> str:
    """Return tenant_id if truthy; raise TenantResolutionError naming `context`
    (e.g. 'centinela.save_alerts') otherwise, so failures are traceable to the
    call site instead of silently defaulting to Cliente Cero.
    """
    if not tenant_id:
        raise TenantResolutionError(f"{context}: tenant_id is required and was not provided")
    return tenant_id


def resolve_caller_tenant(user: dict, client) -> Optional[str]:
    """3-branch caller-tenant resolution, reusable by Centinela, Approval Queue,
    and the Hermes queue (see design.md §9 of centinela-tenant-scoped-alerts):

      1. user.get("resolved_tenant_id") truthy -> return it.
      2. user.get("id") == STAGING_USER_ID      -> resolve_cliente_cero_tenant_id(client)
         (EXPLICIT Cliente Cero, only for the no-auth local/staging identity).
      3. authenticated, no resolved tenant      -> None. Caller MUST degrade
         (skip the write / return empty), NEVER fall back to Cliente Cero.
    """
    from core.deps import STAGING_USER_ID

    resolved_tenant_id = user.get("resolved_tenant_id")
    if resolved_tenant_id:
        return resolved_tenant_id

    if user.get("id") == STAGING_USER_ID:
        return resolve_cliente_cero_tenant_id(client)

    return None
