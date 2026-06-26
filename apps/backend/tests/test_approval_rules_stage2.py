"""
Phase 7 Stage 2: Recurring Transaction Rule Tests

Tests for detecting recurring transactions (same amount, account, vendor).
"""

import pytest
from dataclasses import dataclass
from typing import Optional
from services.approval_rules import (
    RuleType,
    ApprovalDecision,
    APPROVAL_RULES_CONFIG,
)


# Mock JournalEntry for testing
@dataclass
class MockJournalEntry:
    """Mock entry for testing approval rules."""
    id: str
    amount_cents: int
    account_code: str
    vendor_code: str = "V001"
    date: str = "2026-06-25"


class TestRecurringTransactionRule:
    """Test recurring transaction detection."""

    def test_recurring_exact_match_all_three_approves(self):
        """Exact match on last 3 entries → approved (confidence=0.95)."""
        # Setup: 3 identical entries
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100", vendor_code="V001"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100", vendor_code="V001"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100", vendor_code="V001"),
        ]

        # Current entry matches exactly
        current = MockJournalEntry(id="e4", amount_cents=1_000_000, account_code="1100", vendor_code="V001")

        # Import here to avoid circular imports
        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        # Assertions
        assert decision is not None, "Decision should not be None"
        assert decision.approved == True, "Should approve exact match"
        assert decision.confidence == 0.95, f"Expected confidence 0.95, got {decision.confidence}"
        assert decision.rule_id == RuleType.RECURRING_TRANSACTION.value
        assert "RECURRING" in decision.rule_name.upper()

    def test_recurring_within_variance_tolerance_approves(self):
        """Within ±2% variance → approved."""
        # Setup: 3 entries with slight variance
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_010_000, account_code="1100"),  # +1%
            MockJournalEntry(id="e3", amount_cents=1_005_000, account_code="1100"),  # +0.5%
        ]

        # Current entry within tolerance
        current = MockJournalEntry(id="e4", amount_cents=1_002_000, account_code="1100")  # +0.2%

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is not None
        assert decision.approved == True

    def test_recurring_exceeds_variance_rejects(self):
        """Exceeds 2% variance → returns None."""
        # Setup: 3 entries with different amounts
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_100_000, account_code="1100"),  # +10%
            MockJournalEntry(id="e3", amount_cents=1_050_000, account_code="1100"),  # +5%
        ]

        # Current entry far from pattern
        current = MockJournalEntry(id="e4", amount_cents=2_000_000, account_code="1100")  # +100%

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is None, "Should reject large variance"

    def test_recurring_insufficient_history_returns_none(self):
        """Fewer than 3 entries → returns None (not enough data)."""
        # Setup: Only 2 previous entries
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
        ]

        current = MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is None, "Should return None with insufficient history"

    def test_recurring_empty_history_returns_none(self):
        """No history → returns None."""
        history = []
        current = MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is None

    def test_recurring_rule_data_populated(self):
        """Rule data includes matched entries and variance."""
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100"),
        ]
        current = MockJournalEntry(id="e4", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is not None
        assert "matched_entries" in decision.rule_data
        assert "variance" in decision.rule_data
        assert len(decision.rule_data["matched_entries"]) == 3
        assert decision.rule_data["variance"] == 0.0  # Exact match

    def test_recurring_reason_contains_variance_info(self):
        """Reason string includes variance percentage."""
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100"),
        ]
        current = MockJournalEntry(id="e4", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is not None
        assert "variance" in decision.reason.lower()

    def test_recurring_min_confidence_is_0_95(self):
        """Recurring rule confidence is exactly 0.95."""
        config = APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]
        assert config["min_confidence"] == 0.95

    def test_recurring_min_history_is_3(self):
        """Recurring rule requires minimum 3 entries."""
        config = APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]
        assert config["min_history"] == 3

    def test_recurring_variance_tolerance_is_2_percent(self):
        """Recurring rule allows 2% variance."""
        config = APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]
        assert config["variance_tolerance"] == 0.02


class TestPhase7Stage2Acceptance:
    """Acceptance criteria for Stage 2."""

    def test_recurring_rule_matches(self):
        """✅ Exact match on last 3 entries → approved."""
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100"),
        ]
        current = MockJournalEntry(id="e4", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is not None
        assert decision.approved == True
        assert decision.confidence == 0.95

    def test_recurring_rule_insufficient_history(self):
        """✅ Insufficient history → returns None."""
        history = [MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100")]
        current = MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is None

    def test_variance_tolerance_logic_correct(self):
        """✅ Variance calculation within tolerance."""
        # Exactly at 2% variance limit
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100"),
        ]
        current = MockJournalEntry(id="e4", amount_cents=1_020_000, account_code="1100")  # +2%

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision is not None
        assert decision.approved == True

    def test_approval_decision_populated_correctly(self):
        """✅ ApprovalDecision has all required fields."""
        history = [
            MockJournalEntry(id="e1", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100"),
            MockJournalEntry(id="e3", amount_cents=1_000_000, account_code="1100"),
        ]
        current = MockJournalEntry(id="e4", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_recurring_rule

        decision = _check_recurring_rule("test-tenant", current, history)

        assert decision.approved == True
        assert decision.rule_id == RuleType.RECURRING_TRANSACTION.value
        assert len(decision.rule_name) > 0
        assert decision.confidence == 0.95
        assert len(decision.reason) > 0
        assert isinstance(decision.rule_data, dict)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
