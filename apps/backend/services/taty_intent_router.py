"""
Taty's intent router (FASE 4, Slice 4, tasks 4.1–4.3).

Classifies a Telegram message's intent and routes it to the matching
read-only agent call. Taty never calls a write-capable endpoint directly —
status/risk intents resolve to Pulso Diario / Radar Predictivo reads only.

Low-confidence fallback (task 4.2) and sensitive-intent escalation to the
Approval Queue (task 4.3) are handled in this module.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from core.supabase_client import get_supabase
from services.pulso_diario_service import get_daily_summary
from services.radar_service import calculate_cashflow_forecast, calculate_risk_score

STATUS_KEYWORDS = ("cómo va", "como va", "estado", "resumen", "hoy", "status")
RISK_KEYWORDS = ("riesgo", "risk", "alerta", "peligro")
CORRECTION_KEYWORDS = ("arregla", "corrige", "fix", "ajusta", "modifica")

INTENT_CONFIDENCE_THRESHOLD = 0.6


async def enqueue_taty_escalation(tenant_id: str, message: str) -> Optional[str]:
    """
    Create a taty_escalation approval_queue entry for a sensitive request.

    Sensitive intents (corrections, changes) are escalated to the Approval Queue
    for human review instead of being executed directly.

    Args:
        tenant_id: UUID of the tenant
        message: The original user message describing the request

    Returns:
        str: ID of the created approval_queue entry, or None on error.
    """
    supabase = get_supabase()
    try:
        entry_id = str(uuid.uuid4())
        payload = {
            "tenant_id": tenant_id,
            "request": message,
            "escalation_reason": "User requested a sensitive action via Taty",
        }

        supabase.table("approval_queue").insert(
            {
                "id": entry_id,
                "draft_id": f"taty-escalation-{tenant_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "draft_type": "taty_escalation",
                "payload": payload,
                "status": "pending",
                "reason": f"Taty escalation: {message[:100]}",
                "vectorization_status": "pending",
                "created_at": datetime.utcnow().isoformat() + "Z",
            }
        ).execute()

        return entry_id
    except Exception as e:
        return None


def classify_intent(message: str) -> Tuple[str, float]:
    """
    Deterministic keyword-based intent classification.

    Returns:
        (intent, confidence) where intent is one of "status", "risk", "correction", "unknown".
    """
    message_lower = message.lower()

    if any(keyword in message_lower for keyword in CORRECTION_KEYWORDS):
        return "correction", 0.9
    if any(keyword in message_lower for keyword in RISK_KEYWORDS):
        return "risk", 0.8
    if any(keyword in message_lower for keyword in STATUS_KEYWORDS):
        return "status", 0.8

    return "unknown", 0.0


async def route_message(tenant_id: str, message: str) -> Dict[str, Any]:
    """
    Classify the message and dispatch to the matching read-only agent call or escalation.

    Low-confidence messages (intent='unknown', confidence=0.0) trigger a
    clarifying fallback with no agent call (task 4.2).

    Sensitive intents (intent='correction') create an approval_queue entry
    for human review without executing any write (task 4.3).

    Returns:
        {"intent": str, "confidence": float, "reply": str, "approval_id": Optional[str]}
    """
    intent, confidence = classify_intent(message)

    if intent == "status":
        summary = await get_daily_summary(tenant_id)
        reply = (
            f"Resumen del {summary['date']}: "
            f"DIAN facturado {summary['dian_total_minor']}, "
            f"discrepancias {summary['discrepancy_count']}."
        )
        return {"intent": intent, "confidence": confidence, "reply": reply, "approval_id": None}

    if intent == "risk":
        score = await calculate_risk_score(tenant_id)
        forecast = await calculate_cashflow_forecast(tenant_id)
        reply = f"Score de riesgo actual: {score}/100. Pronóstico de flujo a 30 días: {forecast}."
        return {"intent": intent, "confidence": confidence, "reply": reply, "approval_id": None}

    # Sensitive intent escalation (task 4.3): create approval_queue entry, no direct write
    if intent == "correction":
        approval_id = await enqueue_taty_escalation(tenant_id, message)
        reply = (
            f"Tu solicitud fue escalada para revisión por un humano. "
            f"ID de seguimiento: {approval_id}"
        )
        return {"intent": intent, "confidence": confidence, "reply": reply, "approval_id": approval_id}

    # Low-confidence fallback (task 4.2): clarifying reply, no agent call
    if intent == "unknown":
        reply = (
            "No estoy segura de tu pregunta. ¿Puedes aclarar si necesitas "
            "información sobre el estado actual (resumen del día) o sobre "
            "riesgos fiscales?"
        )
        return {"intent": intent, "confidence": confidence, "reply": reply, "approval_id": None}

    raise ValueError(f"No route implemented yet for intent={intent!r}")
