"""Thin async client for the Chatwoot REST API: conversation history, outgoing
reply dispatch, and contact custom attributes.

Uses a single shared httpx.AsyncClient with follow_redirects=True (Chatwoot's
Active Storage attachment URLs can 302) and a 60s timeout (see design.md
decision 9 / Task Group 7).
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config import settings

logger = logging.getLogger(__name__)


def _headers() -> dict[str, str]:
    return {"api_access_token": settings.CHATWOOT_API_TOKEN}


def _base_url() -> str:
    return f"{settings.CHATWOOT_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}"


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(follow_redirects=True, timeout=60.0)


def _map_message(message: dict[str, Any]) -> dict[str, str]:
    """Chatwoot's message_type: 0 == incoming (customer/user), any other value
    (1 == outgoing, etc.) == the agent/bot side (assistant)."""
    role = "user" if message.get("message_type") == 0 else "assistant"
    return {"role": role, "content": message.get("content") or ""}


async def get_recent_messages(conversation_id: int) -> list[dict[str, str]]:
    """Fetch up to settings.MAX_HISTORY most recent messages for a conversation,
    mapped to {role, content} pairs in chronological order."""
    url = f"{_base_url()}/conversations/{conversation_id}/messages"
    async with _client() as client:
        response = await client.get(url, headers=_headers())
        response.raise_for_status()
        payload = response.json().get("payload", [])

    recent = payload[-settings.MAX_HISTORY :]
    return [_map_message(message) for message in recent]


async def send_reply(conversation_id: int, text: str) -> None:
    """Post an outgoing message to the given conversation."""
    url = f"{_base_url()}/conversations/{conversation_id}/messages"
    async with _client() as client:
        response = await client.post(
            url,
            headers=_headers(),
            json={"content": text, "message_type": "outgoing"},
        )
        response.raise_for_status()


async def set_contact_attributes(contact_id: int, attributes: dict[str, Any]) -> None:
    """Set/merge custom attributes on a Chatwoot contact (e.g. tipo_lead, estado).

    Chatwoot has no dedicated custom_attributes route for contacts — that member action exists
    only on conversations (config/routes.rb). Contacts::update's permitted_params accepts
    custom_attributes directly and merges it with the contact's existing ones
    (ContactsController#contact_custom_attributes), so this is a PATCH on the contact's own
    update endpoint, not a POST to a sub-resource.
    """
    url = f"{_base_url()}/contacts/{contact_id}"
    async with _client() as client:
        response = await client.patch(
            url,
            headers=_headers(),
            json={"custom_attributes": attributes},
        )
        response.raise_for_status()


async def find_or_create_contact(phone: str, name: str | None) -> int:
    """Find a contact by phone, or create one (whatsapp-durable-inbox).

    Needed because the poller injects a message Meta already delivered directly — there is no
    Chatwoot-native WhatsApp webhook doing this find-or-create for us on this path.
    """
    async with _client() as client:
        search = await client.get(
            f"{_base_url()}/contacts/search",
            headers=_headers(),
            params={"q": phone},
        )
        search.raise_for_status()
        matches = search.json().get("payload") or []
        if matches:
            return matches[0]["id"]

        created = await client.post(
            f"{_base_url()}/contacts",
            headers=_headers(),
            json={"name": name or phone, "phone_number": f"+{phone.lstrip('+')}"},
        )
        created.raise_for_status()
        return created.json()["payload"]["contact"]["id"]


async def find_or_create_conversation(contact_id: int, phone: str) -> int:
    """Find an open conversation for this contact on the WhatsApp inbox, or create one."""
    inbox_id = settings.CHATWOOT_WHATSAPP_INBOX_ID

    async with _client() as client:
        existing = await client.get(
            f"{_base_url()}/contacts/{contact_id}/conversations",
            headers=_headers(),
        )
        existing.raise_for_status()
        for conversation in existing.json().get("payload") or []:
            if str(conversation.get("inbox_id")) == str(inbox_id) and conversation.get(
                "status"
            ) != "resolved":
                return conversation["id"]

        created = await client.post(
            f"{_base_url()}/conversations",
            headers=_headers(),
            json={"source_id": phone, "inbox_id": inbox_id, "contact_id": contact_id},
        )
        created.raise_for_status()
        return created.json()["id"]


async def create_incoming_message(conversation_id: int, text: str) -> None:
    """Post the customer's own message into Chatwoot as an incoming message, so Tatiana sees
    what the customer actually wrote (whatsapp-durable-inbox) — distinct from send_reply, which
    posts Taty's or an agent's outgoing reply."""
    url = f"{_base_url()}/conversations/{conversation_id}/messages"
    async with _client() as client:
        response = await client.post(
            url,
            headers=_headers(),
            json={"content": text, "message_type": "incoming"},
        )
        response.raise_for_status()
