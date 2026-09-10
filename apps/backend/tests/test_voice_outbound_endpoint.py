"""POST /internal/voice/outbound-call (taty-voice-outbound-calls, Task 2).

Mirrors tests/test_cadence_endpoint.py's shape: the endpoint coroutine is awaited directly.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from config import settings
from presentation.voice_outbound_endpoints import OutboundCallRequest, trigger_outbound_call_endpoint

_KEY = "test-internal-key"


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)


@pytest.fixture(autouse=True)
def _twilio_configured(monkeypatch):
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "ACxxxx")
    monkeypatch.setattr(settings, "TWILIO_AUTH_TOKEN", "fake-token")
    monkeypatch.setattr(settings, "TWILIO_FROM_NUMBER", "+15551234567")


def _request(**overrides) -> OutboundCallRequest:
    payload = {"lead_id": "lead-1", "tenant_id": "tenant-1"}
    payload.update(overrides)
    return OutboundCallRequest(**payload)


async def _call(request, key=_KEY):
    return await trigger_outbound_call_endpoint(payload=request, x_internal_api_key=key)


def _status_of(excinfo) -> int:
    return excinfo.value.status_code


def _lead(**overrides):
    base = {
        "id": "lead-1",
        "tenant_id": "tenant-1",
        "stage": "NUEVOS",
        "whatsapp_phone": "573001234567",
        "lead_type": None,
    }
    base.update(overrides)
    return base


# --- Auth: fails closed -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_internal_key_env_returns_503(monkeypatch):
    monkeypatch.delenv("INTERNAL_API_KEY", raising=False)
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


@pytest.mark.asyncio
async def test_wrong_key_returns_401(keyed):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(), key="not-the-key")
    assert _status_of(excinfo) == 401


# --- Request shape: phone is never taken from the caller -----------------------------------------


@pytest.mark.asyncio
async def test_caller_supplied_phone_field_is_ignored(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(
        voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead(whatsapp_phone="573009999999")
    )

    placed = {}

    async def _place_call(phone, twiml):
        placed["phone"] = phone
        return "CAxxxx"

    monkeypatch.setattr(voice_outbound_endpoints.twilio_client, "place_call", _place_call)

    # A caller-supplied `phone` must be silently ignored by pydantic's `extra = "ignore"` — it is
    # not even a declared field, so passing it must not raise and must not affect the call.
    request = OutboundCallRequest(lead_id="lead-1", tenant_id="tenant-1", phone="573001111111")

    result = await _call(request)

    assert result.placed is True
    assert placed["phone"] == "573009999999", "the resolved crm_leads number must be used, never the caller's"


# --- Non-goal guard: B2B leads are refused --------------------------------------------------------


@pytest.mark.asyncio
async def test_business_interest_lead_is_refused(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(
        voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead(lead_type="business_interest")
    )

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())

    assert _status_of(excinfo) == 403


# --- Lead / tenant resolution ----------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_lead_returns_404(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(voice_outbound_endpoints, "_get_lead_for_call", lambda _id: None)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 404


@pytest.mark.asyncio
async def test_mismatched_tenant_id_returns_404(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(
        voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead(tenant_id="other-tenant")
    )

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 404


# --- Twilio not configured -------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_twilio_not_configured_returns_503(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead())
    monkeypatch.setattr(settings, "TWILIO_ACCOUNT_SID", "")

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 503


# --- No phone --------------------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_phone_reports_not_placed(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(
        voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead(whatsapp_phone=None)
    )

    result = await _call(_request())
    assert result.placed is False
    assert result.reason == "no_phone"


# --- Happy path + generic-voice guarantee ----------------------------------------------------------


@pytest.mark.asyncio
async def test_happy_path_places_call_with_generic_voice(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead())

    captured = {}

    async def _place_call(phone, twiml):
        captured["phone"] = phone
        captured["twiml"] = twiml
        return "CAxxxx"

    monkeypatch.setattr(voice_outbound_endpoints.twilio_client, "place_call", _place_call)

    result = await _call(_request())

    assert result.placed is True
    assert result.call_sid == "CAxxxx"
    assert captured["phone"] == "573001234567"
    # Twilio's own generic <Say> voice, never Tatiana's cloned VoiceBox profile.
    assert '<Say voice="Polly.Lupe"' in captured["twiml"]
    assert "voicebox" not in captured["twiml"].lower()


@pytest.mark.asyncio
async def test_default_flag_never_uses_cloned_voice(keyed, monkeypatch):
    """spec.md: 'With VOICE_OUTBOUND_CALLS_ENABLED unset or false, any outbound call synthesizes
    speech with a generic voice profile, never Tatiana's cloned voice.'"""
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    assert settings.VOICE_OUTBOUND_CALLS_ENABLED is False

    monkeypatch.setattr(voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead())

    captured = {}

    async def _place_call(phone, twiml):
        captured["twiml"] = twiml
        return "CAxxxx"

    monkeypatch.setattr(voice_outbound_endpoints.twilio_client, "place_call", _place_call)

    await _call(_request())

    assert "Polly" in captured["twiml"]


@pytest.mark.asyncio
async def test_enabling_voice_outbound_calls_does_not_touch_whatsapp_voice_flag(keyed, monkeypatch):
    """design.md Decision 2 / spec.md: toggling VOICE_OUTBOUND_CALLS_ENABLED must never affect
    VOICE_ENABLED (WhatsApp voice notes) and vice versa."""
    monkeypatch.setattr(settings, "VOICE_ENABLED", True)
    monkeypatch.setattr(settings, "VOICE_OUTBOUND_CALLS_ENABLED", True)

    assert settings.VOICE_ENABLED is True
    assert settings.VOICE_OUTBOUND_CALLS_ENABLED is True

    monkeypatch.setattr(settings, "VOICE_OUTBOUND_CALLS_ENABLED", False)
    assert settings.VOICE_ENABLED is True, "flipping the outbound-call flag must not affect VOICE_ENABLED"


@pytest.mark.asyncio
async def test_call_failure_reports_not_placed(keyed, monkeypatch):
    import presentation.voice_outbound_endpoints as voice_outbound_endpoints

    monkeypatch.setattr(voice_outbound_endpoints, "_get_lead_for_call", lambda _id: _lead())

    async def _place_call_fails(phone, twiml):
        return None

    monkeypatch.setattr(voice_outbound_endpoints.twilio_client, "place_call", _place_call_fails)

    result = await _call(_request())
    assert result.placed is False
    assert result.reason == "call_failed"
