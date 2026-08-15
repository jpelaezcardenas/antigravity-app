"""Taty's lead-scoped sales/onboarding router (taty-whatsapp-sales-router, Change D).

A NEW, separate module from taty_intent_router.py — that router is tenant-scoped (existing
onboarded businesses asking about their own fiscal status via get_daily_summary(tenant_id) etc.)
and has no notion of a pre-signup crm_leads row. This module reuses the same proven pattern
(deterministic keyword classification, an escalation-style graceful-stub idiom) but operates on
lead identity throughout — see design.md Decision 1 for the full rationale.

route_lead_message no longer generates reply text itself for unmatched (`unknown`-intent)
messages: it hands off to services.taty_service.TatyAgentService — the same brain Telegram and
the PWA use — via the WhatsApp calling convention (taty-whatsapp-renta-sales-capability). This
file keeps its deterministic side effects (CRM stage advance, Wompi HITL enqueue, persona-field
persistence) as tools that turn invokes, not as gates on what gets said.

generate_wompi_link / verify_wompi_transaction are explicit NotImplementedError stubs pending the
Wompi integration (Change C) — never a fabricated payment confirmation.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode

from config import settings
from channels.whatsapp import download_whatsapp_media, send_whatsapp_message
from core.constants import UMBRAL_RENTA_COP
from core.supabase_client import get_service_supabase
from core.tenant_context import resolve_cliente_cero_tenant_id
from services.crm_service import get_crm_service
from services.document_storage_service import upload_tax_document
from services.taty_service import get_taty_service
from services.wompi_signature import compute_integrity_signature

# Sole remaining static reply: the last-resort fallback when TatyAgentService itself is
# unreachable (tenant unresolved, or ask() raises/errors) — never a substitute for a real answer.
# The two-tier static-reply logic this used to gate (a keyword-classified "is this fiscal?" check,
# a separate zero-chunks fallback) was retired in taty-whatsapp-renta-sales-capability: Taty now
# handles both fiscal and conversational messages herself, grounded via her own KB retrieval.
KB_FALLBACK_REPLY = (
    "No tengo esa información a la mano en este momento, pero un asesor de Contexia te puede "
    "ayudar con eso."
)

# Static, code-verified offer facts a WhatsApp lead's Taty turn is given as context — never
# invented. Documents match RUT_REQUEST_MESSAGE/EXTRACTOS_REQUEST_MESSAGE below (the actual
# document-collection flow). Price is deliberately absent (`precio_confirmado: False`): pricing
# tiers are undefined as of this change (founder decision, 2026-08-11) — see
# TatyAgentService._build_system_prompt, which turns this exact flag into an explicit
# never-invent-a-number instruction.
RENTA_OFFER_CONTEXT: Dict[str, Any] = {
    "documentos_requeridos": ["RUT (foto o PDF)", "extractos bancarios del año (PDF o foto)"],
    "precio_confirmado": False,
}

# The campaign's own landing page (same URL as the click-to-WhatsApp ad's caption, see
# taty-whatsapp-renta-sales-capability tasks.md's image-caption finding). Founder-requested
# (2026-08-12): Taty should link back to it on the first message of a conversation.
RENTA_LANDING_URL = "https://www.contexia.online/landing.html"

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


def lead_exists(lead_id: str) -> bool:
    """Public existence check for a lead id (taty-channel-consolidation).

    The internal reply endpoint uses this to answer 404 without creating anything: find-or-create
    belongs to /crm/leads/whatsapp-intake, which the bridge already calls immediately before.
    Deliberately avoids .single(), which raises on a missing row rather than returning empty.
    """
    client = get_service_supabase()
    result = client.table("crm_leads").select("id").eq("id", lead_id).execute()
    return bool(result.data)


def get_lead_phone(lead_id: str) -> Optional[str]:
    """Reads the lead's whatsapp_phone directly from crm_leads (isolated for test patching)."""
    client = get_service_supabase()
    result = (
        client.table("crm_leads").select("whatsapp_phone").eq("id", lead_id).single().execute()
    )
    return (result.data or {}).get("whatsapp_phone")


def _enqueue_wompi_link_approval(lead_id: str) -> None:
    """Enqueue a human-approval draft instead of generating/sending a real Wompi link directly
    (taty-wompi-link-hitl-gate). A plain sync Supabase insert, not
    ApprovalQueueService.enqueue_draft: that method is async, and route_lead_message stays sync
    deliberately (see design.md Decision 1) — matches this file's existing local-helper
    convention (_get_lead_stage, get_lead_phone, etc.) rather than depending on another service.

    Every approval_queue column this needs already defaults safely except tenant_id/draft_id/
    draft_type/payload, all supplied here. draft_id=lead_id (not a fresh uuid) so the draft is
    tied to something a human reviewer can act on directly.
    """
    client = get_service_supabase()
    lead_result = (
        client.table("crm_leads").select("tenant_id").eq("id", lead_id).single().execute()
    )
    tenant_id = (lead_result.data or {}).get("tenant_id")

    client.table("approval_queue").insert(
        {
            "tenant_id": tenant_id,
            "draft_id": lead_id,
            "draft_type": "wompi_payment_link",
            "payload": {"lead_id": lead_id},
        }
    ).execute()


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


