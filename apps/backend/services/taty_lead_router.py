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

from core.supabase_client import get_service_supabase
from services.crm_service import get_crm_service

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
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "¡Con gusto te ayudo! Cuéntame un poco más de tu situación para saber si te toca "
                "declarar renta este año."
            ),
        }

    if intent == "payment_confirmation":
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "Gracias, aún no puedo confirmar pagos automáticamente — un asesor de Contexia "
                "revisará tu caso y te confirmará en breve."
            ),
        }

    return {
        "intent": intent,
        "confidence": confidence,
        "reply": (
            "No estoy segura de tu pregunta. ¿Quieres saber si te toca declarar renta este año?"
        ),
    }


def generate_wompi_link(lead_id: str, amount_cents: int) -> str:
    """Stub pending the real Wompi integration (Change C, crm-wompi-payment-integration)."""
    raise NotImplementedError(
        "generate_wompi_link is not implemented yet — closed by Change C "
        "(crm-wompi-payment-integration)."
    )


def verify_wompi_transaction(lead_id: str) -> Dict[str, Any]:
    """Stub pending the real Wompi integration (Change C, crm-wompi-payment-integration)."""
    raise NotImplementedError(
        "verify_wompi_transaction is not implemented yet — closed by Change C "
        "(crm-wompi-payment-integration)."
    )
