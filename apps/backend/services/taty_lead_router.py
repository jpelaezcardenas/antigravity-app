"""Taty's lead-scoped sales/onboarding router (taty-whatsapp-sales-router, Change D).

A NEW, separate module from taty_intent_router.py — that router is tenant-scoped (existing
onboarded businesses asking about their own fiscal status via get_daily_summary(tenant_id) etc.)
and has no notion of a pre-signup crm_leads row. This module reuses the same proven pattern
(deterministic keyword classification, an escalation-style graceful-stub idiom) but operates on
lead identity throughout — see design.md Decision 1 for the full rationale.

generate_wompi_link / verify_wompi_transaction are explicit NotImplementedError stubs pending the
Wompi integration (Change C) — never a fabricated payment confirmation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from config import settings
from core.supabase_client import get_service_supabase
from services.crm_service import get_crm_service
from services.wompi_signature import compute_integrity_signature

WOMPI_WEB_CHECKOUT_BASE_URL = "https://checkout.wompi.co/p/"

SALES_INTEREST_KEYWORDS = (
    "declarar renta",
    "declaracion de renta",
    "declaración de renta",
    "renta natural",
    "me toca declarar",
    "cuanto cuesta",
    "cuánto cuesta",
    "precio",
    "ayuda con mis impuestos",
)
PAYMENT_CONFIRMATION_KEYWORDS = ("ya pague", "ya pagué", "ya hice el pago", "listo el pago")

INTENT_CONFIDENCE_THRESHOLD = 0.6

_ASALARIADO_KEYWORDS = ("soy asalariado", "trabajo asalariado", "tengo un empleo fijo")
_INDEPENDIENTE_KEYWORDS = ("soy independiente", "trabajo por mi cuenta", "soy freelance", "soy freelancer")


def classify_lead_intent(message: str) -> Tuple[str, float]:
    """Deterministic keyword-based lead-intent classification, mirroring the pattern in
    taty_intent_router.py's classify_intent (same style, different keyword sets and intents —
    this module never imports from or modifies that one).

    Returns: (intent, confidence) where intent is one of "sales_interest",
    "payment_confirmation", "unknown".
    """
    message_lower = message.lower()

    if any(keyword in message_lower for keyword in PAYMENT_CONFIRMATION_KEYWORDS):
        return "payment_confirmation", 0.9
    if any(keyword in message_lower for keyword in SALES_INTEREST_KEYWORDS):
        return "sales_interest", 0.8

    return "unknown", 0.0


def _get_lead_stage(lead_id: str) -> Optional[str]:
    """Reads the lead's current stage directly from crm_leads (isolated for test patching, so
    route_lead_message's tests never need live Supabase credentials)."""
    client = get_service_supabase()
    result = client.table("crm_leads").select("stage").eq("id", lead_id).single().execute()
    return (result.data or {}).get("stage")


