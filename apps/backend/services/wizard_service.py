"""
Wizard de Auditoría Sombra — onboarding gratis 15 minutos.

Toma datos mínimos del prospecto, infiere un perfil financiero sintético
basado en sector/régimen/ingresos, corre Centinela + Analyst, y devuelve
un reporte ejecutivo accionable. Es el principal hook de adquisición GTM
(Nodos Contexia → wizard → trial).

Multi-cliente desde día 1: el `company_id` se deriva determinísticamente
del NIT (sin guiones) → reusable para cualquier prospecto colombiano.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional
import logging
import re

from services.centinela_service import get_centinela_service
from services.crm_service import CrmService
from core.constants import UMBRAL_RENTA_COP, UMBRAL_PATRIMONIO_COP
from agents.agent_6_analyst import AnalystAgent

logger = logging.getLogger(__name__)


# Perfiles base por sector — heurística MVP, post-MVP viene de DIAN benchmark
SECTOR_PROFILES = {
    "Servicios Digitales": {
        "gross_margin_percent": 55,
        "service_share": 0.85,
        "retention_compliance": 0.4,
    },
    "Comercio": {
        "gross_margin_percent": 28,
        "service_share": 0.10,
        "retention_compliance": 0.7,
    },
    "Importaciones": {
        "gross_margin_percent": 22,
        "service_share": 0.05,
        "retention_compliance": 0.5,
    },
    "Restaurantes": {
        "gross_margin_percent": 35,
        "service_share": 0.20,
        "retention_compliance": 0.3,
    },
    "Construcción": {
        "gross_margin_percent": 18,
        "service_share": 0.30,
        "retention_compliance": 0.5,
    },
}

DEFAULT_SECTOR_PROFILE = SECTOR_PROFILES["Servicios Digitales"]


def derive_company_id(nit: str) -> str:
    """Slug determinístico desde el NIT — `900123456-1` → `ctx-900123456`."""
    digits = re.sub(r"[^0-9]", "", nit)
    # Drop verification digit (last char if length > 9)
    base = digits[:-1] if len(digits) > 9 else digits
    return f"ctx-{base or 'unknown'}"


def build_synthetic_profile(
    sector: str,
    regime: str,
    monthly_revenue_cop: float,
) -> Dict:
    """
    Construye un perfil financiero realista a partir de inputs mínimos.

    El objetivo NO es predecir cifras reales — es generar un perfil sobre
    el cual Centinela pueda razonar y revelar riesgos típicos del sector.
    El prospecto valida/corrige en el siguiente paso del wizard.
    """
    profile_base = SECTOR_PROFILES.get(sector, DEFAULT_SECTOR_PROFILE)
    annual_revenue = monthly_revenue_cop * 12
    service_revenue = annual_revenue * profile_base["service_share"]
    expected_retention = service_revenue * 0.03  # 3% Régimen Común
    retention_paid = expected_retention * profile_base["retention_compliance"]

    # Cálculos de balance heurísticos (proporciones típicas PyME)
    total_assets = annual_revenue * 0.45
    total_liabilities = total_assets * 0.40
    total_equity = total_assets - total_liabilities
    accounts_receivable = annual_revenue * 0.12
    allowance = accounts_receivable * 0.02  # subprovisionado a propósito

    return {
        "regime": regime,
        "annual_revenue": annual_revenue,
        "service_revenue": service_revenue,
        "retention_paid": retention_paid,
        "sector": sector,
        "gross_margin_percent": profile_base["gross_margin_percent"],
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "total_equity": total_equity,
        "accounts_receivable": accounts_receivable,
        "allowance_for_doubtful_accounts": allowance,
        "dian_debt": 0,
        "dian_debt_overdue_days": 0,
    }


def build_next_steps(status_level: str, alert_count: int) -> List[str]:
    """Mensajes concretos al prospecto según severidad."""
    base = [
        "Revisa el informe con tu contador habitual.",
        "Programa una sesión con Contexia para profundizar (15 min, gratis).",
    ]
    if status_level in ("alerta", "crítica"):
        return [
            f"Atiende los {min(alert_count, 3)} riesgos críticos en las próximas 72h.",
            "Activa Centinela Pro para monitoreo continuo (evita reincidencia).",
            *base,
        ]
    if status_level == "vigilancia":
        return [
            "Implementa controles preventivos sobre los riesgos identificados.",
            *base,
        ]
    return [
        "Mantén tu disciplina actual — estás en zona sana.",
        "Contexia te avisa antes de que cualquier riesgo escale.",
        *base,
    ]


def run_auditoria_sombra(
    nit: str,
    razon_social: str,
    email: str,
    sector: Optional[str] = None,
    regime: Optional[str] = None,
    monthly_revenue_cop: Optional[float] = None,
    notes: Optional[str] = None,
) -> Dict:
    """
    Orquesta la auditoría sombra completa.

    Flujo: NIT → profile sintético → Centinela rules → Analyst LLM → reporte.
    Todo reusable para cualquier prospecto colombiano sin código nuevo.
    """
    started_at = datetime.now(timezone.utc)

    sector = sector or "Servicios Digitales"
    regime = regime or "Régimen Simple"
    monthly_revenue_cop = monthly_revenue_cop or 80_000_000  # 80M COP default

    company_id = derive_company_id(nit)
    logger.info(
        f"Auditoría sombra start: company_id={company_id}, sector={sector}, regime={regime}"
    )

    # 1. Build synthetic profile
    profile = build_synthetic_profile(sector, regime, monthly_revenue_cop)

    # 2. Centinela evaluation (rules)
    centinela = get_centinela_service()
    alerts = centinela.evaluate(company_id=company_id, data=profile)

    # 3. Analyst synthesis (LLM with fallback)
    analyst = AnalystAgent()
    period = started_at.strftime("%Y-%m")
    analyst_report = analyst.execute({
        "company_id": company_id,
        "alerts": alerts,
        "metrics": {
            "monthly_revenue_cop": monthly_revenue_cop,
            "sector": sector,
            "regime": regime,
            "annual_revenue_estimate": profile["annual_revenue"],
        },
        "period": period,
    })

    # 4. Compose wizard payload
    duration = (datetime.now(timezone.utc) - started_at).total_seconds()
    status_level = analyst_report.get("status_level", "vigilancia")

    return {
        "company_id": company_id,
        "razon_social": razon_social,
        "email": email,
        "nit": nit,
        "sector": sector,
        "regime": regime,
        "status_level": status_level,
        "executive_summary": analyst_report.get("executive_summary", ""),
        "top_risks": analyst_report.get("top_risks", []),
        "opportunities": analyst_report.get("opportunities", []),
        "alert_count": len(alerts),
        "alerts_preview": [
            {
                "rule_id": a["rule_id"],
                "title": a["title"],
                "severity": a["severity"],
                "recommendation": a.get("recommendation", ""),
            }
            for a in alerts[:3]
        ],
        "next_steps": build_next_steps(status_level, len(alerts)),
        "audit_duration_seconds": round(duration, 2),
        "generated_at": started_at.isoformat(),
        "notes": notes,
    }


def run_renta_diagnostico(
    nombre: str,
    whatsapp: str,
    tipo_ingreso: str,
    ingresos_anuales: int,
    patrimonio: int,
    compras: int,
    consumos_tarjeta: int,
    inversiones: int
) -> dict:
    # 1. Evaluar topes DIAN (Art. 592 ET para año gravable) — importados de core.constants
    # (corregido 2026-08-12: los valores hardcodeados aquí antes no correspondían a ningún año
    # de UVT real — 59.376.800 no es 1.400 UVT de ningún año conocido; el valor correcto,
    # verificado contra Resolución DIAN 000193/2024, es $69.718.600).
    TOPE_INGRESOS = UMBRAL_RENTA_COP
    TOPE_PATRIMONIO = UMBRAL_PATRIMONIO_COP
    TOPE_COMPRAS = UMBRAL_RENTA_COP
    TOPE_CONSIGNACIONES = UMBRAL_RENTA_COP

    es_obligado = (
        ingresos_anuales >= TOPE_INGRESOS or
        patrimonio >= TOPE_PATRIMONIO or
        compras >= TOPE_COMPRAS or
        consumos_tarjeta >= TOPE_COMPRAS or
        inversiones >= TOPE_CONSIGNACIONES
    )

    color = "rojo" if es_obligado else "verde"
    mensaje = "¡Atención! Superaste los topes. Estás obligado a declarar renta en 2026." if es_obligado else "¡Tranquilidad! No estás obligado a declarar renta."
    fecha_corte = "Agosto - Octubre 2026"

    # 2. Guardar lead en Supabase CRM
    # Corrected 2026-08-15 (fix-whatsapp-phone-normalization-dedup): the original direct
    # .insert() used column names that don't exist on crm_leads and a hardcoded, invalid
    # tenant_id — it silently failed on every call (verified live: zero rows in crm_leads ever
    # came from this path). Routed through CrmService.whatsapp_intake, the same normalized,
    # deduped, correctly tenant-scoped path the WhatsApp channel uses, so a quiz submission and
    # a WhatsApp message from the same phone land in one crm_leads row, not two.
    try:
        CrmService().whatsapp_intake(whatsapp, full_name=nombre)
        logger.info(f"Renta inbound lead saved: {whatsapp}")
    except Exception as e:
        logger.error(f"Failed to save renta lead to CRM: {e}")

    return {
        "color": color,
        "mensaje": mensaje,
        "fecha_corte": fecha_corte,
        "obligado": es_obligado
    }
