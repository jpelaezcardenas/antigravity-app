"""Day-indexed follow-up cadence schedule (taty-followup-cadence).

Adapted from Dapta's Lead Nurture playbook to Renta Natural, WhatsApp/text-only for this season
(design.md Decision 6 of taty-voice-outbound-calls) — no telephony, no `VOICE_OUTBOUND_CALLS_ENABLED`
dependency. D7's audio-summary idea from that playbook is explicitly OUT of scope here: it would
require `VOICE_ENABLED` and the voice-note send path, and this module stays text-only.

Single source of truth for both the threshold (hours since the lead's last inbound message) and
the message text a given cadence day sends. `presentation/cadence_endpoints.py` is the only
writer that ever advances `crm_leads.cadence_day`; the poller (`apps/hermes-cadence-poller/`)
keeps its own, deliberately duplicated, minimal notion of "is a day due" so it can decide what to
ask for without importing backend code across a process boundary — this module is where the
actual send is authorized and the actual copy lives.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class CadenceStep:
    threshold_hours: int
    message: str


# No pricing figure, no legal claim, no promise of a specific outcome — matches the discipline
# already enforced in taty_lead_router.py's RENTA_OFFER_CONTEXT / system prompt guardrails.
CADENCE_SCHEDULE: Dict[int, CadenceStep] = {
    1: CadenceStep(
        threshold_hours=24,
        message=(
            "¡Hola! Soy Taty, de Contexia 🙂 Vi que preguntaste por tu declaración de renta. "
            "¿Sigues por ahí? Cuéntame en qué te puedo ayudar."
        ),
    ),
    2: CadenceStep(
        threshold_hours=48,
        message=(
            "Hola de nuevo. Sé que a veces se enreda el tiempo — cuando quieras seguimos con tu "
            "declaración de renta, aquí estoy."
        ),
    ),
    4: CadenceStep(
        threshold_hours=96,
        message=(
            "Recordatorio amable: si todavía te toca declarar renta este año, entre antes "
            "empecemos, con más calma armamos todo. ¿Te ayudo a revisar tu caso?"
        ),
    ),
    7: CadenceStep(
        threshold_hours=168,
        message=(
            "Una última cosa: si en algún momento quieres retomar tu declaración de renta, solo "
            "escríbeme por aquí y seguimos donde quedamos."
        ),
    ),
    14: CadenceStep(
        threshold_hours=336,
        message=(
            "No quiero ser insistente, así que este es mi último mensaje por ahora. Si más "
            "adelante necesitas ayuda con tu declaración de renta, aquí sigo. ¡Que estés muy bien!"
        ),
    ),
}

MAX_CADENCE_DAY = max(CADENCE_SCHEDULE)


def next_due_day(current_day: int | None, elapsed_hours: float) -> int | None:
    """Returns the next cadence day that is due given the lead's current position and elapsed
    time since its anchor (last inbound message, or creation if it never replied).

    `current_day=None` means no touch has been sent yet. Returns None if nothing is due yet, or
    if `current_day` is already the last scheduled day (no further automated touch is ever due —
    the day-14-completion guarantee)."""
    if current_day is not None and current_day >= MAX_CADENCE_DAY:
        return None

    candidate_days = sorted(
        day
        for day, step in CADENCE_SCHEDULE.items()
        if (current_day is None or day > current_day) and elapsed_hours >= step.threshold_hours
    )
    return candidate_days[-1] if candidate_days else None
