"""Day-indexed cadence thresholds (taty-followup-cadence) — deliberately duplicated from
apps/backend/core/cadence_schedule.py's `CADENCE_SCHEDULE` hours, NOT imported: this poller is a
separate local process/package and cannot import backend code across that boundary (same
constraint the gmail/siigo pollers already live with).

This module only needs to know WHICH day is due, never the message text — the backend endpoint
(`POST /internal/cadence/send-touch`) is the sole owner of the copy and re-validates the threshold
itself before sending, so a drift here only ever causes an extra (harmless, re-validated,
possibly refused) call, never a wrongly-sent message.
"""

from __future__ import annotations

from typing import Optional

# Hours since the lead's anchor (last_inbound_at, or created_at if it never replied) — must match
# apps/backend/core/cadence_schedule.py's CADENCE_SCHEDULE thresholds.
THRESHOLD_HOURS = {1: 24, 2: 48, 4: 96, 7: 168, 14: 336}
MAX_CADENCE_DAY = max(THRESHOLD_HOURS)


def next_due_day(current_day: Optional[int], elapsed_hours: float) -> Optional[int]:
    """Same rule as the backend's core.cadence_schedule.next_due_day: the furthest day the lead
    now qualifies for that it hasn't already been sent, or None if nothing is due (including a
    lead already at the last scheduled day — day-14 completion sends no further automated touch).
    """
    if current_day is not None and current_day >= MAX_CADENCE_DAY:
        return None

    candidates = sorted(
        day
        for day, threshold in THRESHOLD_HOURS.items()
        if (current_day is None or day > current_day) and elapsed_hours >= threshold
    )
    return candidates[-1] if candidates else None
