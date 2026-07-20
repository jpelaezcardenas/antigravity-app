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
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from config import settings
from core.supabase_client import get_service_supabase
from services.wompi_signature import compute_integrity_signature, verify_event_checksum

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

# B2C sell-machine funnel (crm-b2c-sell-machine-cockpit, Change B)
VALID_LEAD_STAGES = ["NUEVOS", "PROSPECTOS", "POR_APROBAR", "LISTOS_CONTADORA"]
_STAGE_LABELS: Dict[str, str] = {
    "NUEVOS": "Nuevos",
    "PROSPECTOS": "Prospectos",
    "POR_APROBAR": "Por Aprobar",
    "LISTOS_CONTADORA": "Listos Contadora",
}

_DEMO_LEADS: List[Dict[str, Any]] = [
    {"id": "demo-lead-1", "full_name": "Lead Demo Nuevos", "stage": "NUEVOS", "score": 10},
    {"id": "demo-lead-2", "full_name": "Lead Demo Prospectos", "stage": "PROSPECTOS", "score": 40},
]

# Renta Natural 2026 filing service price — matches the seed data convention in
# migrations/0023_seed_crm_b2c_leads.sql ($89.000 COP). Wompi payment integration
# (Change C) — see openspec/changes/wompi-payment-integration.
RENTA_NATURAL_PRICE_CENTS = 8_900_000
RENTA_NATURAL_CURRENCY = "COP"


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


    def b2c_pipeline(self) -> Dict[str, Any]:
        """B2C Renta Natural lead funnel, board-shaped (prefers Supabase when configured)."""
        leads: List[Dict[str, Any]] = []
        source = "demo_fallback"
        try:
            if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
                client = get_service_supabase()
                tenant_id = self._resolve_cliente_cero_tenant_id(client)
                result = (
                    client.table("crm_leads")
                    .select("id, full_name, whatsapp_phone, stage, score, last_message")
                    .eq("tenant_id", tenant_id)
                    .order("score", desc=True)
                    .execute()
                )
                leads = result.data or []
                source = "supabase"
        except Exception as exc:
            logger.warning("CRM b2c pipeline: supabase unavailable, using demo fallback: %s", exc)

        if source == "demo_fallback":
            leads = deepcopy(_DEMO_LEADS)

        columns = []
        for stage in VALID_LEAD_STAGES:
            stage_leads = [lead for lead in leads if lead.get("stage") == stage]
            columns.append({"id": stage, "label": _STAGE_LABELS[stage], "leads": stage_leads})

        return {
            "source": source,
            "columns": columns,
            "summary": {"total_leads": len(leads)},
        }

    def advance_lead(self, lead_id: str, stage: str) -> Dict[str, Any]:
        """Advance a lead to a new stage. Raises ValueError for an invalid stage."""
        if stage not in VALID_LEAD_STAGES:
            raise ValueError(f"Invalid stage: {stage!r}. Must be one of {VALID_LEAD_STAGES}.")

        client = get_service_supabase()
        result = (
            client.table("crm_leads").update({"stage": stage}).eq("id", lead_id).execute()
        )
        return (result.data or [{}])[0]

    def get_tax_profile(self, lead_id: str) -> Dict[str, Any]:
        client = get_service_supabase()
        result = (
            client.table("crm_tax_profiles").select("*").eq("lead_id", lead_id).single().execute()
        )
        return result.data or {}

    def update_tax_profile(self, lead_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        client = get_service_supabase()
        result = (
            client.table("crm_tax_profiles").update(patch).eq("lead_id", lead_id).execute()
        )
        return (result.data or [{}])[0]

    def approve_payment(self, lead_id: str, approved_by: str) -> Dict[str, Any]:
        """HITL gate: only valid for a lead currently in POR_APROBAR. Advances the lead to
        LISTOS_CONTADORA and stamps its associated crm_wompi_transactions row APPROVED."""
        client = get_service_supabase()

        lead_result = (
            client.table("crm_leads").select("id, stage").eq("id", lead_id).single().execute()
        )
        lead = lead_result.data or {}
        if lead.get("stage") != "POR_APROBAR":
            raise ValueError(
                f"Lead {lead_id!r} is not in POR_APROBAR stage (current: {lead.get('stage')!r})."
            )

        from datetime import datetime, timezone

        client.table("crm_wompi_transactions").update(
            {
                "status": "APPROVED",
                "approved_by": approved_by,
                "approved_at": datetime.now(timezone.utc).isoformat(),
            }
        ).eq("lead_id", lead_id).execute()

        updated = (
            client.table("crm_leads")
            .update({"stage": "LISTOS_CONTADORA"})
            .eq("id", lead_id)
            .execute()
        )
        return (updated.data or [{}])[0]

    def checkout_lead_payment(self, lead_id: str) -> Dict[str, Any]:
        """Create a signed Wompi checkout for a lead's Renta Natural payment.

        Creates a PENDING crm_wompi_transactions row keyed by a fresh reference
        and returns the signed data the frontend needs to redirect to Wompi's
        hosted checkout. The real transaction status arrives later via the
        Wompi webhook (see webhook handler), matched by this same reference.
        """
        client = get_service_supabase()

        try:
            lead_result = (
                client.table("crm_leads").select("id, tenant_id").eq("id", lead_id).single().execute()
            )
        except APIError as exc:
            # postgrest-py's .single() raises (rather than returning data=None)
            # when zero rows match — that's the "unknown lead" case here.
            raise LookupError(f"Lead {lead_id!r} not found") from exc
        lead = lead_result.data or {}
        if not lead.get("id"):
            raise LookupError(f"Lead {lead_id!r} not found")

        reference = f"{lead_id}-{int(datetime.now(timezone.utc).timestamp())}"
        amount_in_cents = RENTA_NATURAL_PRICE_CENTS
        currency = RENTA_NATURAL_CURRENCY

        client.table("crm_wompi_transactions").insert(
            {
                "tenant_id": lead["tenant_id"],
                "lead_id": lead_id,
                "reference": reference,
                "amount_cents": amount_in_cents,
                "currency": currency,
                "status": "PENDING",
            }
        ).execute()

        signature = compute_integrity_signature(
            reference, amount_in_cents, currency, settings.WOMPI_INTEGRITY_SECRET
        )

        return {
            "public_key": settings.WOMPI_PUBLIC_KEY,
            "currency": currency,
            "amount_in_cents": amount_in_cents,
            "reference": reference,
            "signature": signature,
        }

    def handle_wompi_webhook(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Verify and process a Wompi transaction-status webhook event.

        Raises PermissionError if the event's checksum doesn't match — callers
        MUST translate that into a 401 and must not have written anything
        before this raises. Idempotent: upserts by wompi_transaction_id, which
        has a unique index (migration 0025), so redelivery of the same event
        never creates a duplicate row.
        """
        if not verify_event_checksum(event, settings.WOMPI_EVENTS_SECRET):
            raise PermissionError("Wompi webhook event signature verification failed")

        transaction = event["data"]["transaction"]
        client = get_service_supabase()

        payload = {
            "wompi_transaction_id": transaction["id"],
            "status": transaction["status"],
            "reference": transaction["reference"],
            "amount_cents": transaction["amount_in_cents"],
        }
        client.table("crm_wompi_transactions").upsert(
            payload, on_conflict="reference"
        ).execute()

        return payload


_crm_service: Optional[CrmService] = None


def get_crm_service() -> CrmService:
    global _crm_service
    if _crm_service is None:
        _crm_service = CrmService()
    return _crm_service
