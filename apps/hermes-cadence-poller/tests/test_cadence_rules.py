"""cadence_rules.next_due_day — mirrors apps/backend/tests/test_cadence_schedule.py's coverage
of spec.md's three scenarios, at this package's own (deliberately duplicated) threshold table."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from cadence_rules import MAX_CADENCE_DAY, THRESHOLD_HOURS, next_due_day


def test_thresholds_match_the_backend_schedule_hours():
    """A silent drift here would only cause an extra (re-validated, harmless) call to the
    backend, never a wrongly-sent message — but it should still match by default."""
    assert THRESHOLD_HOURS == {1: 24, 2: 48, 4: 96, 7: 168, 14: 336}


def test_never_touched_lead_past_threshold_is_due_for_day_1():
    assert next_due_day(None, elapsed_hours=25) == 1


def test_never_touched_lead_under_threshold_is_not_due():
    assert next_due_day(None, elapsed_hours=5) is None


def test_day_1_lead_past_48h_is_due_for_day_2():
    assert next_due_day(1, elapsed_hours=49) == 2


def test_day_14_lead_is_never_due_again():
    assert next_due_day(14, elapsed_hours=100_000) is None


def test_max_cadence_day_is_14():
    assert MAX_CADENCE_DAY == 14