def _get_latest_transaction(lead_id: str) -> Optional[Dict[str, Any]]:
    """Reads the lead's most recent crm_wompi_transactions row directly (isolated for test
    patching, mirroring _get_lead_stage). This table is kept authoritative by the existing,
    unmodified Wompi webhook handler (CrmService.handle_wompi_webhook) — never queried against
    Wompi's API a second time here."""
    client = get_service_supabase()
    result = (
        client.table("crm_wompi_transactions")
        .select("*")
        .eq("lead_id", lead_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def _build_web_checkout_url(
    public_key: str, currency: str, amount_in_cents: int, reference: str, signature: str
) -> str:
    """Builds a Wompi Web Checkout URL (hosted page) from signed checkout data — the same fields
    CrmService.checkout_lead_payment already computes for the Widget Checkout, reused here as URL
    query params per Wompi's documented Web Checkout format (docs.wompi.co)."""
    params = {
        "public-key": public_key,
        "currency": currency,
        "amount-in-cents": amount_in_cents,
        "reference": reference,
        "signature:integrity": signature,
    }
    return f"{WOMPI_WEB_CHECKOUT_BASE_URL}?{urlencode(params)}"


def _create_empty_tax_profile(lead_id: str) -> None:
    """Creates an empty crm_tax_profiles row for a lead that doesn't have one yet (isolated for
    test patching). Mirrors Change B's seed pattern of one tax-profile row per lead."""
    client = get_service_supabase()
    client.table("crm_tax_profiles").insert({"lead_id": lead_id}).execute()


def _detect_persona_fields(message: str) -> Dict[str, Any]:
    """Extracts persona-state fields (es_asalariado, topes) detectable from the message text."""
    message_lower = message.lower()
    fields: Dict[str, Any] = {}
    if any(keyword in message_lower for keyword in _ASALARIADO_KEYWORDS):
        fields["es_asalariado"] = True
    elif any(keyword in message_lower for keyword in _INDEPENDIENTE_KEYWORDS):
        fields["es_asalariado"] = False
    return fields


def find_or_create_lead(whatsapp_phone: str, full_name: Optional[str] = None) -> str:
    """Finds a crm_leads row by whatsapp_phone, or creates a new NUEVOS lead if none exists.
    whatsapp_phone is the identity/mapping key (Change B's column, confirmed live) — no separate
    whatsapp_chat_mappings table (design.md Decision 2)."""
    client = get_service_supabase()
    existing = (
        client.table("crm_leads")
        .select("id")
        .eq("whatsapp_phone", whatsapp_phone)
        .execute()
    )
    if existing.data:
        return existing.data[0]["id"]

    tenant_result = (
        client.table("tenants").select("id").eq("is_cliente_cero", True).single().execute()
    )
    tenant_id = tenant_result.data["id"]

    created = (
        client.table("crm_leads")
        .insert(
            {
                "tenant_id": tenant_id,
                "whatsapp_phone": whatsapp_phone,
                "full_name": full_name or whatsapp_phone,
                "stage": "NUEVOS",
                "source": "whatsapp",
            }
        )
        .execute()
    )
    return created.data[0]["id"]


def route_lead_message(lead_id: str, message: str) -> Dict[str, Any]:
    """Classify the message and route it against the lead's current state.

    - sales_interest: advances NUEVOS -> PROSPECTOS via the existing, unmodified
      CrmService.advance_lead. A lead already past NUEVOS is left unchanged (design.md
      Decision 6) — this routing never re-advances or regresses a stage.
    - payment_confirmation: returns a graceful "not yet available" reply; never calls the Wompi
      stubs, never touches crm_wompi_transactions.
    - Detected persona fields are persisted via CrmService.update_tax_profile, creating an empty
      tax-profile row first if none exists yet for this lead.

    Returns: {"intent": str, "confidence": float, "reply": str}
    """
    intent, confidence = classify_lead_intent(message)
    service = get_crm_service()
    current_stage = _get_lead_stage(lead_id)

    persona_fields = _detect_persona_fields(message)
    if persona_fields:
        tax_profile = service.get_tax_profile(lead_id)
        if not tax_profile:
            _create_empty_tax_profile(lead_id)
        service.update_tax_profile(lead_id, persona_fields)

    if intent == "sales_interest":
        if current_stage == "NUEVOS":
            service.advance_lead(lead_id, "PROSPECTOS")
        link = generate_wompi_link(lead_id)
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "¡Con gusto te ayudo! Aquí tienes el link para hacer tu pago de Renta Natural "
                f"2026 de forma segura: {link}"
            ),
        }

    if intent == "payment_confirmation":
        transaction = verify_wompi_transaction(lead_id)
        status = transaction.get("status")
        if status == "APPROVED":
            if current_stage != "POR_APROBAR":
                service.advance_lead(lead_id, "POR_APROBAR")
            return {
                "intent": intent,
                "confidence": confidence,
                "reply": (
                    "¡Perfecto! Ya confirmamos tu pago. Un asesor de Contexia revisará tu caso "
                    "en breve para continuar con tu declaración."
                ),
            }
        if status == "PENDING":
            return {
                "intent": intent,
                "confidence": confidence,
                "reply": (
                    "Aún no hemos recibido la confirmación de tu pago. Dame un momento y te "
                    "aviso apenas se confirme."
                ),
            }
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "No tengo ningún pago pendiente registrado a tu nombre. ¿Quieres que te envíe el "
                "link de pago?"
            ),
        }

    return {
        "intent": intent,
        "confidence": confidence,
        "reply": (
            "No estoy segura de tu pregunta. ¿Quieres saber si te toca declarar renta este año?"
        ),
    }


def generate_wompi_link(lead_id: str) -> str:
    """Returns a real Wompi Web Checkout URL for this lead's Renta Natural payment
    (taty-wompi-tools-integration, Change H). Reuses an existing PENDING transaction's reference
    if one exists (design.md Decision 2) rather than creating a duplicate on every message;
    otherwise calls the existing, unmodified CrmService.checkout_lead_payment to create a fresh
    one."""
    latest = _get_latest_transaction(lead_id)

    if latest and latest.get("status") == "PENDING":
        signature = compute_integrity_signature(
            latest["reference"], latest["amount_cents"], latest["currency"],
            settings.WOMPI_INTEGRITY_SECRET,
        )
        return _build_web_checkout_url(
            settings.WOMPI_PUBLIC_KEY, latest["currency"], latest["amount_cents"],
            latest["reference"], signature,
        )

    service = get_crm_service()
    checkout = service.checkout_lead_payment(lead_id)
    return _build_web_checkout_url(
        checkout["public_key"], checkout["currency"], checkout["amount_in_cents"],
        checkout["reference"], checkout["signature"],
    )


def verify_wompi_transaction(lead_id: str) -> Dict[str, Any]:
    """Reports the lead's current Wompi transaction status by reading crm_wompi_transactions
    directly (taty-wompi-tools-integration, Change H) — makes no new outbound call to Wompi's
    API, since the existing webhook handler already keeps this row authoritative."""
    latest = _get_latest_transaction(lead_id)
    if not latest:
        return {"status": None, "wompi_transaction_id": None}
    return {
        "status": latest.get("status"),
        "wompi_transaction_id": latest.get("wompi_transaction_id"),
    }
