"""
Unit tests for Agent Critic (double-entry validator).
"""

import sys
import pytest
from pathlib import Path

# Add backend to path to avoid __init__.py import issues
sys.path.insert(0, str(Path(__file__).parent.parent / "apps" / "backend"))

from agents.agent_critic import validate_journal_entry


def test_balanced_entry_passes():
    """Balanced entry with equal débitos and créditos."""
    entry = {
        "lines": [
            {"account": "1105", "debit": 1000000, "credit": 0},
            {"account": "2105", "debit": 0, "credit": 1000000},
        ],
        "memo": "DIAN correction",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is True
    assert reason == "Entry balanced ✓"


def test_unbalanced_entry_fails():
    """Unbalanced entry with débitos != créditos."""
    entry = {
        "lines": [
            {"account": "1105", "debit": 1000000, "credit": 0},
            {"account": "2105", "debit": 0, "credit": 900000},  # 100k short
        ],
        "memo": "Wrong amount",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is False
    assert "Unbalanced" in reason
    assert "1000000" in reason  # débitos
    assert "900000" in reason  # créditos


def test_empty_entry_fails():
    """Empty entry with no lines."""
    entry = {
        "lines": [],
        "memo": "Empty",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is False
    assert "Empty" in reason


def test_all_zeros_fails():
    """Entry with all zero débitos and créditos."""
    entry = {
        "lines": [
            {"account": "1105", "debit": 0, "credit": 0},
            {"account": "2105", "debit": 0, "credit": 0},
        ],
        "memo": "All zeros",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is False
    assert "Empty" in reason


def test_multiple_lines_balanced():
    """Multiple lines that balance correctly."""
    entry = {
        "lines": [
            {"account": "1105", "debit": 500000, "credit": 0},
            {"account": "1110", "debit": 500000, "credit": 0},
            {"account": "2105", "debit": 0, "credit": 700000},
            {"account": "2110", "debit": 0, "credit": 300000},
        ],
        "memo": "Complex transaction",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is True
    assert reason == "Entry balanced ✓"


def test_string_amounts_coerced():
    """String amounts are coerced to numeric."""
    entry = {
        "lines": [
            {"account": "1105", "debit": "1000000", "credit": "0"},
            {"account": "2105", "debit": "0", "credit": "1000000"},
        ],
        "memo": "String amounts",
    }
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is True
    assert reason == "Entry balanced ✓"


def test_missing_lines_key_fails():
    """Entry with missing 'lines' key."""
    entry = {"memo": "No lines"}
    is_valid, reason = validate_journal_entry(entry)
    assert is_valid is False
    assert "Empty" in reason
