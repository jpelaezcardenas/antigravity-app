"""Decides whether a Taty reply may be spoken aloud (voicebox-local-voice-adoption).

This module is the SINGLE owner of that decision. Its verdict travels to the local Chatwoot bridge
as an additive `voice_allowed` field on the `/channels/whatsapp/leads/{lead_id}/reply` response —
the bridge never re-derives the rule, so there is one place to audit and no way to drift.

Why it exists
-------------
ARCHITECTURE.md Decisión #19 recorded, twice (a synthetic A/B and then real production traffic),
that without KB grounding the model states fiscal figures and contact details with total
confidence. Text keeps a quotable record the human operator can correct in Chatwoot; speech does
not. So the voice is allowed to be conversational and is not allowed to be numeric about money,
rates, UVT, or deadlines. Those stay in the text reply, which is always sent — voice is additive
and never replaces it.

What this is NOT
----------------
Not a content-safety classifier. It does not try to detect abusive or off-topic input. Abuse is
prevented upstream: the voice only ever speaks a reply Taty generated for an identified lead, never
operator free-text. The Phase 0 incident where the cloned voice was made to read abusive text came
from typing directly into VoiceBox's own UI, which this code path cannot reach.

Pure function: no network, no credentials, no database.
"""

from __future__ import annotations

import re
from typing import Optional

# Any currency marker or an explicit peso/COP amount.
_CURRENCY = re.compile(r"\$|\bCOP\b|\bpesos?\b", re.IGNORECASE)

# "19%" and "once por ciento" alike.
_PERCENTAGE = re.compile(r"%|\bpor\s+ciento\b", re.IGNORECASE)

# UVT is always a fiscal magnitude in this domain.
_UVT = re.compile(r"\bUVT\b", re.IGNORECASE)

# Magnitudes spelled as words, whether preceded by digits ("120 mil") or by another word
# ("cuatrocientos cincuenta mil"). `millon` covers millón/millones once accents are folded.
_SPELLED_MAGNITUDE = re.compile(r"\b(mil|millon(?:es)?)\b", re.IGNORECASE)

# A day/month deadline: "15/04", "09-10", "28 de abril". Deliberately NOT matching a bare 4-digit
# year — "año gravable 2025" is context, not a due date, and rejecting it would silence almost
# every real fiscal sentence.
_NUMERIC_DEADLINE = re.compile(r"\b(0?[1-9]|[12]\d|3[01])\s*[/-]\s*(0?[1-9]|1[0-2])\b")
_MONTH_NAMES = (
    "enero|febrero|marzo|abril|mayo|junio|julio|"
    "agosto|septiembre|setiembre|octubre|noviembre|diciembre"
)
_NAMED_DEADLINE = re.compile(rf"\b\d{{1,2}}\s+de\s+({_MONTH_NAMES})\b", re.IGNORECASE)

_ACCENT_MAP = str.maketrans("áéíóúÁÉÍÓÚñÑ", "aeiouAEIOUnN")

_FISCAL_PATTERNS = (
    _CURRENCY,
    _PERCENTAGE,
    _UVT,
    _SPELLED_MAGNITUDE,
    _NUMERIC_DEADLINE,
    _NAMED_DEADLINE,
)


def should_speak(text: Optional[str], max_chars: int) -> bool:
    """True when `text` may be synthesised into a voice note.

    Rejects, in order: missing or blank text; text longer than `max_chars`; and any text carrying a
    fiscal claim — a currency marker, a percentage, a UVT reference, a spelled magnitude
    (mil/millones), or a day/month deadline.

    Fails closed: anything unexpected returns False. A missing voice note is a non-event; a spoken
    wrong figure is not.
    """
    if not text or not text.strip():
        return False

    if len(text) > max_chars:
        return False

    normalized = text.translate(_ACCENT_MAP)

    return not any(pattern.search(normalized) for pattern in _FISCAL_PATTERNS)
