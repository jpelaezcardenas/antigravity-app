"""Core service for the CRM/Ventas B2B retainer cockpit (crm-b2b-retainers-cockpit, Change A).

Supabase-preferred / demo-fallback, mirroring services.social_ops_service. Reads use the
service-role Supabase client because there is no per-request end-user Supabase session in
this backend (see design.md Decision 8) — RLS admin-only is defense-in-depth, application-layer
gating (Vercel edge middleware + CRM_CANONICAL flag) is the live access control.
"""

from __future__ import annotations

import logging
import os
import secrets
import uuid
from copy import deepcopy
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional

from postgrest.exceptions import APIError

from channels.whatsapp import send_whatsapp_message
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


def _normalize_whatsapp_phone(whatsapp_phone: str) -> str:
    """Deterministic phone normalization: strip everything but digits and an optional
    leading '+' (E.164-ish), so "+57 300 123 4567" and "573001234567" match the same
    lead. There is no existing normalization helper in this codebase to reuse."""
    digits = "".join(ch for ch in whatsapp_phone if ch.isdigit())
    has_plus = whatsapp_phone.strip().startswith("+")
    return f"+{digits}" if has_plus else digits


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


def get_funnel_snapshot() -> Dict[str, int]:
    """Current crm_leads count per VALID_LEAD_STAGES stage (sell-machine-telemetry-loop, Change G).
    Reads directly, not via CrmService (no tenant filtering needed for this Cliente Cero-only
    funnel), returning zero for any stage with no leads."""
    client = get_service_supabase()
    result = client.table("crm_leads").select("stage").execute()
    counts = {stage: 0 for stage in VALID_LEAD_STAGES}
    for row in result.data or []:
        stage = row.get("stage")
        if stage in counts:
            counts[stage] += 1
    return counts


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
                    .select(
                        "id, name, status, monthly_fee_cents, email, phone, "
                        "contact_name, provision_status"
                    )
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
                    .select("id, name, status, email, phone, contact_name, provision_status")
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


    def create_b2b_client(
        self,
        name: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        contact_name: Optional[str] = None,
        monthly_fee_cents: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Alta: add a client to the roster with its OWN tenant (per-tenant-client-access),
        so its future Shadow GL data never mixes with Cliente Cero's. If an email is given,
        best-effort provisions a PWA login (never blocks the alta itself on that failure —
        the roster row is the source of truth; a failed login can be retried later)."""
        client = get_service_supabase()
        cliente_cero_id = self._resolve_cliente_cero_tenant_id(client)

        nit = f"SYN-{uuid.uuid4().hex[:12].upper()}"
        tenant_result = (
            client.table("tenants")
            .insert({"nit": nit, "legal_name": name, "is_cliente_cero": False})
            .execute()
        )
        client_tenant_id = tenant_result.data[0]["id"]

        row = {
            "tenant_id": cliente_cero_id,
            "client_tenant_id": client_tenant_id,
            "name": name,
            "status": "activo",
            "email": email,
            "phone": phone,
            "contact_name": contact_name,
            "monthly_fee_cents": monthly_fee_cents,
            "provision_status": "not_provisioned" if email else "pending_email",
        }
        inserted = client.table("b2b_clients").insert(row).execute()
        b2b_client = inserted.data[0]

        if email:
            try:
                self._provision_b2b_client_login(
                    client, b2b_client["id"], client_tenant_id, name, email, nit
                )
                b2b_client["provision_status"] = "provisioned"
            except Exception as exc:  # best-effort — alta itself already succeeded
                logger.warning("CRM alta: login provisioning failed for %r: %s", name, exc)

        return b2b_client

    def _provision_b2b_client_login(
        self, client, b2b_client_id: str, tenant_id: str, name: str, email: str, nit: str
    ) -> str:
        """Creates a Supabase Auth login for a client and wires it to the client's OWN
        tenant. No email is sent — the temporary password is generated but not
        persisted anywhere; distribution is the founder's responsibility (same policy
        as the bulk provisioning migration, 0029)."""
        admin_result = client.auth.admin.create_user(
            {
                "email": email,
                "email_confirm": True,
                "password": secrets.token_urlsafe(12),
                "app_metadata": {"role": "cliente", "roles": ["cliente"]},
            }
        )
        user_id = admin_result.user.id

        client.table("usuarios").upsert(
            {
                "id": user_id,
                "email": email,
                "nombre_empresa": name,
                "nit": nit,
                "plan": "starter",
                "password_hash": secrets.token_hex(32),
            }
        ).execute()
        client.table("user_tenants").insert(
            {"user_id": user_id, "tenant_id": tenant_id, "is_owner": True, "is_active": True}
        ).execute()
        client.table("user_roles").insert(
            {"user_id": user_id, "tenant_id": tenant_id, "role": "viewer"}
        ).execute()
        client.table("b2b_clients").update(
            {"login_user_id": user_id, "provision_status": "provisioned"}
        ).eq("id", b2b_client_id).execute()

        return user_id

    def set_b2b_client_status(self, client_id: str, status: str) -> Dict[str, Any]:
        """Baja/reactivar: flips b2b_clients.status and, in lockstep, activates or
        deactivates the client's login membership (user_tenants.is_active) — a baja
        revokes tenant access without deleting the account or its history."""
        if status not in ("activo", "inactivo"):
            raise ValueError(f"Invalid status: {status!r}. Must be 'activo' or 'inactivo'.")

        client = get_service_supabase()
        result = client.table("b2b_clients").update({"status": status}).eq("id", client_id).execute()
        row = (result.data or [{}])[0]

        client_tenant_id = row.get("client_tenant_id")
        if client_tenant_id:
            client.table("user_tenants").update({"is_active": status == "activo"}).eq(
                "tenant_id", client_tenant_id
            ).execute()

        return row

    def upsert_b2b_payment(self, client_id: str, period: str, amount_cents: int) -> Dict[str, Any]:
        """Pago: upsert one (client, calendar month) row — idempotent, matching the
        uq_b2b_payments_client_period constraint (re-recording the same month corrects it,
        it doesn't duplicate it)."""
        client = get_service_supabase()
        client_row = (
            client.table("b2b_clients").select("tenant_id").eq("id", client_id).single().execute()
        )
        tenant_id = client_row.data["tenant_id"]

        period_first_of_month = date.fromisoformat(period).replace(day=1).isoformat()
        result = (
            client.table("b2b_payments")
            .upsert(
                {
                    "tenant_id": tenant_id,
                    "client_id": client_id,
                    "period": period_first_of_month,
                    "amount_cents": amount_cents,
                },
                on_conflict="client_id,period",
            )
            .execute()
        )
        return (result.data or [{}])[0]

    def update_b2b_client_contact(
        self,
        client_id: str,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        contact_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Edit contact fields captured for the roster (name/phone/contact person).
        Does NOT provision or re-provision a login — that's create_b2b_client's job."""
        client = get_service_supabase()
        patch = {
            k: v
            for k, v in {"email": email, "phone": phone, "contact_name": contact_name}.items()
            if v is not None
        }
        if not patch:
            raise ValueError("No contact fields provided to update.")
        result = client.table("b2b_clients").update(patch).eq("id", client_id).execute()
        return (result.data or [{}])[0]

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

    def whatsapp_intake(self, whatsapp_phone: str) -> Dict[str, Any]:
        """Find-or-create a crm_leads row by WhatsApp phone number (chatwoot-hermes-taty-bridge,
        Task Group 1) — the entry point the Chatwoot bridge calls on every inbound WhatsApp
        message so Taty's conversations always map to a lead. Reuses the Cliente Cero
        tenant-scoping pattern from b2c_pipeline/advance_lead."""
        normalized_phone = _normalize_whatsapp_phone(whatsapp_phone)

        client = get_service_supabase()
        tenant_id = self._resolve_cliente_cero_tenant_id(client)

        existing = (
            client.table("crm_leads")
            .select("id, stage")
            .eq("tenant_id", tenant_id)
            .eq("whatsapp_phone", normalized_phone)
            .maybe_single()
            .execute()
        )
        existing_row = (existing.data if existing else None) or None
        if existing_row:
            return {"lead_id": existing_row["id"], "is_new": False, "stage": existing_row["stage"]}

        inserted = (
            client.table("crm_leads")
            .insert({"tenant_id": tenant_id, "whatsapp_phone": normalized_phone, "stage": "NUEVOS"})
            .execute()
        )
        new_row = (inserted.data or [{}])[0]
        return {"lead_id": new_row["id"], "is_new": True, "stage": "NUEVOS"}

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
        """Returns {} (not an error) when the lead has no tax profile row yet — a valid, common
        state for any lead that hasn't reached CrmService.approve_payment. Bug found live during
        taty-persona-fields' Stage 11 (2026-07-20): .single() raises PGRST116 on 0 rows; this
        pre-existing bug was only exposed once route_lead_message started calling
        get_tax_profile unconditionally on every inbound message rather than only when a persona
        field was detected. Fixed via .maybe_single(), which returns data=None on 0 rows instead
        of raising."""
        client = get_service_supabase()
        result = (
            client.table("crm_tax_profiles")
            .select("*")
            .eq("lead_id", lead_id)
            .maybe_single()
            .execute()
        )
        return (result.data if result else None) or {}

    def update_tax_profile(self, lead_id: str, patch: Dict[str, Any]) -> Dict[str, Any]:
        client = get_service_supabase()
        result = (
            client.table("crm_tax_profiles").update(patch).eq("lead_id", lead_id).execute()
        )
        return (result.data or [{}])[0]

    async def approve_payment(self, lead_id: str, approved_by: str) -> Dict[str, Any]:
        """HITL gate: only valid for a lead currently in POR_APROBAR. Advances the lead to
        LISTOS_CONTADORA, stamps its associated crm_wompi_transactions row APPROVED, and
        proactively triggers Taty's document-collection flow (taty-document-collection, Change I)
        by requesting the RUT via WhatsApp — this is the only trigger point for that flow,
        deliberately synchronous (this repo has no scheduler/cron by design)."""
        client = get_service_supabase()

        lead_result = (
            client.table("crm_leads")
            .select("id, stage, whatsapp_phone, tenant_id")
            .eq("id", lead_id)
            .single()
            .execute()
        )
        lead = lead_result.data or {}
        if lead.get("stage") != "POR_APROBAR":
            raise ValueError(
                f"Lead {lead_id!r} is not in POR_APROBAR stage (current: {lead.get('stage')!r})."
            )

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

        existing_profile = (
            client.table("crm_tax_profiles").select("lead_id").eq("lead_id", lead_id).execute()
        )
        if not (existing_profile.data or []):
            client.table("crm_tax_profiles").insert(
                {"lead_id": lead_id, "tenant_id": lead.get("tenant_id")}
            ).execute()
        client.table("crm_tax_profiles").update({"rut_status": "requested"}).eq(
            "lead_id", lead_id
        ).execute()

        phone = lead.get("whatsapp_phone")
        if phone:
            await send_whatsapp_message(
                phone,
                "¡Gracias por tu pago! Para continuar, envíame una foto o PDF de tu RUT.",
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
        before this raises. Updates (does not insert) the row by `reference`:
        checkout_lead_payment() always creates the PENDING row first, so the
        row is guaranteed to exist by the time a webhook for it arrives.
        UPDATE-by-reference is naturally idempotent on redelivery, and avoids
        the NOT NULL violation an upsert would hit — Postgres validates a
        proposed INSERT row's NOT NULL columns (like tenant_id, absent from
        this payload) even when it ultimately resolves via ON CONFLICT DO
        UPDATE, so plain upsert() fails here (found via a real Wompi sandbox
        webhook during Stage 11 verification).
        """
        if not verify_event_checksum(event, settings.WOMPI_EVENTS_SECRET):
            raise PermissionError("Wompi webhook event signature verification failed")

        transaction = event["data"]["transaction"]
        client = get_service_supabase()

        payload = {
            "wompi_transaction_id": transaction["id"],
            "status": transaction["status"],
            "amount_cents": transaction["amount_in_cents"],
        }
        client.table("crm_wompi_transactions").update(payload).eq(
            "reference", transaction["reference"]
        ).execute()

        return {**payload, "reference": transaction["reference"]}


_crm_service: Optional[CrmService] = None


def get_crm_service() -> CrmService:
    global _crm_service
    if _crm_service is None:
        _crm_service = CrmService()
    return _crm_service
