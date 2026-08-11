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


async def send_reply(conversation_id: int, text: str, private: bool = False) -> None:
    """Post a message to the given conversation. `private=True` posts an internal note (visible
    to human agents, never dispatched to the customer's real channel) — see
    create_customer_message_note's docstring for why this exists."""
    url = f"{_base_url()}/conversations/{conversation_id}/messages"
    async with _client() as client:
        response = await client.post(
            url,
            headers=_headers(),
            json={"content": text, "message_type": "outgoing", "private": private},
        )
        response.raise_for_status()


async def create_customer_message_note(conversation_id: int, text: str) -> None:
    """Records the customer's own message as a private note, for human visibility in Chatwoot.

    Found live 2026-08-11 (taty-whatsapp-renta-sales-capability): Chatwoot's Messages API
    rejects `message_type: "incoming"` with a 422 ("Incoming messages are only allowed in Api
    inboxes") for any real-provider inbox (Channel::Whatsapp) — that spoofing path only works on
    the credential-less Channel::Api test inbox this bridge used before Stage 5's cutover. A
    private note is the closest available substitute: it succeeds on a real inbox and is visible
    to a human agent, at the cost of appearing as an internal note rather than the customer's own
    chat bubble. It deliberately does NOT trigger Chatwoot's own message_created webhook back to
    this bridge the way a real incoming message would (private messages are explicitly filtered
    by this bridge's own /webhook handler) — reply generation is triggered directly by
    inbox_poller.poll_once() calling main.process_incoming_message(), not by relying on that
    webhook loopback, which the old create_incoming_message design depended on and which cannot
    work against a real inbox at all."""
    await send_reply(conversation_id, text, private=True)


async def get_conversation_labels(conversation_id: int) -> list[str]:
    """Current labels on a conversation (e.g. to check for bot_off before the poller drives a
    reply directly — mirrors the check main.py's webhook handler does before dispatching to
    process_incoming_message, since the poller bypasses that handler entirely for a real inbox)."""
    url = f"{_base_url()}/conversations/{conversation_id}/labels"
    async with _client() as client:
        response = await client.get(url, headers=_headers())
        response.raise_for_status()
        return response.json().get("payload", [])


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


