"""Tests for the Wompi webhook handler on crm_service (change wompi-payment-integration,
"Change C" for crm-b2c-sell-machine-cockpit's crm_wompi_transactions table).

Mocks the Supabase client entirely, mirroring test_crm_service_b2c_logic.py's approach.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.crm_service import CrmService
from services.wompi_signature import compute_event_checksum


def _patched_env():
    return patch(
        "os.getenv", side_effect=lambda k, *a: "x" if k in ("SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY") else None
    )


EVENTS_SECRET = "test_events_ENcUWtxwRr7paeUyLQhTeabexAEfqYUc"


def _event(status="APPROVED", txn_id="wompi-txn-1", reference="lead-l1-1719000000"):
    event = {
        "event": "transaction.updated",
        "data": {
            "transaction": {
                "id": txn_id,
                "status": status,
                "amount_in_cents": 8_900_000,
                "reference": reference,
            }
        },
        "signature": {
            "properties": ["transaction.id", "transaction.status", "transaction.amount_in_cents"],
            "checksum": "",
        },
        "timestamp": 1719000000,
    }
    event["signature"]["checksum"] = compute_event_checksum(event, EVENTS_SECRET)
    return event


def _patched_events_secret():
    return patch.object(__import__("config").settings, "WOMPI_EVENTS_SECRET", EVENTS_SECRET)


def _mock_update_table(captured_calls):
    """Build a crm_wompi_transactions table mock for the update().eq() chain,
    recording each (payload, reference) pair passed."""

    def table_side_effect(name):
        m = MagicMock()
        if name == "crm_wompi_transactions":
            def _update(payload):
                inner = MagicMock()

                def _eq(column, value):
                    assert column == "reference"
                    captured_calls.append((dict(payload), value))
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    return r

                inner.eq.side_effect = _eq
                return inner

            m.update.side_effect = _update
        return m

    return table_side_effect


class TestHandleWompiWebhook:
    def test_valid_signature_updates_transaction_status_by_reference(self):
        calls = []
        client = MagicMock()
        client.table.side_effect = _mock_update_table(calls)

        event = _event(status="APPROVED", txn_id="wompi-txn-1", reference="lead-l1-1719000000")

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            result = CrmService().handle_wompi_webhook(event)

        assert len(calls) == 1
        payload, reference = calls[0]
        assert payload["wompi_transaction_id"] == "wompi-txn-1"
        assert payload["status"] == "APPROVED"
        assert "tenant_id" not in payload  # must never attempt to set/overwrite tenant_id
        assert reference == "lead-l1-1719000000"
        assert result["status"] == "APPROVED"

    def test_invalid_signature_is_rejected_without_writing(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_wompi_transactions":
                m.update.side_effect = AssertionError("must not write on an invalid signature")
            return m

        client.table.side_effect = table_side_effect
        event = _event(status="APPROVED", txn_id="wompi-txn-1")
        event["data"]["transaction"]["status"] = "DECLINED"  # tamper after checksum computed

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            with pytest.raises(PermissionError):
                CrmService().handle_wompi_webhook(event)

    def test_duplicate_delivery_is_idempotent(self):
        calls = []
        client = MagicMock()
        client.table.side_effect = _mock_update_table(calls)

        event = _event(status="APPROVED", txn_id="wompi-txn-1")

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            CrmService().handle_wompi_webhook(event)
            CrmService().handle_wompi_webhook(event)

        # Both deliveries call update().eq("reference", ...); re-applying the
        # same UPDATE twice is naturally idempotent (no duplicate row, since
        # there's nothing to insert).
        assert len(calls) == 2
        assert calls[0] == calls[1]
