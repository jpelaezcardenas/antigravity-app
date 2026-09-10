"""Call outcome -> CrmService write path (taty-voice-outbound-calls, Task 4.4/4.5).

Design.md Decision 5: a completed call's outcome writes to `crm_leads` through the SAME
`CrmService` methods `taty_lead_router.py` already uses — no new "call outcomes" table, since from
the CRM's perspective a qualified lead is a qualified lead regardless of channel.

`record_call_outcome` is a plain function (not wired into any automatic scheduler/webhook in this
change — no call-status webhook exists yet) so a future call-status callback has a single place to
call once it exists.
"""

from __future__ import annotations

from typing import Any, Dict

from core.voice_call_script import VALID_CALL_OUTCOMES
from services.crm_service import get_crm_service

# "qualified" is the only outcome that advances the funnel stage. The other three leave the lead's
# current stage untouched and only stamp `lead_type` — mirroring `advance_lead`'s own
# "pass the current stage back, only change lead_type" convention (Decisión #16 in ARCHITECTURE.md).
_QUALIFIED_STAGE = "PROSPECTOS"


def record_call_outcome(lead_id: str, current_stage: str, outcome: str) -> Dict[str, Any]:
    """Writes a completed call's outcome to `crm_leads` via `CrmService.advance_lead`.

    A `voicemail` outcome only stamps `lead_type="voicemail"` on the lead's current stage — it does
    NOT place another call. There is no code anywhere in this module (or the endpoint that will
    eventually call it) that re-invokes the outbound-call trigger; a voicemail lead simply becomes
    eligible for the existing `taty-followup-cadence` machinery (Task 1), which reads `crm_leads`
    independently on its own schedule.
    """
    if outcome not in VALID_CALL_OUTCOMES:
        raise ValueError(f"Invalid call outcome {outcome!r}; must be one of {VALID_CALL_OUTCOMES}")

    crm_service = get_crm_service()
    target_stage = _QUALIFIED_STAGE if outcome == "qualified" else current_stage
    return crm_service.advance_lead(lead_id, target_stage, lead_type=outcome)
