from fastapi import APIRouter, HTTPException, Depends
from datetime import date
from typing import Optional
from services.financials_service import compute_pulso_daily_snapshot, compute_liquidity_bridge
from core.supabase_client import get_supabase
from core.deps import get_current_user, _STAGING_USER
from core.plan_features import has_feature

router = APIRouter()


async def _resolve_cliente_cero_tenant_id() -> str:
    """Resolve the Cliente Cero tenant ID from Supabase.

    Kept as a module-level, monkeypatchable function so
    `tests/test_financials_endpoint_tenant_scoping.py` can patch this exact attribute.
    """
    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


async def _resolve_caller_tenant_id(user: dict) -> Optional[str]:
    """Resolve which tenant the caller should see data for.

    Local to this module (not `core.tenant_context`) — deliberately kept separate from
    the canonical `resolve_request_tenant_scope()` that the 6 agent-facing endpoint files
    use (see `core/tenant_context.py`'s module docstring, agent-endpoints-real-tenant-
    filtering Stage 4): `/financials` predates and was never in scope for that
    consolidation, and this policy is a strict 3-branch subset (no operator/all_tenants
    case) of what `resolve_request_tenant_scope` offers, so duplicating it here — rather
    than importing the canonical resolver and ignoring half its contract — keeps this
    file's existing, already-reviewed behavior byte-identical instead of risking a
    behavior change to a shipped, tenant-security-relevant endpoint.

    1. Authenticated caller with a resolved tenant (`user["resolved_tenant_id"]`) -> that
       caller's own tenant.
    2. Unauthenticated/local-dev caller (`AUTH_ENFORCED=False`, no token — the permissive
       staging identity, `core.deps._STAGING_USER`) -> Cliente Cero.
    3. Authenticated caller whose tenant did NOT resolve -> `None`. Callers MUST treat
       `None` as "render an empty/zeroed response" — NEVER fall back to Cliente Cero here,
       that would leak Contexia's own financials to an unrelated logged-in client.
    """
    resolved_tenant_id = user.get("resolved_tenant_id")
    if resolved_tenant_id:
        return resolved_tenant_id

    if user.get("id") == _STAGING_USER["id"]:
        return await _resolve_cliente_cero_tenant_id()

    return None


async def _resolve_plan_tier(tenant_id: str) -> Optional[str]:
    """Look up `tenants.plan_tier` for a resolved tenant (migration 0043).

    A new query, deliberately not reusing `_resolve_caller_tenant_id`'s Cliente Cero lookup
    (which selects only `id`) — see plan-tier-feature-gating/design.md, "Backend endpoint
    insertion points": no existing query in this module already has `plan_tier` in hand.
    """
    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("plan_tier")
        .eq("id", tenant_id)
        .maybe_single()
        .execute()
    )
    return result.data["plan_tier"] if result and result.data else None


def _empty_snapshot() -> dict:
    """Zeroed snapshot for an authenticated caller with no resolved tenant —
    NEVER Cliente Cero, so an unwired client login can't see Contexia's own data."""
    return {
        "caja_real": 0,
        "dinero_disponible": 0,
        "ventas_ayer": 0,
        "gastos_ayer": 0,
        "status": "empty",
    }


def _not_in_plan_snapshot() -> dict:
    """Zeroed snapshot for a resolved tenant whose plan_tier lacks the pulso_diario
    feature (plan-tier-feature-gating) — distinct `status` from `_empty_snapshot`'s
    `"empty"` so the PWA can tell "no data yet" apart from "not in your plan"."""
    return {
        "caja_real": 0,
        "dinero_disponible": 0,
        "ventas_ayer": 0,
        "gastos_ayer": 0,
        "status": "not_in_plan",
    }


