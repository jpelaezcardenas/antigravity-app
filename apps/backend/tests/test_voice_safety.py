"""Unit tests for services/voice_safety.py (voicebox-local-voice-adoption).

`should_speak` is a pure function: no network, no credentials, no Supabase. These tests call it
directly and never patch it — the boundary under test IS the function, and mocking it would test
nothing (ARCHITECTURE.md Decisión #22: a test must not mock the boundary it claims to verify).

Why the rejection classes exist at all: Decisión #19 recorded, in both a synthetic A/B and in real
production, that without KB grounding the model states fiscal figures with total confidence. A
figure that is written down stays quotable by the human operator; a figure that is spoken does not.
So the voice is allowed to be conversational and is not allowed to be numeric about money, rates,
UVT or deadlines.
"""

from __future__ import annotations

import pytest

from services.voice_safety import should_speak

DEFAULT_MAX_CHARS = 320


# --- Accepted: short, conversational, no fiscal claim -------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Hola, soy Taty. Con gusto te ayudo con tu declaracion de renta.",
        "Claro que si, cuentame un poco mas de tu situacion y te oriento.",
        "Perfecto, ya recibi tus documentos. Los estoy revisando.",
        "Buenos dias! En que te puedo ayudar hoy?",
        # A year is not a deadline and not an amount — it must not be rejected, otherwise almost
        # every real fiscal sentence becomes unspeakable.
        "Estoy revisando tu informacion del ano gravable 2025.",
    ],
)
def test_conversational_replies_are_speakable(text):
    assert should_speak(text, DEFAULT_MAX_CHARS) is True


# --- Rejected: empty ----------------------------------------------------------------------------

@pytest.mark.parametrize("text", ["", "   ", "\n\t "])
def test_empty_text_is_never_spoken(text):
    assert should_speak(text, DEFAULT_MAX_CHARS) is False


def test_none_is_never_spoken():
    """The caller reads an optional dict field; None must not raise."""
    assert should_speak(None, DEFAULT_MAX_CHARS) is False


# --- Rejected: too long -------------------------------------------------------------------------

def test_text_longer_than_max_chars_is_rejected():
    assert should_speak("a" * (DEFAULT_MAX_CHARS + 1), DEFAULT_MAX_CHARS) is False


def test_text_exactly_at_max_chars_is_accepted():
    assert should_speak("a" * DEFAULT_MAX_CHARS, DEFAULT_MAX_CHARS) is True


# --- Rejected: fiscal figures -------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        # Currency
        "Tu caja real de hoy es de $350.000.",
        "El honorario seria de 1.490.000 pesos mensuales.",
        "Son COP 250000 al mes.",
        # Percentages
        "Debes reservar el 19% para impuestos.",
        "La retencion es del 11 por ciento.",
        # UVT
        "Superaste las 1.400 UVT de ingresos.",
        "El tope son 1400 uvt para el ano gravable.",
        # Spelled magnitudes
        "Tus ventas de ayer fueron 120 mil.",
        "Facturaste 3 millones el mes pasado.",
        "Son cuatrocientos cincuenta mil pesos.",
    ],
)
def test_fiscal_figures_are_never_spoken(text):
    assert should_speak(text, DEFAULT_MAX_CHARS) is False


# --- Rejected: deadlines ------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Tu plazo vence el 28 de abril.",
        "Recuerda que la fecha limite es 15/04.",
        "Debes declarar antes del 09-10.",
    ],
)
def test_deadlines_are_never_spoken(text):
    assert should_speak(text, DEFAULT_MAX_CHARS) is False


# --- The module must not be able to be bypassed -------------------------------------------------

def test_module_has_no_disable_switch():
    """There is deliberately no env var or flag that turns the gate off.

    VOICE_ENABLED turns the whole feature off; nothing turns the gate off while voice is on. If
    someone adds one, this test should fail and force the conversation.
    """
    import services.voice_safety as voice_safety

    source_names = {name.upper() for name in dir(voice_safety)}
    for forbidden in ("VOICE_SAFETY_DISABLED", "SKIP_GATE", "BYPASS", "DISABLE_GATE"):
        assert forbidden not in source_names
