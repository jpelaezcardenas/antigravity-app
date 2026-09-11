"""Tests for backend_client.submit_whatsapp_document (taty-document-collection-wiring, Task 4).

Fixed 2026-09-11: Chatwoot's data_url is typically http://localhost:<port>/... — reachable from
this bridge (same network as Chatwoot) but NOT from the Railway backend, which previously tried to
re-fetch it directly and always failed in production (found live against a real Chatwoot
attachment). The bridge now downloads the attachment itself and posts the bytes as base64 —
mirrors the same "/internal, not /api/v1" boundary and INTERNAL_API_KEY auth as test_send_voice_note.py,
same fail-soft (never raises, returns None on any failure) contract.
"""

from __future__ import annotations

import base64
import json

import httpx
import pytest
import respx
from httpx import Response

from config import settings

API_URL = "http://127.0.0.1:8080/api/v1"
INTERNAL_URL = "http://127.0.0.1:8080/internal/whatsapp/document"
CHATWOOT_ATTACHMENT_URL = "http://localhost:3020/rails/active_storage/blobs/redirect/xyz/rut.pdf"
KEY = "test-internal-key"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "CONTEXIA_API_URL", API_URL)
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", KEY)


@respx.mock
@pytest.mark.asyncio
async def test_downloads_the_attachment_from_chatwoot_first():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    result = await backend_client.submit_whatsapp_document(
        "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
    )

    assert result == {"processed": True}
    assert route.called, "must post to /internal/whatsapp/document, not under /api/v1"


@respx.mock
@pytest.mark.asyncio
async def test_sends_lead_id_content_base64_and_mime_type_not_data_url():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    await backend_client.submit_whatsapp_document("lead-1", CHATWOOT_ATTACHMENT_URL, "image")

    body = json.loads(route.calls[0].request.content)
    assert body["lead_id"] == "lead-1"
    assert body["mime_type"] == "image"
    assert body["content_base64"] == base64.b64encode(b"fake-pdf-bytes").decode("ascii")
    assert "data_url" not in body or body["data_url"] is None


@respx.mock
@pytest.mark.asyncio
async def test_sends_the_internal_api_key_header():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    await backend_client.submit_whatsapp_document("lead-1", CHATWOOT_ATTACHMENT_URL, "file")

    assert route.calls[0].request.headers["x-internal-api-key"] == KEY


@respx.mock
@pytest.mark.asyncio
async def test_returns_processed_false_dict_verbatim():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": False}))

    import backend_client

    result = await backend_client.submit_whatsapp_document(
        "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
    )

    assert result == {"processed": False}


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_on_503_key_not_configured():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    respx.post(INTERNAL_URL).mock(
        return_value=Response(503, json={"detail": "Internal API key not configured"})
    )

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_on_401():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    respx.post(INTERNAL_URL).mock(return_value=Response(401, json={"detail": "Invalid key"}))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_never_raises_on_network_failure():
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    respx.post(INTERNAL_URL).mock(side_effect=httpx.ConnectError("backend down"))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_without_an_internal_key(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", "")
    get_route = respx.get(CHATWOOT_ATTACHMENT_URL).mock(
        return_value=Response(200, content=b"fake-pdf-bytes")
    )
    post_route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
        )
        is None
    )
    assert not post_route.called
    assert not get_route.called, "must not even attempt the download without an internal key"


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_when_the_chatwoot_download_fails():
    """The download leg can fail independently of the backend call — never raises, never posts
    a partial/empty document."""
    respx.get(CHATWOOT_ATTACHMENT_URL).mock(return_value=Response(404))
    post_route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", CHATWOOT_ATTACHMENT_URL, "file"
        )
        is None
    )
    assert not post_route.called
