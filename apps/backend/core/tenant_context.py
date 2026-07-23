"""Shared tenant-resolution helper.

Extracted from services/operator_task_service.py (hermes-manus-execution-bridge, Change F) so
other write paths (approval_queue_service, centinela_service) can stamp the real Cliente Cero
tenant_id at write time instead of relying on column defaults — see
hermes-multi-tenant-wrapper/tasks.md, Ground Truth Correction #3.
"""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

from core.deps import _STAGING_USER


def resolve_cliente_cero_tenant_id(client) -> Optional[str]:
    """Look up the real Cliente Cero tenant UUID via the `tenants` table.

    Returns None if no row is flagged `is_cliente_cero` (caller decides whether that's fatal).
    """
    result = client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
    return result.data["id"] if result.data else None


async def _default_cliente_cero_resolver() -> Optional[str]:
    """Default Cliente Cero resolver, against the shared anon Supabase client."""
    from core.supabase_client import get_supabase  # local import: avoid import cycles

    return resolve_cliente_cero_tenant_id(get_supabase())


async def resolve_caller_tenant_id(
    user: dict,
    cliente_cero_resolver: Optional[Callable[[], Awaitable[Optional[str]]]] = None,
) -> Optional[str]:
    """Resolve which tenant a caller should see data for (pwa-tenant-aware-screens D1).

    Shared policy — same as `financials_endpoints.get_financials` used inline before this
    extraction, now the single source of truth so every new tenant-scoped route (Stage 2
    alerts, Stage 3 liquidity bridge) reuses it instead of copy-pasting the three branches:

    1. Authenticated caller with a resolved tenant (`user["resolved_tenant_id"]`, wired via
       `user_tenants`) -> that caller's own tenant.
    2. Unauthenticated/local-dev caller (`AUTH_ENFORCED=False`, no token — the permissive
       staging identity, `core.deps._STAGING_USER`) -> Cliente Cero.
    3. Authenticated caller whose tenant did NOT resolve (e.g. membership not yet wired) ->
       `None`. Callers MUST treat `None` as "render an empty/zeroed response" — NEVER fall
       back to Cliente Cero here, that would leak Contexia's own financials to an unrelated
       logged-in client.

    `cliente_cero_resolver` is an optional injectable override for branch 2 (defaults to
    `_default_cliente_cero_resolver`). It exists so call sites that already expose their own
    monkeypatchable resolver (e.g. `financials_endpoints._resolve_cliente_cero_tenant_id`, kept
    for backward compatibility with `tests/test_financials_endpoint_tenant_scoping.py`) can pass
    it through without duplicating the resolution logic itself.
    """
    resolved_tenant_id = user.get("resolved_tenant_id")
    if resolved_tenant_id:
        return resolved_tenant_id

    if user.get("id") == _STAGING_USER["id"]:
        resolver = cliente_cero_resolver or _default_cliente_cero_resolver
        return await resolver()

    return None
