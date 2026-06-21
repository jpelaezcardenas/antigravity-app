"""
Agent Critic: Deterministic validator for journal entry double-entry bookkeeping.

Validates that SUM(débitos) = SUM(créditos) before entries reach Approval Queue.
No LLM calls, deterministic, < 100ms per validation.
"""

from typing import Tuple, Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def validate_journal_entry(entry: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a journal entry follows double-entry bookkeeping rules.

    Args:
        entry: {
            "lines": [
                {"account": "1105", "debit": 1000000, "credit": 0, ...},
                {"account": "2105", "debit": 0, "credit": 1000000, ...},
            ],
            "memo": "DIAN correction",
            ...
        }

    Returns:
        (is_valid: bool, reason: str)
        - (True, "Entry balanced ✓") if SUM(débitos) == SUM(créditos) and > 0
        - (False, "Unbalanced: débitos=X, créditos=Y") if not balanced
        - (False, "Empty entry (no debits/credits)") if no lines or all zeros
    """
    try:
        lines = entry.get("lines", [])

        if not lines:
            return False, "Empty entry (no debits/credits)"

        total_debit = 0
        total_credit = 0

        for line in lines:
            debit = line.get("debit", 0)
            credit = line.get("credit", 0)

            # Coerce to float/int if needed
            if isinstance(debit, str):
                debit = float(debit)
            if isinstance(credit, str):
                credit = float(credit)

            total_debit += debit
            total_credit += credit

        # Check if balanced and non-empty
        if total_debit != total_credit:
            return (
                False,
                f"Unbalanced: débitos={total_debit}, créditos={total_credit}",
            )

        if total_debit == 0 and total_credit == 0:
            return False, "Empty entry (no debits/credits)"

        return True, "Entry balanced ✓"

    except Exception as e:
        logger.error(f"Agent Critic validation error: {str(e)}")
        return False, f"Validation error: {str(e)}"
