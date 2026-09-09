"""`voice_allowed` on the WhatsApp lead-reply response (voicebox-local-voice-adoption).

Two things are asserted here, and the second matters more than the first:

1. `voice_allowed` reflects services/voice_safety.py's verdict.
2. The response stays ADDITIVE — every field the bridge already reads is present and unchanged.
   `apps/chatwoot-bridge/main.py` reads `reply`, `intent`, `confidence` and `persona_fields` from
   this payload; a change that dropped or renamed one of them would break WhatsApp replies for a
   feature that is switched off in production.

The gate is judged on the SANITISED text, because that is the text that would actually be spoken —
`sanitize_for_whatsapp` strips a "Fuentes: ..." footer and Markdown tables, which changes both the
length and whether a figure survives.

Nothing here patches `should_speak`: the point is to verify the wiring reaches the real gate
(ARCHITECTURE.md Decisión #22 — a test must not mock the boundary it claims to verify). Only the
router's own collaborators (lead lookup, LLM routing, phone lookup) are faked, since those are
genuinely other boundaries.

Two environment notes, both PRE-EXISTING and unrelated to this change:

* `TestClient` cannot be used anywhere in this repo right now: httpx 0.28.1 removed the `app=`
  shortcut that starlette 0.27.0's TestClient still passes, so constructing one raises
  `TypeError: Client.__init__() got an unexpected keyword argument 'app'`. These tests therefore
  await the endpoint coroutine directly, which exercises the same function the router calls.
* Importing `presentation.whatsapp_endpoints` takes ~5 minutes on this machine because module
  import triggers KB/pgvector seeding that tries every embedding provider and waits out their
  timeouts. That cost is paid once per session, not per test.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from presentation.whatsapp_endpoints import LeadReplyRequest, taty_lead_reply

# What the real router returns today, so a dropped field is visible.
_ROUTER_RESULT = {
    "intent": "sales_interest",
    "confidence": 0.91,
    "reply": "Hola, soy Taty. Con gusto te ayudo con tu declaracion de renta.",
    "persona_fields": {"es_asalariado": True},
    "stage": "PROSPECTOS",
}


@pytest.fixture
def voice_on(monkeypatch):
    """VOICE_ENABLED is False by default (the shipped production state), so any test asserting a
    speakable reply has to turn it on explicitly."""
    from config import settings

    monkeypatch.setattr(settings, "VOICE_ENABLED", True)


async def _reply(router_result: dict) -> dict:
    """Call the endpoint with its real gate wired in, faking only its collaborators."""
    with patch("presentation.whatsapp_endpoints.lead_exists", return_value=True), patch(
        "presentation.whatsapp_endpoints.route_lead_message", return_value=dict(router_result)
    ), patch("presentation.whatsapp_endpoints.get_lead_phone", return_value=None):
        return await taty_lead_reply(
            lead_id="lead-1",
            payload=LeadReplyRequest(text="hola", deliver=False),
            _user={"sub": "test-caller"},
        )


@pytest.mark.asyncio
async def test_response_keeps_every_pre_existing_field():
    body = await _reply(_ROUTER_RESULT)

    for field in ("intent", "confidence", "persona_fields", "stage"):
        assert body[field] == _ROUTER_RESULT[field], f"pre-existing field '{field}' changed"
    assert body["reply"]


@pytest.mark.asyncio
async def test_conversational_reply_is_voice_allowed(voice_on):
    body = await _reply(_ROUTER_RESULT)
    assert body["voice_allowed"] is True


@pytest.mark.asyncio
async def test_reply_carrying_a_figure_is_not_voice_allowed(voice_on):
    body = await _reply(dict(_ROUTER_RESULT, reply="Tu caja real de hoy es de $350.000."))
    assert body["voice_allowed"] is False


@pytest.mark.asyncio
async def test_voice_allowed_is_judged_after_sanitisation(voice_on):
    """A "Fuentes:" footer is stripped before sending, so it must not decide the verdict.

    Without sanitisation-first ordering, the trailing block's length would reject text the customer
    never hears.
    """
    long_footer = "\n\n**Fuentes**: " + ("norma DIAN 000193 de 2024, " * 20)
    body = await _reply(dict(_ROUTER_RESULT, reply=_ROUTER_RESULT["reply"] + long_footer))
    assert body["voice_allowed"] is True


@pytest.mark.asyncio
async def test_empty_reply_is_not_voice_allowed(voice_on):
    body = await _reply(dict(_ROUTER_RESULT, reply=""))
    assert body["voice_allowed"] is False


@pytest.mark.asyncio
async def test_voice_allowed_is_false_when_the_feature_is_off(monkeypatch):
    """Dark-launch certification for this endpoint.

    VOICE_ENABLED defaults to False, which is the shipped production state. With it off, a reply
    that the gate would happily allow must still report voice_allowed=false, so the bridge never
    synthesises audio the voice-note endpoint would reject with a 503 anyway. The backend is the
    single authoritative switch.
    """
    from config import settings

    monkeypatch.setattr(settings, "VOICE_ENABLED", False)

    body = await _reply(_ROUTER_RESULT)

    assert body["voice_allowed"] is False
    # And the reply itself is untouched — turning voice off never removes the text.
    assert body["reply"] == _ROUTER_RESULT["reply"]
