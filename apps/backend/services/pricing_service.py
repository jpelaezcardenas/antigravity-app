"""Pre-quote engine — pricing-quote-engine.

Sizes a tenant's accounting workload from its own Shadow GL so Tatiana (the licensed
accountant behind Entidad A) starts a quote from evidence instead of from zero. It
**suggests** a service band; it never sets a price, and it writes nothing.

Honesty is the design constraint, not a nicety. Two of the inputs a real fee depends on
are structurally absent from this data model, and the engine declares both in its own
payload rather than only in documentation — the precedent set by
`GET /api/v1/radar/proyeccion-caja` (ARCHITECTURE.md, Radar section):

1. **Labour load / payroll does not exist in the schema.** It is roughly half the fee
   criterion. It is always reported in `drivers_faltantes` and never estimated, which is
   why `confianza` is capped at "media" and is never "alta".
2. **Four of the five quantitative filing-obligation criteria, plus the qualitative IVA
   criterion, are unobservable here.** So `supera_umbral_declarante=False` means "the one
   criterion we can see was not crossed", NOT "not obligated to file". The response names
   the criterion it evaluated and lists the ones it did not.

Unit contract (design.md Decision #1): the Shadow GL stores COP **minor units**; the UVT
is stored in **whole pesos**. The single `// 100` conversion lives in `_annualised_revenue_cop`
and nothing downstream of it sees minor units.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Optional

from services.financials_service import _classify_ventas_salidas
from services.uvt_service import cop_to_uvt, get_uvt_for_year

logger = logging.getLogger(__name__)

# --- Window and history -----------------------------------------------------------

LOOKBACK_MONTHS = 12
#: Below this, annualising is fabrication with a decimal point (CLAUDE.md §9, hard rule 1).
MIN_HISTORY_MONTHS = 3
#: At or below this, the extrapolation factor is large enough to force low confidence.
THIN_HISTORY_MAX_MONTHS = 5

# --- Filing-obligation threshold --------------------------------------------------

#: Gross-revenue threshold for the año-gravable filing obligation. Expressed in UVT so it
#: tracks the yearly resolution automatically; the peso value is derived per tax year.
#: The other criteria share this 1.400 UVT figure but are not computable here — see
#: CRITERIOS_NO_EVALUABLES. Patrimonio bruto's separate 4.500 UVT threshold is
#: deliberately NOT defined as a constant, because nothing in this module may compare
#: against it (design.md, Out of scope).
DECLARANT_THRESHOLD_UVT = 1400

CRITERION_EVALUATED = "ingresos_brutos"

#: Named, not summarised: a caller that renders "no supera el umbral" must be able to show
#: exactly what was left unexamined.
CRITERIOS_NO_EVALUABLES = (
    "compras_y_consumos",
    "consignaciones_y_depositos",
    "consumos_tarjeta_credito",
    "patrimonio_bruto",
    "responsabilidad_iva",
)

# --- Band heuristics --------------------------------------------------------------

#: Micro is the documented exception: minimal movement AND no labour load. Revenue below
#: the filing threshold is the observable half; the labour half never is.
MICRO_MAX_UVT = DECLARANT_THRESHOLD_UVT
MICRO_MAX_MONTHLY_LINES = 20

#: Either driver alone qualifies as Complejo — a low-revenue, very high-movement client is
#: still heavy accounting work.
COMPLEJO_MIN_UVT = 5000
COMPLEJO_MIN_MONTHLY_LINES = 200

BAND_MICRO = "micro"
BAND_ESTANDAR = "estandar"
BAND_COMPLEJO = "complejo"

#: The single source of truth for valid service bands, shared by the engine that suggests
#: one and by `CrmService`, which persists the one the accountant actually agreed. Kept in
#: step with migration 0048's `chk_b2b_clients_service_band` CHECK constraint.
SERVICE_BANDS = (BAND_MICRO, BAND_ESTANDAR, BAND_COMPLEJO)

# --- Missing drivers --------------------------------------------------------------

MISSING_DRIVER_PAYROLL = "carga_laboral_nomina"
MISSING_DRIVER_PATRIMONY = "patrimonio_bruto"
MISSING_DRIVER_IVA = "responsabilidad_iva"

#: Always returned, in every state, including the empty one.
DRIVERS_FALTANTES = (
    MISSING_DRIVER_PAYROLL,
    MISSING_DRIVER_PATRIMONY,
    MISSING_DRIVER_IVA,
)

CONFIANZA_MEDIA = "media"
CONFIANZA_BAJA = "baja"

ESTADO_OK = "ok"
ESTADO_SIN_HISTORICO = "sin_historico_suficiente"


def _lookback_start(today: date) -> date:
    """First day of the month LOOKBACK_MONTHS-1 months back, so the window covers exactly
    LOOKBACK_MONTHS calendar months including the current one."""
    months_back = LOOKBACK_MONTHS - 1
    year = today.year + (today.month - 1 - months_back) // 12
    month = (today.month - 1 - months_back) % 12 + 1
    return date(year, month, 1)


def _distinct_months(entry_dates: list[str]) -> int:
    """Count distinct (year, month) buckets among the given entry_date strings."""
    months = set()
    for raw in entry_dates:
        if not raw:
            continue
        parsed = date.fromisoformat(raw[:10])
        months.add((parsed.year, parsed.month))
    return len(months)


def _annualised_revenue_cop(lines: list[dict], months_observed: int) -> int:
    """Gross revenue scaled to twelve months, in WHOLE pesos.

    Revenue classification is delegated to `financials_service._classify_ventas_salidas`
    rather than re-listing account codes 4100/4105 here — the same private-helper reuse
    `radar_service` already does with `_compute_caja_real_balance`, so the two engines
    can never disagree about what counts as revenue.
    """
    revenue_minor, _salidas_minor = _classify_ventas_salidas(lines)
    observed_cop = revenue_minor // 100  # the ONLY minor-units -> whole-COP conversion
    return int(observed_cop * LOOKBACK_MONTHS / months_observed)


def _suggest_band(revenue_uvt: float, movimientos_mes: int) -> str:
    if revenue_uvt >= COMPLEJO_MIN_UVT or movimientos_mes >= COMPLEJO_MIN_MONTHLY_LINES:
        return BAND_COMPLEJO
    if revenue_uvt < MICRO_MAX_UVT and movimientos_mes < MICRO_MAX_MONTHLY_LINES:
        return BAND_MICRO
    return BAND_ESTANDAR


def _confidence(band: str, months_observed: int) -> str:
    """Never "alta". "baja" when the extrapolation is thin, or when the band is micro —
    micro's defining criterion (no labour load) is the one this engine cannot observe."""
    if band == BAND_MICRO or months_observed <= THIN_HISTORY_MAX_MONTHS:
        return CONFIANZA_BAJA
    return CONFIANZA_MEDIA


