"""Content Critic (evaluator-optimizer) for the Sell Machine creative loop
(sell-machine-creative-swarm, Change E).

NOT related to agents/agent_critic.py (a deterministic double-entry accounting balance
validator) — this module scores marketing hooks against Contexia's brand/tone rubric.

The brand rubric is hardcoded here (condensed from ai-specs/social-content-ops/content_ops_rules.md
Sections 7-8), rather than read from that folder at runtime, because that folder is untracked in
git and would not exist in a deployed environment (see design.md Decision 4).
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Condensed from content_ops_rules.md Sec. 7 ("Never" rules — hard, LLM-independent gates) and
# Sec. 8 (humanizacion rules — the LLM-based tone check below is guided by these, but they are
# not hard-coded as literal string bans since tone is contextual, unlike the identity claims here).
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
# unconditionally, regardless of what the LLM tone check says. This is a deliberate
# non-overridable gate (see design.md Decision 7 / Risk mitigation).
_HARD_BAN_PHRASES = [
    "firma contable regulada",
    "firmamos tus estados financieros",
    "firmamos estados financieros",
    "presentamos tu declaracion de renta",
    "declaramos impuestos en tu nombre",
]


def _hook_text(hook: Dict[str, Any]) -> str:
    return " ".join(
        str(hook.get(field) or "") for field in ("headline", "body", "cta")
    ).lower()


def _hard_ban_violation(hook: Dict[str, Any]) -> str | None:
    text = _hook_text(hook)
    for phrase in _HARD_BAN_PHRASES:
        if phrase in text:
            return f"Hard rule violation: hook text contains banned phrase '{phrase}'."
    return None


def _llm_tone_check(hook: Dict[str, Any]) -> Dict[str, Any]:
    """Isolated so tests can patch this single call point without needing LLM credentials."""
    from agents.llm_engine import get_llm_engine

    llm_engine = get_llm_engine()
    prompt = (
        f"Headline: {hook.get('headline')}\n"
        f"Body: {hook.get('body')}\n"
        f"CTA: {hook.get('cta')}"
    )
    response = llm_engine.get_ai_response_with_profile(
        prompt=prompt,
        profile_name="social-ops-v1",
        system_prompt=BRAND_RUBRIC_SYSTEM_PROMPT,
        response_format="json",
        max_tokens=200,
        temperature=0.3,
        required_keys={"approved", "reason"},
    )
    return response


def evaluate_hook(hook: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate a single hook against the brand rubric.

    Returns {"approved": bool, "reason": str}. The hard-ban check always runs first and can
    only reject, never approve past an LLM's "approved: true" — it is a non-overridable gate.
    If the LLM call fails, falls back to the hard-ban result alone (deterministic).
    """
    hard_ban_reason = _hard_ban_violation(hook)
    if hard_ban_reason:
        return {"approved": False, "reason": hard_ban_reason}

    try:
        llm_result = _llm_tone_check(hook)
        approved = bool(llm_result.get("approved"))
        reason = str(llm_result.get("reason") or ("Passed brand rubric" if approved else "Rejected by tone check"))
        return {"approved": approved, "reason": reason}
    except Exception as exc:
        logger.warning("content_evaluator: LLM tone check unavailable, using hard-ban-only fallback: %s", exc)
        return {"approved": True, "reason": "No hard-rule violations (LLM tone check unavailable)."}
