"""
Phase 7 Stage 1: Rule Design + Thresholds Tests

Validates rule taxonomy, configuration, and validation logic.
"""

import pytest
from enum import Enum
from services.approval_rules import (
    RuleType,
    ApprovalDecision,
    ApprovalRulesError,
    APPROVAL_RULES_CONFIG,
    GLOBAL_MIN_CONFIDENCE,
    RULE_EVALUATION_ORDER,
    get_rule_config,
    is_rule_enabled,
    validate_confidence_score,
)


class TestRuleType:
    """Test RuleType enum."""

    def test_rule_types_defined(self):
        """All 3 rule types exist."""
        assert RuleType.RECURRING_TRANSACTION.value == "RECURRING_TRANSACTION"
        assert RuleType.KNOWN_VENDOR.value == "KNOWN_VENDOR"
        assert RuleType.MICRO_TRANSACTION.value == "MICRO_TRANSACTION"

    def test_rule_type_count(self):
        """Exactly 3 rules defined."""
        rules = list(RuleType)
        assert len(rules) == 3


class TestApprovalDecision:
    """Test ApprovalDecision dataclass."""

    def test_create_approval_decision(self):
        """Create valid approval decision."""
        decision = ApprovalDecision(
            approved=True,
            rule_id="RECURRING_TRANSACTION",
            rule_name="Recurring Match",
            confidence=0.95,
            reason="Matched last 3 entries"
        )
        assert decision.approved == True
        assert decision.confidence == 0.95

    def test_approval_decision_with_rule_data(self):
        """ApprovalDecision includes rule_data."""
        decision = ApprovalDecision(
            approved=True,
            rule_id="RECURRING",
            rule_name="Test",
            confidence=0.95,
            reason="Test",
            rule_data={"matched_entries": ["e1", "e2", "e3"]}
        )
        assert decision.rule_data["matched_entries"] == ["e1", "e2", "e3"]

    def test_confidence_validation_0(self):
        """Confidence 0.0 is valid."""
        decision = ApprovalDecision(
            approved=False,
            rule_id="TEST",
            rule_name="Test",
            confidence=0.0,
            reason="No match"
        )
        assert decision.confidence == 0.0

    def test_confidence_validation_1(self):
        """Confidence 1.0 is valid."""
        decision = ApprovalDecision(
            approved=True,
            rule_id="TEST",
            rule_name="Test",
            confidence=1.0,
            reason="Perfect match"
        )
        assert decision.confidence == 1.0

    def test_confidence_validation_invalid_high(self):
        """Confidence > 1.0 raises error."""
        with pytest.raises(ValueError):
            ApprovalDecision(
                approved=True,
                rule_id="TEST",
                rule_name="Test",
                confidence=1.05,  # Invalid
                reason="Test"
            )

    def test_confidence_validation_invalid_low(self):
        """Confidence < 0.0 raises error."""
        with pytest.raises(ValueError):
            ApprovalDecision(
                approved=True,
                rule_id="TEST",
                rule_name="Test",
                confidence=-0.1,  # Invalid
                reason="Test"
            )


class TestApprovalRulesConfig:
    """Test rule configuration."""

    def test_all_rules_configured(self):
        """All 3 rules have configuration."""
        for rule_type in RuleType:
            assert rule_type in APPROVAL_RULES_CONFIG
            assert APPROVAL_RULES_CONFIG[rule_type] is not None

    def test_recurring_config_structure(self):
        """Recurring rule config has required fields."""
        config = APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]
        assert "enabled" in config
        assert "min_confidence" in config
        assert "min_history" in config
        assert "variance_tolerance" in config
        assert config["enabled"] == True
        assert config["min_confidence"] == 0.95
        assert config["min_history"] == 3
        assert config["variance_tolerance"] == 0.02

    def test_vendor_config_structure(self):
        """Known vendor rule config has required fields."""
        config = APPROVAL_RULES_CONFIG[RuleType.KNOWN_VENDOR]
        assert "enabled" in config
        assert "min_confidence" in config
        assert "amount_tolerance" in config
        assert config["enabled"] == True
        assert config["min_confidence"] == 0.90
        assert config["amount_tolerance"] == 0.10

    def test_micro_config_structure(self):
        """Micro transaction rule config has required fields."""
        config = APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]
        assert "enabled" in config
        assert "min_confidence" in config
        assert "threshold_cents" in config
        assert config["enabled"] == True
        assert config["min_confidence"] == 0.85
        assert config["threshold_cents"] == 1_000_000

    def test_confidence_thresholds_increasing_order(self):
        """Confidence thresholds ordered: Recurring > Vendor > Micro."""
        recurring = APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]["min_confidence"]
        vendor = APPROVAL_RULES_CONFIG[RuleType.KNOWN_VENDOR]["min_confidence"]
        micro = APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]["min_confidence"]

        # Recurring is most strict (0.95)
        # Vendor is medium (0.90)
        # Micro is most permissive (0.85)
        assert recurring > vendor > micro
        assert recurring == 0.95
        assert vendor == 0.90
        assert micro == 0.85

    def test_global_min_confidence_defined(self):
        """Global fallback threshold defined."""
        assert GLOBAL_MIN_CONFIDENCE == 0.85
        assert isinstance(GLOBAL_MIN_CONFIDENCE, float)


