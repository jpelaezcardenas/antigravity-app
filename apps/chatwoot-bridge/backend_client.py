"""Client for the Contexia backend, reused (not duplicated) for CRM lead
intake (design.md decision 5). The bridge only finds-or-creates the CRM lead
and tags the Chatwoot contact — it never triggers the B2B/paid-customer
onboarding flow, which requires company_name/customer_email/payment_reference
that a fresh B2C WhatsApp lead does not have.

Auth: HS256 JWT signed with the shared CONTEXIA_JWT_SECRET, following the
exact contract already documented for Hermes operators in
openspec/changes/hermes-multi-tenant-wrapper/HERMES_CONFIG.md Step 3
(`sub`, `tenant_id`, `exp`) and matching the literal default `workspace_id`
Contexia's own `create_access_token` uses ("contexia-org-1", see
apps/backend/core/identity_resolver.py) — so TenantContextMiddleware and
Supabase RLS need zero backend-side changes (design.md decision 6).

Fail-soft contract (design.md decision 7): whatsapp_intake never raises. Any
failure (network, non-200) is logged and swallowed so a down CRM service
never blocks the WhatsApp reply.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import httpx
from jose import jwt

from config import settings

logger = logging.getLogger(__name__)

_TIMEOUT_SECONDS = 30.0

# Matches the literal default `workspace_id` Contexia's own JWT issuance uses
# for the single-tenant Cliente Cero deployment (see module docstring above).
_TENANT_ID = "contexia-org-1"


def sign_tenant_jwt() -> str:
    """Sign a short-lived (30 min) HS256 JWT with sub/tenant_id/exp claims,
    matching the Hermes-operator contract exactly."""
    payload = {
        "sub": "chatwoot-bridge",
        "tenant_id": _TENANT_ID,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.CONTEXIA_JWT_SECRET, algorithm="HS256")


def _headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {sign_tenant_jwt()}"}


async def whatsapp_intake(phone: str) -> Optional[dict[str, Any]]:
    """Find-or-create the CRM lead for this WhatsApp phone number. Returns
    the backend's response ({lead_id, is_new, stage}), or None on any
    failure — never raises."""
    url = f"{settings.CONTEXIA_API_URL}/crm/leads/whatsapp-intake"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url, headers=_headers(), json={"whatsapp_phone": phone}
            )
        if response.status_code != 200:
            logger.error(
                "whatsapp_intake returned non-200: %s %s",
                response.status_code,
                response.text,
            )
            return None
        return response.json()
    except Exception:
        logger.exception("whatsapp_intake call failed")
        return None


async def taty_reply(lead_id: str, text: str) -> Optional[dict[str, Any]]:
    """Ask the backend's Taty sales router for this lead's reply.

    taty-channel-consolidation: replaces the bridge's previous raw Hermes chat completion so a
    single brain (services/taty_lead_router.py) owns intent classification, Wompi payment links,
    payment verification and KB grounding on every channel.

    `deliver: True` (taty-whatsapp-renta-sales-capability, Stage 5, CORRECTED 2026-08-12 found
    live): the backend delivers Taty's reply to the customer's real WhatsApp number directly via
    Meta's Graph API. An earlier revision set this to False on the theory that Chatwoot itself would
    deliver, now that the bridge targets the real Meta-linked `Channel::Whatsapp` inbox. That theory
    was wrong AND it is mutually incompatible with the 422 fix that had to land at the same time:
    because the durable-inbox webhook lands on Railway (not on Chatwoot) and the poller mirrors the
    customer's message into Chatwoot as a *private note* (a real `incoming` is rejected 422 on a
    real-provider inbox), Chatwoot's WhatsApp channel never records a genuine customer inbound, so
    its own 24-hour-window bookkeeping always believes the window is CLOSED. Every outgoing Chatwoot
    tries to deliver is then rejected by Meta ("Message not sent because the WhatsApp 24-hour
    customer service window is closed... send an approved template instead") — so with deliver=False
    NOTHING reached the customer's phone, for the bot OR a human. Meta's real window is in fact OPEN
    (the customer's inbound arrived at our webhook with a real wamid minutes earlier), so a DIRECT
    Graph API send from the backend succeeds. No double-send: Chatwoot's own delivery attempt fails
    on the closed-window check, so the backend is the only path that actually reaches the phone.
    (Known follow-up, not fixed here: a human's reply typed in Chatwoot still cannot reach the phone
    for the same reason — Chatwoot can't open the window it never saw an inbound for.)

    Same fail-soft contract as whatsapp_intake: returns None on any failure, never raises. The
    caller turns None into the human-takeover fallback rather than answering ungrounded.

    Returns the full backend response dict ({"intent", "confidence", "reply", "persona_fields",
    "stage"}), not just the reply text — chatwoot-auto-tagging needs the classification fields
    to tag the Chatwoot contact/conversation. Callers that only need the reply read
    result["reply"].
    """
    url = f"{settings.CONTEXIA_API_URL}/channels/whatsapp/leads/{lead_id}/reply"
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url, headers=_headers(), json={"text": text, "deliver": True}
            )
        if response.status_code != 200:
            logger.error(
                "taty_reply returned non-200: %s %s", response.status_code, response.text
            )
            return None
        return response.json()
    except Exception:
        logger.exception("taty_reply call failed")
        return None


async def pull_pending_events(limit: int = 50) -> list[dict[str, Any]]:
    """Pull and claim unprocessed WhatsApp inbound events (whatsapp-durable-inbox).

    Unlike whatsapp_intake/taty_reply this is allowed to raise: a poll-loop iteration failing
    loudly and retrying next tick is correct, whereas silently returning an empty list would look
    identical to "nothing pending" and hide an outage from inbox_health.
    """
    url = f"{settings.CONTEXIA_API_URL}/channels/whatsapp/inbox/pending"
    async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
        response = await client.get(url, headers=_headers(), params={"limit": limit})
        response.raise_for_status()
        return response.json().get("events", [])


async def acknowledge_events(event_ids: list[str]) -> None:
    """Mark events processed. Called only after Chatwoot has accepted the injected message —
    see inbox_poller.poll_once."""
    if not event_ids:
        return

    url = f"{settings.CONTEXIA_API_URL}/channels/whatsapp/inbox/ack"
    async with httpx.AsyncClient(timeout=_TIMEOUT_SECONDS) as client:
        response = await client.post(url, headers=_headers(), json={"event_ids": event_ids})
        response.raise_for_status()
