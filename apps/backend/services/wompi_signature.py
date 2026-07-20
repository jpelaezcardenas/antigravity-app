"""Wompi signature helpers (checkout integrity signature + webhook event checksum).

Pure functions, no I/O — see openspec/changes/wompi-payment-integration.

Wompi checksum reference: https://docs.wompi.co/docs/colombia/widget-checkout-web/#firma-de-integridad
"""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Sequence


def compute_integrity_signature(
    reference: str, amount_in_cents: int, currency: str, integrity_secret: str
) -> str:
    """Checkout integrity signature: SHA-256 of reference+amountInCents+currency+secret."""
    concatenated = f"{reference}{amount_in_cents}{currency}{integrity_secret}"
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


def _dig(data: Mapping[str, Any], dotted_path: str) -> Any:
    """Resolve a dotted path like 'transaction.id' against a nested dict."""
    value: Any = data
    for part in dotted_path.split("."):
        value = value[part]
    return value


def compute_event_checksum(event: Mapping[str, Any], events_secret: str) -> str:
    """Webhook event checksum: SHA-256 of the concatenated property values (in the
    order Wompi lists them in event['signature']['properties']) + timestamp + secret.
    """
    properties: Sequence[str] = event["signature"]["properties"]
    concatenated = "".join(str(_dig(event["data"], prop)) for prop in properties)
    concatenated += f"{event['timestamp']}{events_secret}"
    return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()


def verify_event_checksum(event: Mapping[str, Any], events_secret: str) -> bool:
    """True iff the event's checksum matches what we'd compute from its payload."""
    expected = compute_event_checksum(event, events_secret)
    actual = event.get("signature", {}).get("checksum", "")
    return isinstance(actual, str) and expected.lower() == actual.lower()
