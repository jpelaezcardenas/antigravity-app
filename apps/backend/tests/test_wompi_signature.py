"""Tests for Wompi signature helpers (services/wompi_signature.py)."""
import hashlib

from services.wompi_signature import (
    compute_event_checksum,
    compute_integrity_signature,
    verify_event_checksum,
)


class TestComputeIntegritySignature:
    def test_matches_manual_sha256_concatenation(self):
        reference = "lead-abc123-1"
        amount_in_cents = 5_000_000
        currency = "COP"
        secret = "test_integrity_BoVQgAV82orYHL7KaCpQ4DJZ62LmVoHO"

        expected = hashlib.sha256(
            f"{reference}{amount_in_cents}{currency}{secret}".encode("utf-8")
        ).hexdigest()

        assert compute_integrity_signature(reference, amount_in_cents, currency, secret) == expected

    def test_different_amount_changes_signature(self):
        base = compute_integrity_signature("ref-1", 1000, "COP", "secret")
        other = compute_integrity_signature("ref-1", 2000, "COP", "secret")
        assert base != other

    def test_different_reference_changes_signature(self):
        base = compute_integrity_signature("ref-1", 1000, "COP", "secret")
        other = compute_integrity_signature("ref-2", 1000, "COP", "secret")
        assert base != other


def _sample_event(checksum: str) -> dict:
    return {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": "15493-1234567890-12345",
                "status": "APPROVED",
                "amount_in_cents": 5_000_000,
            }
        },
        "signature": {
            "properties": [
                "transaction.id",
                "transaction.status",
                "transaction.amount_in_cents",
            ],
            "checksum": checksum,
        },
        "timestamp": 1719000000,
    }


class TestComputeEventChecksum:
    def test_matches_manual_sha256_concatenation(self):
        secret = "test_events_ENcUWtxwRr7paeUyLQhTeabexAEfqYUc"
        event = _sample_event(checksum="placeholder")

        expected = hashlib.sha256(
            f"15493-1234567890-12345APPROVED5000000{event['timestamp']}{secret}".encode("utf-8")
        ).hexdigest()

        assert compute_event_checksum(event, secret) == expected


class TestVerifyEventChecksum:
    def test_valid_checksum_verifies(self):
        secret = "test_events_ENcUWtxwRr7paeUyLQhTeabexAEfqYUc"
        event = _sample_event(checksum="placeholder")
        event["signature"]["checksum"] = compute_event_checksum(event, secret)

        assert verify_event_checksum(event, secret) is True

    def test_tampered_status_fails_verification(self):
        secret = "test_events_ENcUWtxwRr7paeUyLQhTeabexAEfqYUc"
        event = _sample_event(checksum="placeholder")
        event["signature"]["checksum"] = compute_event_checksum(event, secret)

        # Attacker tampers with the transaction status after the checksum was computed.
        event["data"]["transaction"]["status"] = "DECLINED"

        assert verify_event_checksum(event, secret) is False

    def test_wrong_secret_fails_verification(self):
        event = _sample_event(checksum="placeholder")
        event["signature"]["checksum"] = compute_event_checksum(event, "correct_secret")

        assert verify_event_checksum(event, "wrong_secret") is False

    def test_missing_checksum_fails_verification(self):
        event = _sample_event(checksum="")
        assert verify_event_checksum(event, "any_secret") is False
