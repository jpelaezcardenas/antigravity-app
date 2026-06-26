"""
Phase 7: Automated Approval Rules

Heuristic-based rule engine for auto-approving low-risk accounting entries.
Replaces manual Hermes review for routine transactions.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class RuleType(Enum):
    """Available approval rules."""
    RECURRING_TRANSACTION = "RECURRING_TRANSACTION"
    KNOWN_VENDOR = "KNOWN_VENDOR"
    MICRO_TRANSACTION = "MICRO_TRANSACTION"


@dataclass
class ApprovalDecision:
    """Result of rule evaluation."""
    approved: bool
    rule_id: str
    rule_name: str
    confidence: float  # 0.0 - 1.0
    reason: str
    rule_data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate confidence score."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"Confidence must be 0.0-1.0, got {self.confidence}")


# Rule Configuration
# Thresholds are tuned to balance auto-approval rate (40-60%) vs false positive rate (<2%)

APPROVAL_RULES_CONFIG = {
    RuleType.RECURRING_TRANSACTION: {
        "enabled": True,
        "min_confidence": 0.95,
        "min_history": 3,
        "variance_tolerance": 0.02,  # 2% allowed variance
        "description": "Exact match to last 3 entries (same amount, account, vendor)"
    },
    RuleType.KNOWN_VENDOR: {
        "enabled": True,
        "min_confidence": 0.90,
        "amount_tolerance": 0.10,  # 10% allowed variance
        "description": "Vendor in whitelist + amount within tolerance"
    },
    RuleType.MICRO_TRANSACTION: {
        "enabled": True,
        "min_confidence": 0.85,
        "threshold_cents": 1_000_000,  # 10 COP
        "description": "Transaction below micro-transaction threshold"
    },
}

# Global fallback threshold
# If no rule matches or confidence < this, route to Hermes for human review
GLOBAL_MIN_CONFIDENCE = 0.85

# Rule evaluation order (first match wins)
RULE_EVALUATION_ORDER = [
    RuleType.RECURRING_TRANSACTION,
    RuleType.KNOWN_VENDOR,
    RuleType.MICRO_TRANSACTION,
]


class ApprovalRulesError(Exception):
    """Raised when rule evaluation fails."""


def get_rule_config(rule_type: RuleType) -> Dict[str, Any]:
    """Get configuration for a rule type."""
    return APPROVAL_RULES_CONFIG.get(rule_type, {})


def is_rule_enabled(rule_type: RuleType) -> bool:
    """Check if a rule is enabled."""
    config = get_rule_config(rule_type)
    return config.get("enabled", False)


def validate_confidence_score(score: float) -> bool:
    """Validate that confidence score is in valid range."""
    return 0.0 <= score <= 1.0


# ============================================================================
# Rule Implementations (Stages 2-4)
# ============================================================================
# Placeholder functions - implemented in subsequent stages

def _check_recurring_rule(
    tenant_id: str,
    entry: "JournalEntry",  # noqa: F821
    history: List["JournalEntry"]  # noqa: F821
) -> Optional[ApprovalDecision]:
    """
    Stage 2: Detect recurring transactions.

    Args:
        tenant_id: Tenant context
        entry: Current entry to evaluate
        history: Previous entries for comparison

    Returns:
        ApprovalDecision if entry matches last N entries (within tolerance)
        None if insufficient history or no match
    """
    config = get_rule_config(RuleType.RECURRING_TRANSACTION)

    # Check if rule is enabled
    if not config.get("enabled", False):
        return None

    # Need minimum history
    min_history = config.get("min_history", 3)
    if len(history) < min_history:
        return None  # Not enough data to detect pattern

    # Get last N entries
    last_entries = history[-min_history:]

    # Compare amounts
    amounts = [e.amount_cents for e in last_entries]
    min_amt = min(amounts)
    max_amt = max(amounts)

    # Calculate variance
    if min_amt == 0:
        variance = float('inf')
    else:
        variance = (max_amt - min_amt) / min_amt

    variance_tolerance = config.get("variance_tolerance", 0.02)

    # Check if current entry matches pattern
    if abs(entry.amount_cents - amounts[0]) / amounts[0] <= variance_tolerance:
        # Match found!
        min_confidence = config.get("min_confidence", 0.95)

        return ApprovalDecision(
            approved=True,
            rule_id=RuleType.RECURRING_TRANSACTION.value,
            rule_name="Recurring Transaction Match",
            confidence=min_confidence,
            reason=f"Matched last {min_history} entries (variance={variance:.2%})",
            rule_data={
                "matched_entries": [e.id for e in last_entries],
                "variance": variance,
                "min_amount": min_amt,
                "max_amount": max_amt,
            }
        )

    return None  # No match


async def _check_vendor_rule(
    tenant_id: str,
    entry: "JournalEntry",  # noqa: F821
    supabase_client
) -> Optional[ApprovalDecision]:
    """
    Stage 3: Check if vendor is whitelisted.

    Args:
        tenant_id: Tenant context
        entry: Current entry with vendor_code
        supabase_client: Supabase client for DB lookup

    Returns:
        ApprovalDecision if vendor found + amount within tolerance
        None if vendor not in whitelist or amount out of range
    """
    config = get_rule_config(RuleType.KNOWN_VENDOR)

    # Check if rule is enabled
    if not config.get("enabled", False):
        return None

    # Lookup vendor in whitelist
    try:
        result = (
            supabase_client.table("vendor_whitelist")
            .select("*")
            .eq("tenant_id", tenant_id)
            .eq("vendor_code", entry.vendor_code)
            .eq("enabled", True)
            .single()
            .execute()
        )

        if not result.data:
            return None  # Vendor not found or not enabled

        vendor = result.data

    except Exception as exc:
        logger.error(f"Error looking up vendor {entry.vendor_code}: {exc}")
        return None  # Fallback: not found

    # Check amount tolerance
    avg_amt = vendor.get("avg_amount_cents", 0)
    if avg_amt == 0:
        return None  # Invalid vendor data

    tolerance = vendor.get("tolerance_percent", 0.10)
    variance = abs(entry.amount_cents - avg_amt) / avg_amt

    if variance <= tolerance:
        # Match found!
        min_confidence = config.get("min_confidence", 0.90)

        return ApprovalDecision(
            approved=True,
            rule_id=RuleType.KNOWN_VENDOR.value,
            rule_name="Known Vendor Match",
            confidence=min_confidence,
            reason=f"Vendor {entry.vendor_code} ({vendor.get('vendor_name', '')}) "
                   f"whitelisted (amount within ±{tolerance:.0%})",
            rule_data={
                "vendor_name": vendor.get("vendor_name"),
                "avg_amount": avg_amt,
                "tolerance": tolerance,
                "variance": variance,
            }
        )

    return None  # Amount out of tolerance


def _check_micro_rule(
    entry: "JournalEntry"  # noqa: F821
) -> Optional[ApprovalDecision]:
    """
    Stage 4: Auto-approve micro transactions.

    Args:
        entry: Current entry with amount_cents

    Returns:
        ApprovalDecision if amount < threshold
        None otherwise
    """
    config = get_rule_config(RuleType.MICRO_TRANSACTION)

    # Check if rule is enabled
    if not config.get("enabled", False):
        return None

    threshold = config.get("threshold_cents", 1_000_000)

    if entry.amount_cents < threshold:
        min_confidence = config.get("min_confidence", 0.85)

        return ApprovalDecision(
            approved=True,
            rule_id=RuleType.MICRO_TRANSACTION.value,
            rule_name="Micro Transaction",
            confidence=min_confidence,
            reason=f"Transaction below threshold ({threshold} cents, "
                   f"amount={entry.amount_cents} cents)",
            rule_data={
                "threshold": threshold,
                "amount": entry.amount_cents,
                "savings": threshold - entry.amount_cents,
            }
        )

    return None  # Amount at or above threshold


# ============================================================================
# Rule Orchestration (Stage 5)
# ============================================================================

async def evaluate_auto_approval_rules(
    tenant_id: str,
    entry: "JournalEntry",  # noqa: F821
    history: List["JournalEntry"],  # noqa: F821
    supabase_client
) -> Optional[ApprovalDecision]:
    """
    Stage 5: Evaluate all rules in order.

    Returns:
        ApprovalDecision if any rule approves (first match wins)
        None if no rule matches or all return None
    """
    # Implemented in Stage 5
    pass


__all__ = [
    "RuleType",
    "ApprovalDecision",
    "ApprovalRulesError",
    "APPROVAL_RULES_CONFIG",
    "GLOBAL_MIN_CONFIDENCE",
    "RULE_EVALUATION_ORDER",
    "get_rule_config",
    "is_rule_enabled",
    "validate_confidence_score",
    "evaluate_auto_approval_rules",
]