def _empty_liquidity_bridge() -> dict:
    """Zeroed liquidity bridge for an authenticated caller with no resolved tenant —
    same non-leak rule as `_empty_snapshot` (pwa-tenant-aware-screens Stage 3)."""
    today = date.today()
    return {
        "initial_balance": 0,
        "inflows": 0,
        "outflows": 0,
        "final_balance": 0,
        "period": f"{today.year:04d}-{today.month:02d}",
        "status": "empty",
    }


def _not_in_plan_liquidity_bridge() -> dict:
    """Zeroed liquidity bridge for a resolved tenant whose plan_tier lacks the
    liquidity_bridge feature (plan-tier-feature-gating) — same non-leak shape as
    `_empty_liquidity_bridge`, distinct `status`."""
    today = date.today()
    return {
        "initial_balance": 0,
        "inflows": 0,
        "outflows": 0,
        "final_balance": 0,
        "period": f"{today.year:04d}-{today.month:02d}",
        "status": "not_in_plan",
    }


@router.get("")
async def get_financials(user: dict = Depends(get_current_user)):
    """
    GET /api/v1/financials

    Returns the "Pulso diario" snapshot from Shadow GL aggregation: cumulative
    Caja Real as of today, plus ventas/gastos for yesterday specifically (not a
    monthly aggregate) — daily granularity is the product's core promise.

    Tenant resolution (per-tenant-client-access; see `_resolve_caller_tenant_id` above):
    - Authenticated caller with a resolved tenant (per-client login, wired via
      user_tenants) -> that caller's own tenant. This is what makes each B2B
      client see THEIR OWN Caja Real, not Contexia's.
    - Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token — the
      permissive staging identity) -> Cliente Cero, preserving the existing
      Contexia overview / local dev behavior.
    - Authenticated caller whose tenant did NOT resolve (e.g. membership not
      yet wired) -> an empty snapshot. Never falls back to Cliente Cero here —
      that would leak Contexia's financials to an unrelated logged-in client.

    Response (all amounts in COP minor units — cents):
    {
        "caja_real": 352000000,
        "dinero_disponible": 352000000,
        "ventas_ayer": 80000000,
        "gastos_ayer": 12000000,
        "status": "healthy"
    }
    """
    try:
        tenant_id = await _resolve_caller_tenant_id(user)
        if tenant_id is None:
            return _empty_snapshot()

        plan_tier = await _resolve_plan_tier(tenant_id)
        if not has_feature(plan_tier, "pulso_diario"):
            return _not_in_plan_snapshot()

        today = date.today()
        snapshot = compute_pulso_daily_snapshot(tenant_id, today)
        return snapshot
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing financial snapshot: {str(e)}"
        )


@router.get("/liquidity-bridge")
async def get_liquidity_bridge(user: dict = Depends(get_current_user)):
    """
    GET /api/v1/financials/liquidity-bridge

    Returns the monthly liquidity bridge derived from account 1110 (Bancos) in the Shadow
    GL: cumulative balance the day before the current month starts, plus this month's
    inflows/outflows, plus the resulting final balance (pwa-tenant-aware-screens Stage 3 /
    design.md D3, spec `pulso-financials-api`).

    Tenant resolution: same policy as `GET /api/v1/financials` (`_resolve_caller_tenant_id`
    above) — own resolved tenant, Cliente Cero only for the staging identity, empty for an
    authenticated caller with no resolved tenant.

    Response (all amounts in COP minor units — cents):
    {
        "initial_balance": 500000000,
        "inflows": 200000000,
        "outflows": 80000000,
        "final_balance": 620000000,
        "period": "2026-07",
        "status": "ready"
    }
    """
    try:
        tenant_id = await _resolve_caller_tenant_id(user)
        if tenant_id is None:
            return _empty_liquidity_bridge()

        plan_tier = await _resolve_plan_tier(tenant_id)
        if not has_feature(plan_tier, "liquidity_bridge"):
            return _not_in_plan_liquidity_bridge()

        today = date.today()
        bridge = compute_liquidity_bridge(tenant_id, today.year, today.month)
        return bridge
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error computing liquidity bridge: {str(e)}"
        )
