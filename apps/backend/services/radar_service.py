"""
Radar Service

Deterministic risk-score calculation (0-100) based on Shadow GL history.
Risk score combines four weighted factors:
1. Discrepancy rate (invoices with discrepancies / total invoices) — 40 pts
2. Amount mismatch severity (sum of mismatches / total invoiced amount) — 30 pts
3. Alert frequency (Centinela alerts this month) — 20 pts
4. Days overdue (max days any invoice is overdue) — 10 pts

All computations are deterministic (same inputs always produce same output).
Zero-division safe: defaults to 0 if no history.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from core.supabase_client import get_supabase, get_service_supabase
from services.financials_service import _compute_caja_real_balance

logger = logging.getLogger(__name__)


def _count_centinela_alerts_this_month(supabase, tenant_id: str, month_start, today) -> int:
    """Count this tenant's SHADOW_GL_DISCREPANCY alerts this month.

    Resolves tenant_id -> tenants.company_id (centinela_alerts is keyed on the
    text company_id, not the tenant uuid) AND filters by tenant_id, so one
    tenant's Radar score is never inflated by another tenant's alerts sharing
    the same company_id (centinela-tenant-scoped-alerts).
    """
    tenant_rows = (
        supabase.table("tenants")
        .select("company_id")
        .eq("id", tenant_id)
        .limit(1)
        .execute()
    )
    if not tenant_rows.data:
        return 0
    company_id = tenant_rows.data[0].get("company_id")
    if not company_id:
        return 0

    alerts_this_month = (
        supabase.table("centinela_alerts")
        .select("id")
        .eq("company_id", company_id)
        .eq("tenant_id", tenant_id)
        .eq("rule_id", "SHADOW_GL_DISCREPANCY")
        .gte("created_at", month_start.isoformat() + "Z")
        .lt("created_at", (today + timedelta(days=1)).isoformat() + "Z")
        .execute()
    )
    return len(alerts_this_month.data)


async def calculate_risk_score(tenant_id: str, date: Optional[str] = None, supabase_client: Optional[Any] = None) -> int:
    """
    Calculate a deterministic risk score (0-100) for a tenant based on Shadow GL history.

    Factors (total 100 points):
    - Discrepancy rate (40 pts): (discrepancies / total_invoices) × 100, capped at 40
    - Amount mismatch (30 pts): (sum_mismatches / total_invoiced_amount) × 100, capped at 30
    - Alert frequency (20 pts): alerts_this_month × 4, capped at 20
    - Days overdue (10 pts): (max_days_overdue / 30) × 10, capped at 10

    Args:
        tenant_id: UUID of the tenant
        date: Optional date for filtering (default: today). Used for alert frequency window.

    Returns:
        int: Risk score from 0 to 100. Returns 0 if no history.
    """
    if date is None:
        date = datetime.utcnow().strftime("%Y-%m-%d")

    supabase = supabase_client if supabase_client is not None else get_supabase()

    # Factor 1: Discrepancy Rate (40 pts)
    # Count total DIAN invoices and invoices with discrepancies
    try:
        dian_docs = (
            supabase.table("dian_xml_documents")
            .select("id, cufe")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        total_invoices = len(dian_docs.data)

        if total_invoices > 0:
            # Get unique CUFEs with discrepancies
            discrepancies = (
                supabase.table("shadow_gl_discrepancies")
                .select("cufe")
                .eq("tenant_id", tenant_id)
                .execute()
            )
            discrepancy_cufes = set(d["cufe"] for d in discrepancies.data)
            discrepancy_count = len(discrepancy_cufes)
            discrepancy_rate = (discrepancy_count / total_invoices) * 100
            factor_discrepancy = min(40, discrepancy_rate)
        else:
            factor_discrepancy = 0.0
    except Exception as e:
        logger.warning(f"Error calculating discrepancy rate for tenant {tenant_id}: {e}")
        factor_discrepancy = 0.0

    # Factor 2: Amount Mismatch Severity (30 pts)
    # Sum of absolute differences in amounts as % of total invoiced
    try:
        discrepancies = (
            supabase.table("shadow_gl_discrepancies")
            .select("variance_minor, status")
            .eq("tenant_id", tenant_id)
            .execute()
        )

        total_variance = sum(
            abs(d["variance_minor"] or 0) for d in discrepancies.data if d["status"] == "amount_mismatch"
        )

        dian_totals = (
            supabase.table("dian_xml_documents")
            .select("total_amount_minor")
            .eq("tenant_id", tenant_id)
            .execute()
        )
        total_invoiced_minor = sum(d["total_amount_minor"] for d in dian_totals.data)

        if total_invoiced_minor > 0:
            mismatch_ratio = (total_variance / total_invoiced_minor) * 100
            factor_mismatch = min(30, mismatch_ratio)
        else:
            factor_mismatch = 0.0
    except Exception as e:
        logger.warning(f"Error calculating amount mismatch for tenant {tenant_id}: {e}")
        factor_mismatch = 0.0

    # Factor 3: Alert Frequency This Month (20 pts)
    # Count Centinela alerts in the current month
    try:
        today = datetime.utcnow()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        alert_count = _count_centinela_alerts_this_month(supabase, tenant_id, month_start, today)
        factor_alerts = min(20, alert_count * 4)
    except Exception as e:
        logger.warning(f"Error calculating alert frequency for tenant {tenant_id}: {e}")
        factor_alerts = 0.0

    # Factor 4: Days Overdue (10 pts)
    # Maximum days any invoice is overdue based on issue_date
    try:
        dian_docs = (
            supabase.table("dian_xml_documents")
            .select("issue_date")
            .eq("tenant_id", tenant_id)
            .execute()
        )

        if dian_docs.data:
            today = datetime.utcnow().date()
            max_days_overdue = 0
            for doc in dian_docs.data:
                if doc.get("issue_date"):
                    issue_date = datetime.fromisoformat(doc["issue_date"]).date()
                    days_diff = (today - issue_date).days
                    max_days_overdue = max(max_days_overdue, days_diff)

            # Assume 30-day payment term: overdue if > 30 days old
            actual_overdue_days = max(0, max_days_overdue - 30)
            factor_overdue = min(10, (actual_overdue_days / 30) * 10) if actual_overdue_days > 0 else 0.0
        else:
            factor_overdue = 0.0
    except Exception as e:
        logger.warning(f"Error calculating days overdue for tenant {tenant_id}: {e}")
        factor_overdue = 0.0

    # Combine all factors, cap at 100
    total_score = min(100, factor_discrepancy + factor_mismatch + factor_alerts + factor_overdue)

    return int(total_score)


async def calculate_cashflow_forecast(tenant_id: str, days: int = 30, supabase_client: Optional[Any] = None) -> int:
    """
    Calculate a 30-day cashflow forecast (minor units) based on historical net flux.

    Net flux = sum(DIAN invoiced) - sum(ERP posted) over the last 30 days.
    Forecast = (net_flux / historical_days) × forecast_days

    Args:
        tenant_id: UUID of the tenant
        days: Forecast horizon in days (default: 30)

    Returns:
        int: Projected net cashflow for the next N days in minor units. >= 0.
             Returns 0 if no historical data.
    """
    supabase = supabase_client if supabase_client is not None else get_supabase()

    try:
        # Calculate lookback window (last 30 days)
        today = datetime.utcnow()
        lookback_start = today - timedelta(days=30)
        lookback_start_str = lookback_start.isoformat() + "Z"
        today_str = today.isoformat() + "Z"

        # Sum DIAN invoiced in lookback window
        dian_rows = (
            supabase.table("dian_xml_documents")
            .select("total_amount_minor")
            .eq("tenant_id", tenant_id)
            .gte("created_at", lookback_start_str)
            .lte("created_at", today_str)
            .execute()
        )
        total_dian_minor = sum(row["total_amount_minor"] for row in dian_rows.data)

        # Sum ERP posted in lookback window
        erp_entries = (
            supabase.table("erp_journal_entries")
            .select("id")
            .eq("tenant_id", tenant_id)
            .gte("created_at", lookback_start_str)
            .lte("created_at", today_str)
            .execute()
        )

        total_erp_minor = 0
        if erp_entries.data:
            erp_lines = (
                supabase.table("erp_journal_lines")
                .select("debit_minor")
                .eq("tenant_id", tenant_id)
                .in_("entry_id", [row["id"] for row in erp_entries.data])
                .execute()
            )
            total_erp_minor = sum(line["debit_minor"] for line in erp_lines.data)

        # Net flux over lookback period
        net_flux_minor = total_dian_minor - total_erp_minor

        # Project to forecast horizon
        # If we have 30 days of history, project for the next N days
        if net_flux_minor > 0:
            # Simple linear projection: (net_flux / 30) × forecast_days
            forecast_minor = int((net_flux_minor / 30) * days)
        else:
            # If net flux is 0 or negative, forecast is 0 (conservative)
            forecast_minor = 0

        return forecast_minor

    except Exception as e:
        logger.warning(f"Error calculating cashflow forecast for tenant {tenant_id}: {e}")
        return 0


async def _weekly_net_flux(
    tenant_id: str,
    week_start: datetime,
    week_end: datetime,
    supabase_client: Optional[Any] = None,
) -> int:
    """
    Net cash flux (minor units) for a single tenant within [week_start, week_end).

    Same query shape as calculate_cashflow_forecast's lookback window (DIAN
    invoiced minus ERP posted), extracted so the 13-week projection can bucket
    it per ISO week without duplicating the Shadow GL access pattern
    (design.md Decision #1).

    Returns 0 if the tenant has no rows in the window.
    """
    supabase = supabase_client if supabase_client is not None else get_supabase()

    week_start_str = week_start.isoformat() + "Z"
    week_end_str = week_end.isoformat() + "Z"

    dian_rows = (
        supabase.table("dian_xml_documents")
        .select("total_amount_minor")
        .eq("tenant_id", tenant_id)
        .gte("created_at", week_start_str)
        .lte("created_at", week_end_str)
        .execute()
    )
    total_dian_minor = sum(row["total_amount_minor"] for row in dian_rows.data)

    erp_entries = (
        supabase.table("erp_journal_entries")
        .select("id")
        .eq("tenant_id", tenant_id)
        .gte("created_at", week_start_str)
        .lte("created_at", week_end_str)
        .execute()
    )

    total_erp_minor = 0
    if erp_entries.data:
        erp_lines = (
            supabase.table("erp_journal_lines")
            .select("debit_minor")
            .eq("tenant_id", tenant_id)
            .in_("entry_id", [row["id"] for row in erp_entries.data])
            .execute()
        )
        total_erp_minor = sum(line["debit_minor"] for line in erp_lines.data)

    return total_dian_minor - total_erp_minor


PROJECTION_LOOKBACK_WEEKS = 12
PROJECTION_MIN_HISTORY_WEEKS = 4
PROJECTION_HORIZON_WEEKS = 13
PROJECTION_HIGH_CONFIDENCE_WEEKS = 4


def _distinct_history_weeks(entry_dates: list[str]) -> int:
    """Count distinct ISO (year, week) buckets among the given entry_date strings."""
    weeks = set()
    for raw_date in entry_dates:
        if not raw_date:
            continue
        parsed = datetime.fromisoformat(raw_date)
        iso_year, iso_week, _ = parsed.isocalendar()
        weeks.add((iso_year, iso_week))
    return len(weeks)


async def calculate_cash_projection_13w(
    tenant_id: str, supabase_client: Optional[Any] = None
) -> dict:
    """
    13-week cash projection (radar-cash-projection-13w).

    Methodology is always "solo_historico": no accounts-receivable/payable
    table with due dates exists in the data model, so the projection is a
    naive linear extrapolation of the tenant's average weekly net flux
    (see design.md Decision #3/#4). Confidence is capped at "media" for the
    first PROJECTION_HIGH_CONFIDENCE_WEEKS weeks and "baja" afterward — never
    "alta", since that would claim grounding this methodology doesn't have.

    Returns a dict with `estado: "sin_historico_suficiente"` and no `semanas`
    if the tenant has fewer than PROJECTION_MIN_HISTORY_WEEKS distinct weeks
    of erp_journal_entries activity in the lookback window (never a
    fabricated projection).
    """
    supabase = supabase_client if supabase_client is not None else get_supabase()

    today = datetime.utcnow()
    lookback_start = today - timedelta(weeks=PROJECTION_LOOKBACK_WEEKS)

    entries = (
        supabase.table("erp_journal_entries")
        .select("entry_date")
        .eq("tenant_id", tenant_id)
        .gte("entry_date", lookback_start.date().isoformat())
        .lte("entry_date", today.date().isoformat())
        .execute()
    )
    history_weeks = _distinct_history_weeks(
        [row.get("entry_date") for row in (entries.data or [])]
    )

    base_response = {
        "client_tenant_id": tenant_id,
        "generado_en": today.isoformat() + "Z",
        "metodologia": "solo_historico",
        "impuesto_futuro_estimado": None,
    }

    if history_weeks < PROJECTION_MIN_HISTORY_WEEKS:
        return {**base_response, "estado": "sin_historico_suficiente", "semanas": None}

    total_net_flux = await _weekly_net_flux(
        tenant_id, lookback_start, today, supabase_client=supabase
    )
    avg_weekly_flux = total_net_flux / PROJECTION_LOOKBACK_WEEKS

    current_balance = _compute_caja_real_balance(supabase, tenant_id, today.date())

    semanas = []
    running_balance = current_balance
    for week_num in range(1, PROJECTION_HORIZON_WEEKS + 1):
        running_balance += avg_weekly_flux
        week_start = today + timedelta(weeks=week_num - 1)
        confianza = "media" if week_num <= PROJECTION_HIGH_CONFIDENCE_WEEKS else "baja"
        semanas.append(
            {
                "semana": week_num,
                "fecha_inicio": week_start.date().isoformat(),
                "caja_proyectada": int(running_balance),
                "confianza": confianza,
            }
        )

    return {**base_response, "estado": "ok", "semanas": semanas}


async def record_module_open(
    tenant_id: str,
    user_id: Optional[str] = None,
    supabase_client: Optional[Any] = None,
) -> None:
    """
    Record that the Radar de Caja module was opened, for the adoption KPI
    (radar-adoption-tracking).

    One row per tenant + user + calendar day: the KPI is weekly, so day-grain
    dedupe keeps the table proportional to real usage instead of to renders.
    `user_id` is None for the staging identity, which resolves to a tenant but
    has no auth.uid().

    Best-effort by contract: this NEVER raises. A telemetry failure — including
    the table not existing because migration 0047 has not been applied yet —
    must not degrade a client's cash projection (design.md Decision #3).

    Uses the **service-role** client, not the anon one. Verified against the real
    database: with the anon key this write evaluates
    `radar_module_opens_tenant_isolation`, which reads `user_tenants`, whose own
    policy chain hits a pre-existing `infinite recursion detected in policy for
    relation "user_roles"` error. Combined with fail-soft that would make tracking
    a permanent silent no-op. The write is not request-controlled: `tenant_id`
    comes from the resolved scope and `user_id` from the verified JWT — this is
    the case `radar_module_opens_service_role` exists for, mirroring how the
    metrics_snapshots nightly job writes for every tenant.
    """
    try:
        supabase = (
            supabase_client if supabase_client is not None else get_service_supabase()
        )
        supabase.table("radar_module_opens").insert(
            {
                "tenant_id": tenant_id,
                "user_id": user_id,
                "opened_on": datetime.utcnow().date().isoformat(),
            }
        ).execute()
    except Exception as e:  # noqa: BLE001 - deliberate: telemetry must never surface
        # 23505 = unique violation: this tenant/user already opened the module
        # today, which is the normal path on every load after the first. Not an
        # error. Plain INSERT is used rather than upsert because ON CONFLICT
        # cannot infer a PARTIAL unique index, and the dedupe indexes are partial
        # (they have to be: Postgres treats NULLs as distinct, so a non-partial
        # index would let the NULL-user staging identity insert unbounded rows
        # per day). Verified against the real database — upsert failed with
        # 42P10 "no unique or exclusion constraint matching the ON CONFLICT
        # specification" and recorded nothing.
        if "23505" in str(e) or "duplicate key" in str(e).lower():
            logger.debug(
                f"record_module_open: already recorded today for tenant {tenant_id}"
            )
        else:
            logger.warning(
                f"record_module_open skipped for tenant {tenant_id}: {type(e).__name__}: {e}"
            )


def _format_cop(minor_units: int) -> str:
    """Format minor units (cents) as a whole-COP thousands-separated string, e.g. $8.200.000 COP."""
    whole_cop = round(minor_units / 100)
    return f"${whole_cop:,.0f} COP".replace(",", ".")


def generate_alerta_narrativa(semanas: Optional[list]) -> str:
    """
    Plain Colombian-Spanish narrative for the 13-week projection (task 5.1).

    Deliberately avoids absolute-certainty language ("vas a tener exactamente
    X") per design.md Risk #1 — the underlying methodology is a naive trend
    extrapolation (solo_historico), not a grounded forecast.
    """
    if not semanas:
        return (
            "Todavía no tenemos suficiente historial para proyectar tu caja "
            "con confianza — vuelve en unas semanas."
        )

    first_week = semanas[0]["caja_proyectada"]
    last_week = semanas[-1]["caja_proyectada"]
    delta = last_week - first_week

    if delta < 0:
        return (
            f"A este ritmo, tu caja podría bajar de {_format_cop(first_week)} "
            f"a {_format_cop(last_week)} en las próximas 13 semanas. Vale la "
            "pena revisar tus gastos con calma."
        )
    return (
        f"Tu caja se mantiene estable: hoy proyectamos {_format_cop(first_week)} "
        f"y en 13 semanas alrededor de {_format_cop(last_week)}. Sigue así."
    )


RISK_REVIEW_THRESHOLD = 80


async def enqueue_risk_review_if_critical(tenant_id: str) -> Optional[str]:
    """
    If risk_score >= 80, enqueue a risk_review approval_queue entry.
    If a pending risk_review entry already exists for this tenant, skip (no duplicate).

    Args:
        tenant_id: UUID of the tenant

    Returns:
        str: ID of the created approval_queue entry, or None if no entry created.
    """
    supabase = get_supabase()

    try:
        # Calculate current risk score
        score = await calculate_risk_score(tenant_id)

        # Check if score is critical
        if score < RISK_REVIEW_THRESHOLD:
            logger.info(f"Risk score {score} below threshold {RISK_REVIEW_THRESHOLD} for tenant {tenant_id}, no HITL triggered")
            return None

        # Check if a pending risk_review entry already exists
        existing = (
            supabase.table("approval_queue")
            .select("id")
            .eq("draft_type", "risk_review")
            .eq("status", "pending")
            .execute()
        )

        if existing.data:
            logger.info(f"Pending risk_review already exists for tenant {tenant_id}, skipping duplicate")
            return None

        # Calculate cashflow forecast
        forecast = await calculate_cashflow_forecast(tenant_id)

        # Create risk_review approval_queue entry
        payload = {
            "risk_score": score,
            "forecast_30d_minor": forecast,
            "tenant_id": tenant_id,
            "threshold": RISK_REVIEW_THRESHOLD,
        }

        entry = supabase.table("approval_queue").insert(
            {
                "id": str(uuid.uuid4()),
                "draft_id": f"risk-review-{tenant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "draft_type": "risk_review",
                "payload": payload,
                "status": "pending",
                "reason": f"Risk score {score} exceeds threshold {RISK_REVIEW_THRESHOLD}",
                "vectorization_status": "pending",
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        ).execute()

        created_id = entry.data[0]["id"] if entry.data else None
        logger.info(f"Created risk_review approval_queue entry {created_id} for tenant {tenant_id} (score {score})")
        return created_id

    except Exception as e:
        logger.error(f"Error enqueueing risk_review for tenant {tenant_id}: {e}")
        return None
