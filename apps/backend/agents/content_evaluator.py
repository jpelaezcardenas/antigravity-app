"""Content Critic (evaluator-optimizer) for the Sell Machine creative loop
(sell-machine-creative-swarm, Change E).

NOT related to agents/agent_critic.py (a deterministic double-entry accounting balance
validator) — this module scores marketing hooks against Contexia's brand/tone rubric.

The brand rubric itself (system prompt, hard-ban phrases, Claim Ledger) lives in
agents/brand_rubric.py (brand-voice-canonization) — a single tracked module shared with
services/copywriter_service.py, rather than defined inline here. See that module's docstring for
why it's hardcoded rather than read from the untracked ai-specs/social-content-ops/ folder.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from agents.brand_rubric import BRAND_RUBRIC_SYSTEM_PROMPT, HARD_BAN_PHRASES, check_claims

logger = logging.getLogger(__name__)

# Re-exported name kept for backward compatibility with any existing import of the old inline
# constant's name.
_HARD_BAN_PHRASES = HARD_BAN_PHRASES


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

    Returns {"approved": bool, "reason": str}. The hard-ban check and the Claim Ledger both run
    first and can only reject, never be overridden by an LLM's "approved: true" — they are
    non-overridable gates. If the LLM call fails, Modo A rejects fail-closed so the hook cannot
    reach the Approval Queue without a complete Content Critic evaluation.
    """
    hard_ban_reason = _hard_ban_violation(hook)
    if hard_ban_reason:
        return {"approved": False, "reason": hard_ban_reason}

    claim_ledger_reason = check_claims(hook)
    if claim_ledger_reason:
        return {"approved": False, "reason": claim_ledger_reason}

    try:
        llm_result = _llm_tone_check(hook)
        approved = bool(llm_result.get("approved"))
        reason = str(llm_result.get("reason") or ("Passed brand rubric" if approved else "Rejected by tone check"))
        return {"approved": approved, "reason": reason}
    except Exception as exc:
        # Modo A es fail-closed: sin evaluación completa no se puede entregar el hook a la
        # Approval Queue. Los checks deterministas previos siguen rechazando hard-bans y claims.
        logger.warning("content_evaluator: LLM tone check unavailable; rejecting fail-closed: %s", exc)
        return {"approved": False, "reason": "Content Critic unavailable; held for review (fail-closed)."}
