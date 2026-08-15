"""Brand voice rubric for the Sell Machine creative loop (brand-voice-canonization).

Single tracked source for the Content Critic's (agents/content_evaluator.py) and the
Copywriter's (services/copywriter_service.py) brand rules, so both import from here instead of
each maintaining its own copy. Condensed from ai-specs/social-content-ops/content_ops_rules.md
Sections 7-8, hardcoded here rather than read from that folder at runtime because it is untracked
in git and would not exist in a deployed environment (same reasoning as content_evaluator.py's
original Decision 4).

Also home of the Claim Ledger: a deterministic (non-LLM) check that rejects any hook citing a
peso or UVT figure that doesn't trace to a known constant in core.constants. This exists because
the LLM tone check alone cannot catch a wrong *fact* — POST-01-TOPES-RENTA-2026 shipped $471.000
as the minimum DIAN sanction (10x the 2024 UVT) instead of $523.740 (10x UVT_2026). A rubric that
only screens tone/identity would never have caught that.
"""

from __future__ import annotations

import re
from typing import Any, Dict

from core.constants import UMBRAL_PATRIMONIO_COP, UMBRAL_RENTA_COP, UVT_2025, UVT_2026

# Condensed from content_ops_rules.md Sec. 7 ("Never" rules — hard, LLM-independent gates) and
# Sec. 8 (humanizacion rules — the LLM-based tone check is guided by these, but they are not
# hard-coded as literal string bans since tone is contextual, unlike the identity claims here).
BRAND_RUBRIC_SYSTEM_PROMPT = (
    "Eres el Content Critic de Contexia (una empresa TIC/AAA, NO una firma contable regulada). "
    "Evalua el siguiente hook de marketing contra estas reglas:\n"
    "- NUNCA debe implicar que Contexia es una firma contable regulada, que firma estados "
    "financieros, o que presenta declaraciones tributarias en nombre del cliente.\n"
    "- Evitar jerga opaca o tono robotico/corporativo frio.\n"
    "- El tono debe ser humano, empatico, claro y estrategico (\"amiga contadora con criterio\").\n"
    "- Debe ser accionable, no solo conceptual.\n"
    "Responde en JSON: {\"approved\": true|false, \"reason\": \"<motivo breve>\"}."
)

# Hard-ban phrases: if any appear (case-insensitive) in a hook's text, it is rejected
# unconditionally, regardless of what the LLM tone check says. Non-overridable gate.
HARD_BAN_PHRASES = [
    "firma contable regulada",
    "firmamos tus estados financieros",
    "firmamos estados financieros",
    "presentamos tu declaracion de renta",
    "declaramos impuestos en tu nombre",
]

# Claim Ledger: known-value allowlist, derived from core.constants rather than duplicated here.
# The minimum-sanction figure (10x the current UVT, Art. 641 ET) is the one concrete multiple
# that has actually shipped in copy — pre-computed so a matching hook doesn't need to spell out
# the multiplication for the checker to recognize it.
_KNOWN_COP_VALUES = {
    UVT_2025,
    UVT_2026,
    10 * UVT_2025,
    10 * UVT_2026,
    UMBRAL_RENTA_COP,
    UMBRAL_PATRIMONIO_COP,
}

_PESO_PATTERN = re.compile(r"\$\s?([\d.,]+)")
_UVT_PATTERN = re.compile(r"(\d[\d.,]*)\s*UVT", re.IGNORECASE)

# claim-ledger-market-figures (2026-08-15): recognized Colombian market-research sources. A
# peso/UVT figure that isn't a known fiscal constant is still accepted if it's visibly cited
# alongside one of these — deliberately a small explicit allowlist, not "any parenthetical
# passes", which would defeat the gate. Extend by adding a name here, nothing else.
_RECOGNIZED_MARKET_SOURCES = [
    "CCCE",
    "DANE",
    "Camara de Comercio Aburra Sur",
    "Cámara de Comercio Aburrá Sur",
    "Colombia Fintech",
    "MinTIC",
    "Superintendencia de Sociedades",
]

# Matches a parenthetical group within ~40 chars after a figure, e.g. "$191.850 (−7,6% anual,
# CCCE)" — proximity-based, not full-sentence NLP (design.md Decision 2).
_NEARBY_CITATION_WINDOW = 40


def _has_nearby_citation(text: str, match_end: int) -> bool:
    """A figure counts as sourced if a recognized source name appears either right next to it
    (a `(... CCCE)`-style parenthetical within the proximity window) or anywhere else in the same
    hook text — Manus's real output cites a source once per paragraph covering several stats,
    not once per individual number (design.md Decision 2/3 accept this looseness; a fully
    unsourced hook with no recognized name anywhere still fails, see design.md Risks)."""
    window = text[match_end : match_end + _NEARBY_CITATION_WINDOW]
    paren_close = window.find(")")
    if paren_close != -1:
        citation_text = window[: paren_close + 1]
        if any(source in citation_text for source in _RECOGNIZED_MARKET_SOURCES):
            return True
    return any(source in text for source in _RECOGNIZED_MARKET_SOURCES)


def _parse_cop_number(raw: str) -> int | None:
    """Parses a Colombian-formatted peso figure ('523.740' or '523,740') into an int."""
    digits = re.sub(r"[.,]", "", raw)
    if not digits.isdigit():
        return None
    return int(digits)


def _hook_text(hook: Dict[str, Any]) -> str:
    return " ".join(str(hook.get(field) or "") for field in ("headline", "body", "cta"))


def check_claims(hook: Dict[str, Any]) -> str | None:
    """Deterministic numeric-claim gate: rejects any peso/UVT figure not in the known-value
    allowlist. Returns a rejection reason naming the unrecognized figure, or None if every
    peso/UVT claim in the hook is sourced (or the hook makes no such claim)."""
    text = _hook_text(hook)

    for match in _PESO_PATTERN.finditer(text):
        value = _parse_cop_number(match.group(1))
        if value is None:
            continue
        if value not in _KNOWN_COP_VALUES and not _has_nearby_citation(text, match.end()):
            return (
                f"Claim Ledger violation: unsourced peso figure '${match.group(1)}' does not "
                "match any known constant in core.constants and has no nearby recognized-source "
                "citation."
            )

    for match in _UVT_PATTERN.finditer(text):
        value = _parse_cop_number(match.group(1))
        if value is None:
            continue
        if value not in {UVT_2025, UVT_2026} and not _has_nearby_citation(text, match.end()):
            return (
                f"Claim Ledger violation: unsourced UVT figure '{match.group(1)} UVT' does not "
                "match UVT_2025 or UVT_2026 in core.constants and has no nearby recognized-source "
                "citation."
            )

    return None
