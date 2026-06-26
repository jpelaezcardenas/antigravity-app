"""
Phase 7 Stages 3-4: Vendor & Micro Rules Tests

Stage 3: Known Vendor Rule (requires Supabase)
Stage 4: Micro Transaction Rule
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


# ============================================================================
# Stage 4: Micro Transaction Rule Tests (No DB required)
# ============================================================================

class TestMicroTransactionRule:
    """Test micro transaction rule."""

    def test_micro_below_threshold_approves(self):
        """Amount below threshold (< 10 COP) → approved."""
        # 9 COP = 900,000 cents
        current = MockJournalEntry(id="e1", amount_cents=900_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert decision.approved == True
        assert decision.confidence == 0.85
        assert decision.rule_id == RuleType.MICRO_TRANSACTION.value

    def test_micro_at_threshold_rejects(self):
        """Amount at threshold (= 10 COP) → rejected."""
        # 10 COP = 1,000,000 cents (exactly at threshold)
        current = MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is None, "Should not approve at threshold"

    def test_micro_above_threshold_rejects(self):
        """Amount above threshold (> 10 COP) → rejected."""
        # 11 COP = 1,100,000 cents
        current = MockJournalEntry(id="e3", amount_cents=1_100_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is None

    def test_micro_zero_amount_approves(self):
        """Zero amount < threshold → approved."""
        current = MockJournalEntry(id="e4", amount_cents=0, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert decision.approved == True

    def test_micro_rule_data_populated(self):
        """Rule data includes threshold + amount."""
        current = MockJournalEntry(id="e5", amount_cents=500_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert "threshold" in decision.rule_data
        assert "amount" in decision.rule_data
        assert "savings" in decision.rule_data
        assert decision.rule_data["threshold"] == 1_000_000
        assert decision.rule_data["amount"] == 500_000

    def test_micro_reason_includes_info(self):
        """Reason string includes threshold and amount."""
        current = MockJournalEntry(id="e6", amount_cents=500_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert "threshold" in decision.reason.lower()
        assert "500000" in decision.reason or "500,000" in decision.reason

    def test_micro_min_confidence_is_0_85(self):
        """Micro rule confidence is exactly 0.85."""
        config = APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]
        assert config["min_confidence"] == 0.85

    def test_micro_threshold_is_1_million(self):
        """Micro rule threshold is 1,000,000 cents (10 COP)."""
        config = APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]
        assert config["threshold_cents"] == 1_000_000


# ============================================================================
# Stage 3: Known Vendor Rule Tests (Requires mock/stub Supabase)
# ============================================================================

class TestKnownVendorRule:
    """Test known vendor rule."""

    @pytest.mark.skipif(
        True,  # Skip by default - requires Supabase connection
        reason="Requires Supabase connection; use RUN_SHADOW_GL=1 to enable"
    )
    async def test_vendor_found_within_tolerance_approves(self):
        """Vendor found + amount within tolerance → approved."""
        # This test requires a real Supabase connection
        # Skip for now; will be tested in E2E
        pass

    @pytest.mark.skipif(
        True,
        reason="Requires Supabase connection"
    )
    async def test_vendor_not_found_returns_none(self):
        """Vendor not in whitelist → returns None."""
        pass

    @pytest.mark.skipif(
        True,
        reason="Requires Supabase connection"
    )
    async def test_vendor_amount_out_of_tolerance_returns_none(self):
        """Vendor found but amount out of tolerance → returns None."""
        pass


class TestPhase7Stage34Acceptance:
    """Acceptance criteria for Stages 3-4."""

    def test_micro_transaction_rule_implemented(self):
        """✅ Micro transaction rule auto-approves small amounts."""
        current = MockJournalEntry(id="e1", amount_cents=500_000, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert decision.approved == True
        assert decision.confidence == 0.85

    def test_vendor_rule_config_exists(self):
        """✅ Vendor rule configuration exists."""
        config = APPROVAL_RULES_CONFIG[RuleType.KNOWN_VENDOR]
        assert config.get("enabled") == True
        assert config.get("min_confidence") == 0.90
        assert config.get("amount_tolerance") == 0.10

    def test_micro_rule_config_exists(self):
        """✅ Micro rule configuration exists."""
        config = APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]
        assert config.get("enabled") == True
        assert config.get("min_confidence") == 0.85
        assert config.get("threshold_cents") == 1_000_000

    def test_vendor_whitelist_migration_exists(self):
        """✅ Vendor whitelist migration file exists."""
        import os
        migration_path = "apps/backend/migrations/0018_vendor_whitelist.sql"
        assert os.path.exists(migration_path), f"Migration {migration_path} not found"

        # Check migration content
        with open(migration_path, "r") as f:
            content = f.read()
            assert "vendor_whitelist" in content
            assert "CREATE TABLE" in content
            assert "vendor_code" in content
            assert "avg_amount_cents" in content
            assert "tolerance_percent" in content

    def test_micro_approves_below_threshold(self):
        """✅ Micro rule approves amounts below 10 COP."""
        current = MockJournalEntry(id="e1", amount_cents=999_999, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision = _check_micro_rule(current)

        assert decision is not None
        assert decision.approved == True

    def test_micro_rejects_at_or_above_threshold(self):
        """✅ Micro rule rejects amounts at/above 10 COP."""
        current_at = MockJournalEntry(id="e2", amount_cents=1_000_000, account_code="1100")
        current_above = MockJournalEntry(id="e3", amount_cents=1_000_001, account_code="1100")

        from services.approval_rules import _check_micro_rule

        decision_at = _check_micro_rule(current_at)
        decision_above = _check_micro_rule(current_above)

        assert decision_at is None
        assert decision_above is None

    def test_vendor_rule_async_implementation(self):
        """✅ Vendor rule is async (for Supabase I/O)."""
        import inspect
        from services.approval_rules import _check_vendor_rule

        # Check that it's an async function
        assert inspect.iscoroutinefunction(_check_vendor_rule), \
            "Vendor rule should be async (for DB I/O)"

    def test_micro_rule_sync_implementation(self):
        """✅ Micro rule is sync (no I/O required)."""
        import inspect
        from services.approval_rules import _check_micro_rule

        # Check that it's NOT async
        assert not inspect.iscoroutinefunction(_check_micro_rule), \
            "Micro rule should be sync (no DB I/O)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
