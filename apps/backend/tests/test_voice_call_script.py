"""Tests for core/voice_call_script.py (taty-voice-outbound-calls, Task 4)."""

from __future__ import annotations

import pytest

from core.voice_call_script import (
    AI_DISCLOSURE_SENTENCE,
    MAX_QUALIFICATION_QUESTIONS,
    build_opening_script,
    next_qualification_question,
)

_MONETARY_WORDS = ("$", "cop", "precio", "plan", "oferta", "pago", "costo", "gratis", "descuento")


class TestOpeningScript:
    def test_discloses_ai_identity(self):
        script = build_opening_script()
        assert AI_DISCLOSURE_SENTENCE in script.lower()

    def test_disclosure_comes_before_the_question(self):
        script = build_opening_script().lower()
        disclosure_pos = script.index(AI_DISCLOSURE_SENTENCE)
        question_pos = script.index("?")
        assert disclosure_pos < question_pos

    def test_no_monetary_or_offer_language_in_the_opening(self):
        script = build_opening_script().lower()
        for word in _MONETARY_WORDS:
            assert word not in script, f"opening turn must not mention {word!r}"

    def test_opening_ends_with_a_question(self):
        script = build_opening_script().strip()
        assert script.endswith("?")


class TestQualificationFlow:
    def test_caps_at_three_questions(self):
        assert MAX_QUALIFICATION_QUESTIONS == 3

    def test_returns_the_three_questions_in_situation_problem_urgency_order(self):
        q1 = next_qualification_question(0)
        q2 = next_qualification_question(1)
        q3 = next_qualification_question(2)
        assert [q1.key, q2.key, q3.key] == ["situacion", "problema", "urgencia"]

    def test_a_fourth_question_is_never_returned(self):
        assert next_qualification_question(3) is None

    def test_rejects_a_negative_answered_count(self):
        with pytest.raises(ValueError):
            next_qualification_question(-1)
