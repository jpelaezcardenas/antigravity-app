"""POST /internal/whatsapp/document (taty-document-collection-wiring, Task 3).

Mirrors the voice-note endpoint's auth pattern exactly (presentation/voice_endpoints.py,
tests/test_voice_endpoint_auth.py): INTERNAL_API_KEY fails closed (503 if unset, 401 on a wrong
key, checked before anything else), mounted under /internal (never proxied through vercel.json's
/api/v1/* rewrite).

This endpoint is the delivery half of Task 1 (download_chatwoot_attachment) and Task 2
(route_lead_document's data_url branch). It does not download or store anything itself — it just
authenticates the Chatwoot-bridge caller and forwards to route_lead_document(data_url=...), which
already owns the never-throw contract for the download and the LISTOS_CONTADORA gating.

The endpoint coroutine is awaited directly rather than driven through TestClient — same reason as
test_voice_endpoint_auth.py: httpx 0.28.1 removed the `app=` shortcut TestClient/starlette 0.27.0
still relies on in this repo.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from presentation.whatsapp_document_endpoints import (
    WhatsappDocumentRequest,
    send_whatsapp_document_endpoint,
)

_KEY = "test-internal-key"


def _request(**overrides) -> WhatsappDocumentRequest:
    payload = {
        "lead_id": "lead-1",
        "data_url": "https://chatwoot.example.com/rails/active_storage/blobs/abc/rut.pdf",
        "mime_type": "application/pdf",
    }
    payload.update(overrides)
    return WhatsappDocumentRequest(**payload)


async def _call(request, key=_KEY):
    return await send_whatsapp_document_endpoint(payload=request, x_internal_api_key=key)


def _status_of(excinfo) -> int:
    return excinfo.value.status_code


# --- Auth: fails closed -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_internal_key_env_returns_503(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_empty_internal_key_env_returns_503(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "")

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_wrong_key_returns_401(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key="not-the-key")
    assert _status_of(excinfo) == 401


@pytest.mark.asyncio
async def test_absent_header_returns_401(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key=None)
    assert _status_of(excinfo) == 401


# --- Delegation to route_lead_document -----------------------------------------------------------


@pytest.mark.asyncio
async def test_delegates_to_route_lead_document_with_data_url(monkeypatch):
    """The endpoint must not re-download or re-implement gating — it forwards to the one function
    that already owns that contract, passing data_url (never media_id) since Chatwoot's payload
    never carries a Graph media_id (design.md, Task 2's docstring)."""
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)

    import presentation.whatsapp_document_endpoints as endpoints

    calls = {}

    async def _fake_route(lead_id, media_id=None, mime_type="application/octet-stream", *, data_url=None):
        calls["args"] = (lead_id, media_id, mime_type, data_url)
        return {"processed": True}

    monkeypatch.setattr(endpoints, "route_lead_document", _fake_route)

    result = await _call(_request(lead_id="lead-42", data_url="https://x/y.pdf", mime_type="image/jpeg"))

    assert result.processed is True
    assert calls["args"] == ("lead-42", None, "image/jpeg", "https://x/y.pdf")


@pytest.mark.asyncio
async def test_not_processed_result_is_returned_not_raised(monkeypatch):
    """A document arriving before LISTOS_CONTADORA (or after both docs are collected) is a normal,
    expected outcome per route_lead_document's contract — not an error. Same stance as the
    voice-note endpoint's delivery-failure handling: 200 with a field, not a 4xx/5xx."""
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)

    import presentation.whatsapp_document_endpoints as endpoints

    async def _fake_route(*_args, **_kwargs):
        return {"processed": False}

    monkeypatch.setattr(endpoints, "route_lead_document", _fake_route)

    result = await _call(_request())

    assert result.processed is False


@pytest.mark.asyncio
async def test_uses_the_real_route_lead_document_not_a_reimplementation():
    """The endpoint must call services.taty_lead_router.route_lead_document, not its own copy of
    the download/gating logic."""
    import presentation.whatsapp_document_endpoints as endpoints

    assert endpoints.route_lead_document is __import__(
        "services.taty_lead_router", fromlist=["route_lead_document"]
    ).route_lead_document
