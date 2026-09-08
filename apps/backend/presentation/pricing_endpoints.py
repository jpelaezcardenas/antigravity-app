"""Pre-quote endpoint (pricing-quote-engine).

`GET /api/v1/pricing/pre-cotizacion` sizes the authenticated caller's own accounting
workload from their Shadow GL, so Entidad A's professional fee is quoted from evidence
rather than guessed. It **suggests** a band; the licensed accountant sets the price.

Mounted at the clean `/pricing` prefix rather than under `/agents/*` — this is a
per-tenant read surface like `/financials`, `/centinela`, `/radar` and `/tenant`, not an
agent-internal route. It is deliberately NOT part of `crm_endpoints.py`: that router sits
behind the CRM_CANONICAL flag and is scoped to Cliente Cero's operator roster, which is
the wrong tenant semantics for an endpoint that must resolve the *caller's own* tenant.

Not plan-gated, on purpose: Pro Micro and Pro Estándar are the same software product
(what differs is human workload), and the engine's whole point is sizing **freemium**
leads for an upsell conversation. `core/plan_features.py` is untouched by this change.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from core.deps import get_current_user
from core.supabase_client import get_supabase
from core.tenant_context import TenantScope, resolve_request_tenant_scope
from services.pricing_service import (
    CRITERIOS_NO_EVALUABLES,
    CRITERION_EVALUATED,
    DECLARANT_THRESHOLD_UVT,
    DRIVERS_FALTANTES,
    compute_pre_quote,
)
from services.uvt_service import UvtNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter(tags=["pricing"])

ESTADO_UVT_NO_DISPONIBLE = "uvt_no_disponible"


class PreQuoteResponse(BaseModel):
    """Every field a caller needs to judge how much to trust this pre-quote.

    Nullable fields are null in the `sin_historico_suficiente` and `uvt_no_disponible`
    states — never zero-filled, which would read as a real measurement of zero.
    """

    client_tenant_id: str
    anio_gravable: int
    estado: str

    uvt_cop: Optional[int] = None
    uvt_resolucion: Optional[str] = None

    meses_observados: Optional[int] = None
    ingresos_anualizados_cop: Optional[int] = None
    ingresos_anualizados_uvt: Optional[float] = None
    movimientos_mes: Optional[int] = None

    #: True is a real positive signal. False means ONLY that the gross-revenue criterion
    #: was not crossed — see `criterios_no_evaluables` for what was never examined.
    supera_umbral_declarante: Optional[bool] = None
    criterio_evaluado: str = CRITERION_EVALUATED
    criterios_no_evaluables: List[str] = list(CRITERIOS_NO_EVALUABLES)
    umbral_declarante_uvt: int = DECLARANT_THRESHOLD_UVT
    umbral_declarante_cop: Optional[int] = None

    #: A suggestion for the accountant, never a price and never a stored value.
    banda_sugerida: Optional[str] = None
    #: "media" or "baja" — never "alta", because the payroll driver is always missing.
    confianza: str
    drivers_faltantes: List[str] = list(DRIVERS_FALTANTES)


def _default_tax_year(today: Optional[date] = None) -> int:
    """The previous calendar year — the año gravable currently being assessed, whose
    obligation thresholds are expressed in that same year's UVT."""
    return (today or date.today()).year - 1


@router.get(
    "/pre-cotizacion",
    response_model=PreQuoteResponse,
    summary="Workload pre-quote for the authenticated caller's own tenant",
)
async def get_pre_quote(
    anio_gravable: Optional[int] = Query(
        default=None,
        ge=2000,
        le=2100,
        description="Tax year whose UVT and thresholds apply. Defaults to the previous "
        "calendar year (the año gravable currently being assessed).",
    ),
    user: dict = Depends(get_current_user),
) -> PreQuoteResponse:
    """Return a workload pre-quote for the caller's resolved tenant.

    Tenant resolution uses the canonical `resolve_request_tenant_scope()` (Decisión #17)
    — there is no tenant query parameter. An unresolved tenant gets **404**, never a
    fallback to Cliente Cero: a pre-quote is a commercial sizing artifact, so the
    anti-enumeration policy applies rather than the graceful-200 shape
    `/radar/proyeccion-caja` uses for a client reading about their own business
    (design.md Decision #6).

    Strictly read-only — no approval-queue entry, no telemetry, no state change.
    """
    supabase = get_supabase()
    scope: Optional[TenantScope] = resolve_request_tenant_scope(user, supabase)

    if scope is None:
        raise HTTPException(status_code=404, detail="Pre-quote not available")

    # `isinstance`, not `is not None`: FastAPI substitutes the real value per request, but
    # a DIRECT call to this coroutine (the endpoint suite, or any future internal caller)
    # receives the `Query(...)` sentinel object itself. `is not None` would pass that
    # sentinel straight through as the tax year. The Annotated form that avoids this
    # entirely is not usable here — FastAPI 0.104.1 mishandles Annotated query params
    # against the installed Pydantic 2.x ('FieldInfo' object has no attribute 'in_').
    tax_year = anio_gravable if isinstance(anio_gravable, int) else _default_tax_year()

    try:
        result = compute_pre_quote(scope.tenant_id, tax_year, supabase_client=supabase)
    except UvtNotFoundError:
        # Explicit, in-band state. Substituting an adjacent year's UVT would produce a
        # confidently wrong threshold (design.md Decision #2).
        logger.warning("Pre-quote requested for tax year %s with no UVT row", tax_year)
        return PreQuoteResponse(
            client_tenant_id=scope.tenant_id,
            anio_gravable=tax_year,
            estado=ESTADO_UVT_NO_DISPONIBLE,
            confianza="baja",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error(
            "Pre-quote failed for tenant %s (year %s): %s", scope.tenant_id, tax_year, exc,
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Pre-quote calculation failed: {exc}")

    return PreQuoteResponse(**result)
