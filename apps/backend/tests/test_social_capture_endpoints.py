"""Tests for the public, unauthenticated social-lead-capture endpoint
(b2c-social-lead-capture, Task 2): POST /api/v1/crm/social-capture/partial.

Endpoint tests use the isolated FastAPI app + httpx.ASGITransport pattern from
test_crm_whatsapp_intake.py. Service/throttle-layer behavior is exercised through the
endpoint (mocking only the Supabase-touching CrmService), matching this repo's
convention of testing the public contract rather than internals directly.
"""

from __future__ import annotations

from unittest.mock import patch

import httpx
import pytest
from fastapi import FastAPI

import services.social_capture_throttle as throttle


@pytest.fixture(autouse=True)
def _reset_throttle():
    """Module-level throttle state must never leak across test cases."""
    throttle.reset()
    yield
    throttle.reset()


@pytest.fixture
def social_capture_client():
    from presentation.social_capture_endpoints import router as social_capture_router

    app = FastAPI()
    app.include_router(social_capture_router, prefix="/crm")
    transport = httpx.ASGITransport(app=app)
    return httpx.AsyncClient(transport=transport, base_url="http://testserver")


class TestSocialCapturePartialEndpoint:
    @pytest.mark.asyncio
    async def test_unauthenticated_request_succeeds(self, social_capture_client) -> None:
        """No Authorization header at all — this endpoint is genuinely public, unlike
        almost everything else in this backend (ARCHITECTURE.md Decisions #13-#17)."""
        async with social_capture_client as client:
            with patch(
                "presentation.social_capture_endpoints.get_crm_service"
            ) as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "new-lead-id",
                    "is_new": True,
                    "stage": "NUEVOS",
                }
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567", "source": "facebook_ad_renta2026"},
                )

        assert response.status_code == 200
        assert response.json() == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}

    @pytest.mark.asyncio
    async def test_delegates_to_crm_service_whatsapp_intake_with_source(
        self, social_capture_client
    ) -> None:
        """Reuses CrmService.whatsapp_intake's find-or-create logic (design.md Decision 2)
        rather than a duplicate implementation, and stamps `source`."""
        async with social_capture_client as client:
            with patch(
                "presentation.social_capture_endpoints.get_crm_service"
            ) as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "new-lead-id",
                    "is_new": True,
                    "stage": "NUEVOS",
                }
                await client.post(
                    "/crm/social-capture/partial",
                    json={
                        "whatsapp_phone": "+573001234567",
                        "full_name": "Jane Doe",
                        "source": "instagram_organic",
                    },
                )

        mock_get_service.return_value.whatsapp_intake.assert_called_once_with(
            "+573001234567", full_name="Jane Doe", source="instagram_organic"
        )

    @pytest.mark.asyncio
    async def test_ip_throttle_rejects_excess_requests(self, social_capture_client) -> None:
        """The same IP hammering the endpoint past the window's max gets a 429 — and the
        service layer is never touched for the throttled request."""
        async with social_capture_client as client:
            with patch(
                "presentation.social_capture_endpoints.get_crm_service"
            ) as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.side_effect = (
                    lambda phone, **_: {
                        "lead_id": f"lead-{phone}",
                        "is_new": True,
                        "stage": "NUEVOS",
                    }
                )

                statuses = []
                for i in range(throttle.IP_MAX_REQUESTS + 1):
                    response = await client.post(
                        "/crm/social-capture/partial",
                        json={"whatsapp_phone": f"+5730012340{i:02d}"},
                    )
                    statuses.append(response.status_code)

        assert statuses[: throttle.IP_MAX_REQUESTS] == [200] * throttle.IP_MAX_REQUESTS
        assert statuses[-1] == 429

    @pytest.mark.asyncio
    async def test_repeat_phone_within_window_is_a_no_op(self, social_capture_client) -> None:
        """A repeat phone number within the throttle window never re-hits CrmService —
        it's a no-op, not a new lead/message (design.md's abuse-mitigation risk note)."""
        async with social_capture_client as client:
            with patch(
                "presentation.social_capture_endpoints.get_crm_service"
            ) as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "new-lead-id",
                    "is_new": True,
                    "stage": "NUEVOS",
                }

                first = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )
                second = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "573001234567"},  # same phone, different format
                )

        assert first.status_code == 200
        assert second.status_code == 200
        assert second.json() == {"is_new": False, "throttled_repeat": True}
        mock_get_service.return_value.whatsapp_intake.assert_called_once()

    @pytest.mark.asyncio
    async def test_repeat_phone_does_not_count_against_ip_throttle_capacity(
        self, social_capture_client
    ) -> None:
        """A throttled-repeat response still consumes an IP-window slot (it's still an
        HTTP hit), but must not itself be rejected by the IP throttle before the phone
        check runs, and must not call the service."""
        async with social_capture_client as client:
            with patch(
                "presentation.social_capture_endpoints.get_crm_service"
            ) as mock_get_service:
                mock_get_service.return_value.whatsapp_intake.return_value = {
                    "lead_id": "new-lead-id",
                    "is_new": True,
                    "stage": "NUEVOS",
                }
                await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )
                response = await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )

        assert response.status_code == 200
        assert response.json()["throttled_repeat"] is True
        mock_get_service.return_value.whatsapp_intake.assert_called_once()


