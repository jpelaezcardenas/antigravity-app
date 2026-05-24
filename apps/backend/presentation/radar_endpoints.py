"""
Radar Financiero - REST API endpoints.

Returns three-scenario fiscal projections (pesimista / base / optimista) for
the contexia-app Radar dashboard. MVP: data is computed from per-client
heuristics over current financial state; future: integrate Agent 6 (Analyst)
for richer narrative.
"""

from datetime import date, timedelta
from typing import Dict, List, Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["radar"])

Scenario = Literal["pesimista", "base", "optimista"]


# ---------------------------------------------------------------------------
# Response models — mirror lib/types/contexia.ts on the frontend
# ---------------------------------------------------------------------------

class CashProjection(BaseModel):
    forecast: int
    baselineDate: str
    scenarios: Dict[str, int]


class TaxProvision(BaseModel):
    estimatedMonthly: int
    estimatedQuarterly: int
    notes: str


class StrategicInsight(BaseModel):
    title: str
    description: str
    actionItems: List[str]


class Milestone(BaseModel):
    date: str
    description: str
    impact: Literal["high", "medium", "low"]


class RadarScenarioData(BaseModel):
    cashProjection: CashProjection
    taxProvision: TaxProvision
    strategicInsight: StrategicInsight
    upcomingMilestones: List[Milestone]


class RadarHeader(BaseModel):
    title: str
    subtitle: str


class RadarResponse(BaseModel):
    header: RadarHeader
    scenarios: Dict[Scenario, RadarScenarioData]
    company_id: str
    generated_at: str


# ---------------------------------------------------------------------------
# Heuristic projection (MVP)
# ---------------------------------------------------------------------------

_SCENARIO_MULTIPLIERS = {
    "pesimista": 0.55,
    "base": 1.00,
    "optimista": 1.55,
}

_BASE_PROFILES = {
    # company_id → (base_cash_forecast, base_monthly_tax)
    "ctx-001": (5_200_000, 620_000),
    "ferez-001": (8_500_000, 950_000),
    "martinez-001": (3_200_000, 380_000),
}


def _next_milestone_dates() -> List[Milestone]:
    today = date.today()
    return [
        Milestone(
            date=(today + timedelta(days=15)).isoformat(),
            description="Pago de retención en la fuente",
            impact="high",
        ),
        Milestone(
            date=(today + timedelta(days=37)).isoformat(),
            description="Cierre trimestral",
            impact="medium",
        ),
        Milestone(
            date=(today + timedelta(days=52)).isoformat(),
            description="Presentación renta provisional",
            impact="high",
        ),
    ]


def _build_scenario(
    name: Scenario,
    base_cash: int,
    base_tax: int,
    all_scenarios: Dict[str, int],
) -> RadarScenarioData:
    mult = _SCENARIO_MULTIPLIERS[name]
    forecast = int(base_cash * mult)
    monthly_tax = int(base_tax * mult)

    insights = {
        "pesimista": (
            "Presupuesto ajustado recomendado",
            "En escenario pesimista, mantener reserva de contingencia de $2M mínimo para impuestos y gastos operativos.",
            ["Reducir gastos discrecionales", "Acelerar cobranza a clientes", "Evaluar línea de crédito stand-by"],
        ),
        "base": (
            "Operación normal sostenible",
            "Flujo de caja proyectado cubre obligaciones tributarias y operativas. Sin acciones urgentes requeridas.",
            ["Mantener disciplina de cobranza", "Revisar provisión tributaria mensual", "Evaluar inversiones de bajo riesgo"],
        ),
        "optimista": (
            "Oportunidad de optimización fiscal",
            "Excedente proyectado permite acelerar inversiones deducibles y reducir carga tributaria del próximo periodo.",
            ["Acelerar inversiones deducibles", "Considerar donaciones con beneficio tributario", "Evaluar régimen tributario alternativo"],
        ),
    }
    title, desc, actions = insights[name]

    return RadarScenarioData(
        cashProjection=CashProjection(
            forecast=forecast,
            baselineDate=date.today().isoformat(),
            scenarios=all_scenarios,
        ),
        taxProvision=TaxProvision(
            estimatedMonthly=monthly_tax,
            estimatedQuarterly=monthly_tax * 3,
            notes="Retención por pagar en 15 días. Renta provisional activa.",
        ),
        strategicInsight=StrategicInsight(
            title=title,
            description=desc,
            actionItems=actions,
        ),
        upcomingMilestones=_next_milestone_dates(),
    )


def _compute_radar(company_id: str) -> RadarResponse:
    base_cash, base_tax = _BASE_PROFILES.get(company_id, (4_000_000, 500_000))
    all_scenarios_cash = {
        s: int(base_cash * m) for s, m in _SCENARIO_MULTIPLIERS.items()
    }

    return RadarResponse(
        header=RadarHeader(
            title="Radar Financiero",
            subtitle="Proyecciones de flujo de caja y provisión tributaria en 3 escenarios",
        ),
        scenarios={
            "pesimista": _build_scenario("pesimista", base_cash, base_tax, all_scenarios_cash),
            "base": _build_scenario("base", base_cash, base_tax, all_scenarios_cash),
            "optimista": _build_scenario("optimista", base_cash, base_tax, all_scenarios_cash),
        },
        company_id=company_id,
        generated_at=date.today().isoformat(),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get(
    "/scenarios",
    response_model=RadarResponse,
    summary="Get 3-scenario fiscal projection for a company",
)
async def get_scenarios(
    company_id: str = Query(..., description="Client identifier (e.g., 'ctx-001')"),
) -> RadarResponse:
    try:
        return _compute_radar(company_id)
    except Exception as e:
        logger.error(f"Radar.get_scenarios failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Radar projection failed: {e}")


@router.get(
    "/health",
    summary="Health check for Radar service",
)
async def radar_health():
    return {"status": "ok", "service": "radar", "profiles": list(_BASE_PROFILES.keys())}
