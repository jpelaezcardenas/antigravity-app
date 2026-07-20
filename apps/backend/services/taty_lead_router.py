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

import re
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from config import settings
from agents.secure_llm import get_anonymized_ai_response
from channels.whatsapp import download_whatsapp_media, send_whatsapp_message
from core.constants import UMBRAL_RENTA_COP
from core.supabase_client import get_service_supabase
from services.crm_service import get_crm_service
from services.document_storage_service import upload_tax_document
from services.kb_seeding_service import retrieve_similar
from services.wompi_signature import compute_integrity_signature

KB_FALLBACK_REPLY = (
    "No tengo esa información a la mano en este momento, pero un asesor de Contexia te puede "
    "ayudar con eso."
)
STATIC_UNKNOWN_REPLY = (
    "No estoy segura de tu pregunta. ¿Quieres saber si te toca declarar renta este año?"
)

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

_TOPES_CATEGORY_PATTERNS = (
    ("consignaciones", re.compile(r"consign")),
    ("ingresos", re.compile(r"ingres")),
    ("compras", re.compile(r"compr")),
    ("patrimonio", re.compile(r"patrimonio")),
)
_TOPES_AMOUNT_PATTERN = re.compile(r"(\d[\d.,]*)\s*(millones?|mill|k)?\b")
_TOPES_RENTA_CATEGORIES = ("ingresos", "consignaciones")


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


def _get_lead_phone(lead_id: str) -> Optional[str]:
    """Reads the lead's whatsapp_phone directly from crm_leads (isolated for test patching)."""
    client = get_service_supabase()
    result = (
        client.table("crm_leads").select("whatsapp_phone").eq("id", lead_id).single().execute()
    )
    return (result.data or {}).get("whatsapp_phone")


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
    test patching). Mirrors Change B's seed pattern of one tax-profile row per lead.

    Bug found live during Change I's Stage 11 (2026-07-20): crm_tax_profiles.tenant_id is
    NOT NULL, but this insert never included it — a pre-existing bug from Change D that its
    mocked unit tests never caught. Fixed by reading the lead's tenant_id first."""
    client = get_service_supabase()
    lead_result = client.table("crm_leads").select("tenant_id").eq("id", lead_id).single().execute()
    tenant_id = (lead_result.data or {}).get("tenant_id")
    client.table("crm_tax_profiles").insert({"lead_id": lead_id, "tenant_id": tenant_id}).execute()


def _extract_topes_amount(message: str) -> Optional[Tuple[str, int]]:
    """Extracts a (category, amount_cop) pair from a message that mentions one of the UVT
    topes categories (consignaciones/ingresos/compras/patrimonio) alongside a peso amount
    (taty-persona-fields). Supports plain numbers, a "millones"/"mill" suffix, and a "k"
    (thousands) suffix — the three shapes a WhatsApp lead realistically types. Returns None if no
    category keyword is present, or if a category keyword is present with no adjacent amount."""
    message_lower = message.lower()
    category = next(
        (name for name, pattern in _TOPES_CATEGORY_PATTERNS if pattern.search(message_lower)),
        None,
    )
    if not category:
        return None

    match = _TOPES_AMOUNT_PATTERN.search(message_lower)
    if not match:
        return None

    raw_number = match.group(1).replace(".", "").replace(",", "")
    try:
        number = int(raw_number)
    except ValueError:
        return None

    suffix = match.group(2)
    if suffix and suffix.startswith("mill"):
        amount = number * 1_000_000
    elif suffix == "k":
        amount = number * 1_000
    else:
        amount = number

    return category, amount


def _detect_persona_fields(
    message: str, existing_topes: Optional[Dict[str, int]] = None
) -> Dict[str, Any]:
    """Extracts persona-state fields (es_asalariado, topes, obligado_declarar) detectable from the
    message text. `topes` merges with `existing_topes` (never overwritten wholesale — design.md
    Decision 2). `obligado_declarar` is a preliminary internal signal, not a legally authoritative
    determination (design.md Non-Goals) — computed from the known ingresos/consignaciones amount
    against core.constants.UMBRAL_RENTA_COP whenever topes changes."""
    message_lower = message.lower()
    fields: Dict[str, Any] = {}
    if any(keyword in message_lower for keyword in _ASALARIADO_KEYWORDS):
        fields["es_asalariado"] = True
    elif any(keyword in message_lower for keyword in _INDEPENDIENTE_KEYWORDS):
        fields["es_asalariado"] = False

    topes_result = _extract_topes_amount(message)
    if topes_result:
        category, amount = topes_result
        merged_topes = dict(existing_topes or {})
        merged_topes[category] = amount
        fields["topes"] = merged_topes

        renta_amount = max(merged_topes.get(cat, 0) for cat in _TOPES_RENTA_CATEGORIES)
        if renta_amount:
            fields["obligado_declarar"] = renta_amount >= UMBRAL_RENTA_COP

    return fields


