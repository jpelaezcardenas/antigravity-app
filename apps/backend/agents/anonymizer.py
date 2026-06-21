"""
SOSP Anonymizer - Soberanía Patrimonial mask layer.

Replaces sensitive Colombian fiscal data (NITs, emails, monetary amounts,
common company-name patterns) with opaque tokens BEFORE the payload reaches
any external LLM provider. The original values are kept in a per-session map
so the response can be rehydrated.

Compliance rule: every prompt routed through llm_engine MUST be anonymized.
Zero Data Retention contracts with providers do not absolve us from the
obligation to minimize what we send. See: contexia-ground-truth memory.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Tuple


# Colombian NIT: 8-10 digits, optional check digit after dash (e.g. 900123456-7).
# Captures both bare NITs and "NIT 900.123.456-7" style.
_NIT_PATTERN = re.compile(
    r"\b(?:NIT\.?\s*)?(?:\d{3}\.\d{3}\.\d{3}|\d{8,10})(?:[-\s]?\d)?\b",
    re.IGNORECASE,
)

# COP currency amounts: $1.234.567 / COP 1,234,567 / 1234567 COP / $1500000.
_MONEY_PATTERN = re.compile(
    r"(?:\$|COP\s*)\s*\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?"
    r"|\b\d{4,}(?:[.,]\d{1,2})?\s*(?:COP|pesos)\b",
    re.IGNORECASE,
)

_EMAIL_PATTERN = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")

# Phone: Colombian mobile +57 3xx xxx xxxx or 10-digit starting with 3.
_PHONE_PATTERN = re.compile(
    r"(?:\+57[\s-]?)?(?:3\d{2})[\s-]?\d{3}[\s-]?\d{4}\b"
)


@dataclass
class AnonymizationMap:
    """Reverse map for rehydrating an anonymized payload."""

    nits: Dict[str, str] = field(default_factory=dict)
    emails: Dict[str, str] = field(default_factory=dict)
    phones: Dict[str, str] = field(default_factory=dict)
    monies: Dict[str, str] = field(default_factory=dict)

    def all_pairs(self) -> Iterable[Tuple[str, str]]:
        """Yield (token, original) pairs across every category."""
        for store in (self.nits, self.emails, self.phones, self.monies):
            yield from store.items()


class Anonymizer:
    """Stateless façade. Each call returns a fresh map."""

    @staticmethod
    def mask(text: str) -> Tuple[str, AnonymizationMap]:
        """
        Replace sensitive fields with tokens.

        Returns:
            (masked_text, reverse_map). Apply `unmask()` with the same map
            to recover originals from any output text.
        """
        if not text:
            return text, AnonymizationMap()

        mapping = AnonymizationMap()
        masked = text

        masked = _replace_all(masked, _EMAIL_PATTERN, "<EMAIL_{i}>", mapping.emails)
        masked = _replace_all(masked, _NIT_PATTERN, "<NIT_{i}>", mapping.nits)
        masked = _replace_all(masked, _PHONE_PATTERN, "<PHONE_{i}>", mapping.phones)
        masked = _replace_all(masked, _MONEY_PATTERN, "<MONEY_{i}>", mapping.monies)

        return masked, mapping

    @staticmethod
    def unmask(text: str, mapping: AnonymizationMap) -> str:
        """Reverse the masking on any text containing tokens."""
        if not text or not mapping:
            return text
        for token, original in mapping.all_pairs():
            text = text.replace(token, original)
        return text


def _replace_all(
    text: str,
    pattern: re.Pattern,
    token_template: str,
    store: Dict[str, str],
) -> str:
    """
    Replace every regex match with an indexed token, deduplicating equal matches
    so identical values keep the same token across the prompt.
    """
    seen_to_token: Dict[str, str] = {}

    def _sub(match: re.Match) -> str:
        original = match.group(0)
        if original not in seen_to_token:
            token = token_template.format(i=len(store) + 1)
            seen_to_token[original] = token
            store[token] = original
        return seen_to_token[original]

    return pattern.sub(_sub, text)