def compute_pre_quote(
    tenant_id: str,
    tax_year: int,
    supabase_client: Optional[Any] = None,
    today: Optional[date] = None,
) -> dict:
    """Pre-quote for `tenant_id` against `tax_year`'s UVT.

    Read-only: issues SELECTs against the tenant's own Shadow GL and nothing else.

    Raises:
        UvtNotFoundError: if `uvt_values` has no row for `tax_year`. Deliberately
            propagated rather than defaulted — the caller turns it into an explicit
            `uvt_no_disponible` state (design.md Decision #2).
    """
    if supabase_client is not None:
        supabase = supabase_client
    else:  # pragma: no cover - exercised only against a live client
        from core.supabase_client import get_supabase

        supabase = get_supabase()

    today = today or date.today()
    uvt = get_uvt_for_year(tax_year, supabase_client=supabase)

    window_start = _lookback_start(today)

    entries_result = (
        supabase.table("erp_journal_entries")
        .select("id, entry_date")
        .eq("tenant_id", tenant_id)
        .gte("entry_date", window_start.isoformat())
        .lte("entry_date", today.isoformat())
        .execute()
    )
    entries = entries_result.data or []
    months_observed = _distinct_months([row.get("entry_date") for row in entries])

    base = {
        "client_tenant_id": tenant_id,
        "anio_gravable": tax_year,
        "uvt_cop": uvt.value_cop,
        "uvt_resolucion": uvt.resolution,
        "meses_observados": months_observed,
        "criterio_evaluado": CRITERION_EVALUATED,
        "criterios_no_evaluables": list(CRITERIOS_NO_EVALUABLES),
        "drivers_faltantes": list(DRIVERS_FALTANTES),
    }

    if months_observed < MIN_HISTORY_MONTHS:
        return {
            **base,
            "estado": ESTADO_SIN_HISTORICO,
            "ingresos_anualizados_cop": None,
            "ingresos_anualizados_uvt": None,
            "movimientos_mes": None,
            "supera_umbral_declarante": None,
            "umbral_declarante_uvt": DECLARANT_THRESHOLD_UVT,
            "umbral_declarante_cop": DECLARANT_THRESHOLD_UVT * uvt.value_cop,
            "banda_sugerida": None,
            "confianza": CONFIANZA_BAJA,
        }

    lines_result = (
        supabase.table("erp_journal_lines")
        .select("account_code, debit_minor, credit_minor")
        .eq("tenant_id", tenant_id)
        .in_("entry_id", [row["id"] for row in entries])
        .execute()
    )
    lines = lines_result.data or []

    annualised_cop = _annualised_revenue_cop(lines, months_observed)
    annualised_uvt = cop_to_uvt(annualised_cop, uvt.value_cop)
    movimientos_mes = round(len(lines) / months_observed)

    umbral_cop = DECLARANT_THRESHOLD_UVT * uvt.value_cop
    band = _suggest_band(annualised_uvt, movimientos_mes)

    return {
        **base,
        "estado": ESTADO_OK,
        "ingresos_anualizados_cop": annualised_cop,
        "ingresos_anualizados_uvt": annualised_uvt,
        "movimientos_mes": movimientos_mes,
        # True is a real positive signal; False means only that THIS criterion was not
        # crossed — see `criterios_no_evaluables` for what was never examined.
        "supera_umbral_declarante": annualised_cop > umbral_cop,
        "umbral_declarante_uvt": DECLARANT_THRESHOLD_UVT,
        "umbral_declarante_cop": umbral_cop,
        "banda_sugerida": band,
        "confianza": _confidence(band, months_observed),
    }