class TestRuleEvaluationOrder:
    """Test rule evaluation order."""

    def test_evaluation_order_defined(self):
        """Rule evaluation order has all 3 rules."""
        assert len(RULE_EVALUATION_ORDER) == 3
        assert RuleType.RECURRING_TRANSACTION in RULE_EVALUATION_ORDER
        assert RuleType.KNOWN_VENDOR in RULE_EVALUATION_ORDER
        assert RuleType.MICRO_TRANSACTION in RULE_EVALUATION_ORDER

    def test_recurring_first_in_order(self):
        """Recurring rule evaluated first (most strict)."""
        assert RULE_EVALUATION_ORDER[0] == RuleType.RECURRING_TRANSACTION

    def test_micro_last_in_order(self):
        """Micro rule evaluated last (most permissive)."""
        assert RULE_EVALUATION_ORDER[-1] == RuleType.MICRO_TRANSACTION


class TestHelperFunctions:
    """Test utility functions."""

    def test_get_rule_config_existing(self):
        """Get config for existing rule."""
        config = get_rule_config(RuleType.RECURRING_TRANSACTION)
        assert config["min_confidence"] == 0.95

    def test_get_rule_config_missing(self):
        """Get config for non-existent rule returns empty dict."""
        # Create a fake rule type that doesn't exist
        class FakeRule(Enum):
            NONEXISTENT = "NONEXISTENT"

        config = get_rule_config(FakeRule.NONEXISTENT)
        assert config == {}

    def test_is_rule_enabled(self):
        """Check if rule is enabled."""
        assert is_rule_enabled(RuleType.RECURRING_TRANSACTION) == True
        assert is_rule_enabled(RuleType.KNOWN_VENDOR) == True
        assert is_rule_enabled(RuleType.MICRO_TRANSACTION) == True

    def test_validate_confidence_score_valid(self):
        """Valid confidence scores pass validation."""
        assert validate_confidence_score(0.0) == True
        assert validate_confidence_score(0.5) == True
        assert validate_confidence_score(0.85) == True
        assert validate_confidence_score(0.95) == True
        assert validate_confidence_score(1.0) == True

    def test_validate_confidence_score_invalid(self):
        """Invalid confidence scores fail validation."""
        assert validate_confidence_score(-0.1) == False
        assert validate_confidence_score(1.05) == False
        assert validate_confidence_score(2.0) == False


class TestPhase7Stage1Acceptance:
    """Acceptance criteria for Stage 1."""

    def test_rule_type_enum_complete(self):
        """✅ RuleType enum defined with all rules."""
        assert len(list(RuleType)) == 3

    def test_approval_decision_dataclass_complete(self):
        """✅ ApprovalDecision dataclass created with validation."""
        # Should not raise
        decision = ApprovalDecision(
            approved=True,
            rule_id="TEST",
            rule_name="Test Rule",
            confidence=0.95,
            reason="Test"
        )
        assert decision.confidence == 0.95

    def test_approval_rules_config_documented(self):
        """✅ APPROVAL_RULES_CONFIG documented with thresholds."""
        assert len(APPROVAL_RULES_CONFIG) == 3
        for rule_type, config in APPROVAL_RULES_CONFIG.items():
            assert "enabled" in config
            assert "min_confidence" in config
            assert "description" in config

    def test_thresholds_justified(self):
        """✅ Confidence thresholds have rationale."""
        # Recurring=0.95 (exact match, very confident)
        # Vendor=0.90 (known vendor, fairly confident)
        # Micro=0.85 (small amount, ok risk)
        assert APPROVAL_RULES_CONFIG[RuleType.RECURRING_TRANSACTION]["min_confidence"] == 0.95
        assert APPROVAL_RULES_CONFIG[RuleType.KNOWN_VENDOR]["min_confidence"] == 0.90
        assert APPROVAL_RULES_CONFIG[RuleType.MICRO_TRANSACTION]["min_confidence"] == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
