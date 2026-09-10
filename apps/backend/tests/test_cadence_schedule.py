"""core/cadence_schedule.py — the day-indexed message table + due-day logic
(taty-followup-cadence, spec.md's three scenarios at the schedule level)."""

from __future__ import annotations

from core.cadence_schedule import CADENCE_SCHEDULE, MAX_CADENCE_DAY, next_due_day


def test_schedule_has_the_five_dapta_lead_nurture_days():
    assert set(CADENCE_SCHEDULE.keys()) == {1, 2, 4, 7, 14}


def test_no_message_mentions_a_price_or_promises_a_specific_outcome():
    """Same discipline as taty_lead_router.py's system-prompt guardrails: no invented figure."""
    forbidden = ("$", "%", "garantiz")
    for step in CADENCE_SCHEDULE.values():
        lowered = step.message.lower()
        assert not any(token in lowered for token in forbidden), step.message


class TestNextDueDaySilentLeadGetsNextScriptedTouch:
    """Scenario: A lead silent for the configured threshold receives the next scripted touch."""

    def test_never_touched_lead_past_24h_is_due_for_day_1(self):
        assert next_due_day(current_day=None, elapsed_hours=25) == 1

    def test_never_touched_lead_under_24h_is_not_due(self):
        assert next_due_day(current_day=None, elapsed_hours=5) is None

    def test_day_1_sent_lead_past_48h_is_due_for_day_2(self):
        assert next_due_day(current_day=1, elapsed_hours=49) == 2

    def test_day_1_sent_lead_under_48h_is_not_due_yet(self):
        assert next_due_day(current_day=1, elapsed_hours=30) is None

    def test_skips_straight_to_the_furthest_due_day_if_a_tick_was_missed(self):
        """If the poller didn't run for a while, the lead jumps to the latest day it actually
        qualifies for rather than replaying every skipped day."""
        assert next_due_day(current_day=None, elapsed_hours=200) == 7


class TestNextDueDayDayFourteenCompletionSendsNoFurtherTouch:
    """Scenario: A lead past day 14 with no response gets no further automated touches."""

    def test_day_14_lead_is_never_due_again_regardless_of_elapsed_time(self):
        assert next_due_day(current_day=14, elapsed_hours=10_000) is None

    def test_max_cadence_day_constant_matches_schedule(self):
        assert MAX_CADENCE_DAY == 14
