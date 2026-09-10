"""Tests for backend_client.submit_whatsapp_document (taty-document-collection-wiring, Task 4).

Mirrors test_send_voice_note.py's pattern for the sibling /internal/* endpoint: same
"/internal, not /api/v1" boundary, same INTERNAL_API_KEY auth, same fail-soft (never raises,
returns None on any failure) contract.
"""

from __future__ import annotations

import json

import httpx
import pytest
import respx
from httpx import Response

from config import settings

API_URL = "http://127.0.0.1:8080/api/v1"
INTERNAL_URL = "http://127.0.0.1:8080/internal/whatsapp/document"
KEY = "test-internal-key"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(settings, "CONTEXIA_API_URL", API_URL)
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", KEY)


@respx.mock
@pytest.mark.asyncio
async def test_posts_to_internal_not_api_v1():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    result = await backend_client.submit_whatsapp_document(
        "lead-1", "https://chatwoot/x/rut.pdf", "file"
    )

    assert result == {"processed": True}
    assert route.called, "must post to /internal/whatsapp/document, not under /api/v1"


@respx.mock
@pytest.mark.asyncio
async def test_sends_lead_id_data_url_and_mime_type():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    await backend_client.submit_whatsapp_document("lead-1", "https://chatwoot/x/rut.pdf", "image")

    body = json.loads(route.calls[0].request.content)
    assert body["lead_id"] == "lead-1"
    assert body["data_url"] == "https://chatwoot/x/rut.pdf"
    assert body["mime_type"] == "image"


@respx.mock
@pytest.mark.asyncio
async def test_sends_the_internal_api_key_header():
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    await backend_client.submit_whatsapp_document("lead-1", "https://chatwoot/x/rut.pdf", "file")

    assert route.calls[0].request.headers["x-internal-api-key"] == KEY


@respx.mock
@pytest.mark.asyncio
async def test_returns_processed_false_dict_verbatim():
    respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": False}))

    import backend_client

    result = await backend_client.submit_whatsapp_document(
        "lead-1", "https://chatwoot/x/rut.pdf", "file"
    )

    assert result == {"processed": False}


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_on_503_key_not_configured():
    respx.post(INTERNAL_URL).mock(
        return_value=Response(503, json={"detail": "Internal API key not configured"})
    )

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", "https://chatwoot/x/rut.pdf", "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_on_401():
    respx.post(INTERNAL_URL).mock(return_value=Response(401, json={"detail": "Invalid key"}))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", "https://chatwoot/x/rut.pdf", "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_never_raises_on_network_failure():
    respx.post(INTERNAL_URL).mock(side_effect=httpx.ConnectError("backend down"))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", "https://chatwoot/x/rut.pdf", "file"
        )
        is None
    )


@respx.mock
@pytest.mark.asyncio
async def test_returns_none_without_an_internal_key(monkeypatch):
    monkeypatch.setattr(settings, "INTERNAL_API_KEY", "")
    route = respx.post(INTERNAL_URL).mock(return_value=Response(200, json={"processed": True}))

    import backend_client

    assert (
        await backend_client.submit_whatsapp_document(
            "lead-1", "https://chatwoot/x/rut.pdf", "file"
        )
        is None
    )
    assert not route.called
