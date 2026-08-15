"""Retention/churn risk detection for the B2B roster (retention-loop).

Modeled on centinela_service.py's CentinelaRule pattern (small evaluate()-per-rule classes,
persist-and-read alert history), but kept as a separate module: Centinela's rules evaluate a
single client's own fiscal data, while retention risk needs the whole roster's payment history to
compute each client's own trailing average.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Any, Dict, List, Optional

from core.supabase_client import get_service_supabase
from core.tenant_context import require_tenant_id, resolve_cliente_cero_tenant_id

logger = logging.getLogger(__name__)

_TRAILING_MONTHS = 3
_DROP_THRESHOLD = 0.5  # a payment below 50% of the trailing average counts as a material drop


def _most_recent_complete_month(today: date) -> str:
    """Returns the most recently complete calendar month as 'YYYY-MM-01', e.g. on any day in
    August it returns July's period — the current month's payment may not have landed yet."""
    if today.month == 1:
        return f"{today.year - 1}-12-01"
    return f"{today.year}-{today.month - 1:02d}-01"


def _payments_for(client_id: str, payments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        (p for p in payments if p.get("client_id") == client_id),
        key=lambda p: p["period"],
    )


class MissedPaymentRule:
    rule_id = "missed_payment"
    severity = "warning"

    def evaluate(
        self, client: Dict[str, Any], payments: List[Dict[str, Any]], today: date
    ) -> Optional[Dict[str, Any]]:
        if client.get("status") != "activo":
            return None

        target_period = _most_recent_complete_month(today)
        client_payments = _payments_for(client["id"], payments)
        if any(p["period"] == target_period for p in client_payments):
            return None

        return {
            "rule_id": self.rule_id,
            "severity": self.severity,
            "client_id": client["id"],
            "message": f"Sin pago registrado para {client.get('name', client['id'])} en {target_period}.",
        }


class PaymentDropRule:
    rule_id = "payment_drop"
    severity = "warning"

    def evaluate(
        self, client: Dict[str, Any], payments: List[Dict[str, Any]], today: date
    ) -> Optional[Dict[str, Any]]:
        if client.get("status") != "activo":
            return None

        client_payments = _payments_for(client["id"], payments)
        if len(client_payments) < _TRAILING_MONTHS + 1:
            return None

        trailing = client_payments[-(_TRAILING_MONTHS + 1) : -1]
        latest = client_payments[-1]
        trailing_avg = sum(p["amount_cents"] for p in trailing) / len(trailing)
        if trailing_avg <= 0:
            return None

        if latest["amount_cents"] < trailing_avg * _DROP_THRESHOLD:
            return {
                "rule_id": self.rule_id,
                "severity": self.severity,
                "client_id": client["id"],
                "message": (
                    f"Pago de {client.get('name', client['id'])} en {latest['period']} "
                    f"cayo por debajo del promedio de los ultimos {_TRAILING_MONTHS} meses."
                ),
            }
        return None


class RetentionService:
    def __init__(self) -> None:
        self.rules = [MissedPaymentRule(), PaymentDropRule()]

    def evaluate_roster(
        self, clients: List[Dict[str, Any]], payments: List[Dict[str, Any]], today: date
    ) -> List[Dict[str, Any]]:
        alerts: List[Dict[str, Any]] = []
        for client in clients:
            for rule in self.rules:
                try:
                    alert = rule.evaluate(client, payments, today)
                    if alert:
                        alerts.append(alert)
                except Exception as exc:
                    logger.error("retention_service: rule %s failed: %s", rule.rule_id, exc)
        return alerts

    def save_alerts(self, alerts: List[Dict[str, Any]], tenant_id: Optional[str]) -> List[str]:
        tenant_id = require_tenant_id(tenant_id, context="retention_service.save_alerts")
        if not alerts:
            return []

        supabase = get_service_supabase()
        saved_ids: List[str] = []
        for alert in alerts:
            row = {**alert, "tenant_id": tenant_id}
            result = supabase.table("retention_alerts").insert(row).execute()
            if result.data:
                saved_ids.append(result.data[0]["id"])
        return saved_ids

    def get_alerts(self, tenant_id: Optional[str], limit: int = 50) -> List[Dict[str, Any]]:
        tenant_id = require_tenant_id(tenant_id, context="retention_service.get_alerts")
        supabase = get_service_supabase()
        result = (
            supabase.table("retention_alerts")
            .select("*")
            .eq("tenant_id", tenant_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return result.data or []

    def evaluate_and_persist(self) -> List[Dict[str, Any]]:
        """Orchestration for the API layer: fetch the current B2B roster + full payment
        history from Supabase, evaluate, persist any newly-triggered alerts, and return the
        current alert history. The B2B roster belongs to Cliente Cero (same convention as
        crm_service.py's other B2B methods) — not resolved from the caller's own tenant."""
        supabase = get_service_supabase()
        tenant_id = resolve_cliente_cero_tenant_id(supabase)
        tenant_id = require_tenant_id(tenant_id, context="retention_service.evaluate_and_persist")

        clients = (
            supabase.table("b2b_clients")
            .select("id, name, status")
            .eq("tenant_id", tenant_id)
            .execute()
            .data
            or []
        )
        payments = (
            supabase.table("b2b_payments")
            .select("client_id, period, amount_cents")
            .eq("tenant_id", tenant_id)
            .execute()
            .data
            or []
        )

        existing = self.get_alerts(tenant_id=tenant_id, limit=500)
        existing_keys = {(a["client_id"], a["rule_id"], a["message"]) for a in existing}

        alerts = self.evaluate_roster(clients, payments, today=date.today())
        new_alerts = [
            a for a in alerts if (a["client_id"], a["rule_id"], a["message"]) not in existing_keys
        ]
        if new_alerts:
            self.save_alerts(new_alerts, tenant_id=tenant_id)

        return self.get_alerts(tenant_id=tenant_id)


_service: Optional[RetentionService] = None


def get_retention_service() -> RetentionService:
    global _service
    if _service is None:
        _service = RetentionService()
    return _service