def _build_lead_context(
    current_stage: Optional[str],
    current_persona: Dict[str, Any],
    history: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Assembles the WhatsApp calling-convention context TatyAgentService.ask() expects
    (taty-fiscal-assistant delta spec) from state route_lead_message already has in hand — no
    extra reads beyond what the function already does for its existing CRM side effects.

    `is_first_message` (founder-requested 2026-08-12): empty/None `history` is the direct signal
    that this is the first turn the bridge has ever sent for this conversation — more reliable
    than CRM `lead_stage`, which can stay "NUEVOS" across many messages if the lead hasn't advanced
    through the funnel yet. TatyAgentService turns this into a hard rule: always give the full
    self-introduction (name + company) and the landing link on the first message only, so a
    multi-turn conversation doesn't repeat the same intro on every reply.
    """
    return {
        "lead_stage": current_stage,
        "persona_fields": {
            k: current_persona[k]
            for k in ("es_asalariado", "topes", "obligado_declarar")
            if k in current_persona
        },
        "offer": dict(RENTA_OFFER_CONTEXT),
        "is_first_message": not history,
        "landing_url": RENTA_LANDING_URL,
    }


def find_or_create_lead(whatsapp_phone: str, full_name: Optional[str] = None) -> str:
    """Finds a crm_leads row by whatsapp_phone, or creates a new NUEVOS lead if none exists.
    whatsapp_phone is the identity/mapping key (Change B's column, confirmed live) — no separate
    whatsapp_chat_mappings table (design.md Decision 2).

    Delegates to CrmService.whatsapp_intake (tenant-scoped find-or-create) rather than querying
    Supabase directly — see taty-lead-router-tenant-scoping's design.md Decision 1. Do not
    reintroduce a duplicate, tenant-less crm_leads lookup here."""
    result = get_crm_service().whatsapp_intake(whatsapp_phone, full_name=full_name)
    return result["lead_id"]


def route_lead_message(
    lead_id: str, message: str, history: Optional[List[Dict[str, str]]] = None
) -> Dict[str, Any]:
    """Classify the message and route it against the lead's current state.

    - sales_interest: advances NUEVOS -> PROSPECTOS via the existing, unmodified
      CrmService.advance_lead. A lead already past NUEVOS is left unchanged (design.md
      Decision 6) — this routing never re-advances or regresses a stage.
    - payment_confirmation: returns a graceful "not yet available" reply; never calls the Wompi
      stubs, never touches crm_wompi_transactions.
    - unknown: routed to TatyAgentService (taty-whatsapp-renta-sales-capability) — the same
      shared brain Telegram and the PWA already use, not a second implementation. This function
      no longer generates reply text itself for this branch; it builds the WhatsApp calling
      convention (lead stage, persona fields, offer context) from state already in hand.
    - Detected persona fields are persisted via CrmService.update_tax_profile, creating an empty
      tax-profile row first if none exists yet for this lead.

    `history` (optional, most-recent-last, shape [{"role": "user"|"assistant", "text": "..."}])
    is passed straight through to TatyAgentService for the unknown branch only — the bridge
    supplies it; older callers that omit it get the exact same behavior as before this parameter
    existed.

    Returns: {"intent": str, "confidence": float, "reply": str, "persona_fields": dict,
    "stage": str | None}. persona_fields/stage were added for chatwoot-auto-tagging so the
    bridge can tag Chatwoot contacts/conversations without a second backend call — this
    function already computes both for its own CRM side effects.
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
        # taty-wompi-link-hitl-gate: no real link is generated or sent here. A human must
        # approve the resulting approval_queue draft first (ApprovalQueueService.approve_draft)
        # — see design.md for why this branch used to call generate_wompi_link directly and no
        # longer does.
        _enqueue_wompi_link_approval(lead_id)
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "¡Con gusto te ayudo! Un asesor de Contexia va a validar tu caso y te va a "
                "escribir en un momento para continuar."
            ),
            "persona_fields": persona_fields,
            "stage": current_stage,
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
                "persona_fields": persona_fields,
                "stage": current_stage,
            }
        if status == "PENDING":
            return {
                "intent": intent,
                "confidence": confidence,
                "reply": (
                    "Aún no hemos recibido la confirmación de tu pago. Dame un momento y te "
                    "aviso apenas se confirme."
                ),
                "persona_fields": persona_fields,
                "stage": current_stage,
            }
        return {
            "intent": intent,
            "confidence": confidence,
            "reply": (
                "No tengo ningún pago pendiente registrado a tu nombre. ¿Quieres que te envíe el "
                "link de pago?"
            ),
            "persona_fields": persona_fields,
            "stage": current_stage,
        }

    # unknown intent: hand off to the shared Taty brain rather than generating reply text here.
    reply = KB_FALLBACK_REPLY
    try:
        tenant_id = resolve_cliente_cero_tenant_id(get_service_supabase())
        if tenant_id:
            current_persona = {**(tax_profile or {}), **persona_fields}
            result = get_taty_service().ask(
                tenant_id=tenant_id,
                question=message,
                channel="whatsapp",
                conversation_history=history,
                lead_context=_build_lead_context(current_stage, current_persona, history=history),
            )
            if result.get("answer") and not result.get("error_code"):
                reply = result["answer"]
    except Exception:
        pass  # keep KB_FALLBACK_REPLY — matches this file's existing degrade-gracefully convention

    return {
        "intent": intent,
        "confidence": confidence,
        "reply": reply,
        "persona_fields": persona_fields,
        "stage": current_stage,
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
        phone = get_lead_phone(lead_id)
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