class TestSocialCaptureFirstContactTrigger:
    """b2c-social-lead-capture, Task 3: a new capture fires exactly one WhatsApp
    first-contact message; a repeat capture of an already-contacted phone number
    never fires an additional one. Reuses the same `channels.whatsapp.send_whatsapp_message`
    delivery path cadence_endpoints.py already uses (design.md Decision 4) — no new send
    mechanism, no Twilio/voice dependency."""

    @pytest.mark.asyncio
    async def test_new_capture_sends_exactly_one_whatsapp_message(
        self, social_capture_client
    ) -> None:
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            mock_send.return_value = True

            async with social_capture_client as client:
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )

        assert response.status_code == 200
        mock_send.assert_called_once()
        sent_phone = mock_send.call_args[0][0]
        assert sent_phone == "+573001234567"

    @pytest.mark.asyncio
    async def test_repeat_capture_of_existing_lead_sends_no_message(
        self, social_capture_client
    ) -> None:
        """whatsapp_intake finding an existing lead (is_new=False) never triggers a
        first-contact send — the phone was already contacted in a prior capture."""
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "existing-lead-id",
                "is_new": False,
                "stage": "PROSPECTOS",
            }
            mock_send.return_value = True

            async with social_capture_client as client:
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )

        assert response.status_code == 200
        mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_throttled_repeat_phone_sends_no_message(
        self, social_capture_client
    ) -> None:
        """A throttled-repeat response (same phone, within the throttle window) never
        reaches whatsapp_intake at all, so it can never trigger a duplicate send."""
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            mock_send.return_value = True

            async with social_capture_client as client:
                await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )
                await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )

        mock_send.assert_called_once()


class TestSocialCaptureMetaCapiLeadEvent:
    """empresa-4-0-agentic-gtm-roadmap, meta-capi-attribution spec: a new lead fires
    exactly one Meta CAPI Lead event, gated identically to the first-contact WhatsApp
    send (is_new only); CAPI failure/unavailability never affects the HTTP response."""

    @pytest.mark.asyncio
    async def test_new_capture_sends_exactly_one_capi_lead_event(
        self, social_capture_client
    ) -> None:
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send_whatsapp, patch(
            "presentation.social_capture_endpoints.send_lead_event"
        ) as mock_send_lead:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            mock_send_whatsapp.return_value = True
            mock_send_lead.return_value = True

            async with social_capture_client as client:
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )

        assert response.status_code == 200
        mock_send_lead.assert_called_once()
        _, kwargs = mock_send_lead.call_args
        assert kwargs["lead_id"] == "new-lead-id"
        assert kwargs["normalized_phone"]

    @pytest.mark.asyncio
    async def test_existing_lead_sends_no_capi_event(self, social_capture_client) -> None:
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send_whatsapp, patch(
            "presentation.social_capture_endpoints.send_lead_event"
        ) as mock_send_lead:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "existing-lead-id",
                "is_new": False,
                "stage": "PROSPECTOS",
            }
            mock_send_whatsapp.return_value = True

            async with social_capture_client as client:
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )

        assert response.status_code == 200
        mock_send_lead.assert_not_called()

    @pytest.mark.asyncio
    async def test_throttled_repeat_sends_no_capi_event(self, social_capture_client) -> None:
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send_whatsapp, patch(
            "presentation.social_capture_endpoints.send_lead_event"
        ) as mock_send_lead:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            mock_send_whatsapp.return_value = True
            mock_send_lead.return_value = True

            async with social_capture_client as client:
                await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )
                await client.post(
                    "/crm/social-capture/partial", json={"whatsapp_phone": "+573001234567"}
                )

        mock_send_lead.assert_called_once()

    @pytest.mark.asyncio
    async def test_capi_failure_does_not_affect_response(self, social_capture_client) -> None:
        """send_lead_event returning False (unconfigured/failed) must never change the
        endpoint's success response — the same never-block contract as WhatsApp send."""
        with patch(
            "presentation.social_capture_endpoints.get_crm_service"
        ) as mock_get_service, patch(
            "presentation.social_capture_endpoints.send_whatsapp_message"
        ) as mock_send_whatsapp, patch(
            "presentation.social_capture_endpoints.send_lead_event"
        ) as mock_send_lead:
            mock_get_service.return_value.whatsapp_intake.return_value = {
                "lead_id": "new-lead-id",
                "is_new": True,
                "stage": "NUEVOS",
            }
            mock_send_whatsapp.return_value = True
            mock_send_lead.return_value = False

            async with social_capture_client as client:
                response = await client.post(
                    "/crm/social-capture/partial",
                    json={"whatsapp_phone": "+573001234567"},
                )

        assert response.status_code == 200
        assert response.json() == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}


