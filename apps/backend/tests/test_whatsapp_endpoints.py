"""Tests for WhatsApp channel endpoints (taty-channel-consolidation).

Two surfaces with different threat models:
- `POST /webhook` is the PUBLIC ingress from Meta (live as
  contexia.online/api/v1/channels/whatsapp/webhook via vercel.json's rewrite). It previously
  accepted any POST; these tests pin X-Hub-Signature-256 verification over the RAW body.
- `POST /leads/{lead_id}/reply` is INTERNAL and authenticated — the Chatwoot bridge's entry point
  into the single Taty brain.

Isolated FastAPI app + httpx.AsyncClient(transport=ASGITransport(...)) + pytest.mark.asyncio,
service layer mocked — same pattern established in test_sell_machine_endpoints.py.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

APP_SECRET = "test-app-secret"


def _sign(raw: bytes, secret: str = APP_SECRET) -> str:
    return "sha256=" + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()


@pytest.fixture
def wa_app():
    from presentation.whatsapp_endpoints import router as whatsapp_router

    app = FastAPI()
    app.include_router(whatsapp_router, prefix="/channels/whatsapp")
    return app


@pytest.fixture
def wa_client(wa_app):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=wa_app), base_url="http://testserver"
    )


@pytest.fixture
def configured():
    from config import settings

    with patch.object(settings, "WHATSAPP_APP_SECRET", APP_SECRET), patch.object(
        settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", "correct-verify-token"
    ):
        yield


@pytest.fixture
def reply_client(wa_app):
    """Same app, with auth satisfied for the internal endpoint."""
    from core.deps import get_current_user

    wa_app.dependency_overrides[get_current_user] = lambda: {
        "sub": "bridge",
        "email": "bridge@contexia",
    }
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=wa_app), base_url="http://testserver"
    )


class TestFeatureFlagRetired:
    def test_no_whatsapp_canonical_setting_remains(self) -> None:
        from config import settings

        assert not hasattr(settings, "WHATSAPP_CANONICAL")

    def test_router_is_mounted_unconditionally(self) -> None:
        with open("presentation/router.py", "r", encoding="utf-8") as f:
            router_code = f.read()

        assert "if settings.WHATSAPP_CANONICAL:" not in router_code
        assert 'prefix="/channels/whatsapp"' in router_code


class TestWebhookVerificationHandshake:
    @pytest.mark.asyncio
    async def test_valid_token_echoes_challenge(self, wa_client, configured) -> None:
        async with wa_client as client:
            response = await client.get(
                "/channels/whatsapp/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "correct-verify-token",
                    "hub.challenge": "12345",
                },
            )

        assert response.status_code == 200
        assert response.text == "12345"

    @pytest.mark.asyncio
    async def test_invalid_token_rejected(self, wa_client, configured) -> None:
        async with wa_client as client:
            response = await client.get(
                "/channels/whatsapp/webhook",
                params={
                    "hub.mode": "subscribe",
                    "hub.verify_token": "wrong-token",
                    "hub.challenge": "12345",
                },
            )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unconfigured_verify_token_fails_closed(self, wa_client) -> None:
        """No hardcoded default may be accepted."""
        from config import settings

        async with wa_client as client:
            with patch.object(settings, "WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""):
                response = await client.get(
                    "/channels/whatsapp/webhook",
                    params={
                        "hub.mode": "subscribe",
                        "hub.verify_token": "contexia-whatsapp-webhook",
                        "hub.challenge": "12345",
                    },
                )

        assert response.status_code == 403


class TestInboundWebhookSignature:
    @pytest.mark.asyncio
    async def test_unsigned_payload_is_rejected_without_side_effects(
        self, wa_client, configured
    ) -> None:
        raw = json.dumps({"entry": []}).encode()

        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook"
            ) as mock_normalize:
                response = await client.post(
                    "/channels/whatsapp/webhook",
                    content=raw,
                    headers={"Content-Type": "application/json"},
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()

    @pytest.mark.asyncio
    async def test_wrong_signature_is_rejected(self, wa_client, configured) -> None:
        raw = json.dumps({"entry": []}).encode()

        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook"
            ) as mock_normalize:
                response = await client.post(
                    "/channels/whatsapp/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw, "attacker-secret"),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()

    @pytest.mark.asyncio
    async def test_signed_message_is_stored_not_processed(self, wa_client, configured) -> None:
        """whatsapp-durable-inbox: the webhook stores and returns. Running an LLM call inside
        Meta's request turns a slow model into a retry, and a retry into a duplicate reply — so
        classification and sending must NOT happen here; storage is what makes retries
        idempotent instead."""
        raw = json.dumps({"entry": []}).encode()
        fake_events = [
            {
                "channel": "whatsapp",
                "account_id": "573001234567",
                "source_event_id": "wamid.AAA",
                "text": "Quiero saber si me toca declarar renta este año",
                "actor_name": "Maria Lead",
                "raw_payload": {},
            }
        ]

        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook",
                return_value=fake_events,
            ), patch(
                "presentation.whatsapp_endpoints.store_inbound_events", return_value=1
            ) as mock_store, patch(
                "presentation.whatsapp_endpoints.route_lead_message"
            ) as mock_route:
                response = await client.post(
                    "/channels/whatsapp/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 200
        assert response.json()["events_accepted"] == 1
        mock_store.assert_called_once_with(fake_events)
        mock_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_signature_uses_raw_bytes_not_reserialized_json(
        self, wa_client, configured
    ) -> None:
        """Non-canonical key order and whitespace must still verify. If the handler parsed the
        body and re-serialized it before hashing, this signature would never match."""
        raw = b'{"object":   "whatsapp_business_account",  "entry": []}'

        async with wa_client as client:
            with patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook", return_value=[]
            ):
                response = await client.post(
                    "/channels/whatsapp/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_unconfigured_app_secret_rejects_everything(self, wa_client) -> None:
        from config import settings

        raw = json.dumps({"entry": []}).encode()

        async with wa_client as client:
            with patch.object(settings, "WHATSAPP_APP_SECRET", ""), patch(
                "presentation.whatsapp_endpoints.normalize_whatsapp_webhook"
            ) as mock_normalize:
                response = await client.post(
                    "/channels/whatsapp/webhook",
                    content=raw,
                    headers={
                        "X-Hub-Signature-256": _sign(raw),
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 403
        mock_normalize.assert_not_called()


class TestDurableInboxEndpoints:
    """The local bridge PULLS from these — that is what lets the local node stay unreachable
    from the internet, and is why no tunnel or DNS delegation is needed."""

    @pytest.mark.asyncio
    async def test_pending_returns_claimed_events(self, reply_client) -> None:
        events = [{"id": "e1", "account_id": "573001234567", "body": "hola"}]

        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.pull_pending", return_value=events
            ) as mock_pull:
                response = await client.get("/channels/whatsapp/inbox/pending?limit=10")

        assert response.status_code == 200
        assert response.json()["count"] == 1
        assert response.json()["events"][0]["id"] == "e1"
        mock_pull.assert_called_once_with(limit=10)

    @pytest.mark.asyncio
    async def test_ack_marks_events_processed(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.acknowledge", return_value=2
            ) as mock_ack:
                response = await client.post(
                    "/channels/whatsapp/inbox/ack", json={"event_ids": ["e1", "e2"]}
                )

        assert response.status_code == 200
        assert response.json()["acknowledged"] == 2
        mock_ack.assert_called_once_with(["e1", "e2"])

    @pytest.mark.asyncio
    async def test_health_exposes_backlog(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.inbox_health",
                return_value={"pending": 12, "oldest_pending_at": "2026-07-28T10:00:00+00:00"},
            ):
                response = await client.get("/channels/whatsapp/inbox/health")

        assert response.status_code == 200
        assert response.json()["pending"] == 12

    @pytest.mark.asyncio
    async def test_inbox_endpoints_reject_unauthenticated_access(self, wa_client) -> None:
        """These carry raw customer message text — they must never answer without auth."""
        from config import settings

        with patch.object(settings, "AUTH_ENFORCED", True):
            async with wa_client as client:
                pending = await client.get("/channels/whatsapp/inbox/pending")
                ack = await client.post(
                    "/channels/whatsapp/inbox/ack", json={"event_ids": ["e1"]}
                )
                health = await client.get("/channels/whatsapp/inbox/health")

        assert pending.status_code == 401
        assert ack.status_code == 401
        assert health.status_code == 401


class TestInternalTatyReplyEndpoint:
    @pytest.mark.asyncio
    async def test_authenticated_call_returns_router_reply(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=True
            ), patch(
                "presentation.whatsapp_endpoints.route_lead_message",
                return_value={
                    "intent": "sales_interest",
                    "confidence": 0.8,
                    "reply": "Aquí tienes el link de pago...",
                },
            ) as mock_route:
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply",
                    json={"text": "quiero saber si me toca declarar renta"},
                )

        assert response.status_code == 200
        assert response.json()["reply"] == "Aquí tienes el link de pago..."
        mock_route.assert_called_once_with("lead-1", "quiero saber si me toca declarar renta")

    @pytest.mark.asyncio
    async def test_unknown_lead_returns_404_and_does_not_route(self, reply_client) -> None:
        async with reply_client as client:
            with patch(
                "presentation.whatsapp_endpoints.lead_exists", return_value=False
            ), patch("presentation.whatsapp_endpoints.route_lead_message") as mock_route:
                response = await client.post(
                    "/channels/whatsapp/leads/does-not-exist/reply", json={"text": "hola"}
                )

        assert response.status_code == 404
        mock_route.assert_not_called()

    @pytest.mark.asyncio
    async def test_unauthenticated_call_is_rejected(self, wa_client) -> None:
        """No dependency override here: the real get_current_user must reject a tokenless
        call when AUTH_ENFORCED is on."""
        from config import settings

        with patch.object(settings, "AUTH_ENFORCED", True):
            async with wa_client as client:
                response = await client.post(
                    "/channels/whatsapp/leads/lead-1/reply", json={"text": "hola"}
                )

        assert response.status_code == 401
