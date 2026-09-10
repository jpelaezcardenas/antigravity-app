"""POST /internal/cadence/send-touch (taty-followup-cadence, part of taty-voice-outbound-calls —
ships and deploys independently of the telephony tasks in that change).

Mirrors tests/test_voice_endpoint_auth.py's shape: the endpoint coroutine is awaited directly
rather than driven through TestClient (httpx 0.28.1 removed the `app=` shortcut that starlette
0.27.0's TestClient still passes — pre-existing, unrelated to this change).
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from presentation.cadence_endpoints import SendTouchRequest, send_cadence_touch_endpoint

_KEY = "test-internal-key"


@pytest.fixture
def keyed(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", _KEY)


def _request(**overrides) -> SendTouchRequest:
    payload = {"lead_id": "lead-1", "day": 1}
    payload.update(overrides)
    return SendTouchRequest(**payload)


async def _call(request, key=_KEY):
    return await send_cadence_touch_endpoint(payload=request, x_internal_api_key=key)


def _status_of(excinfo) -> int:
    return excinfo.value.status_code


def _lead(**overrides):
    base = {
        "id": "lead-1",
        "stage": "NUEVOS",
        "whatsapp_phone": "573001234567",
        "cadence_day": None,
        "cadence_completed_at": None,
        "last_inbound_at": None,
        "created_at": "2020-01-01T00:00:00+00:00",  # far enough in the past to always be "due"
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


@pytest.mark.asyncio
async def test_auth_is_checked_before_day_validation(keyed):
    """An unauthenticated caller must not learn anything about the schedule via a 400."""
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(day=999), key="wrong")
    assert _status_of(excinfo) == 401


# --- Request validation --------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_day_outside_schedule_returns_400(keyed):
    with pytest.raises(HTTPException) as excinfo:
        await _call(_request(day=3))
    assert _status_of(excinfo) == 400


@pytest.mark.asyncio
async def test_unknown_lead_returns_404(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    monkeypatch.setattr(cadence_endpoints, "_get_lead_cadence_state", lambda _id: None)

    with pytest.raises(HTTPException) as excinfo:
        await _call(_request())
    assert _status_of(excinfo) == 404


# --- Eligibility / idempotency (soft-fail: 200, sent=False) --------------------------------------


@pytest.mark.asyncio
async def test_lead_past_nuevos_is_not_eligible(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    monkeypatch.setattr(
        cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead(stage="PROSPECTOS")
    )

    result = await _call(_request())
    assert result.sent is False
    assert result.reason == "not_eligible"


@pytest.mark.asyncio
async def test_completed_cadence_sends_no_further_touch(keyed, monkeypatch):
    """spec.md: 'A lead past day 14 with no response gets no further automated touches.'"""
    import presentation.cadence_endpoints as cadence_endpoints

    monkeypatch.setattr(
        cadence_endpoints,
        "_get_lead_cadence_state",
        lambda _id: _lead(cadence_day=14, cadence_completed_at="2026-01-01T00:00:00+00:00"),
    )

    result = await _call(_request(day=14))
    assert result.sent is False
    assert result.reason == "cadence_completed"


@pytest.mark.asyncio
async def test_already_sent_day_is_not_resent(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    monkeypatch.setattr(cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead(cadence_day=2))

    result = await _call(_request(day=1))
    assert result.sent is False
    assert result.reason == "already_sent"


@pytest.mark.asyncio
async def test_not_due_yet_is_refused(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints
    from datetime import datetime, timezone

    recent = datetime.now(timezone.utc).isoformat()
    monkeypatch.setattr(
        cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead(last_inbound_at=recent)
    )

    result = await _call(_request(day=1))
    assert result.sent is False
    assert result.reason == "not_due_yet"


@pytest.mark.asyncio
async def test_no_phone_reports_not_sent(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    monkeypatch.setattr(
        cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead(whatsapp_phone=None)
    )

    result = await _call(_request())
    assert result.sent is False
    assert result.reason == "no_phone"


@pytest.mark.asyncio
async def test_send_failure_reports_not_sent(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    async def _send_fails(_phone, _text):
        return False

    monkeypatch.setattr(cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead())
    monkeypatch.setattr(cadence_endpoints, "send_whatsapp_message", _send_fails)

    result = await _call(_request())
    assert result.sent is False
    assert result.reason == "send_failed"


# --- Happy path: the next scripted touch is sent and cadence position advances -------------------


@pytest.mark.asyncio
async def test_happy_path_sends_and_advances_cadence(keyed, monkeypatch):
    """spec.md: 'the next scripted WhatsApp message for that day is sent, and the lead's cadence
    position advances.'"""
    import presentation.cadence_endpoints as cadence_endpoints

    sent_calls = {}

    async def _send(phone, text):
        sent_calls["phone"] = phone
        sent_calls["text"] = text
        return True

    advance_calls = {}

    def _advance(lead_id, day):
        advance_calls["lead_id"] = lead_id
        advance_calls["day"] = day

    monkeypatch.setattr(cadence_endpoints, "_get_lead_cadence_state", lambda _id: _lead())
    monkeypatch.setattr(cadence_endpoints, "send_whatsapp_message", _send)
    monkeypatch.setattr(cadence_endpoints, "_advance_cadence", _advance)

    result = await _call(_request(day=1))

    assert result.sent is True
    assert sent_calls["phone"] == "573001234567"
    assert advance_calls == {"lead_id": "lead-1", "day": 1}


@pytest.mark.asyncio
async def test_advance_cadence_stamps_completion_on_day_14(keyed, monkeypatch):
    """Real DB-level behaviour of _advance_cadence, not mocked here."""
    import presentation.cadence_endpoints as cadence_endpoints

    mock_client = MagicMock()
    monkeypatch.setattr(cadence_endpoints, "get_service_supabase", lambda: mock_client)

    cadence_endpoints._advance_cadence("lead-1", 14)

    patch_arg = mock_client.table.return_value.update.call_args[0][0]
    assert patch_arg["cadence_day"] == 14
    assert "cadence_completed_at" in patch_arg


@pytest.mark.asyncio
async def test_advance_cadence_does_not_stamp_completion_before_day_14(keyed, monkeypatch):
    import presentation.cadence_endpoints as cadence_endpoints

    mock_client = MagicMock()
    monkeypatch.setattr(cadence_endpoints, "get_service_supabase", lambda: mock_client)

    cadence_endpoints._advance_cadence("lead-1", 1)

    patch_arg = mock_client.table.return_value.update.call_args[0][0]
    assert patch_arg["cadence_day"] == 1
    assert "cadence_completed_at" not in patch_arg