def _classify_fiscal_question(message: str) -> Dict[str, Any]:
    """Reason step 1 of the bounded Reason->Act->Reason loop for Taty's unknown-intent fallback
    (taty-kb-and-react-router, design.md Decision 2). One anonymized, JSON-mode LLM call decides
    whether the message is a fiscal question worth searching the KB for, and if so what to search.
    Never calls the raw (non-anonymized) llm_engine directly — SOSP compliance is mandatory for
    any message that may carry a lead's PII/fiscal specifics."""
    return get_anonymized_ai_response(
        prompt=message,
        system_prompt=(
            "Eres un clasificador. Dado un mensaje de WhatsApp de un lead colombiano, decide si "
            "es una pregunta fiscal/tributaria (sobre declarar renta, DIAN, impuestos, etc.). "
            "Responde solo JSON: {\"is_fiscal_question\": bool, \"search_query\": string}."
        ),
        response_format="json",
        required_keys={"is_fiscal_question", "search_query"},
    )


def _synthesize_kb_reply(message: str, chunks: list) -> str:
    """Reason step 2 of the bounded loop: synthesizes a reply grounded strictly in the retrieved
    KB chunks (never called when zero chunks were retrieved — design.md Decision 2, to avoid
    ungrounded hallucination)."""
    context = "\n\n".join(chunk.get("content", "") for chunk in chunks)
    return get_anonymized_ai_response(
        prompt=message,
        system_prompt=(
            "Eres Taty, la asistente fiscal de Contexia. Responde la pregunta del lead usando "
            "SOLO la siguiente información de referencia. Sé breve y clara.\n\n"
            f"Información de referencia:\n{context}"
        ),
    )


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

    tax_profile = service.get_tax_profile(lead_id)
    existing_topes = (tax_profile or {}).get("topes") or {}
    persona_fields = _detect_persona_fields(message, existing_topes=existing_topes)
    if persona_fields:
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

    reply = STATIC_UNKNOWN_REPLY
    try:
        classification = _classify_fiscal_question(message)
    except Exception:
        classification = {"is_fiscal_question": False, "search_query": ""}

    if classification.get("is_fiscal_question"):
        chunks = retrieve_similar(classification.get("search_query", ""), "__global__", top_k=3)
        if chunks:
            reply = _synthesize_kb_reply(message, chunks)
        else:
            reply = KB_FALLBACK_REPLY

    return {
        "intent": intent,
        "confidence": confidence,
        "reply": reply,
    }


RUT_REQUEST_MESSAGE = "Por favor envíame una foto o PDF de tu RUT para continuar con tu declaración."
EXTRACTOS_REQUEST_MESSAGE = (
    "¡Gracias! Ahora envíame tus extractos bancarios (PDF o foto) para terminar de armar tu carpeta."
)


async def route_lead_document(lead_id: str, media_id: str, mime_type: str) -> Dict[str, Any]:
    """Handles an incoming WhatsApp document/image for a lead (taty-document-collection,
    Change I). Only processes documents once the lead has reached LISTOS_CONTADORA (i.e. a human
    has already approved the payment at the POR_APROBAR HITL gate via CrmService.approve_payment)
    — a document arriving earlier is acknowledged but not stored as RUT/extractos, so this flow
    can never act ahead of that gate.

    Sequential collection (design.md Decision 4): the RUT is whatever arrives first
    (rut_status != 'collected'); once collected, the next document is treated as extractos.
    Reuses the live 'pending'/'requested'/'collected' status vocabulary (the DB CHECK constraint
    only allows these three, extended from the original 'pending'/'collected' pair during Stage 8
    DB verification).

    Returns {"processed": bool}.
    """
    current_stage = _get_lead_stage(lead_id)
    if current_stage != "LISTOS_CONTADORA":
        return {"processed": False}

    service = get_crm_service()
    tax_profile = service.get_tax_profile(lead_id)
    rut_status = tax_profile.get("rut_status")
    extractos_status = tax_profile.get("extractos_status")

    if rut_status != "collected":
        document_type = "rut"
    elif extractos_status != "collected":
        document_type = "extractos"
    else:
        return {"processed": False}

    downloaded = await download_whatsapp_media(media_id)
    if not downloaded:
        return {"processed": False}

    storage_path = upload_tax_document(
        lead_id=lead_id,
        document_type=document_type,
        file_bytes=downloaded["content"],
        mime_type=downloaded.get("mime_type") or mime_type,
    )

    patch = {
        f"{document_type}_status": "collected",
        f"{document_type}_storage_path": storage_path,
    }
    if document_type == "rut":
        patch["extractos_status"] = "requested"

    service.update_tax_profile(lead_id, patch)

    if document_type == "rut":
        phone = _get_lead_phone(lead_id)
        if phone:
            await send_whatsapp_message(phone, EXTRACTOS_REQUEST_MESSAGE)

    return {"processed": True}


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
