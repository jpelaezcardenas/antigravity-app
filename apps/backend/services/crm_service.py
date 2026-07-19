"""Core service for the CRM/Ventas B2B retainer cockpit (crm-b2b-retainers-cockpit, Change A).

Supabase-preferred / demo-fallback, mirroring services.social_ops_service. Reads use the
service-role Supabase client because there is no per-request end-user Supabase session in
this backend (see design.md Decision 8) — RLS admin-only is defense-in-depth, application-layer
gating (Vercel edge middleware + CRM_CANONICAL flag) is the live access control.
"""

from __future__ import annotations

import logging
import os
from copy import deepcopy
from datetime import date
from typing import Any, Dict, List, Optional

from core.supabase_client import get_service_supabase

logger = logging.getLogger(__name__)

# Minimal demo-fallback dataset, used only when Supabase is unreachable/unconfigured, so the
# Búnker never renders blank. Shape mirrors the real seeded data (see migrations 0020/0021).
_DEMO_CLIENTS: List[Dict[str, Any]] = [
    {"id": "demo-client-1", "name": "Cliente Demo Uno", "status": "activo"},
    {"id": "demo-client-2", "name": "Cliente Demo Dos", "status": "activo"},
]
_DEMO_PAYMENTS: List[Dict[str, Any]] = [
    {"client_id": "demo-client-1", "period": "2026-01-01", "amount_cents": 100_000_00},
    {"client_id": "demo-client-2", "period": "2026-01-01", "amount_cents": 50_000_00},
]


def _month_periods(from_period: str, to_period: str) -> List[str]:
    """Return a list of first-of-month ISO date strings from from_period to to_period, inclusive."""
    start = date.fromisoformat(from_period).replace(day=1)
    end = date.fromisoformat(to_period).replace(day=1)
    periods = []
    current = start
    while current <= end:
        periods.append(current.isoformat())
        if current.month == 12:
            current = current.replace(year=current.year + 1, month=1)
        else:
            current = current.replace(month=current.month + 1)
    return periods


class CrmService:
    def _resolve_cliente_cero_tenant_id(self, client) -> Optional[str]:
        result = (
            client.table("tenants")
            .select("id")
            .eq("is_cliente_cero", True)
            .single()
            .execute()
        )
        return result.data["id"] if result.data else None

    def list_b2b_clients(self) -> Dict[str, Any]:
        """B2B retainer client roster (prefers Supabase when configured)."""
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
                client = get_service_supabase()
                tenant_id = self._resolve_cliente_cero_tenant_id(client)
                result = (
                    client.table("b2b_clients")
                    .select("id, name, status, monthly_fee_cents")
                    .eq("tenant_id", tenant_id)
                    .order("name")
                    .execute()
                )
                return {"source": "supabase", "items": result.data or []}
        except Exception as exc:
            logger.warning("CRM b2b clients: supabase unavailable, using demo fallback: %s", exc)

        return {"source": "demo_fallback", "items": deepcopy(_DEMO_CLIENTS)}

    def b2b_payments_grid(
        self, from_period: str = "2026-01-01", to_period: str = "2026-06-30"
    ) -> Dict[str, Any]:
        """Server-pivoted B2B payments grid: clients x months, with totals."""
        clients: List[Dict[str, Any]] = []
        payments: List[Dict[str, Any]] = []
        source = "demo_fallback"
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
                client = get_service_supabase()
                tenant_id = self._resolve_cliente_cero_tenant_id(client)
                clients_result = (
                    client.table("b2b_clients")
                    .select("id, name, status")
                    .eq("tenant_id", tenant_id)
                    .order("name")
                    .execute()
                )
                payments_result = (
                    client.table("b2b_payments")
                    .select("client_id, period, amount_cents")
                    .eq("tenant_id", tenant_id)
                    .gte("period", from_period)
                    .lte("period", to_period)
                    .execute()
                )
                clients = clients_result.data or []
                payments = payments_result.data or []
                source = "supabase"
        except Exception as exc:
            logger.warning("CRM b2b payments grid: supabase unavailable, using demo fallback: %s", exc)

        if source == "demo_fallback":
            clients = deepcopy(_DEMO_CLIENTS)
            payments = deepcopy(_DEMO_PAYMENTS)

        periods = _month_periods(from_period, to_period)

        cells: Dict[str, Dict[str, int]] = {c["id"]: {} for c in clients}
        by_client: Dict[str, int] = {c["id"]: 0 for c in clients}
        by_period: Dict[str, int] = {p: 0 for p in periods}
        grand_total = 0

        for payment in payments:
            client_id = payment["client_id"]
            period = payment["period"]
            amount = int(payment.get("amount_cents") or 0)
            if client_id not in cells:
                continue
            cells[client_id][period] = amount
            by_client[client_id] = by_client.get(client_id, 0) + amount
            if period in by_period:
                by_period[period] += amount
            grand_total += amount

        return {
            "source": source,
            "grid": {
                "clients": clients,
                "periods": periods,
                "cells": cells,
            },
            "totals": {
                "grand_total": grand_total,
                "by_period": by_period,
                "by_client": by_client,
            },
        }


_crm_service: Optional[CrmService] = None


def get_crm_service() -> CrmService:
    global _crm_service
    if _crm_service is None:
        _crm_service = CrmService()
    return _crm_service
