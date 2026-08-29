"""Copywriter agent for the Sell Machine creative loop (sell-machine-creative-swarm, Change E).

Generates marketing hooks and rewrites rejected ones (paired with agents/content_evaluator.py's
Critic, orchestrated by services/sell_machine_service.py).

_SYSTEM_PROMPT below shares its brand rubric source with agents/content_evaluator.py via
agents/brand_rubric.py (brand-voice-canonization) rather than maintaining independent tone
guidance that could drift from what the Critic actually enforces.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from agents.brand_rubric import BRAND_RUBRIC_SYSTEM_PROMPT
from services.kb_seeding_service import retrieve_similar

logger = logging.getLogger(__name__)

_REQUIRED_HOOK_KEYS = {"headline", "body", "cta"}


def _well_shaped_hook(candidate: Any) -> Optional[Dict[str, Any]]:
    """Returns `candidate` if it's a dict with headline/body/cta, else None."""
    if isinstance(candidate, dict) and _REQUIRED_HOOK_KEYS <= set(candidate.keys()):
        return candidate
    return None

_GENERIC_GROUNDING_QUERY = (
    "margen real dropshipping ecommerce, comisiones pasarelas devoluciones, "
    "ingresos por plataformas creadores, honorarios anticipos freelancers, "
    "caja disponible y separación plata personal negocio"
)

_SYSTEM_PROMPT = (
    "Eres el equipo de copywriting de Contexia: contadoras tituladas con licencia + tecnología "
    "para que los negocios entiendan su margen, caja e ingresos. Genera hooks de marketing cortos: "
    "headline + body (1-2 lineas) + CTA, en espanol (tuteo, nunca voseo), tono humano y empatico "
    "tipo 'amiga contadora con criterio'.\n"
    "\n"
    "Distribución objetivo por lote: 60% hooks de nicho/valor, 25% claridad financiera transversal "
    "y 15% protección/cumplimiento. Prioriza dropshippers/e-commerce, creadores y freelancers. "
    "La DIAN puede aparecer como contexto práctico, pero no como protagonista para provocar miedo. "
    "No abras con disclaimers regulatorios: el posicionamiento lidera con contadoras tituladas "
    "con licencia + tecnología.\n"
    "\n"
    "Sigue además esta rúbrica de marca:\n"
    f"{BRAND_RUBRIC_SYSTEM_PROMPT}\n"
    "Responde en JSON como una lista de objetos {\"headline\", \"body\", \"cta\", \"pain_tag\", \"hook_type\"}."
)

_DETERMINISTIC_FALLBACK_HOOKS: List[Dict[str, Any]] = [
    {
        "headline": "¿Dropshipper? ¿Cuánto margen te queda después de pasarela y devoluciones?",
        "body": "Contadoras tituladas con licencia + tecnología para separar venta, costos y plata disponible.",
        "cta": "Revisa tu margen antes de volver a comprar inventario",
        "pain_tag": "margen_dropshipping",
        "hook_type": "NICHO_VALOR",
    },
    {
        "headline": "Si eres creador, tus ingresos de varias plataformas necesitan una sola vista",
        "body": "Ordena lo que entra, lo que gastas y lo que realmente puedes retirar.",
        "cta": "Guarda esta idea y revisa tus ingresos por plataforma",
        "pain_tag": "ingresos_creador",
        "hook_type": "NICHO_VALOR",
    },
    {
        "headline": "Freelancer: ese anticipo no es plata libre todavía",
        "body": "Separa honorarios, gastos y compromisos antes de decidir cuánto puedes gastar.",
        "cta": "¿Qué parte de tus honorarios te cuesta más ordenar?",
        "pain_tag": "honorarios_freelance",
        "hook_type": "NICHO_VALOR",
    },
    {
        "headline": "Facturar más no siempre significa tener más plata disponible",
        "body": "Mira la diferencia entre venta bruta, comisiones, costos y caja real.",
        "cta": "Haz la cuenta con tus últimos 30 días",
        "pain_tag": "claridad_caja",
        "hook_type": "CLARIDAD_FINANCIERA",
    },
    {
        "headline": "Una obligación tributaria se planea mejor cuando conoces tu caja",
        "body": "La DIAN es contexto; la primera decisión es saber qué plata está comprometida.",
        "cta": "Revisa fechas y caja sin alarmismo",
        "pain_tag": "proteccion_cumplimiento",
        "hook_type": "PROTECCION_CUMPLIMIENTO",
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
    falls back to a niche/value query for dropshippers, creators and freelancers when no prior
    signal exists. DIAN is not the cold-start protagonist."""
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
    niche_count = round(count * 0.60)
    clarity_count = round(count * 0.25)
    protection_count = max(0, count - niche_count - clarity_count)
    prompt = (
        f"Genera exactamente {count} hooks de marketing distintos. "
        f"Distribución objetivo: {niche_count} NICHO_VALOR, {clarity_count} CLARIDAD_FINANCIERA "
        f"y {protection_count} PROTECCION_CUMPLIMIENTO."
    )
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
    original hook unchanged if the LLM engine is unavailable OR returns a malformed shape (never
    errors, never propagates a non-hook value downstream — copywriter-rewrite-shape-guard: found
    live 2026-08-15, _SYSTEM_PROMPT's array-response instruction can make the LLM wrap a single
    rewrite in a list, which used to crash evaluate_hooks() with AttributeError)."""
    try:
        rewritten = _llm_rewrite_hook(hook, reason)
        if isinstance(rewritten, list):
            rewritten = rewritten[0] if rewritten else None
        well_shaped = _well_shaped_hook(rewritten)
        if well_shaped is not None:
            return well_shaped
    except Exception as exc:
        logger.warning("copywriter_service: rewrite unavailable, keeping original hook: %s", exc)

    return hook
