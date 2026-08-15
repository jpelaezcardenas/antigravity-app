"""Turns an `operator_tasks` row into the Manus `message.content` string.

Pure functions only — no I/O — so every task_type is unit-testable without network (design.md D4).

Load-bearing rule: for side-effecting task types (post_content, run_ads_ab) the prompt states
explicitly that the copy is ALREADY APPROVED BY A HUMAN and must be published as written. Manus
must not rewrite it — the Approval Queue already gated exactly that text, and silently improving
it would publish something the founder never approved.
"""

from __future__ import annotations

import json
from typing import Any, Dict

# Mirrors services/operator_task_service.py. Kept as a literal (not imported) because this local
# service deploys independently of the backend.
SIDE_EFFECTING_TASK_TYPES = {"post_content", "run_ads_ab"}

_APPROVED_BANNER = (
    "IMPORTANTE: el contenido de abajo YA FUE APROBADO por un humano en el sistema de Contexia. "
    "Publícalo tal cual está escrito. NO reescribas, NO 'mejores' y NO cambies cifras, precios ni "
    "datos de contacto. Si algo te parece incorrecto, DETENTE y repórtalo en vez de publicarlo."
)

_NO_INVENTION_BANNER = (
    "No inventes cifras fiscales, precios ni datos de contacto. Si un dato no está en el payload, "
    "dilo explícitamente en tu resultado en vez de rellenarlo."
)


def _pretty(payload: Dict[str, Any]) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False, indent=2)
    except (TypeError, ValueError):
        return str(payload)


def build_manus_title(task: Dict[str, Any]) -> str:
    """Short, human-scannable title for the Manus task list."""
    task_type = task.get("task_type", "unknown")
    task_id = str(task.get("id", ""))[:8]
    return f"Contexia · {task_type} · {task_id}"


def build_manus_prompt(task: Dict[str, Any]) -> str:
    """Build the Manus prompt for one operator task."""
    task_type = task.get("task_type", "")
    payload = task.get("payload") or {}
    body = _pretty(payload)

    if task_type == "post_content":
        return (
            f"{_APPROVED_BANNER}\n\n"
            "Tarea: publicar este paquete de campaña en las redes de Contexia "
            "(Facebook e Instagram).\n\n"
            f"Paquete aprobado:\n{body}\n\n"
            "Al terminar, reporta: URL de cada publicación, hora de publicación y cualquier error."
        )

    if task_type == "run_ads_ab":
        return (
            f"{_APPROVED_BANNER}\n\n"
            "Tarea: montar una campaña de Meta Ads con prueba A/B usando los hooks aprobados.\n"
            "Respeta EXACTAMENTE el presupuesto indicado en `budget_cents` (está en centavos de "
            "COP). No lo aumentes bajo ninguna circunstancia.\n\n"
            f"Paquete aprobado:\n{body}\n\n"
            "Al terminar, reporta: id de campaña, ids de cada variante, presupuesto realmente "
            "configurado, y métricas iniciales si están disponibles."
        )

    if task_type == "research" and "creative_brief" in payload:
        return (
            f"{_NO_INVENTION_BANNER}\n\n"
            "Tarea de investigación creativa para Contexia (manus-first-creative-pipeline): "
            "investiga tendencias, dolores reales y contexto normativo DIAN vigente relevantes al "
            f"siguiente brief, y produce ganchos de marketing.\n\nBrief:\n{body}\n\n"
            "IMPORTANTE: entrega tu resultado final como salida estructurada (structured output) "
            "en este formato JSON exacto, sin texto adicional fuera del JSON:\n"
            '{"hooks": [{"headline": "...", "body": "...", "cta": "...", "pain_tag": "..."}]}\n'
            "Cada hook debe tener headline, body, cta y pain_tag. No inventes cifras fiscales ni "
            "de contacto — si no encuentras un dato con fuente confiable, omítelo del hook."
        )

    if task_type == "research":
        return (
            f"{_NO_INVENTION_BANNER}\n\n"
            f"Tarea de investigación para Contexia:\n{body}\n\n"
            "Entrega un resumen accionable con fuentes citadas."
        )

    if task_type == "metrics_pull":
        return (
            f"{_NO_INVENTION_BANNER}\n\n"
            f"Tarea: extraer estas métricas y devolverlas estructuradas:\n{body}\n\n"
            "Devuelve los números crudos y la fecha de corte de cada uno."
        )

    if task_type == "generate_doc":
        return (
            f"{_NO_INVENTION_BANNER}\n\n"
            f"Tarea: generar este documento operativo para Contexia:\n{body}\n\n"
            "Entrega el documento terminado y lista cualquier supuesto que hayas tenido que hacer."
        )

    if task_type == "external_integration":
        return (
            f"{_NO_INVENTION_BANNER}\n\n"
            f"Tarea de integración externa (solo lectura/configuración, sin publicar nada):\n{body}\n\n"
            "Reporta qué se conectó y qué quedó pendiente."
        )

    # Unknown type: hand it over verbatim and make the ambiguity explicit rather than guessing
    # an interpretation that could cause an unintended external action.
    return (
        f"{_NO_INVENTION_BANNER}\n\n"
        f"Tarea de Contexia de tipo '{task_type}' (tipo no reconocido por el poller).\n"
        f"Payload:\n{body}\n\n"
        "No ejecutes ninguna acción con efecto externo (publicar, pautar, gastar). "
        "Describe qué harías y detente."
    )
