"""Shared tenant-resolution helper.

Extracted from services/operator_task_service.py (hermes-manus-execution-bridge, Change F) so
other write paths (approval_queue_service, centinela_service) can stamp the real Cliente Cero
tenant_id at write time instead of relying on column defaults — see
hermes-multi-tenant-wrapper/tasks.md, Ground Truth Correction #3.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from core.deps import _STAGING_USER


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


@dataclass(frozen=True)
class TenantScope:
    """The tenant scope a resolved caller is entitled to see/write.

    `all_tenants=True` means the caller is a Contexia operator (their own membership
    resolves to Cliente Cero) and may see/act across every tenant; `tenant_id` still
    carries Cliente Cero's own id for cases that need a concrete value (e.g. stamping
    a new row). `all_tenants=False` means the caller is a normal B2B client scoped
    strictly to `tenant_id`.
    """

    tenant_id: str
    all_tenants: bool = False


def resolve_request_tenant_scope(user: dict, client) -> Optional[TenantScope]:
    """Resolve the tenant scope for an authenticated (or staging) caller.

    Mirrors `financials_endpoints.py`'s three-way policy, plus a 4th outcome for the
    admin/operator case that callers like the approval queue need (see
    `openspec/changes/approval-queue-tenant-scoping/design.md`):

    1. Caller's own `resolved_tenant_id` equals the real Cliente Cero tenant id ->
       operator scope (`all_tenants=True`).
    2. Caller's own `resolved_tenant_id` is set (and not Cliente Cero) -> scoped to
       that tenant only (`all_tenants=False`).
    3. Caller is the staging identity (only reachable when auth is not enforced and no
       token was supplied) -> Cliente Cero, `all_tenants=True` (preserves today's
       local-dev/demo behavior).
    4. Otherwise (authenticated, no resolved tenant) -> `None`. Callers must never fall
       back to Cliente Cero in this case — endpoints treat `None` as "no queue access".
    """
    cliente_cero_id = resolve_cliente_cero_tenant_id(client)
    resolved = user.get("resolved_tenant_id")

    if resolved and cliente_cero_id and resolved == cliente_cero_id:
        return TenantScope(tenant_id=cliente_cero_id, all_tenants=True)
    if resolved:
        return TenantScope(tenant_id=resolved, all_tenants=False)
    if user.get("id") == _STAGING_USER["id"] and cliente_cero_id:
        return TenantScope(tenant_id=cliente_cero_id, all_tenants=True)
    return None


def tenant_exists(client, tenant_id: str) -> bool:
    """True iff a `tenants` row with this id exists.

    Added for hermes-task-queue-tenant-scoping (additive only — does not modify
    resolve_cliente_cero_tenant_id above, owned by the concurrently active
    hermes-multi-tenant-wrapper change). Uses `.maybe_single()` (not `.single()`) so a 0-row
    result returns None instead of raising PGRST116.
    """
    result = client.table("tenants").select("id").eq("id", tenant_id).maybe_single().execute()
    return bool(result and result.data)
