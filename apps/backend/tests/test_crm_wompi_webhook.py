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


class TestHandleWompiWebhook:
    def test_valid_signature_upserts_transaction_status(self):
        client = MagicMock()
        upserted = {}

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_wompi_transactions":
                def _upsert(payload, **kwargs):
                    upserted.update(payload)
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    return r
                m.upsert.side_effect = _upsert
            return m

        client.table.side_effect = table_side_effect
        event = _event(status="APPROVED", txn_id="wompi-txn-1")

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            result = CrmService().handle_wompi_webhook(event)

        assert upserted["wompi_transaction_id"] == "wompi-txn-1"
        assert upserted["status"] == "APPROVED"
        assert upserted["reference"] == "lead-l1-1719000000"
        assert result["status"] == "APPROVED"

    def test_invalid_signature_is_rejected_without_writing(self):
        client = MagicMock()

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_wompi_transactions":
                m.upsert.side_effect = AssertionError("must not write on an invalid signature")
            return m

        client.table.side_effect = table_side_effect
        event = _event(status="APPROVED", txn_id="wompi-txn-1")
        event["data"]["transaction"]["status"] = "DECLINED"  # tamper after checksum computed

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            with pytest.raises(PermissionError):
                CrmService().handle_wompi_webhook(event)

    def test_duplicate_delivery_is_idempotent(self):
        client = MagicMock()
        upsert_calls = []

        def table_side_effect(name):
            m = MagicMock()
            if name == "crm_wompi_transactions":
                def _upsert(payload, **kwargs):
                    upsert_calls.append(payload)
                    r = MagicMock()
                    r.execute.return_value = MagicMock(data=[payload])
                    return r
                m.upsert.side_effect = _upsert
            return m

        client.table.side_effect = table_side_effect
        event = _event(status="APPROVED", txn_id="wompi-txn-1")

        with patch("services.crm_service.get_service_supabase", return_value=client), _patched_env(), _patched_events_secret():
            CrmService().handle_wompi_webhook(event)
            CrmService().handle_wompi_webhook(event)

        # Both deliveries call upsert (DB-level unique index enforces no duplicate row);
        # the handler itself must be safe to call twice with the same payload.
        assert len(upsert_calls) == 2
        assert upsert_calls[0] == upsert_calls[1]
