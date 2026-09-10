"""Opening script + qualification flow for Taty's outbound calls (taty-voice-outbound-calls,
Task 4).

Colombian AI-disclosure law — NOT CONFIRMED (Task 4.1)
-------------------------------------------------------
This session has no access to a legal database and could not confirm the exact Colombian
requirement for disclosing that an outbound sales call is placed by an AI (the Superintendencia de
Industria y Comercio / Habeas Data framework governs Contexia elsewhere in this repo, but this
specific question — AI disclosure on an outbound call — was not verified against a primary
source here). Per design.md's own risk mitigation, the SAFE DEFAULT is used regardless of what
that confirmation would show: the opening always states, explicitly, that the caller is an AI
assistant. Do not remove this disclosure without first closing the Open Question in design.md.

Generic voice only, by default
-------------------------------
This script is spoken via Twilio's own built-in `<Say>` TTS (a real, non-cloned, generic voice) —
see `presentation/voice_outbound_endpoints.py::_build_twiml`. Nothing in this module, or in that
function under any `VOICE_OUTBOUND_CALLS_ENABLED` state, references Tatiana's cloned VoiceBox
profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

# The exact sentence that satisfies the AI-disclosure requirement (Task 4.1's safe default).
# Must appear before the first question — enforced by tests/test_voice_call_script.py.
AI_DISCLOSURE_SENTENCE = "soy un asistente de inteligencia artificial"

# Opening turn: identity -> AI disclosure -> reason (<=10 words) -> question. Never price/plan/offer.
OPENING_SCRIPT = (
    "Hola, te habla Taty de Contexia. Quiero ser transparente: "
    f"{AI_DISCLOSURE_SENTENCE}, no una persona. "
    "Te llamo por tu declaración de renta. "
    "¿Tienes un minuto para contarme en qué punto estás?"
)


def build_opening_script() -> str:
    """Returns the opening turn spoken at the start of every outbound call."""
    return OPENING_SCRIPT


@dataclass(frozen=True)
class QualificationQuestion:
    key: str
    text: str


# situacion -> problema -> urgencia, capped at exactly 3 questions per call (spec.md: "A single
# outbound call SHALL ask at most 3 qualification questions... It SHALL NOT continue past 3
# questions in one call.").
QUALIFICATION_QUESTIONS: List[QualificationQuestion] = [
    QualificationQuestion(
        key="situacion",
        text="Para entender tu situación: ¿ya declaraste renta antes o sería tu primera vez?",
    ),
    QualificationQuestion(
        key="problema",
        text="¿Qué es lo que más te ha complicado o preocupado de tu declaración de renta?",
    ),
    QualificationQuestion(
        key="urgencia",
        text="¿Para cuándo necesitas tener esto resuelto?",
    ),
]

MAX_QUALIFICATION_QUESTIONS = len(QUALIFICATION_QUESTIONS)


def next_qualification_question(answered_count: int) -> Optional[QualificationQuestion]:
    """Returns the next question to ask given how many have already been answered in this call,
    or None once the cap (3) has been reached — the call must proceed to a close/handoff instead
    of a fourth question."""
    if answered_count < 0:
        raise ValueError("answered_count must be zero or positive")
    if answered_count >= MAX_QUALIFICATION_QUESTIONS:
        return None
    return QUALIFICATION_QUESTIONS[answered_count]


VALID_CALL_OUTCOMES = ("qualified", "not_interested", "callback_requested", "voicemail")