class TestMetaCapiClient:
    """Unit tests for services.meta_capi_client.send_lead_event directly — the CAPI
    client's own never-raise/fail-closed contract, independent of the endpoint wiring
    tested above."""

    @pytest.mark.asyncio
    async def test_returns_false_and_no_network_call_when_unconfigured(self, monkeypatch) -> None:
        from services.meta_capi_client import send_lead_event

        monkeypatch.delenv("META_CAPI_ACCESS_TOKEN", raising=False)
        monkeypatch.delenv("META_PIXEL_ID", raising=False)

        with patch("services.meta_capi_client.httpx.AsyncClient") as mock_client_cls:
            result = await send_lead_event(normalized_phone="573001234567", lead_id="lead-1")

        assert result is False
        mock_client_cls.assert_not_called()

    @pytest.mark.asyncio
    async def test_hashes_phone_as_lowercase_sha256(self, monkeypatch) -> None:
        import hashlib

        from services.meta_capi_client import send_lead_event

        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("META_PIXEL_ID", "test-pixel-id")

        captured_payload = {}

        class _FakeResponse:
            status_code = 200
            text = "{}"

        class _FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, url, json=None, params=None):
                captured_payload.update(json or {})
                return _FakeResponse()

        with patch("services.meta_capi_client.httpx.AsyncClient", return_value=_FakeAsyncClient()):
            result = await send_lead_event(normalized_phone="573001234567", lead_id="lead-1")

        assert result is True
        sent_hash = captured_payload["data"][0]["user_data"]["ph"][0]
        assert sent_hash == hashlib.sha256(b"573001234567").hexdigest()

    @pytest.mark.asyncio
    async def test_returns_false_on_non_200_response(self, monkeypatch) -> None:
        from services.meta_capi_client import send_lead_event

        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("META_PIXEL_ID", "test-pixel-id")

        class _FakeResponse:
            status_code = 400
            text = "bad request"

        class _FakeAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, url, json=None, params=None):
                return _FakeResponse()

        with patch("services.meta_capi_client.httpx.AsyncClient", return_value=_FakeAsyncClient()):
            result = await send_lead_event(normalized_phone="573001234567", lead_id="lead-1")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_and_never_raises_on_network_exception(self, monkeypatch) -> None:
        from services.meta_capi_client import send_lead_event

        monkeypatch.setenv("META_CAPI_ACCESS_TOKEN", "test-token")
        monkeypatch.setenv("META_PIXEL_ID", "test-pixel-id")

        class _RaisingAsyncClient:
            async def __aenter__(self):
                return self

            async def __aexit__(self, *args):
                return False

            async def post(self, *args, **kwargs):
                raise httpx.ConnectError("boom")

        with patch("services.meta_capi_client.httpx.AsyncClient", return_value=_RaisingAsyncClient()):
            result = await send_lead_event(normalized_phone="573001234567", lead_id="lead-1")

        assert result is False

    def test_module_source_reads_token_from_env_not_a_literal(self) -> None:
        """The CAPI access token must only ever come from `os.getenv` — never a hardcoded
        literal in source (tasks.md Task 2.2: token never reaches client-served code,
        verified here at the module-source level for the backend client itself)."""
        import inspect
        import re

        import services.meta_capi_client as capi_module

        source = inspect.getsource(capi_module)
        assert 'os.getenv("META_CAPI_ACCESS_TOKEN")' in source
        # No `access_token = "<literal>"`-shaped assignment anywhere in the module.
        assert re.search(r'access_token\s*=\s*"[^"]+"', source) is None


class TestSocialCapturePartialCrmServiceSourceStamping:
    def test_source_stamped_only_on_insert_path(self) -> None:
        """Mirrors test_crm_whatsapp_intake.py's fixture pattern: `source` is written on
        the create path and never overwrites an existing lead's attribution."""
        from unittest.mock import MagicMock

        from services.crm_service import CrmService

        client = MagicMock()
        leads_table = MagicMock()
        leads_table.select.return_value.eq.return_value.eq.return_value.maybe_single.return_value.execute.return_value = (
            MagicMock(data=None)
        )
        leads_table.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "new-lead-id", "stage": "NUEVOS"}]
        )

        def table_side_effect(name):
            if name == "tenants":
                table_mock = MagicMock()
                table_mock.select.return_value.eq.return_value.single.return_value.execute.return_value = (
                    MagicMock(data={"id": "cc-tenant"})
                )
                return table_mock
            if name == "crm_leads":
                return leads_table
            return MagicMock()

        client.table.side_effect = table_side_effect

        with patch("services.crm_service.get_service_supabase", return_value=client):
            result = CrmService().whatsapp_intake(
                "+573001234567", source="facebook_ad_renta2026"
            )

        assert result == {"lead_id": "new-lead-id", "is_new": True, "stage": "NUEVOS"}
        insert_payload = leads_table.insert.call_args[0][0]
        assert insert_payload["source"] == "facebook_ad_renta2026"
