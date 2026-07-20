"""Copywriter agent for the Sell Machine creative loop (sell-machine-creative-swarm, Change E).

Generates marketing hooks and rewrites rejected ones (paired with agents/content_evaluator.py's
Critic, orchestrated by services/sell_machine_service.py).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from services.kb_seeding_service import retrieve_similar

logger = logging.getLogger(__name__)

_GENERIC_GROUNDING_QUERY = "declarar renta, multas DIAN, obligación tributaria"

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


def _format_telemetry_report(report: Dict[str, Any]) -> str:
    """Renders a telemetry report (sell-machine-telemetry-loop, Change G) as a short prompt
    section. Tolerant of an empty/thin report — never raises."""
    hook_performance = report.get("hook_performance") or {}
    funnel_snapshot = report.get("funnel_snapshot") or {}
    return (
        "\n\nContexto de desempeño previo (usa esto para mejorar, no lo repitas literal):\n"
        f"- Resultados de hooks por tipo: {hook_performance}\n"
        f"- Estado actual del embudo (Renta Natural): {funnel_snapshot}"
    )


def _build_grounding_query(report: Optional[Dict[str, Any]] = None) -> str:
    """Derives a KB retrieval query for hook grounding (copywriter-rag). Favors a report's
    hook_performance pain_tags when present (Change G feedback-loop flavor, design.md Decision 2);
    falls back to a generic DIAN-pains query for cold-start generation with no prior signal."""
    hook_performance = (report or {}).get("hook_performance") or {}
    if hook_performance:
        return ", ".join(hook_performance.keys())
    return _GENERIC_GROUNDING_QUERY


def _format_kb_grounding(chunks: List[Dict[str, Any]]) -> str:
    """Renders retrieved KB chunks as a labeled prompt section, mirroring
    _format_telemetry_report's style (copywriter-rag)."""
    content = "\n".join(chunk.get("content", "") for chunk in chunks)
    return f"\n\nContenido de referencia (basa los hooks en dolores fiscales reales):\n{content}"


def _llm_generate_hooks(count: int, report: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Isolated so tests can patch this single call point without needing LLM credentials."""
    from agents.llm_engine import get_llm_engine

    llm_engine = get_llm_engine()
    prompt = f"Genera {count} hooks de marketing distintos."
    if report:
        prompt += _format_telemetry_report(report)

    try:
        chunks = retrieve_similar(_build_grounding_query(report), "__global__", top_k=3)
    except Exception as exc:
        logger.warning("copywriter_service: KB retrieval unavailable, generating ungrounded: %s", exc)
        chunks = []
    if chunks:
        prompt += _format_kb_grounding(chunks)

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


def generate_hooks(count: int = 5, report: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Generate `count` marketing hooks. Falls back to a deterministic hook set (never errors)
    if the LLM engine is unavailable.

    `report` (sell-machine-telemetry-loop, Change G) is an optional prior-performance summary
    (see services.operator_task_service.list_completed_tasks / crm_service.get_funnel_snapshot)
    woven into the prompt as context. Omitting it (every pre-Change-G call site) leaves this
    function's behavior identical to before."""
    try:
        hooks = _llm_generate_hooks(count, report=report)
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
