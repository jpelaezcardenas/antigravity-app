"""Copywriter agent for the Sell Machine creative loop (sell-machine-creative-swarm, Change E).

Generates marketing hooks and rewrites rejected ones (paired with agents/content_evaluator.py's
Critic, orchestrated by services/sell_machine_service.py).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = (
    "Eres el equipo de copywriting de Contexia (GPS Financiero para PyMEs colombianas, NO una "
    "firma contable regulada). Genera hooks de marketing cortos: headline + body (1-2 lineas) + "
    "CTA, en espanol, tono humano y empatico tipo 'amiga contadora con criterio', enfocados en "
    "dolores fiscales reales (multas DIAN, declarar tarde, no saber si toca declarar). "
    "Responde en JSON como una lista de objetos {\"headline\", \"body\", \"cta\", \"pain_tag\"}."
)

_DETERMINISTIC_FALLBACK_HOOKS: List[Dict[str, Any]] = [
    {
        "headline": "¿Sabes si te toca declarar renta este año?",
        "body": "Miles de personas no se enteran hasta que llega la sanción de la DIAN.",
        "cta": "Habla con Taty y salé de dudas",
        "pain_tag": "no_sabe_si_declara",
    },
    {
        "headline": "Declarar tarde te puede costar mucho más de lo que crees",
        "body": "Las multas de la DIAN crecen rápido. Mejor prevenir que pagar de más.",
        "cta": "Averigua tu situación hoy",
        "pain_tag": "multa_dian",
    },
    {
        "headline": "Tu contador no siempre te avisa a tiempo",
        "body": "Nosotros sí: te acompañamos paso a paso para que no se te pase nada.",
        "cta": "Empieza gratis",
        "pain_tag": "falta_acompanamiento",
    },
]


def _llm_generate_hooks(count: int) -> List[Dict[str, Any]]:
    """Isolated so tests can patch this single call point without needing LLM credentials."""
    from agents.llm_engine import get_llm_engine

    llm_engine = get_llm_engine()
    prompt = f"Genera {count} hooks de marketing distintos."
    response = llm_engine.get_ai_response_with_profile(
        prompt=prompt,
        profile_name="social-ops-v1",
        system_prompt=_SYSTEM_PROMPT,
        response_format="json",
        max_tokens=1200,
        temperature=0.8,
    )
    if isinstance(response, dict) and "hooks" in response:
        return response["hooks"]
    if isinstance(response, list):
        return response
    raise ValueError(f"Unexpected hook-generation response shape: {type(response)}")


def _llm_rewrite_hook(hook: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Isolated so tests can patch this single call point without needing LLM credentials."""
    from agents.llm_engine import get_llm_engine

    llm_engine = get_llm_engine()
    prompt = (
        f"Reescribe este hook para corregir: {reason}\n"
        f"Headline: {hook.get('headline')}\nBody: {hook.get('body')}\nCTA: {hook.get('cta')}"
    )
    response = llm_engine.get_ai_response_with_profile(
        prompt=prompt,
        profile_name="social-ops-v1",
        system_prompt=_SYSTEM_PROMPT,
        response_format="json",
        max_tokens=400,
        temperature=0.6,
    )
    return response


def generate_hooks(count: int = 5) -> List[Dict[str, Any]]:
    """Generate `count` marketing hooks. Falls back to a deterministic hook set (never errors)
    if the LLM engine is unavailable."""
    try:
        hooks = _llm_generate_hooks(count)
        if hooks:
            return hooks
    except Exception as exc:
        logger.warning("copywriter_service: LLM unavailable, using deterministic fallback: %s", exc)

    return _DETERMINISTIC_FALLBACK_HOOKS[:count] or _DETERMINISTIC_FALLBACK_HOOKS


def rewrite_hook(hook: Dict[str, Any], reason: str) -> Dict[str, Any]:
    """Rewrite a single rejected hook once, addressing `reason`. Falls back to returning the
    original hook unchanged if the LLM engine is unavailable (never errors)."""
    try:
        rewritten = _llm_rewrite_hook(hook, reason)
        if rewritten:
            return rewritten
    except Exception as exc:
        logger.warning("copywriter_service: rewrite unavailable, keeping original hook: %s", exc)

    return hook
