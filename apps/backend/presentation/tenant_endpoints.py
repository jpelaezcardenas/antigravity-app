"""GET /api/v1/tenant/me (plan-tier-feature-gating).

Lets the caller retrieve their own tenant's identity and plan tier, so the PWA's Config page
can stop hardcoding "Plan Starter · Activo". Unlike financials_endpoints.py's legacy local
resolver, this is a brand-new endpoint with no prior reviewed behavior to preserve, so it uses
the canonical `resolve_request_tenant_scope` directly (design.md D5).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from core.deps import get_current_user
from core.supabase_client import get_supabase
from core.tenant_context import resolve_request_tenant_scope

router = APIRouter()


class TenantMeResponse(BaseModel):
    legal_name: Optional[str] = None
    plan_tier: Optional[str] = None
    status: Optional[str] = None


def _empty_tenant_me_response() -> TenantMeResponse:
    """Explicit-empty response for an unresolved tenant — NEVER Cliente Cero's identity,
    mirroring financials_endpoints.py's `_empty_snapshot()` pattern."""
    return TenantMeResponse(legal_name=None, plan_tier=None, status="empty")


@router.get(
    "/me",
    response_model=TenantMeResponse,
    summary="Get the authenticated caller's own tenant identity and plan tier",
)
async def get_tenant_me(user: dict = Depends(get_current_user)) -> TenantMeResponse:
    """
    GET /api/v1/tenant/me

    Tenant resolution: same 3-way policy as every other canonical-resolver endpoint
    (own resolved tenant; Cliente Cero only for the staging identity; empty for an
    authenticated caller with no resolved tenant — never Cliente Cero's identity leaking
    to an unrelated logged-in client).
    """
    supabase = get_supabase()
    scope = resolve_request_tenant_scope(user, supabase)
    tenant_id = scope.tenant_id if scope else None
    if tenant_id is None:
        return _empty_tenant_me_response()

    result = (
        supabase.table("tenants")
        .select("legal_name, plan_tier")
        .eq("id", tenant_id)
        .maybe_single()
        .execute()
    )
    if not result or not result.data:
        return _empty_tenant_me_response()

    return TenantMeResponse(
        legal_name=result.data.get("legal_name"),
        plan_tier=result.data.get("plan_tier"),
    )
